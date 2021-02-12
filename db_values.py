from replit import db

import utils

db['default'] = utils.BOSSES

for key in db.keys():
    print(key, db[key])
