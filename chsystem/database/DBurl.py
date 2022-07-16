import os
from flask import Flask
from waitress import serve
from paste.translogger import TransLogger

import logs

logger = logs.get_logger(logtail=False, name='DBurl')

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
