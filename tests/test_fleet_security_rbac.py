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
    res_block = client_consulta.post("/fleet/vehicles", json={"plate": "BLK-9999", "vehicle_type": "Van"})
    assert res_block.status_code == 403
    assert res_block.get_json()["required_permission"] == "fleet.manage"

    # 2. Perfil VENDEDOR
    assert client_vendedor.get("/api/fleet/vehicles").status_code == 403
    assert client_vendedor.get("/api/fleet/drivers").status_code == 403
    assert client_vendedor.post("/fleet/vehicles", json={"plate": "BLK-9999"}).status_code == 403

    # 3. Perfil GERENTE
    res_gerente_post = client_gerente.post("/fleet/vehicles", json={
        "plate": "GER-1010",
        "vehicle_type": "Caminhao",
        "status": "AVAILABLE"
    })
    assert res_gerente_post.status_code == 201
