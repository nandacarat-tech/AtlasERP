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
    assert "Usuário ou senha de acesso incorretos" in response.get_data(as_text=True)


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

    # Logout
    logout_res = client.get("/logout")
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
