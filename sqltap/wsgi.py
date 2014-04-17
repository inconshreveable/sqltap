from __future__ import absolute_import

import urlparse
from . import sqltap
try:
    import queue
except ImportError:
    import Queue as queue

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
        self.on = False
        self.collector = queue.Queue(0)
        self.stats = []
        self.profiler = sqltap.ProfilingSession(collect_fn=self.collector.put)

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path == self.path or path == self.path + '/':
            return self.render(environ, start_response)
        return self.app(environ, start_response)
    
    def start(self):
        if not self.on:
            self.on = True
            self.profiler.start()

    def stop(self):
        if self.on:
            self.on = False
            self.profiler.stop()

    def render(self, environ, start_response):
        verb = environ.get('REQUEST_METHOD', 'GET').strip().upper()
        if verb not in ('GET', 'POST'):
            start_response('405 Method Not Allowed', [
                ('Allow', 'GET, POST'),
                ('Content-Type', 'text/plain')
            ])
            return ['405 Method Not Allowed']

        # handle on/off switch
        if verb == 'POST':
            try:
                clen = int(environ.get('CONTENT_LENGTH', '0'))
            except ValueError:
                clen = 0
            body = urlparse.parse_qs(environ['wsgi.input'].read(clen))
            clear = body.get('clear', None)
            if clear:
              del self.stats[:]
              return self.render_response(start_response)

            turn = body.get('turn', ' ')[0].strip().lower()
            if turn not in ('on', 'off'):
                start_response('400 Bad Request',
                               [('Content-Type', 'text/plain')])
                return ['400 Bad Request: parameter "turn=(on|off)" required']
            if turn == 'on':
                self.start()
            else:
                self.stop()

        try:
            while True:
                self.stats.append(self.collector.get(block=False))
        except queue.Empty:
            pass

        return self.render_response(start_response)

    def render_response(self, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        html = sqltap.report(self.stats, middleware=self, template="wsgi.mako")
        return [html.encode('utf-8')]
