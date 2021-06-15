from flask import Flask, render_template, session, request, redirect, Response
from waitress import serve
from paste.translogger import TransLogger
from itertools import islice

import utils
import os
import routine
import db_utils

routine.delete_logs()

app = Flask('')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('dashboard')
    return render_template('index.html')


@app.post('/login')
def login():
    req = request.form
    user = utils.login(req['user_id'], req['api_key'])
    if user:
        utils.logger(f'WEB.login: {req["user_id"]} {req["api_key"][0:5]}')
        session['user_id'] = req['user_id']
        session['api_key'] = req['api_key']
        session['main'] = user['main']
        session['role'] = user['role']
        return redirect('dashboard')

    return render_template('index.html', error='Invalid credentials'), 401


@app.get('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        utils.logger(
            f'WEB.dashboard: {session["main"]} {session["user_id"]} {session["api_key"][0:5]}'
        )
        role = session['role']
        return render_template(
            'dashboard.html',
            timers=utils.get_all_timers(),
            users=db_utils.get_users() if role >= 4 else None,
            roles=utils.ROLES,
            role=role,
            role_colors=utils.ROLES_COLORS,
            main=session['main'],
            islice=islice)
    return redirect('/')


@app.post('/user/create')
def create_user():
    response = Response()
    request_role = session['role']
    if 'user_id' in session and request_role >= 4:
        req = request.json
        utils.logger(
            f'WEB.user.create: {session["main"]} {session["user_id"]} {session["api_key"][0:5]} {req}'
        )
        role = req['role']
        user_id = ''.join(req['user_id'].split())
        main = req['main']
        if role <= 3:
            api_key = utils.create_user(user_id, role, main)
            if api_key:
                return api_key
            response.status_code = 409
            return response
        elif role == 4 and request_role == 5:
            api_key = utils.create_user(user_id, role, main)
            if api_key:
                return api_key
            response.status_code = 409
            return response

    response.status_code = 401
    return response


@app.post('/user/delete')
def delete_user():
    response = Response()
    response.status_code = 200
    request_role = session['role']
    if 'user_id' in session and request_role >= 4:
        req = request.json
        utils.logger(
            f'WEB.user.delete: {session["main"]} {session["user_id"]} {session["api_key"][0:5]} {req}'
        )
        user_id = req['user_id']
        user = db_utils.get_user(user_id)
        if user:
            role = user['role']
            if role <= 3:
                if utils.delete_user(user_id):
                    return response
                response.status_code = 404
                return response
            elif role == 4 and request_role == 5:
                if utils.delete_user(user_id):
                    return response
                response.status_code = 404
                return response
        else:
            response.status_code = 404
            return response

    response.status_code = 401
    return response


@app.post('/boss/sub')
def boss_sub():
    response = Response()
    if 'user_id' in session:
        req = request.json
        utils.logger(
            f'WEB.boss.sub: {session["main"]} {session["user_id"]} {session["api_key"][0:5]} {req}'
        )
        if utils.boss_sub(session['api_key'], req['boss']):
            response.status_code = 200
        else:
            response.status_code = 404
    else:
        response.status_code = 401
    return response


@app.post('/boss/unsub')
def boss_unsub():
    response = Response()
    if 'user_id' in session:
        req = request.json
        utils.logger(
            f'WEB.boss.unsub: {session["main"]} {session["user_id"]} {session["api_key"][0:5]} {req}'
        )
        if utils.boss_unsub(session['api_key'], req['boss']):
            response.status_code = 200
        else:
            response.status_code = 404
    else:
        response.status_code = 401
    return response


@app.post('/boss/set')
def boss_reset():
    response = Response()
    if 'user_id' in session:
        req = request.json
        utils.logger(
            f'WEB.boss.set: {session["main"]} {session["user_id"]} {session["api_key"][0:5]} {req}'
        )
        if utils.boss_reset(session['api_key'], req['boss'], req['timer']):
            response.status_code = 200
        else:
            response.status_code = 404
    else:
        response.status_code = 401
    return response


def run():
    format_logger = '[%(time)s] %(status)s %(REQUEST_METHOD)s %(REQUEST_URI)s'
    serve(TransLogger(app, format=format_logger),
          host='0.0.0.0',
          port=8080,
          url_scheme='https',
          ident=None)


utils.logger('WEB: started')
run()
