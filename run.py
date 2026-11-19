import os
import socket
import webbrowser
from threading import Timer
from app import create_app

app = create_app()


def find_available_port(preferred_ports=[5000, 5055, 5500, 8888, 8000]):
    for port in preferred_ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except Exception:
            continue
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def open_browser(port):
    webbrowser.open(f"http://127.0.0.1:{port}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 0)) or find_available_port()
    print("=" * 60)
    print(f" AtlasERP iniciado com sucesso na porta {port}!")
    print(f" Acessando automaticamente: http://127.0.0.1:{port}")
    print("=" * 60)
    
    # Abre o navegador automaticamente em 1.5 segundo
    Timer(1.5, open_browser, args=[port]).start()
    app.run(host="127.0.0.1", port=port, debug=False)
