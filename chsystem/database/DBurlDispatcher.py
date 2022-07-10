import os
import requests
import logging

from flask import Flask, request, Response
from replit import db
from waitress import serve
from paste.translogger import TransLogger

logging.basicConfig(format='%(levelname)s %(asctime)s - %(message)s', level=logging.INFO)


def update_url():
    res = requests.get(os.getenv('DB_URL'))
    if res.status_code == 200:
        db['DB_URL'] = res.text
        logging.info('Got DB_URL')
    else:
        db['DB_URL'] = None
        logging.info('ERROR DB_URL')


update_url()

app = Flask('')


@app.route('/ping')
def ping():
    return 'pong'


@app.post(f'/{os.getenv("ROUTE")}')
def set_db_url():
    logging.info('DB_URL set')
    db['DB_URL'] = request.json['DB_URL']
    response = Response()
    response.status_code = 200
    return response


@app.get(f'/{os.getenv("ROUTE2")}')
def get_db_url():
    logging.info('DB_URL get')
    if request.args.get('update') == '1':
        update_url()
    if db['DB_URL'] is None:
        response = Response()
        response.status_code = 404
        return response

    return db['DB_URL']


def run():
    format_logger = '[%(time)s] %(REMOTE_ADDR)s %(status)s %(REQUEST_METHOD)s %(REQUEST_URI)s %(HTTP_REFERER)s'
    serve(TransLogger(app, format=format_logger),
          host='0.0.0.0',
          port=8080,
          url_scheme='https',
          ident=None,
          threads=6)


run()
