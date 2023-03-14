import setup
import os
import tempfile

import logs
from waitress import serve
from paste.translogger import TransLogger
from flask import Flask

import api

logger = logs.get_logger('Web', token=os.getenv('LOGTAIL_WEB'), file=True)
logger.info('Starting Web')

cert_f = tempfile.NamedTemporaryFile(delete=False)
cert_f.write(bytes(os.getenv('CERT'), 'utf-8'))
cert_f.close()

key_f = tempfile.NamedTemporaryFile(delete=False)
key_f.write(bytes(os.getenv('CERT_KEY'), 'utf-8'))
key_f.close()

db = api.Api(url=os.getenv('URL'), cf_client_id=os.getenv('CF_CLIENT_ID'),
             cf_client_secret=os.getenv('CF_CLIENT_SECRET'), cert_f=cert_f.name, key_f=key_f.name)

app = Flask(__name__, template_folder='chsystem/web/templates',
            static_folder='chsystem/web/static')
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')


@app.route('/health')
def ping():
    return 'OK' if db.check_valid_conn() else 'BAD'


if __name__ == '__main__':
    format_logger = '[%(time)s] %(status)s %(REQUEST_METHOD)s %(REQUEST_URI)s'
    serve(TransLogger(app, format=format_logger),
          host='0.0.0.0',
          port=8080,
          url_scheme='https',
          ident=None)
