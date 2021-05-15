from xmlrpc import client as xclient

import pytest

from api import create_app


@pytest.fixture(scope='session')
def test_app():
    app = create_app(testing=True)

    models = xclient.ServerProxy(f"{app.config['ODOO_URL']}/xmlrpc/2/object")
    app.config['ODOO_MODELS'] = models

    # create test product
    models.execute_kw(app.config['ODOO_DB'],
                      app.config['ODOO_USER_NAME'],
                      app.config['ODOO_USER_PASSWORD'],
                      'product.product',
                      'create',
                      [{'name': 'Test Product'}])
    return app


@pytest.fixture(scope='session')
def client(test_app):
    client = test_app.test_client()
    return client
