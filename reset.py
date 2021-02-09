from replit import db

for key in db.keys():
  if key.endswith('sub'):
    print(key)
    del db[key]