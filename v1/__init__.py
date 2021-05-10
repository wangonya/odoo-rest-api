import os
from xmlrpc import client

from flask import Flask

app = Flask(__name__)

url = os.getenv('SERVER_URL')
db = os.getenv('DB_NAME')
password = os.getenv('USER_PASSWORD')

common = client.ServerProxy(f'{url}/xmlrpc/2/common')
models = client.ServerProxy(f'{url}/xmlrpc/2/object')
