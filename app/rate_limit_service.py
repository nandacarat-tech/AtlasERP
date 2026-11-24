import time
import threading
from typing import Tuple, Dict, List
from flask import request


_lock = threading.Lock()
# Mapeia key -> lista de timestamps (float) de tentativas com falha
_attempts: Dict[str, List[float]] = {}
# Mapeia key -> timestamp (float) de término do bloqueio
_blocked_until: Dict[str, float] = {}


def get_client_ip() -> str:
    """
    Retorna o endereço IP real do cliente, respeitando headers
    de proxy reverso (Cloud Run / Load Balancer) se presentes.
    """
    if request:
        x_forwarded = request.headers.get("X-Forwarded-For")
        if x_forwarded:
            # O primeiro IP na lista do X-Forwarded-For é o cliente original
            return x_forwarded.split(",")[0].strip()
        return request.remote_addr or "127.0.0.1"
    return "127.0.0.1"


def is_rate_limited(key: str) -> Tuple[bool, int]:
    """
    Verifica se a chave fornecida está atualmente bloqueada.
    Retorna (is_blocked, retry_after_seconds).
    """
    now = time.time()
    with _lock:
        blocked_time = _blocked_until.get(key)
        if blocked_time and blocked_time > now:
            return True, int(blocked_time - now) + 1
        elif blocked_time and blocked_time <= now:
            # Bloqueio expirou; limpa o registro
            _blocked_until.pop(key, None)
            _attempts.pop(key, None)
    return False, 0


def record_failed_attempt(
    key: str, max_attempts: int = 5, window_seconds: int = 60
) -> Tuple[bool, int]:
    """
    Registra uma tentativa com falha para a chave.
    Se o total de falhas dentro de window_seconds atingir max_attempts,
    bloqueia a chave por window_seconds.
    Retorna (is_blocked, retry_after_seconds).
    """
    now = time.time()
    with _lock:
        # Se já estiver bloqueado, retorna o tempo restante
        blocked_time = _blocked_until.get(key)
        if blocked_time and blocked_time > now:
            return True, int(blocked_time - now) + 1

        # Limpa tentativas fora da janela deslizante
        timestamps = _attempts.get(key, [])
        timestamps = [t for t in timestamps if t > now - window_seconds]
        timestamps.append(now)
        _attempts[key] = timestamps

        if len(timestamps) >= max_attempts:
            unlock_time = now + window_seconds
            _blocked_until[key] = unlock_time
            return True, window_seconds

    return False, 0


def reset_attempts(key: str) -> None:
    """
    Limpa o histórico de tentativas e bloqueios para a chave (após autenticação bem-sucedida).
    """
    with _lock:
        _attempts.pop(key, None)
        _blocked_until.pop(key, None)


def clear_all_limits() -> None:
    """
    Limpa todos os registros (utilizado em testes para garantir isolamento).
    """
    with _lock:
        _attempts.clear()
        _blocked_until.clear()
