from app import cache
import time
from typing import List, Literal
from psycopg2 import Error, OperationalError
from psycopg2.extras import DictCursor

from .dao_utils import build_where
from ..database.database_connection import get_connection
from ..utils.logging_config import app_logger, error_logger

@cache.memoize(timeout=60*60*24)
def busca_top_estado(
    tipo: Literal['exp', 'imp'],
    qtd: int = 27,
    anos: List[int] = None,
    meses: List[int] | None = None,
    ncm: List[int] | None = None,
    paises: List[int] | None = None,
    vias: List[int] | None = None,
    urfs: List[int] | None = None,
    crit: Literal['kg_liquido', 'valor_fob', 'valor_agregado', 'registros'] = 'valor_fob',
    cresc: Literal[1, 0] = 0
) -> List[dict] | None:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                tabela_view = f"mv_{tipo}ortacao_estado_anual"
                where_conditions = []
                params = []

                if anos:
                    where_conditions.append("m.ano IN %s")
                    params.append(anos)

                if ncm:
                    where_conditions.append("m.id_produto IN %s")
                    params.append(ncm)

                if paises:
                    where_conditions.append("m.id_pais IN %s")
                    params.append(paises)

                if meses:
                    app_logger.warning("Filtro por meses ignorado - não disponível nas views materializadas")

                if vias or urfs:
                    app_logger.warning("Filtros por vias ou URFs ignorados - não disponíveis nas views materializadas")

                where_sql = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

                query = f"""
                    SELECT 
                        e.id_estado,
                        e.sigla AS sigla_estado,
                        e.nome AS nome_estado,
                        SUM(m.valor_fob_total) AS total_valor_fob,
                        SUM(m.kg_liquido_total) AS total_kg_liquido,
                        CASE 
                            WHEN SUM(m.kg_liquido_total) = 0 THEN 0
                            ELSE CAST(SUM(m.valor_fob_total) / SUM(m.kg_liquido_total) AS DECIMAL(15,2))
                        END AS total_valor_agregado,
                        SUM(m.quantidade_total) AS total_registros
                    FROM {tabela_view} m
                    JOIN estado e ON m.id_estado = e.id_estado
                    {where_sql}
                    GROUP BY e.id_estado, e.sigla, e.nome
                    ORDER BY total_{crit} {'ASC' if cresc else 'DESC'}
                    LIMIT %s
                """

                params.append(qtd)

                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
                
    except Error as e:
        error_logger.error(f"Erro ao buscar ranking dos estados: {str(e)}")
        return None


@cache.memoize(timeout=60*60*24)
def busca_estado_hist(
        tipo:Literal['exp', 'imp'],
        estados: tuple[int, ...],
        paises: tuple[int, ...] = None,
        anos: tuple[int, ...] | None = None,
        meses: tuple[int, ...] | None = None,
        vias: tuple[int, ...] | None = None,
        urfs: tuple[int, ...] | None = None,
        ncm: tuple[int, ...] | None = None,
) -> List[dict] | None:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                where_statement = build_where(anos=anos, meses=meses, paises=paises, estados=estados, vias=vias, urfs=urfs)
                where_statement = where_statement.replace('id_estado', 'estado.id_estado')
                if ncm:
                    where_statement += f" AND id_produto IN ({', '.join([str(n) for n in ncm])})"
                
                query = f"""
                    SELECT estado.id_estado, estado.nome as nome_estado, estado.sigla,
                        ano, mes,
                        SUM(kg_liquido) as kg_liquido_total,
                        SUM(valor_fob) as valor_fob_total,
                        CAST(SUM(valor_fob)/NULLIF(SUM(kg_liquido), 0) AS DECIMAL(15,2)) AS valor_agregado_total
                    FROM estado
                    LEFT JOIN {tipo}ortacao_estado t ON estado.id_estado = t.id_estado
                    {where_statement}
                    GROUP BY estado.id_estado, estado.nome, estado.sigla, ano, mes
                    ORDER BY ano, mes
                """
                inicio = time.time()
                cur.execute(query)
                results = [dict(row) for row in cur.fetchall()]
                fim = time.time()
                tempo = f"Tempo de execução: {fim - inicio:.4f} segundos"
                app_logger.info(f"Histórico dos estados {estados}. {tempo}")
                return results
    except (Error, OperationalError) as e:
        error_logger.error(f"Erro ao buscar o histórico de estados no banco de dados: {str(e)}")
        return None


def pesquisa_estado_por_nome(nome: str) -> List[dict] | None:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query = """
                    SELECT id_estado, sigla, nome FROM estado
                    WHERE unaccent(nome) ILIKE unaccent(%s)
                    ORDER BY 
                        CASE 
                            WHEN nome ILIKE %s THEN 0
                            ELSE 1
                        END,
                        unaccent(nome)
                """
                cur.execute(query, (f"%{nome}%", f"{nome}%"))
                return [dict(row) for row in cur.fetchall()]
    except Error as e:
        error_logger.error(f"Erro ao pesquisar estados por nome: {str(e)}")
        return None


def busca_todos_estados():
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT id_estado, sigla, nome FROM estado ORDER BY nome ASC")
                return [dict(row) for row in cur.fetchall()]
    except Error as e:
        error_logger.error("Erro ao buscar todos os estados.")
        return None


def busca_estado_sigla(id:int) -> str:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(f"SELECT sigla FROM estado WHERE id_estado = {id}")
                res = cur.fetchone()[0]
                print("res: ", res)
                return res
    except Error as e:
        error_logger.error("Erro ao buscar todos os estados.")
        return None