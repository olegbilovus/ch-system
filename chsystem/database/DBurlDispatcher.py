import os
import requests

from flask import Flask, request, Response
from replit import db
from waitress import serve
from paste.translogger import TransLogger

from logtail import LogtailHandler
import logging

handler = LogtailHandler(source_token=os.getenv('LOGTAIL_TOKEN'))

logger = logging.getLogger(__name__)
logger.handlers = []
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def update_url():
    res = requests.get(os.getenv('DB_URL'))
    if res.status_code == 200:
        db['DB_URL'] = res.text
        logger.info('Got DB_URL')
    else:
        db['DB_URL'] = None
        logger.info('ERROR DB_URL')


update_url()

app = Flask('')


@app.route('/ping')
def ping():
    return 'pong'


@app.post(f'/{os.getenv("ROUTE")}')
def set_db_url():
    logger.info('DB_URL set')
    db['DB_URL'] = request.json['DB_URL']
    response = Response()
    response.status_code = 200
    return response


@app.get(f'/{os.getenv("ROUTE2")}')
def get_db_url():
    logger.info('DB_URL get')
    if request.args.get('update') == '1':
        update_url()
    if db['DB_URL'] is None:
        response = Response()
        response.status_code = 404
        return response

    return db['DB_URL']


def run():
    format_logger = '[%(time)s] %(REMOTE_ADDR)s %(status)s %(REQUEST_METHOD)s %(REQUEST_URI)s %(HTTP_REFERER)s'
    serve(TransLogger(app, format=format_logger, logger=logger),
          host='0.0.0.0',
          port=8080,
          url_scheme='https',
          ident=None,
          threads=6)


run()
