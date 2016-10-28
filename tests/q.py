import sqltap
import collections
framework = None

def context_fn(*args):
    """ Associate the request path, unique id with each query statistic """
    return (framework.current_request().path,
            framework.current_request().id)

# start the profiler immediately
profiler = sqltap.start(user_context_fn=context_fn)

def generate_reports():
    """ call this at any time to generate query reports reports """
    all_stats = []
    per_request_stats = collections.defaultdict(list)
    per_page_stats = collections.defaultdict(list)

    qstats = profiler.collect()
    for qs in qstats:
        all_stats.append(qs)

        page = qstats.user_context[0]
        per_page_stats[page].append(qs)

        request_id = qstats.user_context[1]
        per_request_stats[request_id].append(qs)

    # report with all queries
    sqltap.report(all_stats, "report_all.html")

        # a report per page
        for page, stats in per_page_stats.items():
            sqltap.report(stats, "report_page_%s.html" % page)

        # a report per request
        for request_id, stats in per_request_stats.items():
            sqltap.report(stats, "report_request_%s.html" % request_id)