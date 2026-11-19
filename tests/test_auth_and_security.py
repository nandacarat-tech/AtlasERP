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

