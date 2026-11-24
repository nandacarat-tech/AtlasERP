import pytest
from flask import abort


def test_api_404_returns_structured_json(client):
    """
    Comprova que rotas inexistentes de API respondem com JSON estruturado 404
    e não com páginas HTML padrão do framework.
    """
    res = client.get("/api/recurso-inexistente")
    assert res.status_code == 404
    data = res.get_json()
    assert data is not None
    assert data["status"] == 404
    assert "Recurso não encontrado" in data["error"]


def test_web_404_returns_clean_html(client):
    """
    Comprova que rotas web inexistentes respondem com HTML limpo de 404.
    """
    res = client.get("/ui/pagina-que-nao-existe-xyz")
    assert res.status_code == 404
    assert "404 Não Encontrado" in res.get_data(as_text=True)


def test_api_item_not_found_returns_json(client):
    """
    Comprova que buscar um produto inexistente na API (/products/999999)
    retorna 404 JSON estruturado.
    """
    res = client.get("/products/999999")
    assert res.status_code == 404
    data = res.get_json()
    assert data is not None
    assert "não encontrado" in data["error"].lower()


def test_500_internal_error_does_not_leak_internals(app, client):
    """
    Comprova que erros 500 internos do servidor respondem com mensagem genérica
    segura e não vazam stack traces, credenciais ou detalhes de infraestrutura.
    """
    @app.route("/api/test-trigger-500")
    def trigger_error():
        abort(500)

    res = client.get("/api/test-trigger-500")
    assert res.status_code == 500
    data = res.get_json()
    assert data is not None
    assert data["status"] == 500
    assert "erro interno" in data["error"].lower()
    # Garante que nenhum trace ou caminho de arquivo vazou
    assert "Traceback" not in res.get_data(as_text=True)
