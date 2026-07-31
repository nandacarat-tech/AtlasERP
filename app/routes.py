from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request

from app import db
from app.models import Product


main = Blueprint("main", __name__)


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

    return jsonify([
        {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "description": product.description,
            "price": str(product.price),
            "stock_quantity": product.stock_quantity,
            "is_active": product.is_active,
        }
        for product in products
    ])


@main.post("/products")
def create_product():
    data = request.get_json(silent=True) or {}

    required_fields = ("sku", "name", "price")

    if any(not data.get(field) for field in required_fields):
        return jsonify({
            "error": "sku, name and price are required"
        }), 400

    try:
        price = Decimal(str(data["price"]))
    except (InvalidOperation, ValueError):
        return jsonify({"error": "price must be a valid number"}), 400

    if price < 0:
        return jsonify({"error": "price cannot be negative"}), 400

    if Product.query.filter_by(sku=data["sku"]).first():
        return jsonify({"error": "sku already exists"}), 409

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

    return jsonify({
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "price": str(product.price),
        "stock_quantity": product.stock_quantity,
        "is_active": product.is_active,
    }), 201
