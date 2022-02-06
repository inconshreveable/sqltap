<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="sqltap profile">
    <meta name="author" content="inconshreveable">

    <title>${report_title}</title>

    <!-- Bootstrap core CSS -->
    <link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css" rel="stylesheet">

    <!-- syntax highlighting -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.4.0/styles/vs.min.css">

    <style type="text/css">
      body { 
        overflow-y: hidden;
      }
      #query-groups {
        border-right: 1px solid #eee;
        height: calc(100vh - 54px);
        display: flex;
        flex-direction: column;
        padding: 0px;
        width: 320px;
        max-width: 320px;
        min-width: 320px;
      }

      #total-time { color: #fff; }
      #total-time .sum { color: #0f0; font-size: 16px; }
      #total-time .count { color: #0f0; font-size: 16px; }
      a.toggle { cursor: pointer }
      a.toggle strong { color: red; }

      .nav-list-item {
        border-bottom: 1px solid #eee;
        margin-top: 0px !important;
      }

      .nav-pills>li.active>a {
        background-color: #337ab7;
        border-radius: 0px;
      }

      #myTabs {
        flex-grow: 1;
        overflow-y: auto;
        overflow-x: hidden;
      }

      .query-info-container {
        padding-left: 12px;
        padding-right: 12px;
        flex-grow: 1;
        overflow-y: scroll;
        height: calc(100vh - 54px);
      }
    </style>
  </head>

  <body>
    <div class="navbar navbar-inverse" style="border-radius: 0px; margin-bottom: 0px;" role="navigation">
      <div class="container">
        <div class="navbar-header">
          <a class="navbar-brand" href="https://github.com/inconshreveable/sqltap">sqltap</a>
        </div>
        <ul class="navbar-right nav navbar-nav">
          <li><a target="_blank" href="http://sqltap.inconshreveable.com/">Documentation</a></li>
          <li><a target="_blank" href="https://github.com/inconshreveable/sqltap">Code</a></li>
        </ul>
        <p id="total-time" class="navbar-text">
          <span class="count">${len(all_group.queries)}</span> queries spent
          <span class="sum">${'%.2f' % all_group.sum}</span> seconds
          over <span class="sum">${'%.2f' % duration}</span> seconds of profiling
        </p>
        <%block name="header_extra"></%block>
      </div>
    </div>

    <div class="" style="overflow-x: hidden; display: flex;">

        <div id="query-groups">

          <ul class="nav nav-pills nav-stacked" id="myTabs">
            % for i, group in enumerate(query_groups):
            <li class="nav-list-item ${'active' if i==0 else ''}">
              <a href="#query-${i}" data-toggle="tab">
                <div style="display: flex; flex-wrap: wrap;">
                    <div style="width: 100%; font-weight: 700;">
                      ${group.first_word}
                    </div>
                    <div style="width: 100%;">
                      <span class="label label-warning" style="margin-right: 5px; background-color: #1A237E;">
                          Time: ${'%.3f' % group.sum}s
                      </span>
                      <span class="label label-default" style="margin-right: 5px; text-align: right; background-color: #1a557e;">
                          Rows: ${group.rowcounts}
                      </span>
                      <span class="label label-info" style="margin-right: 5px; background-color: #431a7e;">
                          Queries: ${len(group.queries)}
                      </span>
                    </div>
                </div>
              </a>
            </li>
          % endfor
          </ul>

          <div style="background-color: #cacaca; text-align: center; font-weight: 500;">
            <span>Report Generated: ${report_time}</span>
          </div>
        </div>

        <!-- ================================================== -->

        <div class="query-info-container">

          <div class="tab-content">
            % for i, group in enumerate(query_groups):
            <div id="query-${i}" class="tab-pane ${'active' if i==0 else ''}">
              <h4 class="toggle" style="margin-top: 0px;">
                  <ul class="list-inline">
                    <li>
                      <dt>Query Count</dt>
                      <dd>${len(group.queries)}</dd>
                    </li>
                    <li>
                      <dt>Row Count</dt>
                      <dd>${'%d' % group.rowcounts}</dd>
                    </li>
                    <li>
                      <dt>Total Time</dt>
                      <dd>${'%.3f' % group.sum}</dd>
                    </li>
                    <li>
                      <dt>Mean</dt>
                      <dd>${'%.3f' % group.mean}</dd>
                    </li>
                    <li>
                      <dt>Median</dt>
                      <dd>${'%.3f' % group.median}</dd>
                    </li>
                    <li>
                      <dt>Min</dt>
                      <dd>${'%.3f' % group.min}</dd>
                    </li>
                    <li>
                      <dt>Max</dt>
                      <dd>${'%.3f' % group.max}</dd>
                    </li>
                  </ul>
              </h4>

              <hr />
              <pre><code class="language-sql">${group.formatted_text}</code></pre>
              <hr />

              <%
                params = group.get_param_names()
              %>
              <h4>
                Query Breakdown
              </h4>
              <table class="table">
                <tr>
                  <th>Query Time</th>
                % for param_name in params:
                  <th><code>${param_name}</code></th>
                % endfor
                  <th>Row Count</th>
                  <th>Params ID</th>
                </tr>
                % for idx, query in enumerate(reversed(group.queries)):
                <tr class="${'hidden' if idx >= 3 else ''}">
                    <td>${'%.3f' % query.duration}</td>
                    % for param_name in params:
                    <td>${query.params.get(param_name, '')}</td>
                    % endfor
                    <td>${'%d' % query.rowcount}</td>
                    <td>${'%d' % query.params_id}</td>
                </tr>
                % endfor
              </table>
              % if len(group.queries) > 3:
                <a href="#" class="morequeries">show ${len(group.queries)-3} older queries</a>
              % endif

              <hr />
              <% params_hash_count = len(group.params_hashes) %>
              <h4>
                  ${params_hash_count} unique parameter
                  % if params_hash_count == 1:
                      set is
                  % else:
                      sets are
                  % endif
                  supplied.
              </h4>
              <ul class="details">
                % for idx, (count, params_id, params) in enumerate(group.params_hashes.values()):
                  <li class="${'hidden' if idx >= 3 else ''}">
                    <h5>
                      ${count}
                      ${'call' if count == 1 else 'calls'}
                      (Params ID: ${params_id}) with
                      <code class="language-sql">
                        ${", ".join(["%s=%r" % (k,params[k]) for k in sorted(params.keys()) if params[k] is not None])}
                      </code>
                    </h5>
                  </li>
                % endfor
              </ul>
              % if len(group.params_hashes) > 3:
                  <a href="#" class="moreparams">show ${len(group.params_hashes)-3} more parameter sets</a>
              % endif

              <hr />
              <% stack_count = len(group.stacks) %>
              <h4 id="trace-details-title">
                  ${stack_count} unique
                  % if stack_count == 1:
                      stack issues
                  % else:
                      stacks issue
                  % endif
                  this query
              </h4>
              <ul class="details" id="trace-details">
                  % for trace, count in group.stacks.items():
                  <li>
                    <a class="toggle">
                      <h5>
                      <% fr = group.callers[trace] %>
                      ${count}
                      ${'call' if count == 1 else 'calls'} from
                      <strong>${fr[2]}</strong> @${fr[0].split()[-1]}:${fr[1]}
                      </h5>
                    </a>
                    <pre class="trace hidden"><code class="python">${trace}</code></pre>
                  </li>
                  % endfor
              </ul>
            </div>

            <!-- ================================================== -->

            % endfor
          </div>
    </div><!-- /.container -->


    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.0/jquery.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.4.0/highlight.min.js"></script>

    <script type="text/javascript">
        jQuery(function($) {
            hljs.highlightAll();

            $(".toggle").click(function() {
              $(this).siblings(".trace").toggleClass("hidden")
              $("#trace-details-title")[0].scrollIntoView({behavior: "smooth"});
            });
            $('#myTabs a').click(function (e) {
                $(this).tab('show');
                e.preventDefault();
            });
            $(".morequeries").click(function(e) {
                e.preventDefault();
                $(this).hide();
                $(this).prev("table").find("tr.hidden").removeClass("hidden");
            });
            $(".moreparams").click(function(e) {
                e.preventDefault();
                $(this).hide();
                $(this).prev("ul").find("li.hidden").removeClass("hidden");
            });
        });
    </script>
  </body>
</html>
