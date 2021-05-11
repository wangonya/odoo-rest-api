install reqs
create db
update .env
init db (./odoo-bin -d odoo-rest-api -i base)
run odoo server
run this server


* item name used. for purpose of this test, if a duplicate item is found, the first one is used
* would be better to use id but we'd have to find id every time

* product id used according to product.product because that's what we'll use in SO
  * could also have used id in product.template

v1
- chmod +x run_v1.sh
- ./run_v1.sh
