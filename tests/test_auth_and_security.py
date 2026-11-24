def test_unauthenticated_user_redirected_to_login(client):
    """
    Garante que usuários não autenticados são redirecionados para a tela de login.
    """
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.location

    response_products = client.get("/ui/products")
    assert response_products.status_code == 302
    assert "/login" in response_products.location


def test_login_failure(client):
    """
    Testa tentativa de login com credenciais incorretas.
    """
    response = client.post("/login", data={
        "username": "admin",
        "password": "senha_errada"
    })
    assert response.status_code == 200
    assert "Credenciais de acesso incorretas" in response.get_data(as_text=True) or "Usuário ou senha de acesso incorretos" in response.get_data(as_text=True)


def test_login_success_and_logout(client):
    """
    Testa login com sucesso e posterior encerramento de sessão.
    """
    response = client.post("/login", data={
        "username": "admin",
        "password": "admin123"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "Painel Geral" in response.get_data(as_text=True) or "AtlasERP" in response.get_data(as_text=True)

    # Logout via POST (e comprova que GET é rejeitado com 405)
    assert client.get("/logout").status_code == 405
    logout_res = client.post("/logout")
    assert logout_res.status_code == 302
    assert "/login" in logout_res.location


def test_financial_module_password_protection(client):
    """
    Garante que o módulo financeiro exige a senha de acesso financeiro.
    """
    # 1. Faz login no sistema
    client.post("/login", data={"username": "admin", "password": "admin123"})

    # 2. Tenta acessar o financeiro sem desbloquear -> deve redirecionar para unlock
    res_fin = client.get("/ui/financial")
    assert res_fin.status_code == 302
    assert "/financial/unlock" in res_fin.location

    # 3. Tenta desbloquear com senha errada
    res_unlock_fail = client.post("/financial/unlock", data={"financial_password": "errada"})
    assert res_unlock_fail.status_code == 200
    assert "Senha do módulo financeiro incorreta" in res_unlock_fail.get_data(as_text=True)

    # 4. Desbloqueia com a senha financeira correta
    res_unlock_ok = client.post("/financial/unlock", data={"financial_password": "financeiro123"}, follow_redirects=True)
    assert res_unlock_ok.status_code == 200

    # 5. Agora tem acesso liberado ao painel financeiro
    res_fin_unlocked = client.get("/ui/financial")
    assert res_fin_unlocked.status_code == 200


def test_open_redirect_prevention(client):
    """
    Garante que tentativas de Open Redirect para domínios externos são bloqueadas
    e redirecionadas com segurança para /dashboard.
    """
    malicious_urls = [
        "https://evil.com",
        "//evil.com",
        "http://attacker.com/steal",
        "\\\\evil.com",
    ]
    for evil_url in malicious_urls:
        response = client.post("/login", data={
            "username": "admin",
            "password": "admin123",
            "next": evil_url
        })
        assert response.status_code == 302
        assert response.location == "/dashboard"


def test_session_cookie_security_flags(app, client):
    """
    Verifica se a aplicação está configurada com as flags de segurança recomendadas
    para os cookies de sessão.
    """
    assert app.config.get("SESSION_COOKIE_HTTPONLY") is True
    assert app.config.get("SESSION_COOKIE_SAMESITE") in ("Lax", "Strict")

    response = client.post("/login", data={
        "username": "admin",
        "password": "admin123"
    })
    set_cookie_header = response.headers.get("Set-Cookie", "")
    assert "HttpOnly" in set_cookie_header
    assert "SameSite=Lax" in set_cookie_header or "SameSite=Strict" in set_cookie_header


def test_session_fixation_clearing_on_login(client):
    """
    Garante que dados residuais ou IDs de sessão anteriores são purgados
    no momento do login para evitar Session Fixation.
    """
    with client.session_transaction() as sess:
        sess["pre_login_tracker"] = "untrusted_payload"

    client.post("/login", data={"username": "admin", "password": "admin123"})

    with client.session_transaction() as sess:
        assert "pre_login_tracker" not in sess
        assert sess.get("user_authenticated") is True
        assert sess.get("username") == "admin"


def test_one_click_demo_login(client):
    """
    Testa o fluxo de acesso em 1 clique (Live Demo) para visitantes e recrutadores.
    """
    response = client.post("/login/demo", follow_redirects=True)
    assert response.status_code == 200
    assert "Modo Demonstração" in response.get_data(as_text=True)

    with client.session_transaction() as sess:
        assert sess.get("user_authenticated") is True
        assert sess.get("username") == "admin"
        assert sess.get("is_superuser") is True
        assert sess.get("is_demo_session") is True


def test_login_with_demo_credentials(client):
    """
    Testa o login convencional preenchendo as credenciais de demonstração (admin / demo).
    """
    response = client.post("/login", data={
        "username": "admin",
        "password": "demo"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "Modo Demonstração" in response.get_data(as_text=True)

    with client.session_transaction() as sess:
        assert sess.get("user_authenticated") is True
        assert sess.get("is_demo_session") is True


def test_financial_unlock_demo_and_password(client):
    """
    Garante que visitantes podem desbloquear o módulo financeiro com 1 clique
    ou informando a senha 'demo'.
    """
    # 1. Faz login no sistema
    client.post("/login/demo")

    # 2. Desbloqueia com 1 clique (/financial/unlock/demo)
    res_unlock_demo = client.post("/financial/unlock/demo", follow_redirects=True)
    assert res_unlock_demo.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get("financial_unlocked") is True

    # 3. Bloqueia novamente
    client.get("/financial/lock")
    with client.session_transaction() as sess:
        assert sess.get("financial_unlocked") is None

    # 4. Desbloqueia via formulário com a senha "demo"
    res_unlock_pass = client.post("/financial/unlock", data={"financial_password": "demo"}, follow_redirects=True)
    assert res_unlock_pass.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get("financial_unlocked") is True


def test_demo_mode_anti_sabotage_protection(client, app):
    """
    Garante a regra de blindagem: visitantes em modo demonstração não podem
    excluir itens do catálogo mestre original semeado (evitando corrupção da vitrine),
    mas podem criar novos registros e excluí-los livremente.
    """
    from app import db
    from app.models import Product

    with app.app_context():
        # Produto base do catálogo (ID 1)
        p_base = Product(id=1, sku="BASE-PROD", name="Produto Base", price="100.00", is_active=True)
        # Produto criado por um visitante (ID 999)
        p_novo = Product(id=999, sku="VISITOR-PROD", name="Produto Visitante", price="50.00", is_active=True)
        db.session.add_all([p_base, p_novo])
        db.session.commit()

    # 1. Em sessão de demonstração
    with client.session_transaction() as sess:
        sess["user_authenticated"] = True
        sess["username"] = "admin"
        sess["is_demo_session"] = True

    # Tentativa de exclusão do produto base semeado (ID 1) -> Bloqueado com 403
    res_del_base = client.delete("/products/1")
    assert res_del_base.status_code == 403
    assert "Modo Demonstração" in res_del_base.get_json()["error"]

    res_del_perm = client.delete("/products/1/permanent")
    assert res_del_perm.status_code == 403

    # Exclusão do produto criado por visitante (ID 999) -> Permitido normalmente
    res_del_novo = client.delete("/products/999")
    assert res_del_novo.status_code == 200


def test_security_headers_present(client):
    """
    Garante que os cabeçalhos de segurança HTTP recomendados pelo OWASP
    estão presentes em todas as respostas HTTP do ERP.
    """
    response = client.get("/login")
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert "max-age=31536000" in response.headers.get("Strict-Transport-Security", "")
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in response.headers.get("Permissions-Policy", "")
    assert "default-src 'self'" in response.headers.get("Content-Security-Policy", "")


def test_unauthenticated_financial_api_access_control(client):
    """
    Garante que as APIs financeiras rejeitam acessos não autenticados com 401
    e acessos autenticados sem desbloqueio financeiro com 403.
    """
    # 1. Totalmente anônimo -> 401 Unauthorized
    res_anon = client.get("/api/financial/summary")
    assert res_anon.status_code == 401
    assert "Autenticação requerida" in res_anon.get_json()["error"]

    res_trans_anon = client.get("/api/financial/transactions")
    assert res_trans_anon.status_code == 401

    # 2. Usuário autenticado no ERP mas com módulo financeiro bloqueado -> 403 Forbidden
    with client.session_transaction() as sess:
        sess["user_authenticated"] = True
        sess["username"] = "admin"
        sess["financial_unlocked"] = False

    res_blocked = client.get("/api/financial/summary")
    assert res_blocked.status_code == 403
    assert "Acesso bloqueado" in res_blocked.get_json()["error"]

    # 3. Usuário autenticado e com módulo financeiro desbloqueado -> 200 OK
    with client.session_transaction() as sess:
        sess["financial_unlocked"] = True

    res_ok = client.get("/api/financial/summary")
    assert res_ok.status_code == 200
    assert "total_revenue" in res_ok.get_json()



