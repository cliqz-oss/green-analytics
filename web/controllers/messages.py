import json
from index import db
from flask import request
from models.message import Message

class Messages():

    def respond(self):
        data = json.loads(request.data)
        msg = Message(data)
        db.session.add(msg)
        db.session.commit()
        return ('', 201,)
