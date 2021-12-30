from secrets import token_hex

import db


def test_db_create_delete_server():
    server = token_hex(8)
    try:
        response = db.create_server(server, 'test_server')
        assert response['success']
        server_from_db = db.get_server(server)
        assert server_from_db['_id'] == server
    finally:
        db.delete_server(server)
        assert db.get_server(server) is None


def test_db_create_delete_clan():
    server = token_hex(8)
    clan = token_hex(8)
    try:
        db.create_server(server, 'test_server')
        response = db.create_clan(clan, server, 'test_clan')
        assert response['success']
        clan_from_db = db.get_clan(clan)
        assert clan_from_db['_id'] == clan
    finally:
        db.delete_clan(clan)
        assert db.get_clan(clan) is None

        db.delete_server(server)


def test_db_create_delete_user():
    user_main_account = token_hex(8)
    server = token_hex(8)
    clan = token_hex(8)
    role = 1
    try:
        db.create_server(server, 'test_server')
        db.create_clan(clan, server, 'test_clan')
        pw = token_hex(8)
        user = (user_main_account, pw, role, server, clan)
        response = db.create_user(*user, bosses_subbed=[1, 2], discord_id=token_hex(8))

        assert response['success']
        user_from_db = db.get_user(user_main_account, server)
        assert user_from_db['_id'] == db.build_id_account(user_main_account, server)
    finally:
        db.delete_user(user_main_account, server)
        assert db.get_user(user_main_account, server) is None

        db.delete_clan(clan)
        db.delete_server(server)
