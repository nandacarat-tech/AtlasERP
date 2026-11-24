import pytest
from app import db
from app.audit_models import AuditLog


def test_demo_mode_disabled_blocks_all_demo_shortcuts(app, client):
    """
    Comprova que quando ERP_DEMO_MODE=False (modo de produção corporativa estrita),
    todos os atalhos de demonstração, credenciais padrão 'demo' e 1-clique são
    estritamente bloqueados e auditados.
    """
    app.config["ERP_DEMO_MODE"] = False

    # 1. Tentativa de login 1-clique (/login/demo) deve ser rejeitada
    res_demo_click = client.post("/login/demo")
    assert res_demo_click.status_code == 200
    assert "desativado nesta instância" in res_demo_click.get_data(as_text=True)

    with app.app_context():
        log_click = AuditLog.query.filter_by(action="BLOCKED_DEMO_LOGIN").first()
        assert log_click is not None

    # 2. Tentativa de login com usuário 'admin' e senha 'demo' deve ser rejeitada
    res_demo_cred = client.post("/login", data={"username": "admin", "password": "demo"})
    assert res_demo_cred.status_code == 200
    assert "Credenciais de acesso incorretas" in res_demo_cred.get_data(as_text=True)

    with app.app_context():
        log_cred = AuditLog.query.filter_by(action="BLOCKED_DEMO_CREDENTIALS").first()
        assert log_cred is not None

    # 3. Tentativa de desbloqueio financeiro com senha estática 'demo' deve ser rejeitada
    with client.session_transaction() as sess:
        sess["user_authenticated"] = True
        sess["username"] = "usuario_normal"

    res_fin_demo = client.post("/financial/unlock", data={"financial_password": "demo"})
    assert res_fin_demo.status_code == 200
    assert "Senha do módulo financeiro incorreta" in res_fin_demo.get_data(as_text=True)

    # 4. Tentativa de desbloqueio financeiro 1-clique (/financial/unlock/demo) deve ser rejeitada
    res_fin_click = client.post("/financial/unlock/demo")
    assert res_fin_click.status_code == 302
    assert "/financial/unlock" in res_fin_click.headers.get("Location", "")

    # Restaura configuração
    app.config["ERP_DEMO_MODE"] = True


def test_demo_mode_enabled_allows_showcase_evaluation(app, client):
    """
    Comprova que quando ERP_DEMO_MODE=True (vitrine pública de demonstração),
    o avaliador/recrutador consegue testar a plataforma livremente.
    """
    app.config["ERP_DEMO_MODE"] = True

    # Login 1-clique funciona com 302 para /dashboard
    res = client.post("/login/demo")
    assert res.status_code == 302
    assert "/dashboard" in res.headers.get("Location", "")

    with client.session_transaction() as sess:
        assert sess.get("user_authenticated") is True
        assert sess.get("is_demo_session") is True
        assert sess.get("is_superuser") is True
