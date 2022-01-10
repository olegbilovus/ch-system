import sys
import threading
from secrets import token_hex

import requests
from dotenv import dotenv_values

import db

config = dotenv_values('.env')


def get_data(url, key):
    count = requests.get(f'{url}1').json()['TotalResults']
    return requests.get(f'{url}{count}').json()[key]


def get_servers(url):
    return list(requests.get(url).json()['WorldDictionary'].values())


def insert_players(players, t_n, logs=False):
    print('---', t_n, len(players))
    new_users = 0
    for player in players:
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
            new_users += 1

        if res['msg'] == db.ERROR_MESSAGES['clan_not_found']:
            db.create_clan(player['ClanName'], player['WorldName'])
            print('Clan created')
        elif res['msg'] == db.ERROR_MESSAGES['server_not_found']:
            db.create_server(player['WorldName'])
            print('Server created')
    print('---', t_n, new_users)


def insert_servers(servers, t_n, logs=False):
    for server in servers:
        res = db.create_server(server)
        if logs:
            print(t_n, res)


def insert_clans(clans, t_n, logs=False):
    for clan in clans:
        res = db.create_clan(clan['ClanName'], clan['WorldName'])
        if logs:
            print(t_n, res, clan['Index'])


def threads_create_start(data, threads, target, logs=False):
    data_len = len(data)
    mult = data_len // threads

    for i in range(threads):
        start = i * mult
        if i < threads - 1:
            t = threading.Thread(target=target,
                                 args=(data[start:(i + 1) * mult], i + 1, logs))
            print(i + 1, start, (i + 1) * mult)
        else:
            t = threading.Thread(target=target,
                                 args=(data[start:data_len - 1], i + 1, logs))
            print(i + 1, start, data_len - 1)
        t.start()


if __name__ == '__main__':
    if len(sys.argv) == 4:
        db.db = db.get_db(config['URL_MONGODB'], config['DB_NAME'], wTimeoutMS=5000, w=1)
        thr = int(sys.argv[2])
        log = sys.argv[3] == '1'
        print('--- Start ---')
        if sys.argv[1] == 'servers':
            print('--- Insert servers ---')
            threads_create_start(get_servers(config['CH_SERVERS_URL']), thr, insert_servers, logs=log)
        elif sys.argv[1] == 'clans':
            print('--- Insert clans ---')
            threads_create_start(get_data(config['CH_CLANS_URL'], 'TheClanDataList'), thr, insert_clans, logs=log)
        elif sys.argv[1] == 'players':
            print('--- Insert players ---')
            threads_create_start(get_data(config['CH_PLAYERS_URL'], 'RankingDataList'), thr, insert_players, logs=log)
    else:
        print('Usage: python3 insert_new_data.py [servers|clans|players] [threads] [logs]')
