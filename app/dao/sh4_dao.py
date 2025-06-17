from app import cache
import json
import time
from typing import List, Literal
from psycopg2 import Error, OperationalError
from psycopg2.extras import DictCursor
from app.dao.dao_utils import build_where
from app.database.database_connection import get_connection
from app.utils.logging_config import app_logger, error_logger


with open('data_pipeline/tabelas_auxiliares/setores.json', 'r', encoding='utf-8') as f:
    setores: dict = json.load(f)


def busca_todos_sh4() -> List[dict] | None:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor)as cur:
                cur.execute("SELECT sh4.id_sh4, sh4.descricao FROM sh4 ORDER BY id_sh4")
                return [dict(row) for row in cur.fetchall()]
    except Error as e:
        error_logger.error(f'Erro ao buscar todos sh4 no banco de dados: {str(e)}')
        return None    

def pesquisa_sh4_por_nome(nome:str) -> List[dict] | None:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query = """
                    SELECT id_sh4, descricao
                    FROM sh4
                    WHERE unaccent(descricao) ILIKE unaccent (%s)
                    ORDER BY
                        CASE
                            WHEN unaccent(descricao) ILIKE unaccent(%s) THEN 0
                            ELSE 1
                        END,
                        unaccent(descricao) ASC
                """
                cur.execute(query, (f"%{nome}%", f"{nome}%"))
                response = [dict(row) for row in cur.fetchall()]
                app_logger.info(f"Pesquisa sh4 por nome '{nome}' executada.")
                return response
    except Error as e:
        error_logger.error(f"Erro ao pesquisar sh4 pelo nome '{nome}': {str(e)}")
        return None
    

@cache.memoize(timeout=60*60*24)
def busca_vlfob_sh4(
        sh4: tuple[str, ...],
        anos: tuple[int, ...] | None = None,
        estados: tuple[int, ...] | None = None
)-> List[dict] | None:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                where_statement = build_where(anos=anos, estados=estados)
                sh4_str = ', '.join([f"'{s}'" for s in sh4])
                if where_statement.startswith("WHERE"):
                    where_statement += f"AND id_sh4 IN ({sh4_str})"
                else:
                    where_statement = f"WHERE id_sh4 IN ({sh4_str})"

                query = f"""
                    SELECT 
                        COALESCE(SUM(valor_fob_exp), 0) AS total_valor_fob_exp,
                        COALESCE(SUM(valor_fob_imp), 0) AS total_valor_fob_imp
                    FROM mv_vlfob_setores
                    {where_statement}
                """
                inicio = time.time()
                cur.execute(query)
                res = cur.fetchone()
                fim = time.time()
                tempo = f"Tempo de execução: {fim-inicio :.4f} seg"
                app_logger.info(f"Busca de vl_fob por sh4 {sh4} realizada com sucesso. {tempo}")
                return [dict(res)]
    except (Error, OperationalError) as e:
        error_logger.error(f"Erro ao buscar valores por sh4 {sh4}. Erro: {str(e)}")
        return None
    

@cache.memoize(timeout=60*60*24)
def busca_sh4_info(sh4:str):
    try: 
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query = "SELECT id_sh4, descricao FROM sh4 WHERE id_sh4 = %s"
                cur.execute(query, (sh4,))
                info = dict(cur.fetchone())
                query = "SELECT p.id_ncm FROM produto p JOIN sh4 ON p.id_sh4 = sh4.id_sh4 WHERE p.id_sh4 = %s"
                cur.execute(query, (sh4,))
                ncms = [item[0] for item in cur.fetchall()]
                info['ncm'] = ncms
                print(info)
                return info
    except (Error, OperationalError) as e:
        error_logger.error(f"Erro ao buscar informações do sh4 {sh4}. Erro: {str(e)}")
        return None


@cache.memoize(timeout=60*60*24)
def ranking_sh4(
    tipo:str, 
    qtd:int=10, 
    anos:List[int]=None, 
    estados:List[int]=None, 
    paises:List[int] = None,
    crit: Literal['valor_fob', 'kg_liquido', 'valor_agregado'] = 'valor_fob',
    cresc: Literal[1, 0] = 0
) -> List[dict]:
    where_statement = build_where(anos=anos, estados=estados, paises=paises)
    query = f"""
        SELECT s.id_sh4, s.descricao as sh4_descricao,
            SUM(e.valor_fob) as total_valor_fob,
            SUM(e.kg_liquido) as total_kg_liquido,
            CAST(SUM(e.valor_fob)/NULLIF(SUM(e.kg_liquido), 0) AS DECIMAL(15,2)) AS total_valor_agregado
        FROM {tipo}ortacao_estado e 
        JOIN produto p ON e.id_produto = p.id_ncm
        JOIN sh4 s ON s.id_sh4 = p.id_sh4
        {where_statement}
        GROUP BY s.id_sh4, s.descricao
        ORDER BY total_{crit} {'ASC' if cresc else 'DESC'}
        LIMIT %s
    """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                inicio = time.time()
                cur.execute(query, (qtd,))
                results = [dict(row) for row in cur.fetchall()]
                fim = time.time()
                tempo = f"Tempo de execução: {fim - inicio:.4f} segundos"
                app_logger.info(f"Ranking de sh4 que foram mais {tipo}ortados. {tempo}")
                return results
    except (Error, OperationalError) as e:
        error_logger.error(f"erro ao buscar ranking de sh4")
        return


@cache.memoize(timeout=60*60*24)
def sh4_hist(
    tipo: Literal['exp', 'imp'], 
    sh4: List[str], 
    paises: List[int] | None = None,
    estados: List[int] | None = None
) -> List[dict]:
    # sh4 = [str(s).zfill(4) for s in sh4]
    filtro = f"""sh4.id_sh4 IN ({", ".join(f"'{s}'" for s in sh4)})"""
    
    where_statement = build_where(paises=paises, estados=estados)
    if where_statement: 
        where_statement += f" AND {filtro}"
    else:
        where_statement = f"WHERE {filtro}"

    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query = f"""
                    SELECT sh4.id_sh4, sh4.descricao,
                        ano, mes,
                        SUM(valor_fob) as total_valor_fob,
                        SUM(kg_liquido) as total_kg_liquido,
                        CAST(SUM(valor_fob)/NULLIF(SUM(kg_liquido), 0) AS DECIMAL(15,2)) AS total_valor_agregado
                    FROM produto
                    LEFT JOIN {tipo}ortacao_estado ON {tipo}ortacao_estado.id_produto = produto.id_ncm
                    LEFT JOIN sh4 ON sh4.id_sh4 = produto.id_sh4
                    {where_statement}
                    GROUP BY ano, mes, sh4.id_sh4, sh4.descricao
                """
                print(query)
                inicio = time.time()
                cur.execute(query)
                # results = [dict(row) for row in cur.fetchall()]
                results = [dict(row) for row in cur.fetchall() if row['ano'] is not None and row['mes'] is not None]
                fim = time.time()

                app_logger.info(f"Busca de histórico por sh4 {sh4} concluída com sucesso. Tempo: {fim - inicio:.4f} segundos")
                return results
    except Error as e:
        error_logger.error(f'Erro ao buscar histórico para sh4 {sh4} no banco de dados: {str(e)}')
        return None


@cache.memoize(timeout=60*60*24)
def busca_info_setor(setor: str, tipo:str, anos:tuple[int,...]|None, pais:int|None, estado:int|None):
    global setores    
    sh4_list = tuple(setores.get(setor, {}).get('sh4', []))
    sh4_values = ', '.join(f"'{codigo}'" for codigo in sh4_list)

    where_statement = f"""
        WHERE id_sh4 IN ({sh4_values}) {f"AND id_pais = {pais}" if pais else ""} {f"AND id_estado = {estado}" if estado else ""}
    """
    if anos:
        anos_sql = ', '.join(str(ano) for ano in anos)
        where_statement += f" AND ano IN ({anos_sql})"
    query = f"""
        SELECT 
            SUM(valor_fob) as valor_fob_{tipo},
            SUM(kg_liquido) as kg_liquido_{tipo},
            CAST(SUM(valor_fob)/NULLIF(SUM(kg_liquido), 0) AS DECIMAL(15,2)) AS valor_agregado_{tipo}
        FROM {tipo}ortacao_estado e
        JOIN produto p ON p.id_ncm = e.id_produto
        {where_statement}
        """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                    inicio = time.time()
                    cur.execute(query)
                    results = cur.fetchone()
                    fim = time.time()
                    app_logger.info(f"Busca de dados por setor {setor} concluída com sucesso. Tempo: {fim - inicio:.4f} segundos")
                    return results
    except (Error, OperationalError) as e:
        error_logger.error(f"Erro ao buscar informações para o setor {setor} no banco de dados")
        return 


@cache.memoize(timeout=60*60*24)
def busca_info_setores(anos:tuple[int,...]|None, pais:int|None, estado:int|None):
    global setores
    resposta = []
    for setor in setores.keys():
        info_exp = busca_info_setor(setor, 'exp', anos, pais, estado)
        info_imp = busca_info_setor(setor, 'imp', anos, pais, estado)
        resposta.append({
            "setor": setor,
            "valor_fob_exp" : info_exp.get('valor_fob_exp') if info_exp else 0,
            "valor_fob_imp" : info_imp.get('valor_fob_imp') if info_imp else 0,
            "valor_agregado_exp" : info_exp.get("valor_agregado_exp") if info_exp else 0,
            "valor_agregado_imp" : info_imp.get("valor_agregado_imp") if info_imp else 0,
        })
    return resposta
