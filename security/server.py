from flask import Flask, jsonify 
from waitress import serve
from paste.translogger import TransLogger
from replit import db

import os


app = Flask('')


@app.route('/')
def home():
    return db['status']

@app.get(f'/{os.getenv("URI1")}')
def get_members():
    members = list(db['ebk_members'])
    return jsonify(members)


def run():
    format_logger = '[%(time)s] %(status)s %(REQUEST_METHOD)s %(REQUEST_URI)s'
    serve(TransLogger(app, format=format_logger),
          host='0.0.0.0',
          port=8080,
          url_scheme='https',
          ident=None)