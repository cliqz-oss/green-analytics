
from __future__ import unicode_literals
from flask import Flask
from flask import render_template
from flask import request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import json
import time

app = Flask(__name__)
token = os.environ.get('DATA_TOKEN', None)

app.config['SQLALCHEMY_DATABASE_URI']  = os.getenv('DATABASE_URL', None)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # silence the deprecation warning


# Setup db
db = SQLAlchemy(app)


class rows(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    row = db.Column(db.String(12000), nullable=False)

    def __init__(self, row):
        self.row = row

class read_log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, nullable=False)

    def __init__(self, count):
        self.count = count

def write(data):
	r = rows(data)
	db.session.add(r)
	db.session.commit()

def read():
	_rows = rows.query.all()
	return _rows

@app.route("/")
def hello():
	return jsonify(result=True)


@app.route('/collect', methods=['GET', 'POST'])
def collect():
	if request.method == "POST":
		write(json.dumps(json.loads(request.data)))
	return ""

@app.route('/frame')
def frame():
	return render_template('frame.html')


@app.route('/data')
def te():
	auth = request.headers.get('Authorization', None)
	if auth is not None:
		c_token = auth.split('Basic ')[1]
		if c_token == token:
			lines = []
			_rows = read()
			for each in _rows:
				try:
					lines.append([each.id, json.loads(each.row)])
				except:
					pass
			db.session.query(rows).delete()
			db.session.commit()
			return jsonify(result=lines)
	return jsonify(result=[])

if __name__ == "__main__":
  port = int(os.environ.get('PORT',5000))
  app.run(host='0.0.0.0', port=port)
