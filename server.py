from datetime import datetime

from flask import Flask, request, Response, jsonify, render_template
from replit import db
from waitress import serve
from paste.translogger import TransLogger

import utils


def auth(api_key):
	api_keys = db['api_keys']
	for user, key in api_keys.items():
		if api_key == key:
			return user

	return None


def get_api_key(request):
	api_key = request.headers.get('X-ApiKey', type=str)
	if api_key is None:
		try:
			api_key = request.cookies['ApiKey']
		except KeyError:
			pass

	return api_key


app = Flask('')


@app.route('/')
def home():
	return render_template('index.html')


@app.route('/api/get', methods=['POST'])
def api_get():
	api_key = get_api_key(request)
	user = auth(api_key)
	if user is not None:
		res_bosses = {}
		json = request.json
		req_bosses = json['bosses']
		print(f'API: {user} {json} at {datetime.now()}')
		for boss in req_bosses:
			res_bosses[boss] = utils.get_timer(boss)
		return jsonify(res_bosses)
	else:
		response = Response()
		response.status_code = 401
		return response


@app.route('/api/set', methods=['POST'])
def api_set():
	api_key = get_api_key(request)
	user = auth(api_key)
	response = Response()
	if user is not None:
		req_boss = request.json
		print(f'API: {user} {request.json} at {datetime.now()}')
		if utils.set_timer(req_boss['boss'], req_boss['timer']):
			response.status_code = 200
		else:
			response.status_code = 404
	else:
		response.status_code = 401

	return response


def run():
	serve(TransLogger(app), host='0.0.0.0', port=8080, url_scheme='https')
