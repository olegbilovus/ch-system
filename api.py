from replit import db
import uuid

key = 'api_keys'


def create(user):
    id = uuid.uuid4().hex
    api_keys = {}

    try:
        api_keys = db[key]
    except KeyError:
        pass

    api_keys[user] = id
    db[key] = api_keys

    return id


def get(user):
    return db[key][user]


def get_all():
    return db[key]


def delete(user):
    api_keys = get_all()
    del api_keys[user]
    db[key] = api_keys


def delete_all():
    del db[key]


if __name__ == '__main__':
    print(create('BrandonHeath'))
    print(get_all())
