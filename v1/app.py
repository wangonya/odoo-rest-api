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


class DeliveryOperation(Resource):
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
        args = self.parser.parse_args()

        delivery_op = models.execute_kw(db, 2, password, 'stock.picking', 'search_read', [
            [['origin', '=', args['sale_order_name']]]])

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

        serial_number = models.execute_kw(
            db, 2, password, 'stock.production.lot', 'search_read',
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

        # stock_move = models.execute_kw(
        #     db, 2, password, 'stock.move', 'search_read', [
        #         [['picking_id', '=', delivery_op_id]]])
        # stock_move_id = stock_move[0].get('id')
        # demand = stock_move[0].get('product_uom_qty')

        if serial_number[0].get('product_qty') == 0:
            return {
                'message': f"Serial number '{args['product_serial_number']}' "
                "has a quantity of 0 and cannot be used to process the delivery"}, 400

        # line_vals = {
        #     'lot_id': serial_number[0].get('id'),
        #     'qty_done': stock_move_initial_demand,
        #     'product_uom_id': serial_number[0].get('product_uom_id')[0]
        # }

        # stock_move_line = {
        #     'move_line_ids': [(0, 0, line_vals)],
        # }
        # x = models.execute_kw(
        #     db, 2, password, 'stock.move', 'write', [
        #         [stock_move_id], stock_move_line])
        # print(f"x = {x}")

        transfer = models.execute_kw(db,
                                     2,
                                     password,
                                     'stock.immediate.transfer',
                                     'create',
                                     [{'pick_ids': [delivery_op_id]}])
        models.execute_kw(db, 2, password, 'stock.immediate.transfer',
                          'process', [transfer])
        delivery_op_state = models.execute_kw(db, 2, password, 'stock.picking', 'search_read', [
            [['origin', '=', args['sale_order_name']]]], {'fields': ['state']})[0]['state']

        if delivery_op_state == 'done':
            return {'message': 'Delivery operation processed'}, 200
        else:
            return {'message': 'Delivery operation processing failed'}, 400


api.add_resource(Login, '/api/v1/login')
api.add_resource(SaleOrder, '/api/v1/sale-order')
api.add_resource(DeliveryOperation, '/api/v1/process-delivery')


if __name__ == '__main__':
    app.run()
