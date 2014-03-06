import os.path
import urlparse
import mako.template
import sqltap

class SQLTapMiddleware(object):
    """ SQLTap dashboard middleware for WSGI applications.

    For example, if you are using Flask::

        app.wsgi_app = SQLTapMiddleware(app.wsgi_app)

    And then you can use SQLTap dashboard from ``/__sqltap__`` page (this
    path prefix can be set by ``path`` parameter).

    :param app: A WSGI application object to be wrap.
    :param path: A path prefix for access. Default is `'/__sqltap__'`

    """

    def __init__(self, app, path='/__sqltap__'):
        self.app = app
        self.path = path.rstrip('/')
        self.report_path = self.path + '/report'
        self.mode = False

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path == self.path or path == self.path + '/':
            return self.sqltap_switch_app(environ, start_response)
        elif path == self.report_path or path == self.report_path + '/':
            return self.sqltap_report_app(environ, start_response)
        return self.app(environ, start_response)

    def sqltap_switch_app(self, environ, start_response):
        verb = environ.get('REQUEST_METHOD', 'GET').strip().upper()
        if verb not in ('GET', 'POST'):
            start_response('405 Method Not Allowed', [
                ('Allow', 'GET, POST'),
                ('Content-Type', 'text/plain')
            ])
            return ['405 Method Not Allowed']
        if verb == 'POST':
            try:
                clen = int(environ.get('CONTENT_LENGTH', '0'))
            except ValueError:
                clen = 0
            body = urlparse.parse_qs(environ['wsgi.input'].read(clen))
            turn = body.get('turn', '')[0].strip().lower()
            if turn not in ('on', 'off'):
                start_response('400 Bad Request',
                               [('Content-Type', 'text/plain')])
                return ['400 Bad Request: parameter "turn=(on|off)" required']
            self.mode = turn == 'on'
            if self.mode:
                sqltap.start()
            else:
                sqltap.stop()
        start_response('200 OK', [('Content-Type', 'text/html')])
        html = mako.template.Template(
            filename = os.path.join(os.path.dirname(__file__), 
                                    'templates', 'switch.mako')
        ).render(middleware=self)
        return [html.encode('utf-8')]

    def sqltap_report_app(self, environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        stat = sqltap.collect()
        html = sqltap.report(stat)
        return [html.encode('utf-8')]

