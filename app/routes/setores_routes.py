from app.dao import sh4_dao
from . import routes_utils
from flask import Blueprint, jsonify, request
from ..utils.logging_config import error_logger, app_logger

setores_bp = Blueprint("setores", __name__)


@setores_bp.route("/busca_info_setores", methods=["GET"])
def busca_ranking_setores():
    args = routes_utils.get_args(request)
    
    if not isinstance(args, dict):
        return jsonify({'error': f'Erro na requisição: {args}'}), 400
    
    res = sh4_dao.busca_info_setores(anos=args.get("anos"),
                                     pais=args.get('pais'), 
                                     estado=args.get('estado')
                                    )
    return routes_utils.return_response(res)