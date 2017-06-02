from index import db
from flask import request, jsonify, render_template
from models.site import Site
import uuid
import os
class Landing():

    def respond(self):

        site_id  = str(uuid.uuid4())[:8]
        site_key = uuid.uuid4()

        new_site = Site(site_id, site_key)
        db.session.add(new_site)
        db.session.commit()

        domainName = os.environ["DOMAIN_NAME"]
        collectorPath = os.environ["COLLECTOR_PATH"]
        protocol = os.environ["PROTOCOL"]
        dashboardPath = os.environ["DASHBOARD_PATH"]
        domain = protocol + "://" + domainName + collectorPath
        dashboard = protocol + "://" + domainName + dashboardPath

        response = {
            'site_id': site_id,
            'site_key': site_key,
            'endpoint': domain,
            'dashboard': dashboard
        }
        return render_template('template_landing.html', context=response)