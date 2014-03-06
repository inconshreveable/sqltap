<html>
    <head>
        <title>SQLTap</title>

        <style type="text/css">
            p, pre, ul { margin: 0; padding: 0; }
            h1 { font-family: sans-serif; letter-spacing: 0.1em; font-size: 1.6em; }
            .page { width: 800px; margin: 0 auto; }
        </style>
   </head>

    <body>
        <div class="page">
            <h1>SQLTap</h1>
            <p>SQLTap is turned
                % if middleware.mode:
                    on.
                % else:
                    off.
                % endif
                View <a href="${middleware.path}/report">report</a>.
            </p>
            <form action="${middleware.path}" method="post">
                % if middleware.mode:
                    <input type="hidden" name="turn" value="off">
                    <input type="submit" value="Off">
                % else:
                    <input type="hidden" name="turn" value="on">
                    <input type="submit" value="On">
                % endif
            </form>
        </div>
    </body>
</html>
