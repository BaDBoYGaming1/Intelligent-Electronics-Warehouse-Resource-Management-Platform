# Intelligent Electronics Warehouse Resource Management Platform

## Project Structure

```text
intelligent-electronics-warehouse/
|
|-- app/
|   |-- __init__.py
|   |-- extensions.py
|   |-- config.py
|   |-- models/
|   |   |-- __init__.py
|   |   |-- user.py
|   |   |-- category.py
|   |   |-- product.py
|   |   |-- supplier.py
|   |   |-- inventory.py
|   |   |-- order.py
|   |   |-- order_item.py
|   |   |-- purchase_order.py
|   |   |-- purchase_order_item.py
|   |   |-- notification.py
|   |-- routes/
|   |   |-- __init__.py
|   |   |-- auth.py
|   |   |-- views.py
|   |   |-- products.py
|   |   |-- inventory.py
|   |   |-- orders.py
|   |   |-- purchase_orders.py
|   |   |-- admin.py
|   |-- services/
|   |   |-- __init__.py
|   |   |-- auth_service.py
|   |   |-- inventory_service.py
|   |   |-- order_service.py
|   |   |-- purchase_order_service.py
|   |   |-- notification_service.py
|   |-- utils/
|   |   |-- __init__.py
|   |   |-- decorators.py
|   |   |-- validators.py
|   |   |-- security.py
|   |   |-- error_handlers.py
|   |-- workers/
|   |   |-- __init__.py
|   |   |-- inventory_worker.py
|
|-- templates/
|   |-- base.html
|   |-- auth/
|   |   |-- login.html
|   |   |-- register.html
|   |-- customer/
|   |   |-- dashboard.html
|   |   |-- products.html
|   |   |-- product_detail.html
|   |   |-- cart.html
|   |   |-- checkout.html
|   |   |-- my_orders.html
|   |-- employee/
|   |   |-- dashboard.html
|   |   |-- inventory.html
|   |   |-- orders.html
|   |-- admin/
|   |   |-- dashboard.html
|   |   |-- users.html
|   |   |-- products.html
|   |   |-- suppliers.html
|   |   |-- inventory.html
|   |   |-- purchase_orders.html
|   |-- errors/
|       |-- 403.html
|       |-- 404.html
|       |-- 500.html
|
|-- static/
|   |-- css/style.css
|   |-- js/app.js
|   |-- images/logo.png
|   |-- uploads/products/
|
|-- migrations/
|-- scripts/
|   |-- init_db.py
|   |-- seed_demo_data.py
|-- tests/
|   |-- conftest.py
|   |-- test_auth.py
|   |-- test_inventory.py
|   |-- test_orders.py
|   |-- test_purchase_orders.py
|-- docs/
|   |-- system-architecture.png
|
|-- .env.example
|-- .gitignore
|-- requirements.txt
|-- README.md
|-- run.py
```

> **Note:** This is a recommended target structure. Actual filenames and folders may differ depending on the implementation. Keep the existing structure where appropriate, and only include files that exist or are intentionally created and configured.

## Folder and File Descriptions

### 1. `app/` — Main Application

Contains the main Flask application code.

- **`__init__.py`** — Creates the Flask application, loads configuration, initializes extensions, registers blueprints, and sets up error handlers.
- **`extensions.py`** — Initializes shared extensions such as SQLAlchemy, CSRF protection, and login management.
- **`config.py`** — Loads application settings and environment variables. Do not store real passwords or secret keys in source code.

### 2. `app/models/` — Database Models

Defines database tables, fields, relationships, and constraints.

- **`user.py`** — Stores customer, employee, and administrator information, including password hashes and roles.
- **`category.py`** — Stores product categories.
- **`product.py`** — Stores product details, prices, SKUs, and image references.
- **`supplier.py`** — Stores supplier information.
- **`inventory.py`** — Tracks available stock and reorder thresholds.
- **`order.py`** — Stores customer orders and order statuses.
- **`order_item.py`** — Stores individual products and quantities within each order.
- **`purchase_order.py`** — Stores purchase orders created for suppliers.
- **`purchase_order_item.py`** — Stores products and quantities included in supplier orders.
- **`notification.py`** — Stores low-stock alerts and other notifications.

### 3. `app/routes/` — Request Handling

Handles incoming HTTP requests and returns responses.

- **`auth.py`** — Manages registration, login, and logout.
- **`views.py`** — Handles home pages and role-specific dashboards.
- **`products.py`** — Handles product listing, details, creation, and updates.
- **`inventory.py`** — Handles inventory viewing and authorized stock adjustments.
- **`orders.py`** — Handles checkout, customer orders, and order status updates.
- **`purchase_orders.py`** — Handles supplier purchase orders and stock receiving.
- **`admin.py`** — Handles administrator-only operations.

Routes should enforce authentication and authorization, validate requests, call services for business logic, and return templates, redirects, or JSON responses.

### 4. `app/services/` — Business Logic

Contains reusable business logic that can be called by routes, background workers, and tests.

- **`auth_service.py`** — Handles authentication-related operations.
- **`inventory_service.py`** — Manages stock updates and low-stock detection.
- **`order_service.py`** — Handles order creation, total calculation, inventory changes, and status transitions.
- **`purchase_order_service.py`** — Manages supplier orders and stock receiving.
- **`notification_service.py`** — Creates and manages system notifications.

Database-changing workflows should use appropriate transactions and concurrency controls.

### 5. `app/utils/` — Shared Utilities

Contains reusable helper functions and security utilities.

- **`decorators.py`** — Provides authentication and role-checking decorators.
- **`validators.py`** — Validates user input, quantities, prices, and uploaded files.
- **`security.py`** — Contains shared security-related helper functions.
- **`error_handlers.py`** — Handles application errors and displays appropriate error pages.

### 6. `app/workers/` — Background Processing

- **`inventory_worker.py`** — Periodically checks stock levels and generates low-stock alerts.

For production, run background jobs under a managed process and use suitable cross-process coordination to prevent duplicate work.

### 7. `templates/` — Frontend Pages

Contains HTML and Jinja templates for the web interface.

- **`base.html`** — Common layout, navigation, and shared page elements.
- **`auth/`** — Login and registration pages.
- **`customer/`** — Customer dashboard, product catalogue, product details, cart, checkout, and order history.
- **`employee/`** — Employee dashboard, inventory, and order-processing pages.
- **`admin/`** — Administrator dashboards and management pages.
- **`errors/`** — Error pages for forbidden access, missing pages, and server errors.

Templates should display data passed by routes and should not directly query the database.

### 8. `static/` — Frontend Assets

- **`css/style.css`** — Website styling and responsive layouts.
- **`js/app.js`** — Frontend interactions and non-sensitive UI behavior.
- **`images/`** — Fixed project images, logos, and icons.
- **`uploads/products/`** — Runtime product images, if local filesystem storage is configured.

Do not commit private uploads or rely on GitHub to store runtime user uploads.

### 9. `migrations/` — Database Schema Changes

Stores version-controlled database schema changes when Flask-Migrate/Alembic is configured. Migrations help other developers create or update tables consistently.

### 10. `scripts/` — Setup and Sample Data

- **`init_db.py`** — Initializes the database using the project's supported setup process.
- **`seed_demo_data.py`** — Adds optional sample data for demonstration and testing.

Scripts should not automatically erase existing data or create publicly accessible accounts with hardcoded passwords.

### 11. `tests/` — Automated Tests

- **`conftest.py`** — Shared test fixtures and configuration.
- **`test_auth.py`** — Tests authentication and role restrictions.
- **`test_inventory.py`** — Tests stock updates and low-stock detection.
- **`test_orders.py`** — Tests checkout, order totals, and inventory updates.
- **`test_purchase_orders.py`** — Tests purchase-order workflows and duplicate-receipt prevention.

Use an isolated test database and never run destructive tests against production data.

### 12. `docs/` — Documentation and Diagrams

- **`system-architecture.png`** — High-level system architecture diagram.

### 13. Root-Level Files

- **`.env.example`** — Example environment variables with placeholder values only.
- **`.gitignore`** — Excludes virtual environments, secrets, caches, and temporary files.
- **`requirements.txt`** — Lists required Python packages.
- **`README.md`** — Project overview, installation instructions, configuration, usage, and troubleshooting.
- **`run.py`** — Application startup entry point, if used by the project.

## Technology Stack

- **Backend:** Python and Flask
- **Frontend:** HTML, CSS, JavaScript, and Jinja
- **Database:** MySQL
- **ORM:** SQLAlchemy / Flask-SQLAlchemy
- **Security:** Authentication, role-based authorization, input validation, and CSRF protection
- **Background Processing:** Inventory monitoring and low-stock alerts
- **Testing:** Python testing framework
- **Version Control:** Git and GitHub

## Security Notes

1. Never commit `.env`, database passwords, secret keys, or private credentials.
2. Keep `.env.example` free of real secrets.
3. Validate permissions on the server for every protected operation.
4. Use password hashing, CSRF protection, and safe file-upload validation.
5. Use transactions and concurrency controls for stock and order changes.
6. Keep production secrets and database credentials outside the source code.

## Important Note

This is a recommended project structure, not a claim that every listed file already exists in the current implementation. Keep filenames consistent with the actual codebase, and only include modules that are implemented or intentionally planned.
