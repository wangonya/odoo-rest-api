import os

from flask_restful import Resource, fields, reqparse

from v1 import api, app, common, db, models, password


class Login(Resource):
    def post(self):
        username = os.getenv('USER_NAME')
        auth = common.authenticate(
            db,
            username,
            password,
            {})  # {} -> user_agent_env

        if not auth:
            response = {'message': 'Invalid username / password'}
            return response, 401

        response = {
            'message': 'Login successful',
            'user_id': auth
        }

        return response


class SaleOrder(Resource):
    """Handles sale order creation.
    Sales orders are created as draft (Quotations).
    Confirmation is handled by `SalesOrderConfirm`"""

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            'item_name',
            type=str,
            required=True,
            help='Item name is required to create a sale order')
        self.parser.add_argument(
            'customer_name',
            type=str,
            required=True,
            help='Customer name is required to create a sale order')
        self.parser.add_argument(
            'quantity',
            type=float,
            required=True,
            help='Quantity (number) is required to create a sale order')
        super().__init__()

    resource_fields = {
        'item_id': fields.Integer,
        'customer_name': fields.String,
        'quantity': fields.Float,
    }

    def post(self):
        args = self.parser.parse_args()

        item = models.execute_kw(db, 2, password, 'product.product', 'search',
                                 [[['name', '=', args['item_name']]]])
        if item:
            item = item[0]
        else:
            item_name = args.get('item_name')
            not_found = f"Item '{item_name}' not found"
            return {'message': not_found}, 404

        customer = models.execute_kw(db, 2, password, 'res.partner', 'search',
                                     [[['name', '=', args['customer_name']]]])
        if customer:
            customer = customer[0]
        else:
            customer_name = args.get('customer_name')
            customer = models.execute_kw(db, 2, password, 'res.partner',
                                         'create', [{'name': customer_name}])

        line_vals = {
            'product_id': item,
            'product_uom_qty': args.get('quantity'),
            'price_unit': 1,
        }

        sale_order_data = {
            'partner_id': customer,
            'order_line': [(0, 0, line_vals)],
        }

        sale_order = models.execute_kw(db, 2, password, 'sale.order', 'create',
                                       [sale_order_data])

        if sale_order:
            return {'message': 'Sale order created'}, 201
        else:
            return {'message': 'Sale order creation failed'}, 400


class SaleOrderConfirm(Resource):
    """Converts quotations to confirmed sales orders
    POST is used here since only a single field (state) is being updated.
    No data is required in the body. The id to update is taked from the url.
    If flexibility was required to update more details, PATCH would be used,
    with information to update being taken from the body."""

    def post(self, sale_order_id):
        sale_order = models.execute_kw(
            db, 2, password, 'sale.order', 'write',
            [[sale_order_id], {'state': 'sale'}]
        )

        if sale_order:
            return {'message': 'Sale order confirmed'}, 200
        else:
            return {'message': 'Sale order confirmation failed'}, 400


api.add_resource(Login, '/api/v1/login')
api.add_resource(SaleOrder, '/api/v1/sale-order')
api.add_resource(
    SaleOrderConfirm,
    '/api/v1/sale-order/<int:sale_order_id>/confirm')

if __name__ == '__main__':
    app.run()
