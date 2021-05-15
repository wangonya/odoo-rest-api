from xmlrpc import client

info = client.ServerProxy('https://demo.odoo.com/start').start()
url, db, username, password = \
    info['host'], info['database'], info['user'], info['password']

TESTING = True
ODOO_URL = url
ODOO_DB = db
ODOO_USER_NAME = username
ODOO_USER_PASSWORD = password
SECRET_KEY = 'test'
