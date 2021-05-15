from xmlrpc import client

from flask import current_app, request
from flask_restful import Resource, fields, reqparse


class ApiResource(Resource):
    def __init__(self):
        app = current_app

        self.url = app.config['ODOO_URL']
        self.db = app.config['ODOO_DB']
        self.common = client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.models = client.ServerProxy(f'{self.url}/xmlrpc/2/object')

        if request.authorization:
            self.username = request.authorization.username
            self.password = request.authorization.password

        super().__init__()

    def check_auth_details(self):
        return request.authorization and all(
            [request.authorization.username,
             request.authorization.password])


class Login(ApiResource):

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            'username',
            type=str,
            required=True,
            help='Username is required to log in')
        self.parser.add_argument(
            'password',
            type=str,
            required=True,
            help='Password is required to log in')
        super().__init__()

    def post(self):
        args = self.parser.parse_args()

        username = args['username']
        password = args['password']

        user = self.common.authenticate(
            self.db,
            username,
            password,
            {})  # {} -> user_agent_env

        if not user:
            response = {'message': 'Invalid username / password'}
            return response, 401

        response = {
            'message': 'Login successful',
            'user_id': user,
        }

        return response


class SaleOrder(ApiResource):
    """Handles sale order creation.
    Sales orders are created as draft (Quotations)."""

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
        if not self.check_auth_details():
            return {'message': 'Auth required'}, 401

        args = self.parser.parse_args()

        item = self.models.execute_kw(self.db,
                                      self.username,
                                      self.password,
                                      'product.product',
                                      'search',
                                      [[['name', '=', args['item_name']]]])
        if item:
            item = item[0]
        else:
            item_name = args.get('item_name')
            not_found = f"Item '{item_name}' not found"
            return {'message': not_found}, 404

        customer = self.models.execute_kw(self.db,
                                          self.username,
                                          self.password,
                                          'res.partner',
                                          'search',
                                          [[['name', '=', args['customer_name']]]])
        if customer:
            customer = customer[0]
        else:
            customer_name = args.get('customer_name')
            customer = self.models.execute_kw(self.db,
                                              self.username,
                                              self.password,
                                              'res.partner',
                                              'create',
                                              [{'name': customer_name}])

        line_vals = {
            'product_id': item,
            'product_uom_qty': args.get('quantity'),
            'price_unit': 1,
        }

        sale_order_data = {
            'partner_id': customer,
            'order_line': [(0, 0, line_vals)],
        }

        sale_order = self.models.execute_kw(
            self.db,
            self.username,
            self.password,
            'sale.order',
            'create',
            [sale_order_data])

        if sale_order:
            return {'message': 'Sale order created'}, 201
        else:
            return {'message': 'Sale order creation failed'}, 400


class DeliveryOperation(ApiResource):
    """Handles delivery operation validation.
    Full initial quantity ordered is processed by default to avoid having to create a backorder."""

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            'product_serial_number',
            type=str,
            required=True,
            help='Prduct serial number is required to validate the delivery operation')
        self.parser.add_argument(
            'sale_order_name',
            type=str,
            required=True,
            help='Sale order name is required to validate the delivery operation')
        super().__init__()

    def post(self):
        if not self.check_auth_details():
            return {'message': 'Auth required'}, 401

        args = self.parser.parse_args()

        delivery_op = self.models.execute_kw(self.db,
                                             self.username,
                                             self.password,
                                             'stock.picking',
                                             'search_read',
                                             [[['origin', '=', args['sale_order_name']]]])

        if not delivery_op:
            return {
                'message': f"Delivery operation for sale order "
                f"'{args['sale_order_name']}' not found"
            }, 404

        if delivery_op[0].get('state') in ['done', 'cancel']:
            return {
                'message': f"Cannot process delivery operation in state: "
                f"'{delivery_op[0].get('state')}'"
            }, 400

        delivery_op_id = delivery_op[0].get('id')
        product = delivery_op[0].get('product_id')[1]
        product_id = delivery_op[0].get('product_id')[0]

        serial_number = self.models.execute_kw(
            self.db, self.username, self.password, 'stock.production.lot', 'search_read',
            [[
                '&',
                ('name', '=', args['product_serial_number']),
                ('product_id', '=', product_id)
            ]]
        )

        if not serial_number:
            return {
                'message': f"Serial number '{args['product_serial_number']}' "
                f"for product '{product}' not found"
            }, 404

        if serial_number[0].get('product_qty') == 0:
            return {
                'message': f"Serial number '{args['product_serial_number']}' "
                "has a quantity of 0 and cannot be used to process the delivery"}, 400

        transfer = self.models.execute_kw(self.db,
                                          self.username,
                                          self.password,
                                          'stock.immediate.transfer',
                                          'create',
                                          [{'pick_ids': [delivery_op_id]}])
        self.models.execute_kw(
            self.db,
            self.username,
            self.password,
            'stock.immediate.transfer',
            'process',
            [transfer])
        delivery_op_state = self.models.execute_kw(self.db,
                                                   self.username,
                                                   self.password,
                                                   'stock.picking',
                                                   'search_read', [
                                                       [['origin', '=', args['sale_order_name']]]],
                                                   {'fields': ['state']})[0]['state']

        if delivery_op_state == 'done':
            return {'message': 'Delivery operation processed'}, 200
        else:
            return {'message': 'Delivery operation processing failed'}, 400
