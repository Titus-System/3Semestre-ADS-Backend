import time
from typing import List
from psycopg2 import Error
from app.dao.dao_utils import build_where
from app.database.database_connection import get_connection
from psycopg2.extras import DictCursor
from app.utils.logging_config import app_logger, error_logger
from app import cache

@cache.memoize(timeout=60*60*24)
def busca_balanca_comercial(
        anos: List[int] = None,
        meses: List[int] = None,
        paises: List[int] = None,
        estados: List[int] = None,
) -> List[dict]:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                where_statement = build_where(anos = anos, meses = meses, paises= paises, estados=estados)
                query = f"""
                    SELECT 
                        ano, {'mes,' if meses else ''}
                        SUM(balanca_comercial) as balanca_comercial, 
                        SUM(total_exportado) as total_exportado, 
                        SUM(total_importado) as total_importado 
                        FROM mv_balanca_comercial 
                        {where_statement}
                        GROUP BY ano {', mes' if meses else ''}
                        ORDER BY ano {', mes' if meses else ''}
                """
                inicio = time.time()
                cur.execute(query)
                fim = time.time()
                tempo = f"Tempo de execução: {fim-inicio :.4f} seg"
                res = cur.fetchall()
                app_logger.info(f"Busca de balança comercial realizada com sucesso. {tempo}")
                return [dict(row) for row in res]

    except Error as e:
        error_logger.error(f"erro ao acessar balança comercial, {e}")
        return None
