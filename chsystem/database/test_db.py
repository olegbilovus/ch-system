from random import randint
from secrets import token_hex

import bcrypt
import pytest
from dotenv import dotenv_values

import db

config = dotenv_values('.env')


def generate_user():
    server = token_hex(8)
    clan = token_hex(8)
    main_account = token_hex(8)
    pw = str(token_hex(8))
    role = randint(1, 5)
    clazz = token_hex(8)
    level = randint(1, 240)
    subs = [x for x in range(randint(1, 10))]
    bosses_type_len = randint(3, 10)
    bosses_types = [x for x in range(bosses_type_len)]
    discord_id = token_hex(8)

    db.create_server(server)
    db.create_clan(clan, server)
    db.create_role(role)
    for bosses_type in bosses_types:
        db.create_boss_type(bosses_type)
    for boss in subs:
        db.create_boss(boss, randint(1, bosses_type_len - 1), randint(10, 2000))

    return main_account, pw, role, clazz, level, server, clan, subs, discord_id


def asserts_user(user):
    user_from_db = db.get_user(user['server'], user['main_account'])
    assert user_from_db['main_account'] == user['main_account']
    assert bcrypt.checkpw(user['pw'].encode('utf-8'), user_from_db['hash_pw'].encode('utf-8'))
    assert user_from_db['role'] == user['role']
    assert user_from_db['class'] == user['class']
    assert user_from_db['level'] == user['level']
    assert user_from_db['server'] == user['server']
    assert user_from_db['clan'] == user['clan']
    assert user_from_db['subs'] == user['subs']
    assert user_from_db['discord_id'] == user['discord_id']

    role_stats_from_db = db.get_role_stats(user['role'], user['clan'], user['server'])
    assert role_stats_from_db['count_users'] == 1
    server_from_db = db.get_server(user['server'])
    assert server_from_db['count_users'] == 1
    clan_from_db = db.get_clan(user['clan'], user['server'])
    assert clan_from_db['count_users'] == 1

    for boss in user['subs']:
        assert user['discord_id'] in db.get_bosses_timer(boss, user['clan'], user['server'])[
            'subs'], f'discord_id not in {boss} subs'


@pytest.fixture(autouse=True, scope='session')
def setup_db():
    db_name = config['DB_NAME_TEST']
    db_url = config['URL_MONGODB_TEST']

    db.get_db(db_url).drop_database(db_name)
    db.db = db.get_db(db_url, db_name, wTimeoutMS=5000, w=1)

    yield

    db.get_db(db_url).drop_database(db_name)


def test_create_boss_01():
    """Test to create a boss with invalid boss type"""
    boss = 1
    boss_type = 1
    response = db.create_boss(boss, boss_type, 0)
    assert not response['success']
    assert response['msg'] == db.ERROR_MESSAGES['boss_type_not_found']


def test_create_boss_02():
    """Test to create a boss which already exists"""
    boss = 1
    _type = 1
    db.create_boss_type(_type)
    db.create_boss(boss, _type, 0)
    response = db.create_boss(boss, _type, 0)
    assert not response['success']
    assert response['msg'] == db.ERROR_MESSAGES['boss_already_exists']


def test_create_boss_type_01():
    """Test to create a type which already exists"""
    boss_type = 1
    db.create_boss_type(boss_type)
    response = db.create_boss_type(boss_type)
    assert not response['success']
    assert response['msg'] == db.ERROR_MESSAGES['boss_type_already_exists']


def test_create_server_01():
    """Test to create a server"""
    server = token_hex(8)
    response = db.create_server(server)
    assert response['success'], response['msg']
    server_from_db = db.get_server(server)
    assert server_from_db['server'] == server


def test_delete_server_01():
    """Test to delete a server"""
    server = token_hex(8)
    db.create_server(server)
    response = db.delete_server(server)
    assert response['success'], response['msg']
    assert not db.get_server(server)


def test_delete_server_02():
    """Test to delete a server which doesn't exist"""
    server = token_hex(8)
    response = db.delete_server(server)
    assert not response['success']
    assert response['msg'] == db.ERROR_MESSAGES['server_not_found']


def test_create_clan_01():
    """Test to create a clan"""
    server = token_hex(8)
    clan = token_hex(8)
    db.create_server(server)
    response = db.create_clan(clan, server)
    assert response['success'], response['msg']
    clan_from_db = db.get_clan(clan, server)
    assert clan_from_db['clan'] == clan
    assert clan_from_db['server'] == server


def test_delete_clan_01():
    """Test to delete a clan"""
    server = token_hex(8)
    clan = token_hex(8)
    db.create_server(server)
    db.create_clan(clan, server)
    response = db.delete_clan(clan, server)
    assert response['success'], response['msg']
    assert not db.get_clan(clan, server)


def test_delete_clan_02():
    """Test to delete a clan which doesn't exist"""
    server = token_hex(8)
    clan = token_hex(8)
    db.create_server(server)
    response = db.delete_clan(clan, server)
    assert not response['success']
    assert response['msg'] == db.ERROR_MESSAGES['clan_not_found']


def test_create_user_01():
    """Test to create a user"""
    main_account, pw, role, clazz, level, server, clan, subs, discord_id = generate_user()
    user = (main_account, pw, role, clazz, level, server, clan)
    response = db.create_user(*user, subs=subs, discord_id=discord_id)

    assert response['success'], response['msg']
    asserts_user(
        {'main_account': main_account, 'pw': pw, 'role': role, 'class': clazz, 'level': level, 'server': server,
         'clan': clan, 'subs': subs, 'discord_id': discord_id})


def test_delete_user_01():
    """Test to delete a user"""
    main_account, pw, role, clazz, level, server, clan, subs, discord_id = generate_user()
    user = (main_account, pw, role, clazz, level, server, clan)
    db.create_user(*user, subs=subs, discord_id=discord_id)

    response = db.delete_user(main_account, server)
    assert response['success'], response['msg']
    assert not db.get_user(server, main_account)

    role_stats_from_db = db.get_role_stats(role, clan, server)
    assert role_stats_from_db['count_users'] == 0
    server_from_db = db.get_server(server)
    assert server_from_db['count_users'] == 0
    clan_from_db = db.get_clan(clan, server)
    assert clan_from_db['count_users'] == 0

    for boss in subs:
        assert discord_id not in db.get_bosses_timer(boss, clan, server)['subs'], f'discord_id in {boss} subs'


def test_update_user_01():
    """Test to update a user"""
    main_account, pw, role, clazz, level, server, clan, subs, discord_id = generate_user()
    user = (main_account, pw, role, clazz, level, server, clan)
    db.create_user(*user, subs=subs, discord_id=discord_id)

    main_account2, pw, role2, clazz, level, server2, clan2, subs2, discord_id = generate_user()
    response = db.update_user(main_account, server, clan=clan2, pw=pw, role=role2, clazz=clazz, level=level, subs=subs2,
                              discord_id=discord_id)

    assert response['success'], response['msg']
    asserts_user(
        {'main_account': main_account, 'pw': pw, 'role': role2, 'class': clazz, 'level': level, 'server': server,
         'clan': clan2, 'subs': subs2, 'discord_id': discord_id})

    role_stats_from_db = db.get_role_stats(role, clan, server)
    assert role_stats_from_db['count_users'] == 0
    clan_from_db = db.get_clan(clan, server)
    assert clan_from_db['count_users'] == 0

    for boss in subs:
        assert discord_id not in db.get_bosses_timer(boss, clan, server)['subs'], f'discord_id in {boss} subs'
