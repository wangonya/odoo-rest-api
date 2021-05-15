from xmlrpc import client

info = client.ServerProxy('https://demo.odoo.com/start').start()
url, db, password = \
    info['host'], info['database'], info['password']

TESTING = True
ODOO_URL = url
ODOO_DB = db
ODOO_USER_NAME = 2  # usual admin user id
ODOO_USER_PASSWORD = password
SECRET_KEY = 'test'
