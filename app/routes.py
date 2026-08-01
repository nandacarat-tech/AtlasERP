from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request

from app import db
from app.customer_models import Customer
from app.models import Product
from app.sale_models import Sale, SaleItem


main = Blueprint("main", __name__)


def product_to_dict(product):
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "price": str(product.price),
        "stock_quantity": product.stock_quantity,
        "is_active": product.is_active,
    }


def customer_to_dict(customer):
    return {
        "id": customer.id,
        "document": customer.document,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "is_active": customer.is_active,
    }


def sale_to_dict(sale):
    return {
        "id": sale.id,
        "customer_id": sale.customer_id,
        "status": sale.status,
        "total_amount": str(sale.total_amount),
        "items": [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "subtotal": str(item.subtotal),
            }
            for item in sale.items
        ],
    }


@main.get("/")
def index():
    return {
        "application": "AtlasERP",
        "status": "online",
        "message": "AtlasERP iniciado com sucesso",
    }


@main.get("/products")
def list_products():
    products = Product.query.order_by(Product.id).all()
    return jsonify([product_to_dict(product) for product in products])


@main.post("/products")
def create_product():
    data = request.get_json(silent=True) or {}

    if any(not data.get(field) for field in ("sku", "name", "price")):
        return jsonify({
            "error": "sku, name and price are required"
        }), 400

    try:
        price = Decimal(str(data["price"]))
    except (InvalidOperation, ValueError):
        return jsonify({
            "error": "price must be a valid number"
        }), 400

    if price < 0:
        return jsonify({
            "error": "price cannot be negative"
        }), 400

    if Product.query.filter_by(sku=data["sku"]).first():
        return jsonify({
            "error": "sku already exists"
        }), 409

    product = Product(
        sku=data["sku"],
        name=data["name"],
        description=data.get("description"),
        price=price,
        stock_quantity=data.get("stock_quantity", 0),
        is_active=data.get("is_active", True),
    )

    db.session.add(product)
    db.session.commit()

    return jsonify(product_to_dict(product)), 201


@main.get("/products/<int:product_id>")
def get_product(product_id):
    product = db.get_or_404(Product, product_id)
    return jsonify(product_to_dict(product))


@main.put("/products/<int:product_id>")
def update_product(product_id):
    product = db.get_or_404(Product, product_id)
    data = request.get_json(silent=True) or {}

    if "name" in data:
        if not data["name"]:
            return jsonify({
                "error": "name cannot be empty"
            }), 400

        product.name = data["name"]

    if "price" in data:
        try:
            price = Decimal(str(data["price"]))
        except (InvalidOperation, ValueError):
            return jsonify({
                "error": "price must be a valid number"
            }), 400

        if price < 0:
            return jsonify({
                "error": "price cannot be negative"
            }), 400

        product.price = price

    if "stock_quantity" in data:
        if not isinstance(data["stock_quantity"], int):
            return jsonify({
                "error": "stock_quantity must be an integer"
            }), 400

        if data["stock_quantity"] < 0:
            return jsonify({
                "error": "stock_quantity cannot be negative"
            }), 400

        product.stock_quantity = data["stock_quantity"]

    if "description" in data:
        product.description = data["description"]

    if "is_active" in data:
        product.is_active = bool(data["is_active"])

    db.session.commit()

    return jsonify(product_to_dict(product))


@main.delete("/products/<int:product_id>")
def deactivate_product(product_id):
    product = db.get_or_404(Product, product_id)
    product.is_active = False

    db.session.commit()

    return jsonify(product_to_dict(product))


@main.get("/customers")
def list_customers():
    customers = Customer.query.order_by(Customer.id).all()
    return jsonify([customer_to_dict(customer) for customer in customers])


@main.post("/customers")
def create_customer():
    data = request.get_json(silent=True) or {}

    if not data.get("document") or not data.get("name"):
        return jsonify({
            "error": "document and name are required"
        }), 400

    if Customer.query.filter_by(document=data["document"]).first():
        return jsonify({
            "error": "document already exists"
        }), 409

    if data.get("email"):
        if Customer.query.filter_by(email=data["email"]).first():
            return jsonify({
                "error": "email already exists"
            }), 409

    customer = Customer(
        document=data["document"],
        name=data["name"],
        email=data.get("email"),
        phone=data.get("phone"),
        is_active=data.get("is_active", True),
    )

    db.session.add(customer)
    db.session.commit()

    return jsonify(customer_to_dict(customer)), 201


@main.get("/customers/<int:customer_id>")
def get_customer(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    return jsonify(customer_to_dict(customer))


@main.put("/customers/<int:customer_id>")
def update_customer(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    data = request.get_json(silent=True) or {}

    if "document" in data:
        if not data["document"]:
            return jsonify({
                "error": "document cannot be empty"
            }), 400

        existing = Customer.query.filter(
            Customer.document == data["document"],
            Customer.id != customer.id,
        ).first()

        if existing:
            return jsonify({
                "error": "document already exists"
            }), 409

        customer.document = data["document"]

    if "name" in data:
        if not data["name"]:
            return jsonify({
                "error": "name cannot be empty"
            }), 400

        customer.name = data["name"]

    if "email" in data:
        if data["email"]:
            existing = Customer.query.filter(
                Customer.email == data["email"],
                Customer.id != customer.id,
            ).first()

            if existing:
                return jsonify({
                    "error": "email already exists"
                }), 409

        customer.email = data["email"]

    if "phone" in data:
        customer.phone = data["phone"]

    if "is_active" in data:
        customer.is_active = bool(data["is_active"])

    db.session.commit()

    return jsonify(customer_to_dict(customer))


@main.delete("/customers/<int:customer_id>")
def deactivate_customer(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    customer.is_active = False

    db.session.commit()

    return jsonify(customer_to_dict(customer))


@main.post("/sales")
def create_sale():
    data = request.get_json(silent=True) or {}

    customer_id = data.get("customer_id")
    items_data = data.get("items")

    if not customer_id:
        return jsonify({
            "error": "customer_id is required"
        }), 400

    if not isinstance(items_data, list) or not items_data:
        return jsonify({
            "error": "items must be a non-empty list"
        }), 400

    product_ids = [item.get("product_id") for item in items_data]

    if len(product_ids) != len(set(product_ids)):
        return jsonify({
            "error": "duplicate products are not allowed"
        }), 400

    customer = db.session.get(Customer, customer_id)

    if customer is None:
        return jsonify({
            "error": "customer not found"
        }), 404

    if not customer.is_active:
        return jsonify({
            "error": "customer is inactive"
        }), 400

    sale = Sale(
        customer=customer,
        status="OPEN",
        total_amount=Decimal("0.00"),
    )

    db.session.add(sale)

    for item_data in items_data:
        product_id = item_data.get("product_id")
        quantity = item_data.get("quantity")

        if not product_id or not isinstance(quantity, int):
            return jsonify({
                "error": "product_id and integer quantity are required"
            }), 400

        if quantity <= 0:
            return jsonify({
                "error": "quantity must be greater than zero"
            }), 400

        product = db.session.get(Product, product_id)

        if product is None:
            return jsonify({
 "error": "product not found"
            }), 404

        if not product.is_active:
            return jsonify({
                "error": "product is inactive"
            }), 400

        if quantity > product.stock_quantity:
            return jsonify({
               "error": f"insufficient stock for product {product.sku}"
            }), 400

        sale.items.append(SaleItem(
            product=product,
            quantity=quantity,
            unit_price=product.price,
        ))

    sale.recalculate_total()

    db.session.commit()

    return jsonify(sale_to_dict(sale)), 201


@main.get("/sales")
def list_sales():
    query = Sale.query.order_by(Sale.id)

    status = request.args.get("status")
    customer_id = request.args.get("customer_id")

    if status:
        query = query.filter_by(status=status)

    if customer_id:
        try:
            customer_id = int(customer_id)
        except ValueError:
            return jsonify({
                "error": "customer_id must be an"
            }), 400

        query = query.filter_by(customer_id=customer_id)

    sales = query.all()

    return jsonify([sale_to_dict(sale) for sale in sales])


@main.get("/sales/<int:sale_id>")
def get_sale(sale_id):
    sale = db.get_or_404(Sale, sale_id)

    return jsonify(sale_to_dict(sale))


@main.post("/sales/<int:sale_id>/confirm")
def confirm_sale(sale_id):
    sale = db.get_or_404(Sale, sale_id)

    if sale.status != "OPEN":
        return jsonify({
            "error": "only open sales can be confirmed"
        }), 400

    for item in sale.items:
        product = item.product

        if item.quantity > product.stock_quantity:
           return jsonify({
              "error": f"insufficient stock for product {product.sku}"
        }), 400

    for item in sale.items:
        item.product.stock_quantity -= item.quantity

    sale.status = "CONFIRMED"
    db.session.commit()

    return jsonify(sale_to_dict(sale))
@main.post("/sales/<int:sale_id>/cancel")
def cancel_sale(sale_id):
    sale = db.session.get(Sale, sale_id)

    if sale is None:
        return jsonify({"error": "sale not found"}), 404

    if sale.status != "OPEN":
        return jsonify({"error": "only open sales can be cancelled"}), 400

    sale.status = "CANCELLED"
    db.session.commit()

    return jsonify({
        "id": sale.id,
        "status": sale.status,
        "total_amount": str(sale.total_amount),
    }), 200