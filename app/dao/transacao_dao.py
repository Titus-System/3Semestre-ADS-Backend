from app import cache
from typing import List, Literal
from psycopg2 import Error, OperationalError
from psycopg2.extras import DictCursor

from app.dao.dao_utils import build_where
from app.database.database_connection import get_connection
from app.utils.logging_config import app_logger, error_logger

def busca_transacoes_por_ncm(
        ncm: int,
        tipo: Literal['imp', 'exp'],
        qtd: int = 25,
        paises: List[int] = None,
        estados: List[int] = None,
        anos : List[int] = None,
        meses: List[int] = None,
        vias: List[int] = None,
        urfs: List[int] = None,
        peso: int = None
) -> List[dict]:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                where_statement = build_where(paises=paises, estados=estados, anos=anos, meses=meses, urfs=urfs, vias=vias)
                if peso:
                    if where_statement.startswith('WHERE'):
                        where_statement += f"AND kg_liquido > {peso}"
                    else:
                        where_statement = f"WHERE kg_liquido > {peso}"

                query = f"""
                    SELECT id_transacao, ano, id_pais, valor_fob, kg_liquido, valor_agregado 
                    FROM {tipo}ortacao_estado
                    {where_statement}
                    LIMIT %s
                """
                cur.execute(query, (qtd, ))
                res = cur.fetchall()
                app_logger.info(f"Transações buscadas para o ncm: {ncm}")
                return [dict(row) for row in res]
    except (Error, OperationalError) as e:
        error_logger.error(f'Erro ao buscar NCM {ncm} no banco de dados: {str(e)}')
        return None


def busca_transacao_por_id(id_transacao:int, tipo:Literal['imp', 'exp']):
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query = f"""
                    SELECT * 
                    FROM {tipo}ortacao_estado
                    WHERE id_transacao = %s
                """
                cur.execute(query, (id_transacao, ))
                res = cur.fetchall()
                app_logger.info(f"Transação buscada para o id: {id_transacao}")
                return [dict(row) for row in res]
    except (Error, OperationalError) as e:
        error_logger.error(f'Erro ao buscar transação de id {id_transacao} no banco de dados: {str(e)}')
        return None


@cache.memoize(timeout=60*60*24)
def info_geral(
    tipo: Literal['imp', 'exp'],
    ncm: int = None,
    paises: List[int] = None,
    estados: List[int] = None,
    anos : List[int] = None,
    vias: List[int] = None,
    urfs: List[int] = None,
):
    where_statement = build_where(anos=anos, paises=paises, estados=estados, vias=vias, urfs=urfs, ncm=ncm)
    if ncm: where_statement = where_statement.replace('produto.id_ncm', 'id_produto')
    select_statement = "SUM(valor_fob) as total_valor_fob, SUM(kg_liquido) as total_kg_liquido"
    if tipo == 'imp':
        select_statement += ", SUM(valor_seguro) as total_valor_seguro, SUM(valor_frete) as total_valor_frete"
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query = f"""
                    SELECT {select_statement}
                    FROM {tipo}ortacao_estado
                    {where_statement}
                """
                cur.execute(query)
                res = cur.fetchall()
                app_logger.info(f"Informações gerais buscadas com sucesso")
                return [dict(row) for row in res]
    except (Error, OperationalError) as e:
        error_logger.error(f"Erro ao buscar informações gerais no banco de dados")
        return None


def build_query_hhi(
    tipo: Literal['exp', 'imp'],
    crit: Literal['pais', 'estado', 'ncm'],
    ncm: int | None = None,
    estado: int | None = None,
    pais: int | None = None
) -> str:
    tabela = f"{tipo}ortacao_estado"
    
    condicoes = []

    if crit == 'pais':
        select_group = "id_pais"
        if ncm is not None:
            condicoes.append(f"id_produto = {ncm}")
        if estado is not None:
            condicoes.append(f"id_estado = {estado}")

    elif crit == 'estado':
        select_group = "id_estado"
        if ncm is not None:
            condicoes.append(f"id_produto = {ncm}")
        if pais is not None:
            condicoes.append(f"id_pais = {pais}")

    elif crit == 'ncm':
        select_group = "id_produto"
        if estado is not None:
            condicoes.append(f"id_estado = {estado}")
        if pais is not None:
            condicoes.append(f"id_pais = {pais}")

    where_clause = ""
    if condicoes:
        where_clause = "WHERE " + " AND ".join(condicoes)

    query = f"""
        SELECT ano, mes, {select_group}, 
               SUM(valor_fob) as VL_FOB_{tipo.upper()}
        FROM {tabela}
        {where_clause}
        GROUP BY ano, mes, {select_group}
    """
    print(query)
    return query


@cache.memoize(timeout=60*60*24)
def busca_dados_para_analise_hhi(tipo:Literal['exp','imp'], crit:Literal['pais', 'estado', 'ncm'], ncm:int, estado:int|None=None, pais:int|None=None) -> List[dict]:    
    print("iniciando busca no banco de dados para dados de hhi")
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query = build_query_hhi(tipo, crit, ncm, estado, pais)
                cur.execute(query)
                res = cur.fetchall()
                print("busca por dados de hhi no banco de dados encerrada")
                r = [dict(row) for row in res]
                return r
    except (Error, OperationalError) as e:
        error_logger.error(f'Erro ao buscar agregado para hhi no banco de dados: {str(e)}')
        return None


@cache.memoize(timeout=60*60*24)
def busca_hist(tipo:Literal['exp','imp'], estado:int|None=None, pais:int|None=None) -> List[dict]:
    try:
        where_statement = ""
        condicoes = []
        if estado:
            condicoes.append(f"id_estado = {estado}")
        if pais:
            condicoes.append(f"id_pais = {pais}")
        if condicoes:
            where_statement = "WHERE " + " AND ".join(condicoes)

        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query = f"""
                    SELECT ano, mes,
                        SUM(total_{tipo}ortado) as total_valor_fob
                    FROM mv_balanca_comercial
                    {where_statement}
                    GROUP BY ano, mes
                """
                cur.execute(query)
                res = cur.fetchall()
                return [dict(row) for row in res]
    except (Error, OperationalError) as e:
        error_logger.error(f'busca_hist: Erro ao buscar histórico sem ncm no banco de dados: {str(e)}')
        return None
    

@cache.memoize(timeout=60*60*24)
def hist_geral(
    tipo: Literal['imp', 'exp'],
    ncm: int = None,
    paises: List[int] = None,
    estados: List[int] = None,
    anos : List[int] = None,
    vias: List[int] = None,
    urfs: List[int] = None,
):
    where_statement = build_where(anos=anos, paises=paises, estados=estados, vias=vias, urfs=urfs, ncm=ncm)
    if ncm: where_statement = where_statement.replace('produto.id_ncm', 'id_produto')
    select_statement = "SUM(valor_fob) as total_valor_fob, SUM(kg_liquido) as total_kg_liquido"
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query = f"""
                    SELECT ano, mes, {select_statement}
                    FROM {tipo}ortacao_estado
                    {where_statement}
                    GROUP BY ano, mes
                """
                cur.execute(query)
                res = cur.fetchall()
                app_logger.info(f"Informações gerais buscadas com sucesso")
                return [dict(row) for row in res]
    except (Error, OperationalError) as e:
        error_logger.error(f"Erro ao buscar informações gerais no banco de dados")
        return None