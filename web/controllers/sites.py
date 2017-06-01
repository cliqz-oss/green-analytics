from flask import request
from models.site import Site

class Sites():

    def respond(self):
        sites = Site.query.all()
        return 'test' + str(len(sites))
