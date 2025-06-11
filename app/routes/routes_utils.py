from typing import List
from flask import Request, Response, json, jsonify


def get_args(request: Request) -> dict | list:
    errors = []
    args= {}

    params = {
        "tipo": str,
        "qtd": int,
        "anos": [int],
        "meses": [int],
        "paises": [int],
        "crit": str,
        "cresc": int,

        "municipios": [int],
        "estados": [int],
        "vias": [int],
        "urfs": [int],

        "estado": int,
        "estado_sigla":str,
        "pais": int,

        "ncm": [int],
        "sh4": [str],
        "peso": int
    }

    for param, tipo in params.items():
        if isinstance(tipo, list):
            value = request.args.getlist(param, type=tipo[0])
            value = tuple(value) if value else None
        else:
            value = request.args.get(param, type=tipo)
        
        if value:
            args[param] = value

    if (tipo:= args.get('tipo')) and tipo not in ['exp', 'imp']:
        errors.append("Tipo de transação deve ser 'exp' ou 'imp'.")

    if (qtd:= args.get('qtd')) is not None and qtd <= 0:
        errors.append('Quantidade informada deve ser um número inteiro positivo.')

    for ano in args.get('anos', ()):
        if isinstance(ano, int) and ano not in range(2014, 2026):
            errors.append(f'Ano inválido: {ano}. Utilize um ano entre 2014 e 2025.')
            break
    
    criterios_validos = {'kg_liquido', 'valor_fob', 'valor_agregado', 'registros'}
    if (crit:=args.get('crit')) and crit not in criterios_validos:
        errors.append(f"Critério de ordenação inválido. Utilize um dos critérios válidos: {', '.join(criterios_validos)}.")

    if (cresc:=args.get('cresc')) and cresc not in (1, 0):
        errors.append(f"Critério 'cresc' deve ser 1 ou 0.")
    
    if (peso:=args.get('peso')) and peso <= 0:
        errors.append("Peso especificado deve ser maior que 0.")


    if errors: return errors

    return args



def return_response(data: List | List[dict]) -> Response:
    if data is not None:
        response = Response(
            json.dumps({'status':200,'resposta': data}, ensure_ascii=False),
            content_type = 'application/json; charset=utf-8',
            status = 200
        )
        return response
    
    return jsonify({'error': 'Ocorreu um erro inesperado. Por favor tente novamente mais tarde.'}), 500