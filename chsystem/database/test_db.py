from secrets import token_hex

import pytest
from dotenv import dotenv_values

import db

config = dotenv_values('.env')


@pytest.fixture(autouse=True)
def setup_db():
    db_name = f'{config["DB_NAME"]}_test'
    db.db = db.get_db(config['URL_MONGODB'], db_name, wTimeoutMS=5000, w=1)

    yield

    db.get_db(config['URL_MONGODB']).drop_database(db_name)


def test_db_create_delete_server():
    server = token_hex(8)
    response = db.create_server(server, 'test_server')
    assert response['success']
    server_from_db = db.get_server(server)
    assert server_from_db['_id'] == server


def test_db_create_delete_clan():
    server = token_hex(8)
    clan = token_hex(8)
    db.create_server(server, 'test_server')
    response = db.create_clan(clan, server, 'test_clan')
    assert response['success']
    clan_from_db = db.get_clan(clan)
    assert clan_from_db['_id'] == clan


def test_db_create_delete_user():
    main_account = token_hex(8)
    pw = token_hex(8)
    server = token_hex(8)
    clan = token_hex(8)
    role = 1
    subs = [1, 2]
    bosses_type = 1
    discord_id = token_hex(8)
    id_account = db.build_id_account(server, main_account)

    db.create_server(server, 'test_server')
    db.create_clan(clan, server, 'test_clan')
    db.create_role(role, 'test_role')
    db.create_boss_type(bosses_type, 'test_type')
    for boss in subs:
        db.create_boss(boss, 'test_boss', bosses_type, 0)

    user = (main_account, pw, role, server, clan)
    response = db.create_user(*user, subs=subs, discord_id=discord_id)

    assert response['success'], response['msg']
    user_from_db = db.get_user(server, main_account)
    assert user_from_db['_id'] == id_account
    assert user_from_db['server'] == server
    assert user_from_db['clan'] == clan
    assert user_from_db['role'] == role
    assert user_from_db['subs'] == subs
    assert user_from_db['discord_id'] == discord_id

    role_stats_from_db = db.get_role_stats(role, clan)
    for user in role_stats_from_db['users']:
        if user['_id'] == id_account:
            break
    else:
        assert False

    for boss in subs:
        assert discord_id in db.get_bosses_timer(boss, clan)['subs'], f'discord_id not in {boss} subs'
