import os
import requests
from flask import Flask
from waitress import serve
from paste.translogger import TransLogger

import logs

logger = logs.get_logger(logatile=False)

res = requests.post(os.getenv('DB_SERVER_URL'), json={'DB_URL': os.getenv('DATABASE_URL')})
logger.info(f'DB_URL set: {res.status_code}')

app = Flask('')


@app.route(f'/{os.getenv("ROUTE")}')
def get_url():
    logger.info('Requested DATABASE_URL')
    return os.getenv('DATABASE_URL')


@app.route('/ping')
def ping():
    return 'pong'


format_logger = '[%(time)s] %(status)s %(REQUEST_METHOD)s %(REQUEST_URI)s'
serve(TransLogger(app, format=format_logger, logger=logger),
      host='0.0.0.0',
      port=os.getenv('PORT'),
      url_scheme='https',
      ident=None)
