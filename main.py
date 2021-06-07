from flask import Flask, request, Response, jsonify
from replit import db
from waitress import serve
from paste.translogger import TransLogger
from secrets import compare_digest
from datetime import datetime

import utils


def auth(api_key):
    api_keys = db['api_keys']
    for user, key in api_keys.items():
        if compare_digest(api_key, key):
            return user

    return None


def get_api_key(_request):
    api_key = _request.headers.get('X-ApiKey', type=str)

    return api_key


app = Flask('')


@app.route('/')
def status():
    return db['status']


@app.post('/api/get')
def api_get():
    api_key = get_api_key(request)
    user = auth(api_key)
    if user is not None:
        res_bosses = {}
        json = request.json
        req_bosses = json['bosses']
        utils.logger(f'API.get: {user} {json}')
        for boss in req_bosses:
            res_bosses[boss] = utils.get_timer(boss)
        return jsonify(res_bosses)
    response = Response()
    response.status_code = 401
    return response


@app.post('/api/set')
def api_set():
    api_key = get_api_key(request)
    user = auth(api_key)
    response = Response()
    if user is not None:
        req_boss = request.json
        utils.logger(f'API.set: {user} {request.json}')
        if utils.set_timer(str(req_boss['boss']), req_boss['timer']):
            response.status_code = 200
        else:
            response.status_code = 404
    else:
        response.status_code = 401

    return response


def run():
    format_logger = '[%(time)s] %(REMOTE_ADDR)s %(status)s %(REQUEST_METHOD)s %(REQUEST_URI)s %(HTTP_REFERER)s'
    serve(TransLogger(app, format=format_logger),
          host='0.0.0.0',
          port=8080,
          url_scheme='https',
          ident=None,
          threads=6)


utils.logger('DB: started')
db['status'] = f'Alive since {datetime.now()}'
run()
