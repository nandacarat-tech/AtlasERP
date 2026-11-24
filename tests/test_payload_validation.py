import pytest


def test_products_rejects_non_dict_payload(client):
    """Garante que POST /products rejeita payloads que não sejam objetos JSON com 400 Bad Request."""
    resp = client.post("/products", json=["item1", "item2"])
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_customers_rejects_non_dict_payload(client):
    """Garante que POST /customers rejeita payloads que não sejam objetos JSON com 400 Bad Request."""
    resp = client.post("/customers", json="raw_string_not_dict")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_sales_rejects_non_dict_payload(client):
    """Garante que POST /sales rejeita payloads que não sejam objetos JSON com 400 Bad Request."""
    resp = client.post("/sales", json=[{"customer_id": 1}])
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_purchases_rejects_non_dict_payload(client):
    """Garante que POST /purchases rejeita payloads que não sejam objetos JSON com 400 Bad Request."""
    resp = client.post("/purchases", json=12345)
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_products_rejects_excessive_string_length(client):
    """Garante que POST /products rejeita nomes com mais de 100 caracteres."""
    huge_name = "A" * 101
    resp = client.post("/products", json={
        "sku": "SKU-HUGE-1",
        "name": huge_name,
        "price": "10.00"
    })
    assert resp.status_code == 400
    assert "100" in resp.get_json()["error"] or "tamanho" in resp.get_json()["error"] or "length" in resp.get_json()["error"].lower()


def test_products_rejects_excessive_price(client):
    """Garante que POST /products rejeita preços astronômicos (> 1 bilhão)."""
    resp = client.post("/products", json={
        "sku": "SKU-EXPENSIVE",
        "name": "Produto Super Caro",
        "price": "1000000001.00"
    })
    assert resp.status_code == 400
    assert "price" in resp.get_json()["error"].lower()


def test_sales_rejects_malformed_items(client):
    """Garante que POST /sales valida a estrutura e quantidade máxima dos itens."""
    # 1. Item que não é dicionário
    resp = client.post("/sales", json={
        "customer_id": 1,
        "items": ["não_é_um_dicionario"]
    })
    assert resp.status_code == 400

    # 2. Quantidade abusiva (> 10.000)
    resp = client.post("/sales", json={
        "customer_id": 1,
        "items": [{"product_id": 1, "quantity": 9999999}]
    })
    assert resp.status_code == 400
