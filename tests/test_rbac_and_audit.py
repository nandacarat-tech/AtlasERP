import pytest
from datetime import datetime, timezone, timedelta
from flask import Flask

from sqlalchemy import update, delete, text
from app import db
from app.auth_models import User, Role, Permission, EmergencyAdminIdentity
from app.audit_models import AuditLog, AuditLogImmutableError
from app.auth_service import (
    authenticate_user,
    logout_user,
    log_audit_event,
    permission_required,
    role_required,
)
from app.seed_auth import seed_rbac


def test_seed_rbac_creates_roles_and_permissions(app):
    with app.app_context():
        roles = seed_rbac()
        assert "ADMIN" in roles
        assert "VENDEDOR" in roles
        assert "FINANCEIRO" in roles

        admin_role = Role.query.filter_by(name="ADMIN").first()
        vendedor_role = Role.query.filter_by(name="VENDEDOR").first()

        assert admin_role.has_permission("financial.manage") is True
        assert vendedor_role.has_permission("sales.create") is True
        assert vendedor_role.has_permission("financial.manage") is False


def test_user_password_hashing_and_validation(app):
    with app.app_context():
        user = User(
            username="maria.silva",
            email="maria@empresa.com",
            full_name="Maria Silva",
        )
        user.set_password("segredoForte123")
        db.session.add(user)
        db.session.commit()

        assert user.password_hash != "segredoForte123"
        assert user.check_password("segredoForte123") is True
        assert user.check_password("senhaErrada") is False

        # Valida rejeicao de senha curta
        with pytest.raises(ValueError):
            user.set_password("123")


def test_user_rbac_permissions(app):
    with app.app_context():
        seed_rbac()
        vendedor_role = Role.query.filter_by(name="VENDEDOR").first()

        vendedor = User(
            username="joao.vendedor",
            email="joao@empresa.com",
            full_name="João Vendedor",
            role=vendedor_role,
        )
        vendedor.set_password("senhaValida123")

        superuser = User(
            username="admin.chefe",
            email="admin@empresa.com",
            full_name="Administrador Chefe",
            is_superuser=True,
        )
        superuser.set_password("adminSenha123")

        db.session.add_all([vendedor, superuser])
        db.session.commit()

        # Vendedor pode vender, mas não pode gerenciar financeiro
        assert vendedor.can("sales.create") is True
        assert vendedor.can("financial.manage") is False

        # Superuser pode tudo
        assert superuser.can("financial.manage") is True
        assert superuser.can("qualquer.coisa") is True

        # Usuário inativo não pode nada
        vendedor.is_active = False
        db.session.commit()
        assert vendedor.can("sales.create") is False


def test_authentication_and_brute_force_lockout(app, client):
    with app.app_context():
        user = User(
            username="carlos.financeiro",
            email="carlos@empresa.com",
            full_name="Carlos Financeiro",
        )
        user.set_password("minhaSenha123")
        db.session.add(user)
        db.session.commit()

        # 1. Tentativas com senha errada
        for i in range(1, 5):
            success, msg = authenticate_user("carlos.financeiro", "senhaErrada", max_attempts=5)
            assert success is False
            assert user.failed_login_attempts == i
            assert user.is_locked() is False

        # 2. 5ª tentativa errada -> Bloqueia a conta
        success, msg = authenticate_user("carlos.financeiro", "senhaErrada", max_attempts=5, lock_minutes=10)
        assert success is False
        assert user.is_locked() is True

        # 3. Mesmo com a senha certa agora, deve recusar por estar bloqueado
        success, msg = authenticate_user("carlos.financeiro", "minhaSenha123")
        assert success is False
        assert "Credenciais de acesso incorretas" in msg

        # 4. Simula o tempo passando (desbloqueio)
        user.locked_until = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.session.commit()
        assert user.is_locked() is False

        # 5. Agora com senha correta -> autentica e reseta contadores
        success, logged_user = authenticate_user("carlos.financeiro", "minhaSenha123")
        assert success is True
        assert logged_user.failed_login_attempts == 0
        assert logged_user.last_login_at is not None


def test_audit_log_tracking(app):
    with app.app_context():
        user = User(
            username="auditoria.teste",
            email="audit@empresa.com",
            full_name="Auditor Teste",
        )
        user.set_password("senhaAuditoria123")
        db.session.add(user)
        db.session.commit()

        # Dispara evento de auditoria
        log = log_audit_event(
            action="UPDATE",
            entity_type="Sale",
            entity_id="105",
            changes={"status": {"before": "OPEN", "after": "CONFIRMED"}},
            user=user,
            commit=True,
        )

        assert log.id is not None
        assert log.username_snapshot == "auditoria.teste"
        assert log.action == "UPDATE"
        assert log.entity_type == "Sale"
        assert log.entity_id == "105"
        assert log.get_changes()["status"]["after"] == "CONFIRMED"


def test_permission_required_decorator(app):
    @app.route("/test-permission-vendas")
    @permission_required("sales.create")
    def rota_vendas():
        return "Acesso Permitido a Vendas", 200

    client = app.test_client()

    with app.app_context():
        seed_rbac()
        vendedor_role = Role.query.filter_by(name="VENDEDOR").first()
        consulta_role = Role.query.filter_by(name="CONSULTA").first()

        u_vendedor = User(username="vendedor1", email="v1@t.com", full_name="Vendedor", role=vendedor_role)
        u_vendedor.set_password("senhaSegura123")

        u_consulta = User(username="consulta1", email="c1@t.com", full_name="Consulta", role=consulta_role)
        u_consulta.set_password("senhaSegura123")

        db.session.add_all([u_vendedor, u_consulta])
        db.session.commit()

        u_vendedor_id = u_vendedor.id
        u_consulta_id = u_consulta.id

    # 1. Sem login -> redireciona para login
    res = client.get("/test-permission-vendas")
    assert res.status_code == 302
    assert "/login" in res.location

    # 2. Login com usuário sem permissão (CONSULTA) -> 403 Forbidden
    with client.session_transaction() as sess:
        sess["user_authenticated"] = True
        sess["user_id"] = u_consulta_id
        sess["username"] = "consulta1"

    res_forbidden = client.get("/test-permission-vendas")
    assert res_forbidden.status_code == 403

    # 3. Login com usuário autorizado (VENDEDOR) -> 200 OK
    with client.session_transaction() as sess:
        sess["user_authenticated"] = True
        sess["user_id"] = u_vendedor_id
        sess["username"] = "vendedor1"

    res_ok = client.get("/test-permission-vendas")
    assert res_ok.status_code == 200
    assert "Acesso Permitido" in res_ok.get_data(as_text=True)


def test_individual_user_web_login_and_logout_flow(app, client):
    with app.app_context():
        user = User(
            username="roberto.web",
            email="roberto@empresa.com",
            full_name="Roberto Web",
        )
        user.set_password("senhaForte123")
        db.session.add(user)
        db.session.commit()

    # 1. Login com senha errada
    res_fail = client.post("/login", data={"username": "roberto.web", "password": "senhaInvalida"})
    assert res_fail.status_code == 200
    assert "Credenciais de acesso incorretas" in res_fail.get_data(as_text=True)

    # 2. Login com sucesso
    res_login = client.post("/login", data={"username": "roberto.web", "password": "senhaForte123"}, follow_redirects=True)
    assert res_login.status_code == 200

    with client.session_transaction() as sess:
        assert sess.get("user_authenticated") is True
        assert sess.get("username") == "roberto.web"

    # 3. Logout via POST
    res_logout = client.post("/logout", follow_redirects=True)
    assert res_logout.status_code == 200

    with client.session_transaction() as sess:
        assert sess.get("user_authenticated") is None

    # 4. Verifica se os logs de auditoria foram registrados
    with app.app_context():
        logs = AuditLog.query.filter_by(username_snapshot="roberto.web").all()
        actions = [l.action for l in logs]
        assert "FAILED_PASSWORD" in actions
        assert "LOGIN" in actions
        assert "LOGOUT" in actions


def test_audit_log_immutability_prevents_update_and_delete(app):
    """
    Comprova que registros de auditoria são estritamente imutáveis na aplicação:
    qualquer tentativa de UPDATE ou DELETE via ORM, SQLAlchemy Core ou SQL bruto
    levanta AuditLogImmutableError e é barrada antes de atingir o banco.
    """
    with app.app_context():
        log = log_audit_event(
            action="CREATE",
            entity_type="FinancialTransaction",
            entity_id="99",
            changes={"valor": 1000},
            commit=True,
        )
        log_id = log.id
        assert log_id is not None

        # 1. Tentativa de adulterar o log via ORM (UPDATE)
        log.username_snapshot = "hacker"
        with pytest.raises(AuditLogImmutableError) as exc_info:
            db.session.commit()
        assert "imutaveis" in str(exc_info.value)
        db.session.rollback()

        # 2. Tentativa de apagar o log via ORM (DELETE)
        fresh_log = db.session.get(AuditLog, log_id)
        db.session.delete(fresh_log)
        with pytest.raises(AuditLogImmutableError) as exc_info_del:
            db.session.commit()
        assert "imutaveis" in str(exc_info_del.value)
        db.session.rollback()

        # 3. Tentativa via SQLAlchemy Core (UPDATE)
        with pytest.raises(AuditLogImmutableError) as exc_core_up:
            db.session.execute(
                update(AuditLog).where(AuditLog.id == log_id).values(username_snapshot="hacker_core")
            )
        assert "proibidas" in str(exc_core_up.value).lower()
        db.session.rollback()

        # 4. Tentativa via SQLAlchemy Core (DELETE)
        with pytest.raises(AuditLogImmutableError) as exc_core_del:
            db.session.execute(
                delete(AuditLog).where(AuditLog.id == log_id)
            )
        assert "proibidas" in str(exc_core_del.value).lower()
        db.session.rollback()

        # 5. Tentativa via SQL bruto direto (UPDATE text)
        with pytest.raises(AuditLogImmutableError) as exc_raw_up:
            db.session.execute(
                text(f"UPDATE audit_logs SET username_snapshot = 'hacker_raw' WHERE id = {log_id}")
            )
        assert "proibidas" in str(exc_raw_up.value).lower()
        db.session.rollback()

        # 6. Tentativa via SQL bruto direto (DELETE text)
        with pytest.raises(AuditLogImmutableError) as exc_raw_del:
            db.session.execute(
                text(f"DELETE FROM audit_logs WHERE id = {log_id}")
            )
        assert "proibidas" in str(exc_raw_del.value).lower()
        db.session.rollback()


def test_transactional_atomicity_audit_log_rolls_back_with_operation(app):
    """
    Comprova que log_audit_event(commit=False) é transacionalmente atômico com a operação:
    se a operação de negócio sofrer rollback, o log de auditoria também é revertido.
    """
    with app.app_context():
        initial_logs_count = AuditLog.query.count()

        # Simula operação de negócio que gera log mas falha antes do commit
        try:
            log_audit_event(
                action="CONFIRM",
                entity_type="Sale",
                entity_id="999",
                changes={"status": "CONFIRMED"},
                commit=False,
            )
            # Simula falha catastrófica no banco ou regra de negócio
            raise ValueError("Erro de negócio: estoque insuficiente")
        except ValueError:
            db.session.rollback()

        # NENHUM registro inconsistente deve ter sido persistido
        final_logs_count = AuditLog.query.count()
        assert final_logs_count == initial_logs_count


def test_inactive_and_locked_users_cannot_login_via_web(app, client):
    """
    Comprova que usuários inativos ou bloqueados são barrados na rota web de login
    com resposta genérica para mitigar enumeração de contas, gerando os eventos de auditoria corretos.
    """
    with app.app_context():
        u_inativo = User(username="inativo.teste", email="inativo@t.com", full_name="Inativo", is_active=False)
        u_inativo.set_password("senhaForte123")

        u_bloqueado = User(
            username="bloqueado.teste",
            email="bloq@t.com",
            full_name="Bloqueado",
            locked_until=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        u_bloqueado.set_password("senhaForte123")

        db.session.add_all([u_inativo, u_bloqueado])
        db.session.commit()

    # 1. Tentativa de login de usuário inativo
    res_inativo = client.post("/login", data={"username": "inativo.teste", "password": "senhaForte123"})
    assert res_inativo.status_code == 200
    assert "Credenciais de acesso incorretas" in res_inativo.get_data(as_text=True)

    # 2. Tentativa de login de usuário com conta bloqueada
    res_bloqueado = client.post("/login", data={"username": "bloqueado.teste", "password": "senhaForte123"})
    assert res_bloqueado.status_code == 200
    assert "Credenciais de acesso incorretas" in res_bloqueado.get_data(as_text=True)

    # 3. Verifica auditoria interna detalhada
    with app.app_context():
        logs_inativo = AuditLog.query.filter_by(action="BLOCKED_LOGIN").count()
        logs_bloqueado = AuditLog.query.filter_by(action="LOCKED_LOGIN_ATTEMPT").count()
        assert logs_inativo >= 1
        assert logs_bloqueado >= 1


def test_emergency_admin_disabled_by_default(app, client):
    """
    Comprova que quando ERP_EMERGENCY_ADMIN_ENABLED=False, o login emergencial
    é estritamente recusado e gera um alerta em AuditLog.
    """
    app.config["ERP_EMERGENCY_ADMIN_ENABLED"] = False

    res = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    assert "Acesso emergencial desativado" in res.get_data(as_text=True)

    with app.app_context():
        alert = AuditLog.query.filter_by(action="DISABLED_EMERGENCY_ADMIN_ATTEMPT").first()
        assert alert is not None
        assert alert.entity_type == "ConfigAdmin"

    # Restaura configuração para testes subsequentes
    app.config["ERP_EMERGENCY_ADMIN_ENABLED"] = True


def test_fine_grained_role_authorization_forbidden(app):
    """
    Comprova a segregação estrita de funções:
    - Vendedor não tem permissão para aprovar financeiro (financial.approve)
    - Estoquista não tem permissão para gerenciar financeiro (financial.manage)
    - Ambas as tentativas abortam com HTTP 403 Forbidden
    """
    @app.route("/test-financial-approve")
    @permission_required("financial.approve")
    def rota_aprovar():
        return "Pagamento Aprovado", 200

    client = app.test_client()

    with app.app_context():
        seed_rbac()
        vendedor_role = Role.query.filter_by(name="VENDEDOR").first()
        estoquista_role = Role.query.filter_by(name="ESTOQUISTA").first()

        u_vendedor = User(username="vendedor.sec", email="vsec@t.com", full_name="Vendedor Sec", role=vendedor_role)
        u_vendedor.set_password("senhaSegura123")

        u_estoquista = User(username="estoquista.sec", email="esec@t.com", full_name="Estoquista Sec", role=estoquista_role)
        u_estoquista.set_password("senhaSegura123")

        db.session.add_all([u_vendedor, u_estoquista])
        db.session.commit()

        u_vendedor_id = u_vendedor.id
        u_estoquista_id = u_estoquista.id

    # 1. Vendedor tenta aprovar pagamento financeiro -> 403 Forbidden
    with client.session_transaction() as sess:
        sess["user_authenticated"] = True
        sess["user_id"] = u_vendedor_id
        sess["username"] = "vendedor.sec"

    res_vend = client.get("/test-financial-approve")
    assert res_vend.status_code == 403

    # 2. Estoquista tenta aprovar pagamento financeiro -> 403 Forbidden
    with client.session_transaction() as sess:
        sess["user_authenticated"] = True
        sess["user_id"] = u_estoquista_id
        sess["username"] = "estoquista.sec"

    res_est = client.get("/test-financial-approve")
    assert res_est.status_code == 403

    # 3. Verifica se as tentativas indevidas foram registradas na trilha de auditoria
    with app.app_context():
        unauthorized_logs = AuditLog.query.filter_by(action="UNAUTHORIZED_ACCESS").all()
        assert len(unauthorized_logs) >= 2


def test_authorization_bypass_prevention_with_orphan_session(app):
    """
    Comprova que uma sessão sem identidade válida (ex: user_id inexistente ou
    apenas session['user_authenticated'] = True sem g.current_user) NUNCA consegue
    bypassar o decorator permission_required: a requisição é barrada.
    """
    @app.route("/test-secure-admin-area")
    @permission_required("users.manage")
    def rota_restrita():
        return "Area de Seguranca Maxima", 200

    client = app.test_client()

    # Tentativa de bypass injetando session['user_authenticated'] = True sem identidade válida
    with client.session_transaction() as sess:
        sess["user_authenticated"] = True
        sess["user_id"] = 9999999  # ID inexistente no banco
        sess["username"] = "fantasma"

    res = client.get("/test-secure-admin-area")
    # login_required detecta a inconsistência, invalida a sessão e redireciona para login
    assert res.status_code == 302
    assert "/login" in res.location

    # Garante que a sessão órfã foi limpa
    with client.session_transaction() as sess:
        assert sess.get("user_authenticated") is None


def test_emergency_admin_restricted_scope(app):
    """
    Comprova que o administrador de emergência (Break-Glass) possui escopo ESTRITO:
    - PODE acessar rotas de gestão de usuários (users.manage) para restaurar acessos
    - NÃO PODE aprovar operações financeiras (financial.approve)
    - NÃO PODE contornar regras de negócio
    """
    @app.route("/test-emergency-users-manage")
    @permission_required("users.manage")
    def rota_emergencia_permitida():
        return "Gestao de Usuarios Liberada", 200

    @app.route("/test-emergency-financial-approve")
    @permission_required("financial.approve")
    def rota_financeira_restrita():
        return "Pagamento Aprovado", 200

    client = app.test_client()
    app.config["ERP_EMERGENCY_ADMIN_ENABLED"] = True

    # Sessão de emergência autenticada
    with client.session_transaction() as sess:
        sess["user_authenticated"] = True
        sess["username"] = "admin"
        sess["user_id"] = None
        sess["is_emergency_admin"] = True

    # 1. Recuperação de desastres: Acesso permitido a gestão de usuários
    res_users = client.get("/test-emergency-users-manage")
    assert res_users.status_code == 200
    assert "Gestao de Usuarios Liberada" in res_users.get_data(as_text=True)

    # 2. Operação financeira: Acesso NEGADO (403 Forbidden)!
    res_fin = client.get("/test-emergency-financial-approve")
    assert res_fin.status_code == 403


def test_password_whitespace_preserved(app, client):
    """
    Comprova que espaços intencionais no início ou fim da senha não são removidos
    por .strip() indevido, permitindo autenticação bem-sucedida de senhas com espaços.
    """
    senha_com_espacos = "  minhaSenhaForte123  "

    with app.app_context():
        user = User(
            username="lucas.espacos",
            email="lucas@espacos.com",
            full_name="Lucas Espaços",
        )
        user.set_password(senha_com_espacos)
        db.session.add(user)
        db.session.commit()

    # Login enviando exatamente a senha com espaços
    res = client.post("/login", data={
        "username": "lucas.espacos",
        "password": senha_com_espacos,
    }, follow_redirects=True)
    assert res.status_code == 200

    with client.session_transaction() as sess:
        assert sess.get("user_authenticated") is True
        assert sess.get("username") == "lucas.espacos"


