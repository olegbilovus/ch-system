from datetime import datetime

from flask import Flask, request, Response
from replit import db

from utils import BOSSES

app = Flask('')


@app.route('/')
def home():
    return '<h1>Alive</h1>'


@app.route('/api')
def api():
    response = Response()
    api_key = request.headers.get('X-ApiKey', type=str)
    api_keys = db['api_keys']

    for user, api_key_db in api_keys.items():
        if api_key == api_key_db:
            boss = request.args['boss']
            print(f'API: {user} requested {boss} at {datetime.now()}')
            if boss in BOSSES:
                response.status_code = 200
                response.data = str(db[boss])
            else:
                response.status_code = 404
            break
    else:
        response.status_code = 401

    return response


def run():
    app.run(host='0.0.0.0', port=8080)
