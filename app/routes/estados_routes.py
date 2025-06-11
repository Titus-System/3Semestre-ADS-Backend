from typing import List
from flask import Request, Response, json, jsonify, Blueprint, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from ..dao import estado_dao
from .routes_utils_estados import get_args
from app.routes import routes_utils, routes_utils_estados


estado_bp = Blueprint('estado', __name__)

limiter = Limiter(
    get_remote_address,
    default_limits=["100 per hour"]
)


@estado_bp.route('/ranking_estado', methods=["GET"])
@limiter.limit("10 per minute")
def busca_top_estados():
    args = get_args(request)

    if not isinstance(args, dict):
        return jsonify({'error': f'Erro na requisição: {args}'}), 400

    if 'tipo' not in args:
        return jsonify({'error': "Erro na requisição: Parâmetro 'tipo' é obrigatório."}), 400

    tipos = args['tipo']
    if isinstance(tipos, str):
        tipos = [tipos]

    resultados = []
    for tipo in tipos:
        args_copia = args.copy()
        args_copia['tipo'] = tipo
        resultado = estado_dao.busca_top_estado(**args_copia)
        resultados.append({"tipo": tipo, "dados": resultado})

    return routes_utils_estados.return_response(resultados)


@estado_bp.route('/busca_estado_hist', methods=["GET"])
@limiter.limit('10 per minute')
def busca_estado_hist():
    args = routes_utils.get_args(request)

    if not isinstance(args, dict):
        return jsonify({'error': f'Erro na requisição: {args}'}), 400

    if 'estados' not in args or 'tipo' not in args:
        return jsonify({'error': "Erro na requisição: Parâmetros 'tipo' e 'estados' são obrigatórios."}), 400

    resultado = estado_dao.busca_estado_hist(**args)
    return routes_utils_estados.return_response(resultado)


@estado_bp.route('/pesquisa_estado_por_nome', methods=["GET"])
@limiter.limit('10 per minute')
def pesquisa_estado():
    nome = request.args.get('nome')
    if nome is None:
        pesquisa = estado_dao.busca_todos_estados()
    else:
        pesquisa = estado_dao.pesquisa_estado_por_nome(nome)
    return routes_utils_estados.return_response(pesquisa)