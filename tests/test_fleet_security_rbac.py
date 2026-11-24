import pytest
from app import db
from app.models import FleetVehicle, Driver, Route, DeliveryReturn, Product
from app.customer_models import Customer
from app.sale_models import Sale, SaleItem


def test_anonymous_access_blocked_on_all_fleet_endpoints(unauthenticated_client):
    """
    Garante que qualquer requisição sem autenticação em qualquer endpoint da frota
    é terminantemente barrada com HTTP 401 Unauthorized, protegendo dados sensíveis de motoristas.
    """
    # 1. Veículos
    res = unauthenticated_client.get("/api/fleet/vehicles")
    assert res.status_code == 401
    assert res.get_json()["error"] == "Autenticação requerida."

    res_post = unauthenticated_client.post("/fleet/vehicles", json={"plate": "ABC-1234"})
    assert res_post.status_code == 401

    # 2. Motoristas (LGPD - Proteção de CPFs e CNHs)
    res_drivers = unauthenticated_client.get("/api/fleet/drivers")
    assert res_drivers.status_code == 401

    res_post_driver = unauthenticated_client.post("/fleet/drivers", json={"name": "Hacker Anonimo"})
    assert res_post_driver.status_code == 401

    # 3. Rotas de Transporte
    res_routes = unauthenticated_client.get("/api/fleet/routes")
    assert res_routes.status_code == 401

    res_post_route = unauthenticated_client.post("/fleet/routes", json={"route_name": "Rota Invasor"})
    assert res_post_route.status_code == 401

    # 4. Devoluções e Ocorrências
    res_returns = unauthenticated_client.get("/api/fleet/returns")
    assert res_returns.status_code == 401

    res_post_return = unauthenticated_client.post("/api/fleet/returns", json={"customer_name": "Anonimo"})
    assert res_post_return.status_code == 401

    # 5. Métricas e Resumos de Frota
    assert unauthenticated_client.get("/api/fleet/returns/summary").status_code == 401
    assert unauthenticated_client.get("/api/fleet/vehicles/summary").status_code == 401
    assert unauthenticated_client.get("/api/fleet/drivers/count").status_code == 401
    assert unauthenticated_client.get("/api/fleet/routes/active/count").status_code == 401


def test_rbac_role_boundaries_on_fleet_management(client_factory, app):
    """
    Valida a fronteira de privilégios (BFLA):
    - CONSULTA pode ler (fleet.view), mas não pode criar/alterar (403).
    - VENDEDOR não tem acesso nem de leitura nem de escrita na frota (403).
    - GERENTE tem acesso pleno (fleet.view e fleet.manage).
    """
    client_consulta = client_factory("CONSULTA")
    client_vendedor = client_factory("VENDEDOR")
    client_gerente = client_factory("GERENTE")

    # 1. Perfil CONSULTA
    assert client_consulta.get("/api/fleet/vehicles").status_code == 200
    assert client_consulta.get("/api/fleet/drivers").status_code == 200
    assert client_consulta.get("/api/fleet/routes").status_code == 200
    assert client_consulta.get("/api/fleet/returns").status_code == 200

    # Bloqueio de mutação (403) para CONSULTA
    res_block = client_consulta.post("/fleet/vehicles", json={"plate": "BLK-9999", "vehicle_type": "Van"})
    assert res_block.status_code == 403
    assert res_block.get_json()["required_permission"] == "fleet.manage"
    assert client_consulta.post("/fleet/drivers", json={"name": "Motorista Fake"}).status_code == 403
    assert client_consulta.post("/fleet/routes", json={"route_name": "Rota Fake"}).status_code == 403
    assert client_consulta.put("/fleet/drivers/1", json={"name": "Alterado"}).status_code == 403
    assert client_consulta.put("/fleet/routes/1", json={"route_name": "Alterado"}).status_code == 403
    assert client_consulta.delete("/fleet/drivers/1").status_code == 403
    assert client_consulta.delete("/fleet/routes/1").status_code == 403
    assert client_consulta.post("/api/fleet/returns/1/resolve", json={"status": "RETURNED_TO_STOCK"}).status_code == 403

    # 2. Perfil VENDEDOR (sem permissões de frota - 403 em leitura e escrita)
    assert client_vendedor.get("/api/fleet/vehicles").status_code == 403
    assert client_vendedor.get("/api/fleet/drivers").status_code == 403
    assert client_vendedor.get("/api/fleet/routes").status_code == 403
    assert client_vendedor.get("/api/fleet/returns").status_code == 403
    assert client_vendedor.post("/fleet/vehicles", json={"plate": "BLK-9999"}).status_code == 403
    assert client_vendedor.post("/fleet/drivers", json={"name": "Motorista Fake"}).status_code == 403
    assert client_vendedor.post("/fleet/routes", json={"route_name": "Rota Fake"}).status_code == 403
    assert client_vendedor.put("/fleet/drivers/1", json={"name": "Alterado"}).status_code == 403
    assert client_vendedor.put("/fleet/routes/1", json={"route_name": "Alterado"}).status_code == 403
    assert client_vendedor.delete("/fleet/drivers/1").status_code == 403
    assert client_vendedor.delete("/fleet/routes/1").status_code == 403
    assert client_vendedor.post("/api/fleet/returns/1/resolve", json={"status": "RETURNED_TO_STOCK"}).status_code == 403

    # 3. Perfil ESTOQUISTA (não possui fleet.manage - 403 nas mutações de frota)
    client_estoquista = client_factory("ESTOQUISTA")
    assert client_estoquista.post("/fleet/vehicles", json={"plate": "EST-1234"}).status_code == 403
    assert client_estoquista.post("/fleet/drivers", json={"name": "Motorista Fake"}).status_code == 403
    assert client_estoquista.post("/fleet/routes", json={"route_name": "Rota Fake"}).status_code == 403
    assert client_estoquista.delete("/fleet/drivers/1").status_code == 403
    assert client_estoquista.delete("/fleet/routes/1").status_code == 403

    # 4. Perfil GERENTE (possui fleet.view e fleet.manage)
    res_gerente_post = client_gerente.post("/fleet/vehicles", json={
        "plate": "GER-1010",
        "vehicle_type": "Caminhao",
        "status": "AVAILABLE"
    })
    assert res_gerente_post.status_code == 201


def test_demo_showcase_anti_sabotage_protection_returns_403(app, client):
    """
    Comprova que a função is_protected_demo_record protege com HTTP 403 Forbidden
    os registros semeados da vitrine quando uma sessão de demonstração tenta excluí-los.
    """
    from datetime import date
    with app.app_context():
        # Cria rota semeada com ID baixo (<= 25)
        seeded_route = Route(
            id=10,
            route_name="Rota Vitrine Semeada",
            start_date=date(2026, 9, 1),
            status="PENDING"
        )
        # Cria rota efêmera criada por visitante com ID alto (> 25)
        ephemeral_route = Route(
            id=999,
            route_name="Rota Criada pelo Visitante",
            start_date=date(2026, 9, 1),
            status="PENDING"
        )
        db.session.add(seeded_route)
        db.session.add(ephemeral_route)
        db.session.commit()

    # Simula sessão de demonstração da vitrine (is_demo_session = True, ADMIN)
    with client.session_transaction() as sess:
        sess["user_authenticated"] = True
        sess["username"] = "demo_admin"
        sess["is_demo_session"] = True
        sess["is_superuser"] = True
        sess["role"] = "ADMIN"

    # 1. Tentativa de exclusão do registro semeado (ID=10) -> DEVE RETORNAR 403 FORBIDDEN
    res_del_seeded = client.delete("/fleet/routes/10")
    assert res_del_seeded.status_code == 403
    assert "Modo Demonstração" in res_del_seeded.get_json()["error"]
    assert "preservar o acervo mestre da vitrine" in res_del_seeded.get_json()["error"]

    # 2. Exclusão de registro efêmero criado pelo próprio visitante (ID=999) -> DEVE RETORNAR 200 OK
    res_del_ephemeral = client.delete("/fleet/routes/999")
    assert res_del_ephemeral.status_code == 200
    assert res_del_ephemeral.get_json()["message"] == "Rota excluída com sucesso."

