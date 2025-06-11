from typing import Literal
from psycopg2.extensions import connection
from psycopg2 import Error, connect
import pandas as pd

from data_pipeline.models.tabelasComexStat import TabelasComexStat
from app.utils.logging_config import app_logger, error_logger


class BuildDatabase:
    def __init__(self, config:dict):
        try:
            self.conn:connection = connect(**config)
            self.tabelas = TabelasComexStat()
        except Error as e:
            error_logger.error("Erro ao conectar ao banco de dados: %s", str(e))
            self.conn = None


    def close_connection(self):
        if self.conn: self.conn.close()


    def registra_paises(self) -> None:
        pais_df = pd.read_csv(self.tabelas.auxiliar('PAIS'), delimiter=';' ,encoding='latin1')

        try:
            cur = self.conn.cursor()
            for _, row in pais_df.iterrows():
                id_pais = row['CO_PAIS']
                nome = row['NO_PAIS']
                cur.execute(
                    "INSERT INTO pais (id_pais, nome) VALUES (%s, %s) ON CONFLICT (id_pais) DO NOTHING",
                    (id_pais, nome)
                )
            self.conn.commit()
            cur.close()
            app_logger.info("Paises cadastrados no banco de dados com sucesso")
        except Error as e:
            self.conn.rollback()
            error_logger.error("Erro ao cadastrar paises no banco de dados: %s", str(e))

    
    def registra_blocos(self) -> None:
        bloco_df = pd.read_csv(self.tabelas.auxiliar('PAIS_BLOCO'), delimiter=';', encoding='latin1')
        blocos = bloco_df.drop_duplicates(subset=["CO_BLOCO"])
        try:
            cur = self.conn.cursor()
            for _, row in blocos.iterrows():
                id_bloco = row["CO_BLOCO"]
                nome_bloco = row["NO_BLOCO"]
                cur.execute(
                    "INSERT INTO bloco (id_bloco, nome_bloco) VALUES (%s, %s) ON CONFLICT (id_bloco) DO NOTHING", 
                    (id_bloco, nome_bloco)
                )
            for _, row in bloco_df.iterrows():
                id_pais = row['CO_PAIS']
                id_bloco = row['CO_BLOCO']
                cur.execute(
                    "UPDATE pais SET id_bloco = %s WHERE id_pais = %s",
                    (id_bloco, id_pais)
                )
            self.conn.commit()
            cur.close()
            app_logger.info("Blocos cadastrados no banco de dados com sucesso")
        except Error as e:
            self.conn.rollback()
            error_logger.error("Erro ao cadastrar blocos no banco de dados: %s", str(e))

    
    def registra_estados(self) -> None:
        estados_df = pd.read_csv(self.tabelas.auxiliar('UF'), delimiter=';', encoding='latin1')
        try:
            cur = self.conn.cursor()
            for _, row in estados_df.iterrows():
                id_estado = row['CO_UF']
                sigla = row['SG_UF']
                nome=row['NO_UF']
                regiao = row['NO_REGIAO']
                cur.execute(
                    "INSERT INTO estado (id_estado, sigla, nome, regiao) VALUES (%s, %s, %s, %s) ON CONFLICT (id_estado) DO NOTHING",
                    (id_estado, sigla, nome, regiao)
                )
            self.conn.commit()
            cur.close()
            app_logger.info("Estados cadastrados no banco de dados com sucesso")
        except Error as e:
            self.conn.rollback()
            error_logger.error("Erro ao cadastrar estados no banco de dados: %s", str(e))


    def registra_municipios(self) -> None:
        mun_df = pd.read_csv(self.tabelas.auxiliar('UF_MUN'), delimiter=';', encoding='latin1')
        estados_df = pd.read_csv(self.tabelas.auxiliar('UF'), delimiter=';', encoding='latin1')
        mun_df = mun_df.merge(estados_df, on="SG_UF", how="left")
        try:
            cur = self.conn.cursor()
            for _, row in mun_df.iterrows():
                id_municipio = row['CO_MUN_GEO']
                nome = row['NO_MUN_MIN']
                id_estado = row['CO_UF']
                cur.execute(
                    "INSERT INTO municipio (id_municipio, nome, id_estado) VALUES (%s, %s, %s) ON CONFLICT (id_municipio) DO NOTHING",
                    (id_municipio, nome, id_estado)
                )
            self.conn.commit()
            app_logger.info("Municípios cadastrados no banco de dados com sucesso")
        except Error as e:
            self.conn.rollback()
            error_logger.error("Erro ao cadastrar municipios no banco de dados: %s", str(e))


    def registra_modal_transporte(self) -> None:
        via_df = pd.read_csv(self.tabelas.auxiliar('VIA'), delimiter=';', encoding='latin1')
        try:
            cur = self.conn.cursor()
            for _, row in via_df.iterrows():
                id_modal = row['CO_VIA']
                descricao = row['NO_VIA']
                cur.execute(
                    "INSERT INTO modal_transporte (id_modal_transporte, descricao) VALUES (%s, %s) ON CONFLICT (id_modal_transporte) DO NOTHING",
                    (id_modal, descricao)
                )
            self.conn.commit()
            cur.close()
            app_logger.info("Modais de transporte cadastrados no banco de dados com sucesso")
        except Error as e: 
            self.conn.rollback()
            error_logger.error("Erro ao cadastrar modais de transporte no banco de dados: %s", str(e))


    def registra_urfs(self) -> None:
        urf_df = pd.read_csv(self.tabelas.auxiliar('URF'), delimiter=';', encoding='latin1')
        try:
            cur = self.conn.cursor()
            for _, row in urf_df.iterrows():
                id_unidade = row['CO_URF']
                nome = row['NO_URF'].split(' - ')[1]
                cur.execute(
                    "INSERT INTO unidade_receita_federal (id_unidade, nome) VALUES (%s, %s) ON CONFLICT (id_unidade) DO NOTHING",
                    (id_unidade, nome)
                )
            self.conn.commit()
            cur.close()
            app_logger.info("URFs cadastrados no banco de dados com sucesso")
        except Error as e:
            self.conn.rollback()
            error_logger.error("Erro ao cadastrar URFs no banco de dados: %s", str(e))


    def registra_cgce_n3(self) -> None:
        cg_df = pd.read_csv(self.tabelas.auxiliar('NCM_CGCE'), delimiter=';', encoding='latin1')
        cg_df = cg_df.drop_duplicates(subset=['CO_CGCE_N3'])
        try:
            cur = self.conn.cursor()
            for _, row in cg_df.iterrows():
                id_n3 = row['CO_CGCE_N3']
                descricao = row['NO_CGCE_N3']
                cur.execute(
                    "INSERT INTO cgce_n3 (id_n3, descricao) VALUES (%s, %s) ON CONFLICT (id_n3) DO NOTHING",
                    (id_n3, descricao)
                )
            self.conn.commit()
            cur.close()
            app_logger.info("Códigos CGCE_N3 cadastrados no banco de dados com sucesso")
        except Error as e:
            self.conn.rollback()
            error_logger.error("Erro ao cadastrar códigos CGCE_N3 no banco de dados: %s", str(e))
        

    def registra_sh(self) -> None:
        file_url = 'data_pipeline/tabelas_auxiliares/codigos.csv'
        sh_df = pd.read_csv(file_url, delimiter=';', encoding='utf-8', dtype={'CO_SH4': str, 'CO_SH2': str})
        sh4 = sh_df.drop_duplicates(subset=['CO_SH4'])
        sh2 = sh_df.drop_duplicates(subset=['CO_SH2'])
        try:
            cur = self.conn.cursor()
            for _, row in sh4.iterrows():
                id_sh4 = row['CO_SH4']
                descricao = row['NO_SH4_POR']
                cur.execute(
                    "INSERT INTO sh4 (id_sh4, descricao) VALUES (%s, %s) ON CONFLICT (id_sh4) DO NOTHING",
                    (id_sh4, descricao)
                )
            
            for _, row in sh2.iterrows():
                id_sh2 = row['CO_SH2']
                descricao = row['NO_SH2_POR']
                cur.execute(
                    "INSERT INTO sh2 (id_sh2, descricao) VALUES (%s, %s) ON CONFLICT (id_sh2) DO NOTHING",
                    (id_sh2, descricao)
                )

            self.conn.commit()
            cur.close()
            app_logger.info("códigos SH2 e SH4 cadastrados no banco de dados com sucesso")
        except Error as e:
            self.conn.rollback()
            error_logger.error("Erro ao cadastrar códigos SH2 e SH4 no banco de dados: %s", str(e))


    def registra_produto(self) -> None:
        ncm_df = pd.read_csv(self.tabelas.auxiliar('NCM'), delimiter=";", encoding="latin1", dtype={'CO_NCM': int})
        unidades_df = pd.read_csv(self.tabelas.auxiliar('NCM_UNIDADE'), delimiter=";", encoding="latin1")
        ncm_df = ncm_df.merge(unidades_df[['CO_UNID', 'NO_UNID']], on='CO_UNID', how='left')
        file_url = 'data_pipeline/tabelas_auxiliares/codigos.csv'
        sh_df = pd.read_csv(file_url, delimiter=';', encoding='latin1', dtype={'CO_NCM': int, 'CO_SH4': str, 'CO_SH2': str})
        ncm_df = ncm_df.merge(sh_df[['CO_NCM', 'CO_SH4', 'CO_SH2']], on='CO_NCM', how='left')
        ncm_df = ncm_df.where(pd.notna(ncm_df), None)
        try:
            cur = self.conn.cursor()
            for _, row in ncm_df.iterrows():
                id_ncm = row['CO_NCM']
                descricao = row['NO_NCM_POR']
                unidade_medida = row['NO_UNID']
                id_sh4 = row['CO_SH4']
                id_sh2 = row['CO_SH2']
                id_cgce_n3 = int(row['CO_CGCE_N3'])
                cur.execute('''
                    INSERT INTO produto (id_ncm, descricao, unidade_medida, id_sh4, id_cgce_n3, id_sh2) 
                    VALUES (%s, %s, %s, %s, %s, %s) 
                    ON CONFLICT (id_ncm) DO NOTHING''',
                    (id_ncm, descricao, unidade_medida, id_sh4, id_cgce_n3, id_sh2)
                )
            self.conn.commit()
            cur.close()
            app_logger.info("Produtos cadastrados no banco de dados com sucesso")
        except Error as e:
            self.conn.rollback()
            error_logger.error("Erro ao cadastrar produtos no banco de dados: %s", str(e))


    def registra_transacao_estado (self, ano:int, tipo:Literal["exp", "imp"]) -> None:
        if tipo not in ['exp', 'imp']:
            raise ValueError("O tipo deve ser 'exp' ou 'imp'")
        transacao_df = pd.read_csv(f'data_pipeline/datasets/limpo/{ano}/{tipo.upper()}_{ano}.csv', dtype={'CO_NCM': int})
        uf_df = pd.read_csv(self.tabelas.auxiliar('UF'), delimiter=';', encoding='latin1')
        uf_df = uf_df.rename(columns={'SG_UF': 'SG_UF_NCM'})
        transacao_df = transacao_df.merge(uf_df, on='SG_UF_NCM', how='left')
        count = 0
        try:
            cur = self.conn.cursor()
            for _, row in transacao_df.iterrows():
                ano = row['CO_ANO']
                mes = row['CO_MES']
                tipo_transacao = tipo
                id_produto = row['CO_NCM']
                id_pais = row['CO_PAIS']
                id_estado = row['CO_UF']
                id_modal_transporte = row['CO_VIA']
                id_unidade_receita_federal = row['CO_URF']
                quantidade = int(row['QT_ESTAT'])
                kg_liquido = row['KG_LIQUIDO']
                valor_fob = row['VL_FOB']
                valor_agregado = valor_fob/kg_liquido
                
                if tipo == 'imp':
                    valor_seguro = row['VL_SEGURO']
                    valor_frete = row['VL_FRETE']
                    cur.execute(
                        '''INSERT INTO importacao_estado (ano, mes, id_produto, id_pais, id_estado, id_modal_transporte, id_unidade_receita_federal, quantidade, kg_liquido, valor_fob, valor_agregado, valor_seguro, valor_frete) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                        (ano, mes, id_produto, id_pais, id_estado, id_modal_transporte, id_unidade_receita_federal, quantidade, kg_liquido, valor_fob, valor_agregado, valor_seguro, valor_frete)
                    )
                else:
                    cur.execute(
                        '''INSERT INTO exportacao_estado (ano, mes, id_produto, id_pais, id_estado, id_modal_transporte, id_unidade_receita_federal, quantidade, kg_liquido, valor_fob, valor_agregado) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                        (ano, mes, id_produto, id_pais, id_estado, id_modal_transporte, id_unidade_receita_federal, quantidade, kg_liquido, valor_fob, valor_agregado)
                    )
                count += 1
            self.conn.commit()
            cur.close()
            app_logger.info(f"{count} Transações por estado de {tipo}ortação do ano {ano} cadastrados no banco de dados com sucesso")
        except Error as e:
            self.conn.rollback()
            error_logger.error("Erro ao cadastrar transações comerciais por estado no banco de dados para o ano %s: %s", ano, str(e))


    def registra_transacao_municipio(self, ano:int, tipo:Literal["exp", "imp"]) -> None:
        if tipo not in ['exp', 'imp']:
            raise ValueError("O tipo deve ser 'exp' ou 'imp'")        
        transacao_df = pd.read_csv(f'data_pipeline/datasets/limpo/{ano}/{tipo.upper()}_{ano}_MUN.csv', dtype={'SH4': str})
        transacao_df['SH4'] = transacao_df['SH4'].str.strip().str.zfill(4)
        uf_df = pd.read_csv(self.tabelas.auxiliar('UF'), delimiter=';', encoding='latin1')
        uf_df = uf_df.rename(columns={'SG_UF': 'SG_UF_MUN'})
        transacao_df = transacao_df.merge(uf_df, on='SG_UF_MUN', how='left')
        count = 0
        try:
            cur = self.conn.cursor()
            for _, row in transacao_df.iterrows():
                ano = row['CO_ANO']
                mes = row['CO_MES']
                tipo_transacao = tipo
                id_sh4 = row['SH4']
                id_pais = row['CO_PAIS']
                id_municipio = row['CO_MUN']
                kg_liquido = row['KG_LIQUIDO']
                valor_fob = row['VL_FOB']
                valor_agregado = valor_fob/kg_liquido
                if tipo == 'exp':
                    cur.execute(
                        '''INSERT INTO exportacao_municipio (ano, mes, id_sh4, id_pais, id_municipio, kg_liquido, valor_fob, valor_agregado) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                        (ano, mes, id_sh4, id_pais, id_municipio, kg_liquido, valor_fob, valor_agregado)
                    )
                else:
                    cur.execute(
                        '''INSERT INTO importacao_municipio (ano, mes, id_sh4, id_pais, id_municipio, kg_liquido, valor_fob, valor_agregado) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                        (ano, mes, id_sh4, id_pais, id_municipio, kg_liquido, valor_fob, valor_agregado)
                    )
                count += 1
            self.conn.commit()
            cur.close()
            app_logger.info(f"{count} Transações por município de {tipo}ortação do ano {ano} cadastrados no banco de dados com sucesso")
        except Error as e:
            print(id_sh4)
            self.conn.rollback()
            error_logger.error("Erro ao cadastrar transações comerciais por municipio no banco de dados: %s", str(e))


    def registra_transacoes_estado(self) -> None:
        for tipo in ('exp', 'imp'):
            for ano in range(2014, 2026):
                try:
                    cur = self.conn.cursor()
                    cur.execute(f"SELECT COUNT(*) FROM {tipo}ortacao_estado WHERE ano = {ano}")
                    res = cur.fetchone()[0]
                    print(res)
                    if res > 0:
                        app_logger.info(f"Transações de {tipo}ortação para o ano de {ano} já está cadastradas.")
                        continue
                    else:
                        self.registra_transacao_estado(ano, tipo)
                        # self.atualizar_views_materializadas()
                except Error as e:
                    error_logger.error(f"Erro ao verificar existência de registros para o ano de {ano}: {str(e)}")
                    self.conn.rollback()
                finally:
                    if cur:cur.close()


    def registra_transacoes_municipio(self) -> None:
        for tipo in ('exp', 'imp'):
            for ano in range(2014, 2025):
                try:
                    cur = self.conn.cursor()
                    cur.execute(f"SELECT COUNT(*) FROM {tipo}ortacao_municipio WHERE ano = {ano}")
                    res = cur.fetchone()[0]
                    print(res)
                    if res > 0:
                        app_logger.info(f"Transações por município de {tipo}ortação para o ano de {ano} já estão cadastradas.")
                        continue
                    else:
                        self.registra_transacao_municipio(ano, tipo)
                        # self.atualizar_views_materializadas()
                except Error as e:
                    error_logger.error(f"Erro ao verificar existência de registros para o ano de {ano}: {str(e)}")
                    self.conn.rollback()
                finally:
                    if cur:cur.close()

    def atualizar_views_materializadas(self) -> None:
        atualizacoes = [
            "SELECT atualizar_mv_exportacao_estado_anual()",
            "SELECT atualizar_mv_importacao_estado_anual()",
            "SELECT atualizar_mv_balanca_comercial()",
            "SELECT atualizar_mv_vlfob_setores()",
        ]
        with self.conn.cursor() as cur:
            for foo in atualizacoes:
                try:
                    app_logger.info(f"Iniciando função {foo}")
                    cur.execute(foo)
                    self.conn.commit()
                    app_logger.info(f"Função {foo} finalizada com sucesso")
                except Error as e:
                    self.conn.rollback()
                    error_logger.error("Erro ao atualizar views materializadas: %s", str(e))
                    pass
                

    def buid_db(self) -> None:
        self.registra_paises()
        self.registra_blocos()
        self.registra_estados()
        self.registra_municipios()
        self.registra_modal_transporte()
        self.registra_urfs()
        self.registra_cgce_n3()
        self.registra_sh()
        self.registra_produto()
        self.registra_transacoes_estado()
        # self.registra_transacoes_municipio()
        self.atualizar_views_materializadas()
        