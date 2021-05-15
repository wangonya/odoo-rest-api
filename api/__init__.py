from flask import Flask
from flask_restful import Api

from .endpoints import DeliveryOperation, Login, SaleOrder


def create_app(testing=False):
    app = Flask(__name__, instance_relative_config=True)

    if testing:
        app.config.from_pyfile('test_config.py')
    else:
        app.config.from_pyfile('config.py')

    api = Api(app)
    api.add_resource(Login, '/api/login')
    api.add_resource(SaleOrder, '/api/sale-order')
    api.add_resource(DeliveryOperation, '/api/process-delivery')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run()
