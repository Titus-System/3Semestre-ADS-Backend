from app import cache
import time
from typing import List, Literal
from psycopg2 import Error
from psycopg2.extras import DictCursor

from .dao_utils import build_where

from ..database.database_connection import get_connection
from ..utils.logging_config import app_logger, error_logger


@cache.memoize(timeout=60*60*24)
def busca_top_pais(
        tipo: Literal['exp', 'imp'],
        qtd: int = 10, 
        anos: tuple[int, ...] | None = None, 
        meses: tuple[int, ...] | None = None,
        ncm: tuple[int, ...] | None = None,
        estados: tuple[int, ...] | None = None,
        vias: tuple[int, ...] | None = None,
        urfs: tuple[int, ...] | None = None,
        crit: Literal['kg_liquido', 'valor_fob', 'valor_agregado', 'registros'] = 'valor_fob',
        cresc: Literal[1, 0] = 0
) -> List[dict] | None:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                where_statement = build_where(anos=anos, estados=estados, meses=meses, vias=vias, urfs=urfs)
                if ncm:
                    if where_statement.startswith('WHERE'):
                        where_statement += f" AND id_produto IN ({', '.join([str(n) for n in ncm])})"
                    else:
                        where_statement = f"WHERE id_produto IN ({', '.join([str(n) for n in ncm])})"

                # Se não houver filtro por mês, usar a view materializada
                if not meses and not vias and not urfs:
                    
                    query = f"""
                        SELECT pais.id_pais,
                            pais.nome AS nome_pais,
                            {f"SUM(mv_{tipo}ortacao_estado_anual.quantidade_total) AS total_registros, " if crit == 'registros' else ''}
                            SUM(mv_{tipo}ortacao_estado_anual.valor_fob_total) as total_valor_fob,
                            SUM(mv_{tipo}ortacao_estado_anual.kg_liquido_total) as total_kg_liquido,
                            CAST(SUM(mv_{tipo}ortacao_estado_anual.valor_fob_total)/NULLIF(SUM(mv_{tipo}ortacao_estado_anual.kg_liquido_total), 0) AS DECIMAL(15,2)) AS total_valor_agregado
                        FROM pais
                        JOIN mv_{tipo}ortacao_estado_anual ON mv_{tipo}ortacao_estado_anual.id_pais = pais.id_pais
                        {where_statement}
                        GROUP BY pais.id_pais, pais.nome
                        ORDER BY total_{crit} {'ASC' if cresc else 'DESC'}
                        LIMIT %s
                    """
                else:
                    # Usar a tabela original se houver filtro por mês
                    query = f"""
                        SELECT pais.id_pais,
                            pais.nome AS nome_pais,
                            SUM(valor_fob) as total_valor_fob,
                            SUM(kg_liquido) as total_kg_liquido,
                            CAST(SUM(valor_fob)/NULLIF(SUM(kg_liquido), 0) AS DECIMAL(15,2)) AS total_valor_agregado,
                            COUNT(*) AS total_registros
                        FROM {tipo}ortacao_estado 
                        JOIN pais ON {tipo}ortacao_estado.id_pais = pais.id_pais
                        {where_statement}
                        GROUP BY pais.id_pais, pais.nome
                        ORDER BY total_{crit} {'ASC' if cresc else 'DESC'}
                        LIMIT %s
                    """
                inicio = time.time()
                cur.execute(query, (qtd,))
                results = [dict(row) for row in cur.fetchall()]
                fim = time.time()
                tempo = f"Tempo de execução: {fim - inicio:.4f} segundos"
                app_logger.info(f"Ranking de países que mais {tipo}ortam. {tempo}")
                return results
    except Error as e:
        error_logger.error(f'Erro ao buscar top NCM no banco de dados: {str(e)}')
        return None


@cache.memoize(timeout=60*60*24)
def busca_pais_exp_imp_info(
        paises: tuple[int, ...],
        qtd: int = 10, 
        anos: tuple[int, ...] = None, 
        meses: tuple[int, ...] | None = None,
        ncm: tuple[int, ...] | None = None,
        estados: tuple[int, ...] | None = None,
        vias: tuple[int, ...] | None = None,
        urfs: tuple[int, ...] | None = None
) -> List[dict] | None:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                where_statement = build_where(paises=paises, anos=anos, estados=estados, meses=meses, vias=vias, urfs=urfs)
                where_statement = where_statement.replace('id_pais', "pais.id_pais")
                where_statement = where_statement.replace('ano', "mv_exportacao_estado_anual.ano")
                
                if ncm:
                    if where_statement.startswith('WHERE'):
                        where_statement += f" AND id_produto IN ({', '.join([str(n) for n in ncm])})"
                    else:
                        where_statement = f"WHERE id_produto IN ({', '.join([str(n) for n in ncm])})"

                # Se não houver filtro por mês, usar a view materializada
                if not meses and not vias and not urfs:
                    
                    query = f"""
                        SELECT pais.id_pais,
                            pais.nome AS nome_pais,
                            SUM(mv_exportacao_estado_anual.quantidade_total) AS total_registros_exp,
                            SUM(mv_exportacao_estado_anual.valor_fob_total) as total_valor_fob_exp,
                            SUM(mv_exportacao_estado_anual.kg_liquido_total) as total_kg_liquido_exp,
                            CAST(SUM(mv_exportacao_estado_anual.valor_fob_total)/NULLIF(SUM(mv_exportacao_estado_anual.kg_liquido_total), 0) AS DECIMAL(15,2)) AS total_valor_agregado_exp,
                            
                            SUM(mv_importacao_estado_anual.quantidade_total) AS total_registros_imp,
                            SUM(mv_importacao_estado_anual.valor_fob_total) as total_valor_fob_imp,
                            SUM(mv_importacao_estado_anual.kg_liquido_total) as total_kg_liquido_imp,
                            CAST(SUM(mv_importacao_estado_anual.valor_fob_total)/NULLIF(SUM(mv_importacao_estado_anual.kg_liquido_total), 0) AS DECIMAL(15,2)) AS total_valor_agregado_imp
                        FROM pais
                        LEFT JOIN mv_exportacao_estado_anual ON mv_exportacao_estado_anual.id_pais = pais.id_pais
                        LEFT JOIN mv_importacao_estado_anual ON mv_importacao_estado_anual.id_pais = pais.id_pais
                        {where_statement}
                        GROUP BY pais.id_pais, pais.nome
                    """
                else:
                    # Usar a tabela original se houver filtro por mês
                    query = f"""
                        SELECT
                            p.id_pais,
                            p.nome AS nome_pais,

                            SUM(e.valor_fob) AS total_valor_fob_exp,
                            SUM(e.kg_liquido) AS total_kg_liquido_exp,
                            CAST(SUM(e.valor_fob)/NULLIF(SUM(e.kg_liquido), 0) AS DECIMAL(15,2)) AS total_valor_agregado_exp,
                            COUNT(e.id_exportacao) AS total_registros_exp,

                            SUM(i.valor_fob) AS total_valor_fob_imp,
                            SUM(i.kg_liquido) AS total_kg_liquido_imp,
                            CAST(SUM(i.valor_fob)/NULLIF(SUM(i.kg_liquido), 0) AS DECIMAL(15,2)) AS total_valor_agregado_imp,
                            COUNT(i.id_importacao) AS total_registros_imp

                        FROM pais p
                        LEFT JOIN exportacao_estado e ON e.id_pais = p.id_pais
                        LEFT JOIN importacao_estado i ON i.id_pais = p.id_pais
                        {where_statement}
                        GROUP BY p.id_pais, p.nome;
                    """
                inicio = time.time()
                cur.execute(query, (qtd,))
                results = [dict(row) for row in cur.fetchall()]
                fim = time.time()
                tempo = f"Tempo de execução: {fim - inicio:.4f} segundos"
                app_logger.info(f"Informações dos paises {paises} foram acessadas. {tempo}")
                return results
    except Error as e:
        error_logger.error(f'Erro ao buscar top NCM no banco de dados: {str(e)}')
        return None


@cache.memoize(timeout=60*60*24)
def busca_pais_hist(
        tipo:Literal['exp', 'imp'],
        paises: tuple[int, ...],
        anos: tuple[int, ...] | None = None,
        meses: tuple[int, ...] | None = None,
        estados: tuple[int, ...] | None = None,
        vias: tuple[int, ...] | None = None,
        urfs: tuple[int, ...] | None = None,
        ncm: tuple[int, ...] | None = None,
) -> List[dict] | None:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:

                where_statement = build_where(anos=anos, meses=meses, paises=paises, estados=estados, vias=vias, urfs=urfs)
                where_statement = where_statement.replace('id_pais', 'pais.id_pais')
                if ncm:
                    where_statement += f" AND id_produto IN ({', '.join([str(n) for n in ncm])})"

                query = f"""
                    SELECT pais.id_pais, pais.nome AS nome_pais,
                        ano, {'mes, ' if meses else ''}
                        SUM(kg_liquido) as kg_liquido_total,
                        SUM(valor_fob) as valor_fob_total,
                        CAST(SUM(valor_fob)/NULLIF(SUM(kg_liquido), 0) AS DECIMAL(15,2)) AS valor_agregado_total,
                        COUNT(*) AS total_registros
                    FROM pais
                    LEFT JOIN bloco ON pais.id_bloco = bloco.id_bloco
                    LEFT JOIN {tipo}ortacao_estado ON pais.id_pais = {tipo}ortacao_estado.id_pais
                    {where_statement}
                    GROUP BY pais.id_pais, ano {', mes' if meses else ''}
                    ORDER BY ano {', mes' if meses else ''}
                """

                inicio = time.time()
                cur.execute(query)
                results = [dict(row) for row in cur.fetchall()]
                fim = time.time()
                tempo = f"Tempo de execução: {fim - inicio:.4f} segundos"
                app_logger.info(f"Histórico dos países {paises}. {tempo}")
                return results
    except Error as e:
        error_logger.error(f"Erro ao buscar o histórico de países no banco de dados: {str(e)}")
        return None


def pesquisa_pais_por_nome(nome:str) -> List[dict] | None:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query = """
                    SELECT id_pais, nome FROM pais
                    WHERE unaccent(nome) ILIKE unaccent(%s)
                    ORDER BY 
                        CASE 
                            WHEN nome ILIKE %s THEN 0
                            ELSE 1
                        END,
                        unaccent(nome) ASC
                """
                cur.execute(query, (f"%{nome}%", f"{nome}%"))
                
                results = [dict(row) for row in cur.fetchall()]
                app_logger.info(f"pesquisa por paises com '{nome}' realizada.")
                return results
    except Error as e:
        error_logger.error(f"Erro ao pesquisar países por nome no banco de dados: {str(e)}")
        return None


def busca_todos_paises():
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT id_pais, nome FROM pais ORDER BY nome ASC")
                results = [dict(row) for row in cur.fetchall()]
                app_logger.info("Todos os países buscados com sucesso.")
                return results
    except Error as e:
        error_logger.error("Erro ao buscar todos os países.")
        return None