import json
from datetime import datetime, timezone
from app import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    # SQLite requer Integer para autoincrement; MySQL/PostgreSQL suportam BigInteger
    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    username_snapshot = db.Column(db.String(80), nullable=False, index=True)

    action = db.Column(db.String(50), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=False, index=True)
    entity_id = db.Column(db.String(50), nullable=True)
    changes_json = db.Column(db.Text, nullable=True)

    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    user = db.relationship("User", backref=db.backref("audit_logs", lazy="dynamic"))

    def get_changes(self):
        if not self.changes_json:
            return {}
        try:
            return json.loads(self.changes_json)
        except Exception:
            return {"raw": self.changes_json}

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username_snapshot,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "changes": self.get_changes(),
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.entity_type}:{self.entity_id} by {self.username_snapshot}>"


from sqlalchemy import event


class AuditLogImmutableError(RuntimeError):
    """Excecao de seguranca disparada ao tentar alterar ou remover registros imutaveis de auditoria."""
    pass


@event.listens_for(AuditLog, "before_update")
def prevent_audit_log_update(mapper, connection, target):
    raise AuditLogImmutableError(
        f"VIOLACAO DE INTEGRIDADE: Registros de auditoria sao estritamente imutaveis! (Tentativa de UPDATE no log #{target.id})"
    )


@event.listens_for(AuditLog, "before_delete")
def prevent_audit_log_delete(mapper, connection, target):
    raise AuditLogImmutableError(
        f"VIOLACAO DE INTEGRIDADE: Registros de auditoria sao estritamente imutaveis! (Tentativa de DELETE no log #{target.id})"
    )


from sqlalchemy import Engine

@event.listens_for(Engine, "before_cursor_execute", retval=False)
def prevent_audit_log_sql_mutation(conn, cursor, statement, parameters, context, executemany):
    """
    Camada de Defesa em Profundidade no Driver/Engine:
    Bloqueia estritamente qualquer instrucao SQL (SQLAlchemy Core, session.execute, CTEs com WITH ou SQL direto)
    de UPDATE ou DELETE que vise a tabela audit_logs antes que ela seja despachada ao cursor do banco.
    A garantia primária definitiva permanece a revogação de privilégios (REVOKE UPDATE, DELETE) no MySQL.
    """
    stmt_clean = " ".join(statement.strip().split()).upper()
    if stmt_clean.startswith(("CREATE", "ALTER", "DROP", "SELECT", "INSERT", "SHOW", "DESCRIBE", "EXPLAIN", "PRAGMA")):
        return

    if "AUDIT_LOGS" in stmt_clean:
        if (
            stmt_clean.startswith("UPDATE")
            or stmt_clean.startswith("DELETE")
            or " UPDATE " in stmt_clean
            or " DELETE FROM " in stmt_clean
            or " DELETE " in stmt_clean
        ):
            raise AuditLogImmutableError(
                "VIOLACAO CRITICA DE INTEGRIDADE: Operacoes SQL de UPDATE ou DELETE na tabela audit_logs sao estritamente proibidas!"
            )


