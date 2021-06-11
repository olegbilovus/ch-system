from flask import Flask, render_template, session, request, redirect
from waitress import serve
from paste.translogger import TransLogger

import utils
import os
import routine

routine.delete_logs()

app = Flask('')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(410)
@app.errorhandler(500)
def error_handler(error):
    return render_template('error.html')


@app.route('/')
def home():
    if 'user_id' in session:
        return render_template('index.html', user_id=session['user_id'])
    return render_template('index.html')


@app.post('/login')
def login():
    req = request.form
    if utils.login(req['user_id'], req['api_key']):
        utils.logger(f'WEB.login: {req["user_id"]} {req["api_key"][0:5]}')
        session['user_id'] = req['user_id']
        session['api_key'] = req['api_key']
        return redirect('dashboard')

    return render_template('index.html', error='Invalid credentials'), 401


@app.route('/dashboard')
def dashboard():
    try:
        return session['user_id']
    except KeyError:
        return redirect('/')


def run():
    format_logger = '[%(time)s] %(status)s %(REQUEST_METHOD)s %(REQUEST_URI)s'
    serve(TransLogger(app, format=format_logger),
          host='0.0.0.0',
          port=8080,
          url_scheme='https',
          ident=None)


utils.logger('WEB: started')
run()
