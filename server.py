from datetime import datetime

from flask import Flask, request, Response, jsonify
from replit import db

import utils


def auth(api_key):
    api_keys = db['api_keys']
    for user, key in api_keys.items():
        if api_key == key:
            return user
            break
    else:
        return None


app = Flask('')


@app.route('/')
def home():
    return '<h1>Alive</h1>'


@app.route('/api/get', methods=['POST'])
def api_get():
    api_key = request.headers.get('X-ApiKey', type=str)
    res_bosses = {}
    user = auth(api_key)
    if user is not None:
        json = request.json
        req_bosses = json['bosses']
        print(f'API: {user} {json} at {datetime.now()}')
        for boss in req_bosses:
            res_bosses[boss] = utils.get_timer(boss)
    else:
        response = Response()
        response.status_code = 401
        return response

    return jsonify(res_bosses)


@app.route('/api/set', methods=['POST'])
def api_set():
    api_key = request.headers.get('X-ApiKey', type=str)
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
    app.run(host='0.0.0.0', port=8080)
