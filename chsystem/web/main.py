from setup import setup

setup()
import os
import tempfile
from datetime import datetime, timedelta
from secrets import token_hex

import logs
from flask import Flask, redirect, render_template, request, make_response, jsonify
from paste.translogger import TransLogger
from waitress import serve
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
import uuid

from api import Api
from models import Base, User

logger = logs.get_logger('Web', token=os.getenv('LOGTAIL_WEB'), file=True)
logger.info('Starting Web')

cert_f = tempfile.NamedTemporaryFile(delete=False)
cert_f.write(bytes(os.getenv('CERT'), 'utf-8'))
cert_f.close()

key_f = tempfile.NamedTemporaryFile(delete=False)
key_f.write(bytes(os.getenv('CERT_KEY'), 'utf-8'))
key_f.close()

api = Api(url=os.getenv('URL'), cf_client_id=os.getenv('CF_CLIENT_ID'),
          cf_client_secret=os.getenv('CF_CLIENT_SECRET'), cert_f=cert_f.name, key_f=key_f.name)

engine = create_engine("sqlite:///sessions.db")
Base.metadata.create_all(engine)
session = Session(engine)

app = Flask(__name__, template_folder='templates', static_folder='static')
SESSION_NAME = "SessionID"

ROLES = ['Recruit', 'Clansman', 'Guardian', 'General', 'Admin']
ROLES_COLORS = ['#f1c21b', '#e67f22', '#3398dc', '#9a59b5', '#1abc9b']


def get_user(sessionid):
    stmt = select(User).where(User.sessionid == sessionid)
    try:
        return session.scalars(stmt).one()
    except NoResultFound:
        return None


def check_logged():
    sessionid = request.cookies.get(SESSION_NAME)
    if sessionid is not None:
        return get_user(sessionid)
    return None


def login_req(fun):
    def wrapper(*args, **kwargs):
        user = check_logged()
        if user is not None:
            user.last_use = datetime.utcnow()
            return fun(user, *args, **kwargs)

        return redirect('/')

    wrapper.__name__ = fun.__name__
    return wrapper


@app.get('/health')
def ping():
    return 'OK' if api.check_valid_conn() else 'BAD'


@app.get('/')
def home():
    if check_logged():
        return redirect('dashboard')
    return render_template('index.html', servers=api.get_servers_names())


@app.post('/login')
def login():
    req = request.form
    user = api.login(req['username'].lower(), req['password'], int(req['server']), req['clan'])
    if user:
        sessionid = token_hex(64)

        user = User(
            id=str(uuid.uuid4()),
            sessionid=sessionid,
            username=req['username'],
            userprofileid=user['userprofileid'],
            name=user['name'],
            role=user['role'],
            clanid=user['clanid'],
            serverid=user['serverid'],
            change_pw=user['change_pw'],
            last_use=datetime.utcnow()
        )
        session.add(user)
        logger.info(f'LOGIN:{user}')

        resp = make_response(redirect('dashboard'))
        resp.set_cookie(SESSION_NAME, sessionid, httponly=True, secure=True, samesite='Lax',
                        max_age=timedelta(days=3))
        return resp

    cache = {
        'username': req['username'],
        'server': int(req['server']),
        'clan': req['clan']
    }

    return render_template('index.html', error='We could not find you', servers=api.get_servers_names(),
                           cache=cache), 401


@app.get('/logout')
@login_req
def logout(user: User):
    session.delete(user)
    resp = make_response(redirect('/'))
    resp.delete_cookie(SESSION_NAME)
    return resp


@app.get('/sessions/get')
@login_req
def get_sessions(user: User):
    stmt = select(User).where(User.username == user.username)
    user_sessions = session.scalars(stmt).all()
    data = {'sessions': [], 'current': -1}
    for i, us in enumerate(user_sessions):
        if us.id == user.id:
            data['current'] = i
        data['sessions'].append(us.get_external_data())

    return jsonify(data)


if __name__ == '__main__':
    format_logger = '[%(time)s] %(status)s %(REQUEST_METHOD)s %(REQUEST_URI)s'
    serve(TransLogger(app, format=format_logger),
          host='0.0.0.0',
          port=8080,
          url_scheme='https',
          ident=None)
