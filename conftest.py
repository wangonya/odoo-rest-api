import pytest

from api import create_app


@pytest.fixture(scope='session')
def client():
    app = create_app(testing=True)
    client = app.test_client()
    return client
