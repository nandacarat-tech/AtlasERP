import pytest
from app import db
from app.rate_limit_service import (
    record_failed_attempt,
    is_rate_limited,
    reset_attempts,
    clear_all_limits,
)
from app.auth_models import User, Role


@pytest.fixture(autouse=True)
def clean_rate_limits():
    """Garante estado limpo dos limitadores antes e depois de cada teste."""
    clear_all_limits()
    yield
    clear_all_limits()


def test_rate_limit_service_unit():
    """Valida o serviço interno de rate limiting."""
    key = "test_ip_1"
    
    # Tentativas 1 a 4 não devem bloquear
    for i in range(1, 5):
        blocked, retry_after = record_failed_attempt(key, max_attempts=5, window_seconds=60)
        assert not blocked
        assert retry_after == 0

    # 5ª tentativa atinge o limite e bloqueia
    blocked, retry_after = record_failed_attempt(key, max_attempts=5, window_seconds=60)
    assert blocked
    assert retry_after > 0

    # Chamada subsequente confirma bloqueio ativo
    is_blocked, retry = is_rate_limited(key)
    assert is_blocked
    assert retry > 0

    # Reset limpa o bloqueio
    reset_attempts(key)
    is_blocked, _ = is_rate_limited(key)
    assert not is_blocked


def test_login_brute_force_protection(client, app):
    """Valida bloqueio HTTP 429 após 5 tentativas de login falhas."""
    with app.app_context():
        user = User(username="victim_user", full_name="Vitima Teste", email="victim@example.com", is_active=True)
        user.set_password("CorrectPassword123!")
        db.session.add(user)
        db.session.commit()

    # 5 tentativas com senha errada
    for i in range(5):
        resp = client.post("/login", data={"username": "victim_user", "password": "wrong_password"})
        assert resp.status_code in (200, 302)

    # 6ª tentativa deve ser bloqueada com 429 Too Many Requests
    resp = client.post("/login", data={"username": "victim_user", "password": "wrong_password"})
    assert resp.status_code == 429
    assert resp.headers.get("Retry-After") is not None


def test_login_success_resets_attempts(client, app):
    """Valida que um login bem-sucedido limpa tentativas acumuladas."""
    with app.app_context():
        user = User(username="valid_user", full_name="Valido Teste", email="valid@example.com", is_active=True)
        user.set_password("RightPass123!")
        db.session.add(user)
        db.session.commit()

    # 3 tentativas incorretas
    for _ in range(3):
        client.post("/login", data={"username": "valid_user", "password": "bad"})

    # Login correto
    resp = client.post("/login", data={"username": "valid_user", "password": "RightPass123!"})
    assert resp.status_code == 302

    # Próxima tentativa errada não deve somar com as anteriores para estourar o limite
    resp = client.post("/login", data={"username": "valid_user", "password": "bad"})
    assert resp.status_code != 429


def test_financial_unlock_brute_force_protection(client, app):
    """Valida proteção de força bruta na senha mestra do módulo financeiro."""
    with client.session_transaction() as sess:
        sess["user_authenticated"] = True
        sess["username"] = "admin"
        sess["is_superuser"] = True
        sess["financial_unlocked"] = False

    # 5 tentativas com senha incorreta
    for _ in range(5):
        client.post("/financial/unlock", data={"password": "wrong_financial_pass"})

    # 6ª tentativa deve ser bloqueada
    resp = client.post("/financial/unlock", data={"password": "wrong_financial_pass"})
    assert resp.status_code == 429
    assert resp.headers.get("Retry-After") is not None


def test_demo_login_not_blocked(client, app):
    """Valida que o login de demonstração de 1-clique permanece funcional e não gera 429."""
    for _ in range(3):
        resp = client.post("/login/demo")
        assert resp.status_code == 302
        assert resp.location.endswith("/dashboard")


def test_products_query_limit_validation(client):
    """Valida rejeição de limites abusivos ou inválidos em GET /products para mitigar DoS."""
    # Teste de limite abusivo (> 100)
    resp = client.get("/products?limit=150")
    assert resp.status_code == 400
    assert "between 1 and 100" in resp.get_json()["error"]

    # Teste de limite negativo
    resp = client.get("/products?limit=-5")
    assert resp.status_code == 400
    assert "between 1 and 100" in resp.get_json()["error"]

    # Teste de limite inválido
    resp = client.get("/products?limit=invalido")
    assert resp.status_code == 400
    assert "must be an integer" in resp.get_json()["error"]

    # Teste de limite válido
    resp = client.get("/products?limit=5")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)
    assert len(resp.get_json()) <= 5


def test_customers_query_limit_validation(client):
    """Valida rejeição de limites abusivos ou inválidos em GET /customers para mitigar DoS."""
    # Teste de limite abusivo (> 100)
    resp = client.get("/customers?limit=150")
    assert resp.status_code == 400
    assert "between 1 and 100" in resp.get_json()["error"]

    # Teste de limite negativo
    resp = client.get("/customers?limit=-10")
    assert resp.status_code == 400
    assert "between 1 and 100" in resp.get_json()["error"]

    # Teste de limite inválido
    resp = client.get("/customers?limit=abc")
    assert resp.status_code == 400
    assert "must be an integer" in resp.get_json()["error"]

    # Teste de limite válido
    resp = client.get("/customers?limit=3")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)
    assert len(resp.get_json()) <= 3
