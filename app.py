
from __future__ import unicode_literals
from flask import Flask
from flask import render_template
from flask import request, jsonify
import os
import redis
import json
import zlib
import msgpack
app = Flask(__name__)
db=redis.from_url(os.environ.get('REDIS_URL', None))
token = os.environ.get('DATA_TOKEN', None)

def write(data):
	db.rpush("collect:queue:logs", data)

@app.route("/")
def hello():
	return jsonify(result=True)


@app.route('/collect', methods=['GET', 'POST'])
def collect():
	if request.method == "POST":
		write(zlib.compress(msgpack.dumps(json.loads(request.data))))
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
			while(True):
				count = 0
				data = db.lpop("collect:queue:logs")
				if data is None:
					count += 1
					return jsonify(result=lines)
				else:
					data = msgpack.loads(zlib.decompress(data))
					_data = {}
					for k,v in data.items():
						_data[k.decode('utf-8')] = v.decode('utf-8')
					lines.append(_data)
	return jsonify(result=[])

if __name__ == "__main__":
  port = int(os.environ.get('PORT',5000))
  app.run(host='0.0.0.0', port=port)
