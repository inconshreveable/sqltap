<html>
    <head>
        <title>${name}</title>

        <style type="text/css">
            p, pre, ul { margin: 0; padding: 0; }
            li { list-style-type: none; }
            h1 { font-family: sans-serif; letter-spacing: 0.1em; font-size: 1.6em; }
            h4 { margin: .2em; }

            .page { width: 800px; margin: 0 auto; }
            .query { background-color: rgba(200, 200, 150, 0.2); border-radius: 4px; 
                     padding: 10px; margin: 15px 0; border: 2px #777 solid; }

            .details { display: none; margin: 20px 0; }
            .text { padding: 10px; background-color: white; border: 3px double #bbb; 
                    overflow: hidden; }
            .text:hover { overflow: visible; }
            .toggle { cursor: pointer; font-family: sans-serif; }
            .toggle:hover { color: green; }
            .details .toggle { margin-top: 20px; }
            .total-time { color: red; }
        </style>

        <script type="text/javascript" 
            src="https://ajax.googleapis.com/ajax/libs/jquery/1.6.1/jquery.min.js">
        </script>
        <script type="text/javascript">
            jQuery(function($) {
                $(".toggle").click(function() {
                    $(this).siblings(".details").toggle();
                });
            });
        </script>
    </head>

    <body>
        <div class="page">
            <h1>
                SQLTap Report: 
                ${len(all_group.queries)} queries spent 
                <span class='total-time'>${'%.2f' % all_group.sum}</span> seconds
            </h1>
            <ul>
                % for text, group in sorted(query_groups.items(),\
                        key = lambda pair: pair[1].sum, reverse = True):
                <li class="query">
                    <h4 class="toggle">
                        Query count: ${len(group.queries)},
                        durations:
                        Avg: ${'%.2f' % group.mean}
                        Total: ${'%.2f' % group.sum}
                        Max: ${'%.2f' % group.max}
                    </h4>
                    <div class="details">
                        <pre class="text">${text}</pre>

                        <% stack_count = len(group.stacks) %>
                        <h4 class="toggle">
                            ${stack_count} unique
                            % if stack_count == 1:
                                stack issues
                            % else:
                                stacks issue
                            % endif
                            this query
                        </h4>
                        <ul class="details">
                            % for trace, count in group.stacks.items():
                            <li class="stacktrace">
                                <p>${count} stacks traces</p>
                                <pre class="text">${trace}</pre>
                            </li>
                            % endfor
                        </ul>
                    </div>
                </li>
                % endfor
            </ul>
        </div>
    </body>
</html>
