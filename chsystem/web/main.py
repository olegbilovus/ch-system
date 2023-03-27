from setup import setup

setup()
import os
from functools import wraps
import tempfile
from datetime import timedelta

import logs
from flask import Flask, redirect, render_template, request, make_response, jsonify
from paste.translogger import TransLogger
from waitress import serve
from models import User

from api import Api

logger = logs.get_logger('Web', token=os.getenv('LOGTAIL_WEB'))
logger.info('Starting Web')

cert_f = tempfile.NamedTemporaryFile(delete=False)
cert_f.write(bytes(os.getenv('CERT'), 'utf-8'))
cert_f.close()

key_f = tempfile.NamedTemporaryFile(delete=False)
key_f.write(bytes(os.getenv('CERT_KEY'), 'utf-8'))
key_f.close()

api = Api(url=os.getenv('URL'), cf_client_id=os.getenv('CF_CLIENT_ID'),
          cf_client_secret=os.getenv('CF_CLIENT_SECRET'), cert_f=cert_f.name, key_f=key_f.name)

app = Flask(__name__, template_folder='templates', static_folder='static')
SESSION_NAME = "SessionID"

ROLES = ['Recruit', 'Clansman', 'Guardian', 'General', 'Admin', 'Chief']
ROLES_COLORS = ['#f1c21b', '#e67f22', '#3398dc', '#9a59b5', '#1abc9b', '#000000']


def logout_fun(sessionid):
    api.delete_session(sessionid)
    resp = make_response(redirect('/'))
    resp.delete_cookie(SESSION_NAME)
    return resp


def get_user(sessionid) -> User | None:
    return api.get_user_by_sessionid(sessionid)


def check_logged():
    sessionid = request.cookies.get(SESSION_NAME)
    if sessionid is not None:
        return get_user(sessionid)


def login_req(role=0):
    def decorate(fun):
        @wraps(fun)
        def wrapper(*args, **kwargs):
            user = check_logged()
            if user is not None:
                logger.info(f'{fun.__name__}:{user}')
                api.session_used(user.sessionid)
                if user.role >= role:
                    return fun(user, *args, **kwargs)

                return logout_fun(user.sessionid)

            return redirect('/')

        return wrapper

    return decorate


def no_login(fun):
    @wraps(fun)
    def wrapper(*args, **kwargs):
        if check_logged():
            return redirect('/dashboard')

        return fun(*args, **kwargs)

    return wrapper


@app.get('/health')
def ping():
    return 'OK' if api.check_valid_conn() else 'BAD'


@app.get('/')
@no_login
def home():
    return render_template('index.html', servers=api.get_servers_names())


@app.post('/login')
@no_login
def login():
    req = request.form
    user = api.login(req['username'].lower(), req['password'], int(req['server']), req['clan'].lower())
    if user:
        logger.info(f'{login.__name__}:{user}')
        resp = make_response(redirect('dashboard'))
        resp.set_cookie(SESSION_NAME, user.sessionid, httponly=True, secure=True, samesite='Lax',
                        max_age=timedelta(days=3))
        return resp

    cache = {
        'username': req['username'],
        'server': int(req['server']),
        'clan': req['clan']
    }
    logger.warning(f'{login.__name__}:{cache}')

    return render_template('index.html', error='We could not find you', servers=api.get_servers_names(),
                           cache=cache), 401


@app.get('/logout')
@login_req()
def logout(user: User):
    return logout_fun(user.sessionid)


@app.get('/sessions')
@login_req()
def get_sessions(user: User):
    user_sessions = api.get_user_sessions(user.userprofileid)
    data = {'sessions': [], 'current': -1}
    for i, us in enumerate(user_sessions):
        data['sessions'].append(us.get_data_select('id', 'creation', 'lastuse', 'host'))
        if us.id == user.id:
            data['current'] = i

    return jsonify(data)


@app.get('/dashboard')
@login_req()
def dashboard(user: User):
    return render_template('dashboard.html', user=user, role_name=ROLES[user.role], role_color=ROLES_COLORS[user.role])


if __name__ == '__main__':
    format_logger = '[%(time)s] %(status)s %(REQUEST_METHOD)s %(REQUEST_URI)s'
    serve(TransLogger(app, format=format_logger),
          host='0.0.0.0',
          port=8080,
          url_scheme='https',
          ident=None)
