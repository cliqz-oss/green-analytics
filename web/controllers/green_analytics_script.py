from flask import request, render_template
import os

class GreenAnalyticsScript():

    def respond(self):
        domainName = os.environ["DOMAIN_NAME"]
        collectorPath = os.environ["COLLECTOR_PATH"]
        protocol = os.environ["PROTOCOL"]
        domain = protocol + "://" + domainName + collectorPath
        return render_template('template_iframe.html', context={ "endpoint": domain })
