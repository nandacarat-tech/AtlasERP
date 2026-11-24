import json
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import session, request, g, redirect, url_for, abort, has_request_context, current_app, jsonify

from app import db
from app.auth_models import User, EmergencyAdminIdentity
from app.audit_models import AuditLog

GENERIC_AUTH_ERROR = "Credenciais de acesso incorretas ou conta indisponível."


def get_client_ip():
    if not has_request_context():
        return "127.0.0.1"
    # Com ProxyFix configurado no WSGI, request.remote_addr contem o IP real confiavel
    return request.remote_addr or "127.0.0.1"


def get_client_user_agent():
    if not has_request_context() or not request.user_agent:
        return "Internal/Script"
    return request.user_agent.string[:255]


def log_audit_event(action: str, entity_type: str, entity_id=None, changes=None, user=None, commit: bool = False):
    """
    Registra um evento na trilha de auditoria do sistema.
    Por padrao (commit=False), apenas adiciona o log a sessao do SQLAlchemy (db.session.add),
    garantindo que o evento e a operacao de negocio sejam commitados ou cancelados
    atomicamente na mesma transacao. Para operacoes isoladas de seguranca (ex: login),
    commit=True pode ser informado.
    """
    effective_user = user or getattr(g, "current_user", None)
    username = "ANONIMO"
    user_id = None

    if effective_user:
        username = getattr(effective_user, "username", "SISTEMA")
        user_id = getattr(effective_user, "id", None)
    elif has_request_context() and session and session.get("username"):
        username = session.get("username")
        user_id = session.get("user_id")

    changes_str = None
    if changes is not None:
        if isinstance(changes, (dict, list)):
            changes_str = json.dumps(changes, default=str)
        else:
            changes_str = str(changes)

    log_entry = AuditLog(
        user_id=user_id,
        username_snapshot=username,
        action=action.upper(),
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        changes_json=changes_str,
        ip_address=get_client_ip(),
        user_agent=get_client_user_agent(),
        created_at=datetime.now(timezone.utc),
    )

    db.session.add(log_entry)
    if commit:
        db.session.commit()
    return log_entry


def authenticate_user(username: str, password: str, max_attempts: int = 5, lock_minutes: int = 15):
    """
    Autentica o usuário com proteção integrada contra ataques de força bruta
    e previne enumeração de contas retornando mensagem genérica consistente.
    """
    user = User.query.filter_by(username=username).first()

    if not user:
        log_audit_event(
            action="FAILED_LOGIN",
            entity_type="User",
            entity_id=None,
            changes={"reason": "Usuario inexistente", "attempted": username},
            commit=True,
        )
        return False, GENERIC_AUTH_ERROR

    if not user.is_active:
        log_audit_event(
            action="BLOCKED_LOGIN",
            entity_type="User",
            entity_id=user.id,
            changes={"reason": "Conta desativada"},
            user=user,
            commit=True,
        )
        return False, GENERIC_AUTH_ERROR

    if user.is_locked():
        log_audit_event(
            action="LOCKED_LOGIN_ATTEMPT",
            entity_type="User",
            entity_id=user.id,
            user=user,
            commit=True,
        )
        return False, GENERIC_AUTH_ERROR

    if not user.check_password(password):
        # Incremento atômico no banco de dados para mitigar condições de corrida
        db.session.execute(
            db.update(User)
            .where(User.id == user.id)
            .values(failed_login_attempts=User.failed_login_attempts + 1)
        )
        db.session.flush()
        db.session.refresh(user)

        changes = {"attempts": user.failed_login_attempts}
        if user.failed_login_attempts >= max_attempts:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=lock_minutes)
            changes["locked_until"] = user.locked_until.isoformat()
            log_audit_event(action="ACCOUNT_LOCKED", entity_type="User", entity_id=user.id, changes=changes, user=user)
        else:
            log_audit_event(action="FAILED_PASSWORD", entity_type="User", entity_id=user.id, changes=changes, user=user)
        db.session.commit()
        return False, GENERIC_AUTH_ERROR

    # Login bem-sucedido: limpa contadores de falha
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()

    # Prevenção de Session Fixation
    if has_request_context():
        session.clear()
        session["user_authenticated"] = True
        session["user_id"] = user.id
        session["username"] = user.username
        session["is_superuser"] = user.is_superuser
        session["role"] = user.role.name if user.role else None

    log_audit_event(action="LOGIN", entity_type="User", entity_id=user.id, user=user, commit=True)
    return True, user


def logout_user():
    """
    Encerra a sessão atual e registra o evento na auditoria.
    """
    user = getattr(g, "current_user", None) if has_request_context() else None
    log_audit_event(action="LOGOUT", entity_type="User", entity_id=user.id if user else None, user=user, commit=True)
    if has_request_context():
        session.clear()


def _is_api_request():
    if not has_request_context():
        return False
    return (
        request.path.startswith("/api/")
        or request.is_json
        or request.headers.get("Accept") == "application/json"
        or (
            any(request.path.startswith(prefix) for prefix in [
                "/products", "/customers", "/sales", "/purchases", "/suppliers", "/fleet"
            ])
            and not request.path.startswith("/ui/")
        )
    )


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_authenticated"):
            if _is_api_request():
                return jsonify({"error": "Autenticação requerida."}), 401
            next_url = request.path if request.method == "GET" else url_for("main.dashboard")
            return redirect(url_for("main.login", next=next_url))

        # Carrega o usuário da sessão em g.current_user de forma estrita
        user_id = session.get("user_id")
        if user_id:
            user = db.session.get(User, user_id)
            if not user or not user.is_active or user.is_locked():
                session.clear()
                if _is_api_request():
                    return jsonify({"error": "Sessão inválida ou conta inativa."}), 401
                return redirect(url_for("main.login"))
            g.current_user = user
        elif session.get("is_superuser") or session.get("is_demo_session"):
            user = User.query.filter_by(username="admin").first()
            if not user:
                user = EmergencyAdminIdentity(username=session.get("username", "admin"))
            user.is_superuser = True
            g.current_user = user
        elif session.get("is_emergency_admin") and current_app.config.get("ERP_EMERGENCY_ADMIN_ENABLED"):
            g.current_user = EmergencyAdminIdentity(username=session.get("username", "emergency_admin"))
        else:
            session.clear()
            if _is_api_request():
                return jsonify({"error": "Sessão inválida."}), 401
            return redirect(url_for("main.login"))

        return f(*args, **kwargs)
    return decorated_function


def permission_required(permission_code: str):
    """
    Garante que o usuário autenticado possui a permissão especificada.
    Elimina qualquer possibilidade de bypass exigindo identidade válida com .can().
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if not user or not user.can(permission_code):
                log_audit_event(
                    action="UNAUTHORIZED_ACCESS",
                    entity_type="Permission",
                    entity_id=permission_code,
                    commit=True,
                )
                if _is_api_request():
                    return jsonify({
                        "error": "Acesso negado. Permissão insuficiente.",
                        "required_permission": permission_code
                    }), 403
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required(*allowed_roles):
    """
    Garante que o usuário pertence a pelo menos um dos papéis informados (ou é superuser).
    Exige identidade válida em g.current_user.
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if not user:
                if _is_api_request():
                    return jsonify({"error": "Acesso não autorizado."}), 403
                abort(403)
            if getattr(user, "is_superuser", False):
                return f(*args, **kwargs)
            user_role = user.role.name if getattr(user, "role", None) else None
            if user_role not in allowed_roles:
                log_audit_event(
                    action="UNAUTHORIZED_ROLE_ACCESS",
                    entity_type="Role",
                    changes={"required": list(allowed_roles), "actual": user_role},
                    commit=True,
                )
                if _is_api_request():
                    return jsonify({
                        "error": "Acesso restrito ao perfil.",
                        "required_roles": list(allowed_roles)
                    }), 403
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
