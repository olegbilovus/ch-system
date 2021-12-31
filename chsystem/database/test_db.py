from secrets import token_hex

import pytest
from dotenv import dotenv_values

import db

config = dotenv_values('.env')


@pytest.fixture(autouse=True, scope='session')
def setup_db():
    db_name = f'{config["DB_NAME"]}_test_database'
    db.get_db(config['URL_MONGODB']).drop_database(db_name)
    db.db = db.get_db(config['URL_MONGODB'], db_name, wTimeoutMS=5000, w=1)

    yield

    db.get_db(config['URL_MONGODB']).drop_database(db_name)


def test_db_create_delete_server():
    server = token_hex(8)
    response = db.create_server(server)
    assert response['success']
    server_from_db = db.get_server(server)
    assert server_from_db['server'] == server


def test_db_create_delete_clan():
    server = token_hex(8)
    clan = token_hex(8)
    db.create_server(server)
    response = db.create_clan(clan, server)
    assert response['success']
    clan_from_db = db.get_clan(clan, server)
    assert clan_from_db['clan'] == clan
    assert clan_from_db['server'] == server


def test_db_create_delete_user():
    server = token_hex(8)
    clan = token_hex(8)
    main_account = token_hex(8)
    pw = token_hex(8)
    role = 1
    clazz = 'Druid'
    level = 50
    subs = [1, 2]
    bosses_type = 1
    discord_id = token_hex(8)

    db.create_server(server)
    db.create_clan(clan, server)
    db.create_role(role)
    db.create_boss_type(bosses_type, )
    for boss in subs:
        db.create_boss(boss, bosses_type, 0)

    user = (main_account, pw, role, clazz, level, server, clan)
    response = db.create_user(*user, subs=subs, discord_id=discord_id)

    assert response['success'], response['msg']
    user_from_db = db.get_user(server, main_account)
    assert user_from_db['main_account'] == main_account
    assert user_from_db['server'] == server
    assert user_from_db['clan'] == clan
    assert user_from_db['role'] == role
    assert user_from_db['class'] == clazz
    assert user_from_db['level'] == level
    assert user_from_db['subs'] == subs
    assert user_from_db['discord_id'] == discord_id

    role_stats_from_db = db.get_role_stats(role, clan, server)
    assert role_stats_from_db['count_users'] == 1

    for boss in subs:
        assert discord_id in db.get_bosses_timer(boss, clan, server)['subs'], f'discord_id not in {boss} subs'
