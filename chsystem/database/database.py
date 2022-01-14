import bcrypt
import pymongo


class MongoDB:
    ERROR_MESSAGES = {
        'boss_not_found': 'Boss not found',
        'boss_already_exists': 'Boss already exists',
        'user_not_found': 'User not found',
        'user_already_exists': 'User already exists',
        'user_no_discord_id': 'User has no discord id',
        'role_not_found': 'Role not found',
        'role_already_exists': 'Role already exists',
        'clan_not_found': 'Clan not found',
        'clan_already_exists': 'Clan already exists',
        'server_not_found': 'Server not found',
        'server_already_exists': 'Server already exists',
        'sub_already_exists': 'Sub already exists',
        'sub_not_found': 'Sub not found',
    }

    PROJECTS_MONGODB = {
        'check': {'_id': 1},
        'user.discord_id': {'discord_id': 1},
    }

    def __init__(self, url_db, server_name, *vargs, **kwargs):
        self._db = pymongo.MongoClient(url_db, *vargs, **kwargs)
        self.db = self._db[server_name]

    def get_bosses(self):
        return self.db.boss.find({})

    def check_boss_is_valid(self, boss):
        return self.db.boss.find_one({'boss': boss}, MongoDB.PROJECTS_MONGODB['check'])

    def create_boss(self, boss, _type, reset, alias=None):
        if self.check_boss_is_valid(boss):
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['boss_already_exists']}
        self.db.boss.insert_one({'boss': boss, 'type': _type, 'reset': reset, 'alias': alias})
        return {'success': True, 'msg': 'Boss created'}

    def get_bosses_timer(self, boss, clan, server, project=None):
        return self.db.boss_timer.find_one({'boss': boss, 'server': server, 'clan': clan}, project)

    def get_user(self, server, main_account, project=None):
        return self.db.user.find_one({'server': server, 'main_account': main_account}, project)

    def create_user(self,
                    main_account,
                    pw,
                    role,
                    clazz,
                    level,
                    server,
                    clan,
                    subs=None,
                    discord_id=None,
                    alts=None,
                    bans=None,
                    notes=None,
                    change_pw=False):
        if self.get_user(server, main_account, MongoDB.PROJECTS_MONGODB['check']) is not None:
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['user_already_exists']}
        user_references = self.check_user_references_exists(clan, server)
        if not user_references['success']:
            return user_references
        if not self.check_role_is_valid(role):
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['role_not_found']}

        self.db.user.insert_one({
            'main_account': main_account,
            'role': role,
            'server': server,
            'clan': clan,
            'class': clazz,
            'level': level,
            'discord_id': discord_id,
            'alts': alts if alts else [],
            'bans': bans if bans else [],
            'notes': notes if notes else [],
            'subs': [],
            'hash_pw': bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'change_pw': change_pw,
            'last_login': 0,
            'count_login': 0,
            'count_bosses_reset': 0
        })

        self.db.role_stats.update_one({'role': role, 'server': server, 'clan': clan}, {'$inc': {'count_users': 1}},
                                      upsert=True)
        self.db.server.update_one({'server': server}, {'$inc': {'count_users': 1}})
        self.db.clan.update_one({'server': server, 'clan': clan}, {'$inc': {'count_users': 1}})
        if subs:
            for boss in subs:
                if not self.check_boss_is_valid(boss):
                    return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['boss_not_found']}
                response = self.add_sub_to_boss_timer(server, clan, main_account, boss)
                if not response['success']:
                    return response

        return {'success': True, 'msg': 'User account created'}

    def delete_user(self, main_account, server):
        user = self.get_user(server, main_account)
        if not user:
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['user_not_found']}
        self.db.role_stats.update_one({'role': user['role'], 'server': server, 'clan': user['clan']},
                                      {'$inc': {'count_users': -1}})
        self.db.server.update_one({'server': server}, {'$inc': {'count_users': -1}})
        self.db.clan.update_one({'server': server, 'clan': user['clan']}, {'$inc': {'count_users': -1}})
        if 'subs' in user:
            for boss in user['subs']:
                response = self.remove_sub_from_boss_timer(
                    server, user['clan'], main_account, boss)
                if not response['success']:
                    return response
        self.db.user.delete_one({'server': server, 'main_account': main_account})

        return {'success': True, 'msg': 'User account deleted'}

    def update_user(self, main_account, server, **kwargs):
        user = self.get_user(server, main_account)
        if not user:
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['user_not_found']}
        old_clan = user['clan']
        if 'clan' in kwargs and kwargs['clan'] != old_clan:
            self.db.clan.update_one({'server': server, 'clan': old_clan}, {'$inc': {'count_users': -1}})
            self.db.clan.update_one({'server': server, 'clan': kwargs['clan']}, {'$inc': {'count_users': 1}},
                                    upsert=True)
            user['clan'] = kwargs['clan']
        if 'role' in kwargs and kwargs['role'] != user['role']:
            if not self.check_role_is_valid(kwargs['role']):
                return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['role_not_found']}
            self.db.role_stats.update_one({'role': user['role'], 'server': server, 'clan': old_clan},
                                          {'$inc': {'count_users': -1}})
            self.db.role_stats.update_one({'role': kwargs['role'], 'server': server, 'clan': user['clan']},
                                          {'$inc': {'count_users': 1}}, upsert=True)
            user['role'] = kwargs['role']
        if 'clazz' in kwargs:
            user['class'] = kwargs['clazz']
        if 'pw' in kwargs:
            user['hash_pw'] = bcrypt.hashpw(str.encode(kwargs['pw']), bcrypt.gensalt()).decode()
        if 'level' in kwargs:
            user['level'] = kwargs['level']
        if 'discord_id' in kwargs:
            user['discord_id'] = kwargs['discord_id']
        if 'alts' in kwargs:
            user['alts'] = kwargs['alts']
        if 'bans' in kwargs:
            user['bans'] = kwargs['bans']
        if 'notes' in kwargs:
            user['notes'] = kwargs['notes']
        if 'change_pw' in kwargs:
            user['change_pw'] = kwargs['change_pw']
        if 'last_login' in kwargs:
            user['last_login'] = kwargs['last_login']
        if 'count_login' in kwargs:
            user['count_login'] = kwargs['count_login']
        if 'count_bosses_reset' in kwargs:
            user['count_bosses_reset'] = kwargs['count_bosses_reset']
        if 'subs' in kwargs and kwargs['subs'] != user['subs']:
            for boss in user['subs']:
                response = self.remove_sub_from_boss_timer(
                    server, old_clan, main_account, boss)
                if not response['success']:
                    return response
            user['subs'] = []
            self.db.user.update_one({'server': server, 'main_account': main_account}, {'$set': user})
            for boss in kwargs['subs']:
                if not self.check_boss_is_valid(boss):
                    return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['boss_not_found']}
                response = self.add_sub_to_boss_timer(server, user['clan'], user['main_account'], boss)
                if not response['success']:
                    return response
        else:
            self.db.user.update_one({'server': server, 'main_account': main_account}, {'$set': user})

        return {'success': True, 'msg': 'User account updated'}

    def get_user_details(self, server, main_account):
        return self.db.user.find_one({'server': server, 'main_account': main_account},
                                     {'_id': 0, 'alts': 1, 'bans': 1, 'notes': 1})

    def get_user_sensitive(self, server, main_account):
        return self.db.user_sensitive.find_one({'server': server, 'main_account': main_account},
                                               {'_id': 0, 'hash_pw': 1, 'change_pw': 1})

    def get_user_stats(self, server, main_account, project=None):
        return self.db.user_stats.find_one({'server': server, 'main_account': main_account},
                                           {'_id': 0, 'last_login': 1, 'count_login': 1, 'count_bosses_reset': 1},
                                           project)

    def get_role_stats(self, role, clan, server, project=None):
        return self.db.role_stats.find_one({'role': role, 'server': server, 'clan': clan}, project)

    def get_roles(self):
        return self.db.role.find({})

    def check_role_is_valid(self, role):
        return self.db.role.find_one({'role': role}, MongoDB.PROJECTS_MONGODB['check'])

    def create_role(self, role, name):
        if self.check_role_is_valid(role):
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['role_already_exists']}
        self.db.role.insert_one({'role': role, 'name': name})
        return {'success': True, 'msg': 'Role created'}

    def get_clan(self, clan, server, project=None):
        return self.db.clan.find_one({'server': server, 'clan': clan}, project)

    def create_clan(self, clan, server, count_users=0):
        if self.get_clan(clan, server, MongoDB.PROJECTS_MONGODB['check']):
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['clan_already_exists']}
        if not self.get_server(server, MongoDB.PROJECTS_MONGODB['check']):
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['server_not_found']}

        self.db.clan.insert_one({'clan': clan, 'server': server, 'count_users': count_users})
        return {'success': True, 'msg': 'Clan created'}

    def delete_clan(self, clan, server):
        if not self.get_clan(clan, server, MongoDB.PROJECTS_MONGODB['check']):
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['clan_not_found']}

        self.db.clan.delete_one({'server': server, 'clan': clan})
        self.db.role_stats.delete_many({'server': server, 'clan': clan})
        self.db.boss_timer.delete_many({'server': server, 'clan': clan})
        return {'success': True, 'msg': 'Clan deleted'}

    def get_server(self, server, project=None):
        return self.db.server.find_one({'server': server}, project)

    def create_server(self, server, count_users=0, status='Online'):
        if self.get_server(server, MongoDB.PROJECTS_MONGODB['check']):
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['server_already_exists']}

        self.db.server.insert_one({'server': server, 'count_users': count_users, 'status': status})
        return {'success': True, 'msg': 'Server created'}

    def delete_server(self, server):
        if not self.get_server(server, MongoDB.PROJECTS_MONGODB['check']):
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['server_not_found']}

        self.db.server.delete_one({'server': server})
        return {'success': True, 'msg': 'Server deleted'}

    def check_user_references_exists(self, clan, server):
        if self.get_clan(clan, server, MongoDB.PROJECTS_MONGODB['check']) is None:
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['clan_not_found']}
        if self.get_server(server, MongoDB.PROJECTS_MONGODB['check']) is None:
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['server_not_found']}
        return {'success': True, 'msg': 'User references exists'}

    def add_sub_to_boss_timer(self, server, clan, main_account, boss):
        user = self.get_user(server, main_account, MongoDB.PROJECTS_MONGODB['user.discord_id'])
        if not user:
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['user_not_found']}
        if not user['discord_id']:
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['user_no_discord_id']}
        if self.db.boss_timer.find_one(
                {'server': server, 'boss': boss, 'clan': clan, 'subs': {'$in': [user['discord_id']]}},
                MongoDB.PROJECTS_MONGODB['check']):
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['sub_already_exists']}

        self.db.user.update_one({'server': server, 'main_account': main_account}, {'$push': {'subs': boss}})
        self.db.boss_timer.update_one({'server': server, 'boss': boss, 'clan': clan},
                                      {'$push': {'subs': user['discord_id']}},
                                      upsert=True)

        return {'success': True, 'msg': 'User added to boss timer subs'}

    def remove_sub_from_boss_timer(self, server, clan, main_account, boss):
        user = self.get_user(server, main_account, MongoDB.PROJECTS_MONGODB['user.discord_id'])
        if not user:
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['user_not_found']}
        if not user['discord_id']:
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['user_no_discord_id']}
        if not self.db.boss_timer.find_one(
                {'server': server, 'boss': boss, 'clan': clan, 'subs': {'$in': [user['discord_id']]}}):
            return {'success': False, 'msg': MongoDB.ERROR_MESSAGES['sub_not_found']}

        self.db.user.update_one({'server': server, 'main_account': main_account}, {
            '$pull': {'subs': boss}})
        self.db.boss_timer.update_one({'server': server, 'boss': boss, 'clan': clan}, {
            '$pull': {'subs': user['discord_id']}})

        return {'success': True, 'msg': 'User removed from boss timer subs'}
