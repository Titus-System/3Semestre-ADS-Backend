from app.estatisticas import sh4_stats, tendencias_stats
from app.estatisticas.crescimento_mensal import crescimento_mensal_balanca, crescimento_mensal_vlfob
from app.estatisticas.estatisticas_auxiliares import gerar_estatisticas_auxiliares
from app.estatisticas.regressao_linear import calcular_regressao_linear
from app.estatisticas.volatilidade import volatilidade_balanca, volatilidade_vlfob
from data_pipeline.models.vidente import Vidente
from . import routes_utils
from flask import Blueprint, jsonify, request


tendencias_bp = Blueprint("tendencias", __name__)

vidente = Vidente()


@tendencias_bp.route('/crescimento_mensal_vlfob', methods=["GET"])
def crescimento_mensal():
    args: dict = routes_utils.get_args(request)

    if not isinstance(args, dict):
        return jsonify({'error': f'Erro na requisição: {args}'}), 400

    if 'tipo' not in args:
        return jsonify({'error': "Erro na requisição: Parâmetro 'tipo' é obrigatório."}), 400
    
    args["estados"] = (args.get("estado"), ) if args.get("estado") else None
    args["paises"] = (args.get("pais"), ) if args.get("pais") else None
    
    dados = crescimento_mensal_vlfob(tipo=args.get('tipo'), ncm=args.get('ncm'), estados=args.get('estados'), paises=args.get('paises'))
    return routes_utils.return_response(dados)


@tendencias_bp.route('/volatilidade_vlfob', methods=["GET"])
def volatilidade_vlfob_rota():
    args: dict = routes_utils.get_args(request)

    if not isinstance(args, dict):
        return jsonify({'error': f'Erro na requisição: {args}'}), 400

    if 'tipo' not in args:
        return jsonify({'error': "Erro na requisição: Parâmetro 'tipo' é obrigatório."}), 400

    args["estados"] = (args.get("estado"), ) if args.get("estado") else None
    args["paises"] = (args.get("pais"), ) if args.get("pais") else None
    dados = volatilidade_vlfob(tipo=args.get('tipo'), ncm=args.get('ncm'), estados=args.get('estados'), paises=args.get('paises'))

    return routes_utils.return_response(dados)


@tendencias_bp.route('/regressao_linear_vlfob', methods=["GET"])
def regressao_linear_vlfob():
    args: dict = routes_utils.get_args(request)

    if not isinstance(args, dict):
        return jsonify({'error': f'Erro na requisição: {args}'}), 400

    if 'tipo' not in args:
        return jsonify({'error': "Erro na requisição: Parâmetro 'tipo' é obrigatório."}), 400
    
    args["estados"] = (args.get("estado"), ) if args.get("estado") else None
    args["paises"] = (args.get("pais"), ) if args.get("pais") else None
        
    dados = calcular_regressao_linear(crit="valor_fob", tipo=args.get('tipo'), ncm=args.get('ncm'), estados=args.get('estados'), paises=args.get('paises'))
    return routes_utils.return_response(dados)


@tendencias_bp.route('/regressao_linear_balanca_comercial', methods=["GET"])
def regressao_linear_balanca_comercial():
    args: dict = routes_utils.get_args(request)

    if not isinstance(args, dict):
        return jsonify({'error': f'Erro na requisição: {args}'}), 400
    
    args["estados"] = (args.get("estado"), ) if args.get("estado") else None
    args["paises"] = (args.get("pais"), ) if args.get("pais") else None

    dados = calcular_regressao_linear(crit="balanca", ncm=args.get('ncm'), estados=args.get('estados'), paises=args.get('paises'))
    return routes_utils.return_response(dados)


@tendencias_bp.route('/crescimento_mensal_balanca_comercial', methods=["GET"])
def crescimento_mensal_balanca_comercial():
    args: dict = routes_utils.get_args(request)

    if not isinstance(args, dict):
        return jsonify({'error': f'Erro na requisição: {args}'}), 400
    
    args["estados"] = (args.get("estado"), ) if args.get("estado") else None
    args["paises"] = (args.get("pais"), ) if args.get("pais") else None
    
    dados = crescimento_mensal_balanca(ncm=args.get('ncm'), estados=args.get('estados'), paises=args.get('paises'))
    return routes_utils.return_response(dados)


@tendencias_bp.route('/volatilidade_balanca_comercial', methods=["GET"])
def volatilidade_balanca_comercial():
    args: dict = routes_utils.get_args(request)

    if not isinstance(args, dict):
        return jsonify({'error': f'Erro na requisição: {args}'}), 400
    
    args["estados"] = (args.get("estado"), ) if args.get("estado") else None
    args["paises"] = (args.get("pais"), ) if args.get("pais") else None
    dados = volatilidade_balanca(ncm=args.get('ncm'), estados=args.get('estados'), paises=args.get('paises'))
    return routes_utils.return_response(dados)


@tendencias_bp.route('/estatisticas_auxiliares_vlfob', methods=["GET"])
def estatisticas_auxiliares_vlfob():
    args: dict = routes_utils.get_args(request)
    if not isinstance(args, dict):
        return jsonify({'error': f'Erro na requisição: {args}'}), 400
    
    args["estados"] = (args.get("estado"), ) if args.get("estado") else None
    args["paises"] = (args.get("pais"), ) if args.get("pais") else None
    
    dados = gerar_estatisticas_auxiliares(ncm=args.get('ncm'), estados=args.get('estados'), paises=args.get('paises'))
    print(dados)
    return routes_utils.return_response(dados)


@tendencias_bp.route('/busca_tendencias_dashboard', methods=['GET'])
def busca_tendencia_sh4():
    args = routes_utils.get_args(request)
    if not isinstance(args, dict):
        return jsonify({'error': f'Erro na requisição: {args}'}), 400

    # if args.get('sh4'):
    #     args['sh4'] = str(args.get('sh4')[0])
    if args.get('ncm'):
        args['ncm'] = int(args.get('ncm')[0])

    if args.get('sh4'):
        tendencias = sh4_stats.tendencia_sh4(sh4=args.get('sh4'), estado=args.get('estado'), pais=args.get('pais'))
        print(args)
        # tendencias = sh4_dao.sh4_hist(**args)
    else:
        tendencias = tendencias_stats.tendencias_dashboard(ncm=args.get('ncm'), estado=args.get('estado'), pais=args.get('pais'))
    
    return routes_utils.return_response(tendencias)