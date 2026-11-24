import pytest
from app import db
from app.models import Product, DeliveryReturn
from app.customer_models import Customer
from app.sale_models import Sale, SaleItem


def test_create_delivery_return(client):
    res = client.post("/api/fleet/returns", json={
        "customer_name": "Empresa ABC Ltda",
        "reason": "CLIENT_ABSENT",
        "attempt_date": "2026-09-11",
        "notes": "Tentativa realizada às 14:30. Portão fechado."
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["customer_name"] == "Empresa ABC Ltda"
    assert data["reason"] == "CLIENT_ABSENT"
    assert data["status"] == "PENDING_RETURN"


def test_create_delivery_return_validation(client):
    res = client.post("/api/fleet/returns", json={
        "customer_name": "",
        "reason": "CLIENT_ABSENT"
    })
    assert res.status_code == 400
    assert "Nome do cliente" in res.get_json()["error"]

    res2 = client.post("/api/fleet/returns", json={
        "customer_name": "Cliente Teste",
        "reason": ""
    })
    assert res2.status_code == 400
    assert "Motivo" in res2.get_json()["error"]


def test_list_and_filter_delivery_returns(client):
    client.post("/api/fleet/returns", json={
        "customer_name": "Cliente Filtro 1",
        "reason": "ADDRESS_NOT_FOUND",
        "status": "PENDING_RETURN"
    })
    client.post("/api/fleet/returns", json={
        "customer_name": "Cliente Filtro 2",
        "reason": "CARGO_DAMAGED",
        "status": "RETURNED_TO_STOCK"
    })

    res_all = client.get("/api/fleet/returns")
    assert res_all.status_code == 200
    assert len(res_all.get_json()) >= 2

    res_pending = client.get("/api/fleet/returns?status=PENDING_RETURN")
    assert res_pending.status_code == 200
    for item in res_pending.get_json():
        assert item["status"] == "PENDING_RETURN"

    res_damaged = client.get("/api/fleet/returns?reason=CARGO_DAMAGED")
    assert res_damaged.status_code == 200
    for item in res_damaged.get_json():
        assert item["reason"] == "CARGO_DAMAGED"


def test_resolve_delivery_return_with_stock_restoration(client, app):
    with app.app_context():
        # Criar cliente
        customer = Customer(
            name="Cliente Retorno",
            document="529.982.247-25",
            email="retorno@cliente.com"
        )
        db.session.add(customer)
        db.session.commit()

        # Criar produto com estoque inicial 10
        product = Product(
            sku="PROD-RET-01",
            name="Monitor LED 27",
            price="1200.00",
            stock_quantity=10,
            minimum_stock=2
        )
        db.session.add(product)
        db.session.commit()
        prod_id = product.id

        # Criar venda com 3 itens
        sale = Sale(customer_id=customer.id, total_amount="3600.00", status="CONFIRMED")
        db.session.add(sale)
        db.session.commit()

        sale_item = SaleItem(sale_id=sale.id, product_id=prod_id, quantity=3, unit_price="1200.00")
        db.session.add(sale_item)
        db.session.commit()
        sale_id = sale.id

    # Criar ocorrência de entrega mal-sucedida
    res_create = client.post("/api/fleet/returns", json={
        "customer_name": "Cliente Retorno",
        "sale_id": sale_id,
        "reason": "CLIENT_REFUSED",
        "notes": "Cliente recusou por desistência."
    })
    assert res_create.status_code == 201
    return_id = res_create.get_json()["id"]

    # Resolver ocorrência alterando status para RETURNED_TO_STOCK
    res_resolve = client.post(f"/api/fleet/returns/{return_id}/resolve", json={
        "status": "RETURNED_TO_STOCK",
        "action_taken": "Mercadoria retornada ao estoque da matriz."
    })
    assert res_resolve.status_code == 200
    assert res_resolve.get_json()["status"] == "RETURNED_TO_STOCK"

    # Verificar se o estoque do produto aumentou de 10 para 13
    with app.app_context():
        p = db.session.get(Product, prod_id)
        assert p.stock_quantity == 13


def test_fleet_returns_summary(client):
    res = client.get("/api/fleet/returns/summary")
    assert res.status_code == 200
    data = res.get_json()
    assert "total" in data
    assert "pending" in data
    assert "returned_to_stock" in data


def test_exploit_infinite_stock_inflation_via_status_ping_pong(client, app):
    """
    PoC: Demonstra que alternar status entre RETURNED_TO_STOCK e RESCHEDULED
    permite creditar o estoque indefinidamente em multiplas resolucoes da mesma devolucao.
    """
    with app.app_context():
        customer = Customer(name="Cliente Inflacao", document="529.982.247-25", email="infla@teste.com")
        db.session.add(customer)
        product = Product(sku="PROD-INFLA-01", name="Notebook Gamer", price="5000.00", stock_quantity=10, minimum_stock=1)
        db.session.add(product)
        db.session.commit()
        prod_id = product.id

        sale = Sale(customer_id=customer.id, total_amount="5000.00", status="CONFIRMED")
        db.session.add(sale)
        db.session.commit()

        sale_item = SaleItem(sale_id=sale.id, product_id=prod_id, quantity=5, unit_price="5000.00")
        db.session.add(sale_item)
        db.session.commit()
        sale_id = sale.id

    # 1. Cria devolucao
    res_create = client.post("/api/fleet/returns", json={
        "customer_name": "Cliente Inflacao",
        "sale_id": sale_id,
        "reason": "CLIENT_REFUSED"
    })
    return_id = res_create.get_json()["id"]

    # 2. Primeira devolucao ao estoque: 10 + 5 = 15 unidades
    client.post(f"/api/fleet/returns/{return_id}/resolve", json={"status": "RETURNED_TO_STOCK"})

    with app.app_context():
        p1 = db.session.get(Product, prod_id)
        assert p1.stock_quantity == 15

    # 3. Ataque: Altera para RESCHEDULED
    client.post(f"/api/fleet/returns/{return_id}/resolve", json={"status": "RESCHEDULED"})

    # 4. Ataque: Altera novamente para RETURNED_TO_STOCK
    client.post(f"/api/fleet/returns/{return_id}/resolve", json={"status": "RETURNED_TO_STOCK"})

    with app.app_context():
        p2 = db.session.get(Product, prod_id)
        # Com a protecao idempotente ativa, o estoque NAO infla para 20, permanecendo em 15!
        assert p2.stock_quantity == 15
        ret = db.session.get(DeliveryReturn, return_id)
        assert ret.stock_restored is True


def test_concurrent_resolve_delivery_return_race_condition(app, client_factory):
    """
    Simula 5 requisições concorrentes disparadas simultaneamente para resolver a mesma ocorrência
    com status RETURNED_TO_STOCK.
    Garante que exatamente uma transação consiga incrementar o estoque no banco (atomicidade SQL).
    """
    import concurrent.futures

    with app.app_context():
        customer = Customer(name="Cliente Concorrencia", document="529.982.247-25", email="race@teste.com")
        db.session.add(customer)
        product = Product(sku="PROD-RACE-01", name="Placa de Video Concorrente", price="3000.00", stock_quantity=10, minimum_stock=1)
        db.session.add(product)
        db.session.commit()
        prod_id = product.id

        sale = Sale(customer_id=customer.id, total_amount="3000.00", status="CONFIRMED")
        db.session.add(sale)
        db.session.commit()

        sale_item = SaleItem(sale_id=sale.id, product_id=prod_id, quantity=3, unit_price="3000.00")
        db.session.add(sale_item)
        db.session.commit()
        sale_id = sale.id

    client = client_factory("ADMIN")
    res_create = client.post("/api/fleet/returns", json={
        "customer_name": "Cliente Concorrencia",
        "sale_id": sale_id,
        "reason": "CLIENT_ABSENT"
    })
    return_id = res_create.get_json()["id"]

    # Dispara chamadas simultaneas com isolamento seguro por thread
    def call_resolve(worker_id):
        with app.app_context():
            worker_client = client_factory("ADMIN")
            try:
                return worker_client.post(
                    f"/api/fleet/returns/{return_id}/resolve",
                    json={"status": "RETURNED_TO_STOCK", "action_taken": f"Concorrencia Worker {worker_id}"}
                )
            finally:
                db.session.remove()

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(call_resolve, i) for i in range(3)]
        responses = [f.result() for f in futures]

    # Todas as requisições devem ser processadas com sucesso (200)
    for res in responses:
        assert res.status_code == 200

    # O estoque inicial era 10. A venda foi de 3 itens.
    # O estoque final DEVE ser 10 + 3 = 13.
    # Se houvesse race condition, o estoque seria 10 + (3 * 5) = 25!
    with app.app_context():
        final_product = db.session.get(Product, prod_id)
        assert final_product.stock_quantity == 13
        ret = db.session.get(DeliveryReturn, return_id)
        assert ret.stock_restored is True


def test_resolve_delivery_return_all_or_nothing_missing_sale_or_product(client, app):
    """
    Comprova que se a venda ou o produto vinculado à ocorrência não existir,
    a resolução com RETURNED_TO_STOCK falha com erro 422, sofre rollback
    e NUNCA marca stock_restored como True.
    """
    from datetime import date
    with app.app_context():
        # Cria uma devolução apontando para uma venda inexistente (ID=99999)
        ret_ghost_sale = DeliveryReturn(
            customer_name="Cliente Fantasma",
            sale_id=99999,
            reason="CLIENT_REFUSED",
            status="PENDING_RETURN",
            stock_restored=False
        )
        db.session.add(ret_ghost_sale)
        db.session.commit()
        ghost_id = ret_ghost_sale.id

    # Tentativa de resolução deve falhar com 422 e não confirmar stock_restored
    res_fail = client.post(f"/api/fleet/returns/{ghost_id}/resolve", json={
        "status": "RETURNED_TO_STOCK",
        "action_taken": "Tentando forçar reposição de venda inexistente"
    })
    assert res_fail.status_code == 422
    assert "Venda vinculada à devolução não encontrada" in res_fail.get_json()["error"]

    with app.app_context():
        r = db.session.get(DeliveryReturn, ghost_id)
        assert r.stock_restored is False
        assert r.status == "PENDING_RETURN"


