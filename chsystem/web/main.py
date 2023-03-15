import setup
import os
import tempfile

import logs
from flask import Flask, session, redirect, render_template, request
from paste.translogger import TransLogger
from waitress import serve

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

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')


@app.get('/health')
def ping():
    return 'OK' if db.check_valid_conn() else 'BAD'


@app.get('/')
def home():
    if 'username' in session:
        return redirect('dashboard')
    return render_template('index.html', servers=db.get_servers_names())


@app.post('/login')
def login():
    req = request.form
    user = db.login(req['username'].lower(), req['password'], int(req['server']), req['clan'])
    if user:
        logger.info(f'Login: {user}')
        session['username'] = req['username']
        session['userprofileid'] = user['userprofileid']
        session['name'] = user['name']
        session['role'] = user['role']
        session['clanid'] = user['clanid']
        session['serverid'] = user['serverid']
        session['change_pw'] = user['change_pw']
        return redirect('dashboard')

    cache = {
        'username': req['username'],
        'server': int(req['server']),
        'clan': req['clan']
    }

    return render_template('index.html', error='We could not find you', servers=db.get_servers_names(),
                           cache=cache), 401


if __name__ == '__main__':
    format_logger = '[%(time)s] %(status)s %(REQUEST_METHOD)s %(REQUEST_URI)s'
    serve(TransLogger(app, format=format_logger),
          host='0.0.0.0',
          port=8080,
          url_scheme='https',
          ident=None)
