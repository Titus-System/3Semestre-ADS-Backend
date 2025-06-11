from app.database.database_connection import get_connection
from app.utils.logging_config import app_logger, error_logger
from psycopg2 import Error, OperationalError
from psycopg2.extras import DictCursor


def busca_urf_por_nome(nome:str):
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query = """
                    SELECT id_unidade as id_urf, nome
                    FROM unidade_receita_federal
                    WHERE unaccent(nome) ILIKE unaccent (%s)
                    ORDER BY
                        CASE
                            WHEN unaccent(nome) ILIKE unaccent(%s) THEN 0
                            ELSE 1
                        END,
                        unaccent(nome) ASC
                """
                cur.execute(query, (f"%{nome}%", f"{nome}%"))
                response = [dict(row) for row in cur.fetchall()]
                app_logger.info(f"Pesquisa urf por nome '{nome}' executada.")
                return response
    except (Error, OperationalError) as e:
        error_logger.error(f"Erro ao pesquisar urf pelo nome '{nome}': {str(e)}")
        return None
    

def busca_todos_urf():
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT id_unidade as id_urf, nome FROM unidade_receita_federal ORDER BY id_urf")
                return [dict(row) for row in cur.fetchall()]
    except Error as e:
        error_logger.error(f"Erro ao buscar todas urf no banco de dados: {str(e)}")
        return None