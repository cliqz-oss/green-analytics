from flask import request, render_template
from datetime import datetime, timedelta
from controllers.metric_detail import MetricData

class Analyze():

    def respond(self):
        metrics = MetricData()
        stop = datetime.utcnow()
        start = stop - timedelta(30)
        token = request.args.get('token')
        sites = metrics.report_domains({'token': token})
        context = {
            'from': start.strftime('%Y/%m/%d %H:%Mh'),
            'to': stop.strftime('%Y/%m/%d %H:%Mh'),
            'token': token,
            'sites': sites,
            'selected_site': request.args.get('site', sites[0][0])
        }
        return render_template('dashboard.html', context=context)
