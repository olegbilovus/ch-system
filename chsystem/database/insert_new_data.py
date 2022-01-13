import queue
import sys
import threading
from secrets import token_hex

import requests
from dotenv import dotenv_values

from database import MongoDB

config = dotenv_values('.env')
db = MongoDB(config['URL_MONGODB'], config['DB_NAME'])


def get_data(url, key):
    count = requests.get(f'{url}1').json()['TotalResults']
    return requests.get(f'{url}{count}').json()[key]


def get_servers(url, key):
    return list(requests.get(url).json()[key].values())


def worker_players(jobs, results, t_n, logs=False):
    while True:
        try:
            player = jobs.get()
            res = db.create_user(player['Name'],
                                 token_hex(8),
                                 'Created',
                                 player['ClassName'],
                                 player['Level'],
                                 player['WorldName'],
                                 player['ClanName'],
                                 change_pw=True)
            if logs:
                print(t_n, res, player['Index'])

            if res['msg'] == db.ERROR_MESSAGES['user_already_exists']:
                db.update_user(player['Name'], player['WorldName'],
                               **{'clazz': player['ClassName'], 'level': player['Level'], 'clan': player['ClanName']})
            else:
                results[t_n] = results[t_n] + 1

            if res['msg'] == db.ERROR_MESSAGES['clan_not_found']:
                db.create_clan(player['ClanName'], player['WorldName'])
                print('Clan created')
            elif res['msg'] == db.ERROR_MESSAGES['server_not_found']:
                db.create_server(player['WorldName'])
                print('Server created')
        finally:
            jobs.task_done()


def worker_clans(jobs, results, t_n, logs=False):
    while True:
        try:
            clan = jobs.get()
            res = db.create_clan(clan['ClanName'], clan['WorldName'])
            if logs:
                print(t_n, res, clan['Index'])
            if res['success']:
                results[t_n] = results[t_n] + 1
        finally:
            jobs.task_done()


def worker__servers(jobs, results, t_n, logs=False):
    while True:
        try:
            server = jobs.get()
            res = db.create_server(server)
            if logs:
                print(t_n, res)
            if res['success']:
                results[t_n] = results[t_n] + 1
        finally:
            jobs.task_done()


def worker_add_jobs(jobs, data):
    for d in data:
        jobs.put(d)


def add_jobs(data_extractor, jobs, url, key):
    data = data_extractor(url, key)
    t = threading.Thread(target=worker_add_jobs, args=(jobs, data))
    t.daemon = True
    t.start()


def create_threads(worker, jobs, results, threads, logs=False):
    for t in range(threads):
        t = threading.Thread(target=worker, args=(jobs, results, t, logs))
        t.daemon = True
        t.start()


def process(jobs, results, threads):
    jobs.join()
    for t in range(threads):
        print(f'{t} - {results[t]}')
    print(f'Total: {sum(results)}')


def main_players(threads, logs=False):
    jobs = queue.Queue()
    results = [0] * threads
    add_jobs(get_data, jobs, config['CH_PLAYERS_URL'], 'RankingDataList')
    create_threads(worker_players, jobs, results, threads, logs)
    process(jobs, results, threads)


def main_clans(threads, logs=False):
    jobs = queue.Queue()
    results = [0] * threads
    add_jobs(get_data, jobs, config['CH_CLANS_URL'], 'TheClanDataList')
    create_threads(worker_clans, jobs, results, threads, logs)
    process(jobs, results, threads)


def main_servers(threads, logs=False):
    jobs = queue.Queue()
    results = [0] * threads
    add_jobs(get_servers, jobs, config['CH_SERVERS_URL'], 'WorldDictionary')
    create_threads(worker__servers, jobs, results, threads, logs)
    process(jobs, results, threads)


if __name__ == '__main__':
    if len(sys.argv) == 4:
        thr = int(sys.argv[2])
        log = sys.argv[3] == '1'
        print('--- Start ---')
        if sys.argv[1] == 'servers':
            print('--- Insert servers ---')
            main_servers(thr, log)
        elif sys.argv[1] == 'clans':
            print('--- Insert clans ---')
            main_clans(thr, log)
        elif sys.argv[1] == 'players':
            print('--- Insert players ---')
            main_players(thr, logs=log)
    else:
        print('Usage: python3 insert_new_data.py [servers|clans|players] [threads] [logs]')
