# ShopEase

A responsive e-commerce storefront built with Django templates, Django ORM, and SQLite. It includes a searchable/category-filtered catalog, product pages, session-based shopping cart, account registration and login, and authenticated Cash on Delivery checkout with server-side pricing and stock validation.

## Requirements

- Python 3.10 or newer
- pip

## Set up locally

Run these commands from the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_products
python manage.py createsuperuser
python manage.py runserver
```

If the `py` launcher is not installed, replace `py` with `python` when creating the virtual environment. Visit <http://127.0.0.1:8000/> for the storefront and <http://127.0.0.1:8000/admin/> for the Django admin. Use the superuser credentials to manage categories, products, stock, and orders.

The seed command adds a small sample catalog and can be run again safely. New products can also be created from the admin panel. Customers register an account before checkout; the only supported payment option is Cash on Delivery.

## Configuration

For local development, Django uses SQLite at `db.sqlite3` and a development-only secret key. Before deployment, set a strong `DJANGO_SECRET_KEY`, set `DJANGO_DEBUG=0`, and provide the deployment hostnames as a comma-separated `DJANGO_ALLOWED_HOSTS` value. Configure HTTPS and production-grade static-file serving in the deployment environment.

## Tests

Run the Django test suite with:

```powershell
python manage.py test
```

Tests cover catalog filters, cart behavior, authentication requirements, price calculation, and inventory validation during checkout.
