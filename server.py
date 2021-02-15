from datetime import datetime

from flask import Flask, request, Response, jsonify
from replit import db

from utils import BOSSES

app = Flask('')


@app.route('/')
def home():
    return '<h1>Alive</h1>'


@app.route('/api', methods=['POST'])
def api():
    api_key = request.headers.get('X-ApiKey', type=str)
    api_keys = db['api_keys']
    res_bosses = {}
    for user, api_key_db in api_keys.items():
        if api_key == api_key_db:
            json = request.json
            req_bosses = json['bosses']
            print(f'API: {user} {json} at {datetime.now()}')
            for boss in req_bosses:
                if boss in BOSSES:
                    res_bosses[boss] = db[boss]
                else:
                    res_bosses[boss] = 404
            break
    else:
        response = Response()
        response.status_code = 401
        return response

    return jsonify(res_bosses)


def run():
    app.run(host='0.0.0.0', port=8080)
