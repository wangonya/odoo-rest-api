from base64 import b64encode


def test_login(client):
    response = client.post('/api/login', json={
        'username': 'admin', 'password': 'admin'
    })

    assert response.status_code == 200
    assert response.get_json()['message'] == 'Login successful'


def test_login_failure(client):
    response = client.post('/api/login', json={
        'username': 'badadmin', 'password': 'badadmin'
    })

    assert response.status_code == 401
    assert response.get_json()['message'] == 'Invalid username / password'


def test_create_sale_order(client):
    data = {
        "item_name": "Test Product",
        "customer_name": "customer",
        "quantity": 1
    }
    response = client.post('/api/sale-order', json=data)

    assert response.status_code == 201
    assert response.get_json()['message'] == 'Sale order created'


def test_sale_order_404_if_product_does_not_exist(client):
    data = {
        "item_name": "Bad Test Product",
        "customer_name": "customer",
        "quantity": 1
    }
    response = client.post('/api/sale-order', json=data)

    assert response.status_code == 404
    assert response.get_json(
    )['message'] == "Item 'Bad Test Product' not found"


def test_sale_order_customer_created_if_does_not_exist(client, test_app):
    models = test_app.config['ODOO_MODELS']
    customer_name = "New Koko Test Customer"
    customer = models.execute_kw(test_app.config['ODOO_DB'],
                                 test_app.config['ODOO_USER_NAME'],
                                 test_app.config['ODOO_USER_PASSWORD'],
                                 'res.partner',
                                 'search',
                                 [[['name', '=', customer_name]]])

    assert customer == []

    data = {
        "item_name": "Test Product",
        "customer_name": customer_name,
        "quantity": 1
    }
    response = client.post('/api/sale-order', json=data)

    assert response.status_code == 201

    customer = models.execute_kw(test_app.config['ODOO_DB'],
                                 test_app.config['ODOO_USER_NAME'],
                                 test_app.config['ODOO_USER_PASSWORD'],
                                 'res.partner',
                                 'search',
                                 [[['name', '=', customer_name]]])

    assert customer != []


def test_process_delivery_404_if_does_not_exist(client):
    data = {
        "product_serial_number": "12",
        "sale_order_name": "Bad Sale Order"
    }
    response = client.post('/api/process-delivery', json=data)

    assert response.status_code == 404
    assert response.get_json(
    )['message'] == "Delivery operation for sale order 'Bad Sale Order' not found"
