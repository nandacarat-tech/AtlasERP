import pytest
from flask import session
from app.csrf_service import generate_csrf_token, validate_csrf_token


@pytest.fixture(autouse=True)
def enforce_csrf(app):
    """Força validação estrita de token CSRF para todos os testes deste módulo."""
    app.config["ENFORCE_CSRF_IN_TESTS"] = True
    yield
    app.config["ENFORCE_CSRF_IN_TESTS"] = False


def test_csrf_service_unit(app):
    """Valida o serviço interno de tokens CSRF."""
    with app.test_request_context():
        token1 = generate_csrf_token()
        assert token1 is not None
        assert len(token1) == 64  # secrets.token_hex(32)
        assert session.get("csrf_token") == token1

        # Chamadas subsequentes no mesmo contexto retornam o mesmo token
        token2 = generate_csrf_token()
        assert token1 == token2

        # Validação positiva
        assert validate_csrf_token(token1) is True

        # Validação negativa
        assert validate_csrf_token("token_forjado_invalido") is False
        assert validate_csrf_token(None) is False
        assert validate_csrf_token("") is False


def test_cross_site_fetch_site_blocked(client):
    """Valida bloqueio HTTP 403 para requisições com Sec-Fetch-Site: cross-site."""
    resp = client.post("/logout", headers={"Sec-Fetch-Site": "cross-site"})
    assert resp.status_code == 403
    data = resp.get_data(as_text=True)
    assert "cross-site" in data.lower() or "csrf" in data.lower() or "origem" in data.lower()


def test_cross_origin_header_blocked(client):
    """Valida bloqueio HTTP 403 quando Origin aponta para domínio externo."""
    resp = client.post(
        "/logout",
        headers={"Origin": "https://malicious-attacker.com", "Sec-Fetch-Site": "cross-site"}
    )
    assert resp.status_code == 403


def test_native_form_requires_csrf_token(client):
    """Valida que formulários POST nativos sem token CSRF são bloqueados com 403."""
    # POST sem token
    resp = client.post("/logout")
    assert resp.status_code == 403


def test_native_form_with_valid_csrf_token_succeeds(client):
    """Valida que formulários com token CSRF válido são processados com sucesso."""
    # 1. Faz GET para obter a página de login e gerar o token na sessão
    get_resp = client.get("/login")
    assert get_resp.status_code == 200

    with client.session_transaction() as sess:
        valid_token = sess.get("csrf_token")
    assert valid_token is not None

    # 2. Faz POST em /login/demo enviando o token válido
    post_resp = client.post("/login/demo", data={"csrf_token": valid_token})
    assert post_resp.status_code == 302
    assert post_resp.location.endswith("/dashboard")
