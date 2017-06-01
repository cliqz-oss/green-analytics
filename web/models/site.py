from index import db

class Site(db.Model):

    __tablename__ = 'sites'

    id = db.Column(db.Integer, primary_key=True)
    site_id  = db.Column(db.String, nullable=False)
    site_key = db.Column(db.String, nullable=False)

    def __init__(self, site_id, site_key):
        self.site_id  = site_id
        self.site_key = site_key
