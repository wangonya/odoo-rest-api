# odoo-rest-api

## Setup

1. Install requirements (`pip install -r requirements.txt`)
2. Create an Odoo db (skip this if you want to use an existing one)
3. Update `.env`
4. Run odoo server
5. Run api server:
    - `chmod +x run_api.sh` (first time only)
    - `./run_api.sh`
6. Run tests:
    - `chmod +x run_tests.sh` (first time only)
    - `./run_tests.sh`

## Endpoints

|endpoint|method|sample request object|
|---|---|---|
|`/api/login`|`POST`|`{"username": "admin", "password": "admin"}`|
|`/api/sale-order`|`POST`|`{"item_name": "Test Product1", "customer_name": "customer", "quantity": 1}`|
|`api/process-delivery`|`POST`|`{"product_serial_number": "13", "sale_order_name": "S00040"}`|

## Implementation Details

* The `login` endpoint returns the user id if successful. This user id should be used as the username for the other endpoints.
* Basic authentication is used for the sale order and delivery order processing endpoints. Username (user id) and Password are required.
* Item name is used as the search parameter for products when creating sale orders. If there are multiple items with the same name, the first one found is used.
