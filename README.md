# Intelligent-Electronics-Warehouse-Resource-Management-Platform




intelligent-electronics-warehouse/
│
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── category.py
│   │   ├── product.py
│   │   ├── supplier.py
│   │   ├── inventory.py
│   │   ├── order.py
│   │   ├── order_item.py
│   │   ├── purchase_order.py
│   │   ├── purchase_order_item.py
│   │   └── notification.py
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── views.py
│   │   ├── products.py
│   │   ├── inventory.py
│   │   ├── orders.py
│   │   ├── purchase_orders.py
│   │   └── admin.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── inventory_service.py
│   │   ├── order_service.py
│   │   ├── purchase_order_service.py
│   │   └── notification_service.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── decorators.py
│   │   ├── validators.py
│   │   ├── security.py
│   │   └── error_handlers.py
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   └── inventory_worker.py
│   │
│   └── config.py
│
├── templates/
│   ├── base.html
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── customer/
│   │   ├── dashboard.html
│   │   ├── products.html
│   │   ├── product_detail.html
│   │   ├── cart.html
│   │   ├── checkout.html
│   │   └── my_orders.html
│   ├── employee/
│   │   ├── dashboard.html
│   │   ├── inventory.html
│   │   └── orders.html
│   ├── admin/
│   │   ├── dashboard.html
│   │   ├── users.html
│   │   ├── products.html
│   │   ├── suppliers.html
│   │   ├── inventory.html
│   │   └── purchase_orders.html
│   └── errors/
│       ├── 403.html
│       ├── 404.html
│       └── 500.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   ├── images/
│   │   └── logo.png
│   └── uploads/
│       └── products/
│
├── migrations/
├── scripts/
│   ├── init_db.py
│   └── seed_demo_data.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_inventory.py
│   ├── test_orders.py
│   └── test_purchase_orders.py
├── docs/
│   └── system-architecture.png
│
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── run.py
