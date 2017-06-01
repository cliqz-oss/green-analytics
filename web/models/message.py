import json
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from index import db

class Message(db.Model):

    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.ForeignKey('sites.id'), index=True)
    received = db.Column(db.DateTime, nullable=False)
    ts = db.Column(db.DateTime, nullable=False, index=True)
    message = db.Column(JSONB, nullable=False)

    def __init__(self, message):
        self.message = message
        self.site_id = message['site_id']
        self.received = datetime.utcnow()
        self.ts = datetime.strptime(message['ts'], '%Y%m%d%H%M%S')

db.Index('message_type', Message.message['type'])
db.Index('message_content', Message.message, postgresql_using='gin')
