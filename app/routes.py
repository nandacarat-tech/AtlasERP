from flask import Blueprint


main = Blueprint("main", __name__)


@main.get("/")
def index():
    return {
        "application": "AtlasERP",
        "status": "online",
        "message": "AtlasERP iniciado com sucesso"
    }
