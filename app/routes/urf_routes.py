from flask import Blueprint, Response, json, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.dao import urf_dao
from app.routes import routes_utils


urf_bp = Blueprint('urf', __name__)

limiter = Limiter(
    get_remote_address,  # Usa o IP do cliente para limitar requisições
    default_limits=["100 per hour"]  # Definição de um limite padrão
)


@urf_bp.route('/busca_urf_por_nome', methods=["GET"])
def busca_urf_por_nome():
    nome = request.args.get('nome')
    if nome is None:
        pesquisa = urf_dao.busca_todos_urf()
    else:
        pesquisa = urf_dao.busca_urf_por_nome(nome)
    return routes_utils.return_response(pesquisa)