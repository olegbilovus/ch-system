import os
import requests

from datetime import datetime

res = requests.get(os.getenv('DB_URL'))
if res.status_code == 200:
    db['DB_URL'] = res.text
    utils.logger('Got DB_URL')
else:
    db['DB_URL'] = None
    utils.logger('ERROR DB_URL')


app = Flask('')


@app.route('/ping')
def ping():
    return 'pong'


@app.post(f'/{os.getenv("ROUTE")}')
def set_db_url():
    utils.logger('DB_URL request')
    db['DB_URL'] = request.json['DB_URL']
    response = Response()
    response.status_code = 201
    return response


@app.post('/api/get')
def api_get():
    api_key = get_api_key(request)
    user = auth(api_key)
    if user is not None:
        res_bosses = {}
        json = request.json
        req_bosses = json['bosses']
        utils.logger(f'API.get: {user} {json}')
        for boss in req_bosses:
            res_bosses[boss] = api.get_timer(boss)
        return jsonify(res_bosses)
    response = Response()
    response.status_code = 401
    return response


@app.post('/api/set')
def api_set():
    api_key = get_api_key(request)
    user = auth(api_key)
    response = Response()
    if user is not None:
        req_boss = request.json
        utils.logger(f'API.set: {user} {request.json}')
        if api.set_timer(str(req_boss['boss']), req_boss['timer']):
            response.status_code = 200
        else:
            response.status_code = 404
    else:
        response.status_code = 401

    return response


@app.post('/api/sub')
def api_sub():
    api_key = get_api_key(request)
    user = auth(api_key)
    response = Response()
    if user is not None:
        req = request.json
        utils.logger(f'API.sub: {user} {request.json}')
        if api.add_sub(req['boss'], user):
            response.status_code = 200
        else:
            response.status_code = 404
    else:
        response.status_code = 401

    return response


@app.post('/api/unsub')
def api_unsub():
    api_key = get_api_key(request)
    user = auth(api_key)
    response = Response()
    if user is not None:
        req = request.json
        utils.logger(f'API.unsub: {user} {request.json}')
        if api.remove_sub(req['boss'], user):
            response.status_code = 200
        else:
            response.status_code = 404
    else:
        response.status_code = 401

    return response


@app.post('/api/getsubs')
def api_getsubs():
    api_key = get_api_key(request)
    user = auth(api_key)
    response = Response()
    if user is not None and user == NOTIFIER_NAME:
        utils.logger(f'API.getsubs: {user}')
        subs = {}
        for boss in utils.BOSSES:
            subs[boss] = list(api.get_subs(boss))
        return jsonify(subs)
    response.status_code = 401

    return response


@app.post('/api/create')
def api_create():
    api_key = get_api_key(request)
    user = auth(api_key)
    response = Response()
    if user is not None and user == WEB_NAME:
        req = request.json
        utils.logger(f'API.create: {user} {request.json}')
        return jsonify(api.create(req['user_id']))
    response.status_code = 401

    return response


@app.post('/api/delete')
def api_delete():
    api_key = get_api_key(request)
    user = auth(api_key)
    response = Response()
    if user is not None and user == WEB_NAME:
        req = request.json
        utils.logger(f'API.delete: {user} {request.json}')
        if api.delete(req['user_id']):
            response.status_code = 200
        else:
            response.status_code = 404
    else:
        response.status_code = 401

    return response


@app.post('/api/validate')
def api_validate():
    api_key = get_api_key(request)
    user = auth(api_key)
    response = Response()
    if user is not None:
        req = request.json
        utils.logger(
            f'API.validate: {user} {req["user_id"]}')
        if api.validate_apikey(req['user_id'], req['api_key']):
            response.status_code = 200
        else:
            response.status_code = 404
    else:
        response.status_code = 401

    return response


def run():
    format_logger = '[%(time)s] %(REMOTE_ADDR)s %(status)s %(REQUEST_METHOD)s %(REQUEST_URI)s %(HTTP_REFERER)s'
    serve(TransLogger(app, format=format_logger),
          host='0.0.0.0',
          port=8080,
          url_scheme='https',
          ident=None,
          threads=6)


routine.delete_logs()
routine.delete_old_timers()
utils.logger('DB: started')
db['status'] = f'Alive since {datetime.now()}'
run()
