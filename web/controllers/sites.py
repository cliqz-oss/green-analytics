from index import db
from flask import request, jsonify, render_template
from models.site import Site
import uuid

class Sites():

    def respond(self):

        site_id  = str(uuid.uuid4())[:8]
        site_key = uuid.uuid4()

        new_site = Site(site_id, site_key)
        db.session.add(new_site)
        db.session.commit()

        response = {
            'site_id': site_id,
            'site_key': site_key
        }
        return render_template('template_signup.html', context=response)
