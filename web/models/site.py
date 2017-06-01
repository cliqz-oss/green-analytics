from index import db

class Site(db.Model):

    __tablename__ = 'sites'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String, nullable=False)

    def __init__(self, token):
        self.token = token
