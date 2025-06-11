create_tables_script = '''
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_transacao_enum') THEN
        CREATE TYPE tipo_transacao_enum AS ENUM ('exp', 'imp');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS estado (
    id_estado SERIAL PRIMARY KEY,
    sigla VARCHAR(2),
    nome VARCHAR(100),
    regiao VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS municipio (
    id_municipio SERIAL PRIMARY KEY,
    nome VARCHAR(100),
    id_estado INT,
    FOREIGN KEY (id_estado) REFERENCES estado(id_estado)
);

CREATE TABLE IF NOT EXISTS bloco (
    id_bloco SERIAL PRIMARY KEY,
    nome_bloco VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS pais (
    id_pais SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    id_bloco INT,
    FOREIGN KEY (id_bloco) REFERENCES bloco(id_bloco)
);

CREATE TABLE IF NOT EXISTS unidade_receita_federal (
    id_unidade SERIAL PRIMARY KEY,
    nome VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS modal_transporte (
    id_modal_transporte SERIAL PRIMARY KEY,
    descricao VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS cgce_n3 (
    id_n3 VARCHAR(3) PRIMARY KEY,
    descricao TEXT
);

CREATE TABLE IF NOT EXISTS sh2 (
    id_sh2 VARCHAR(2) PRIMARY KEY,
    descricao TEXT
);

CREATE TABLE IF NOT EXISTS sh4 (
    id_sh4 VARCHAR(4) PRIMARY KEY,
    descricao TEXT
);

CREATE TABLE IF NOT EXISTS produto (
    id_ncm INT PRIMARY KEY,
    descricao TEXT,
    unidade_medida VARCHAR(50),
    id_sh4 VARCHAR(4),
    id_cgce_n3 VARCHAR(3),
    id_sh2 VARCHAR(2),
    FOREIGN KEY (id_sh4) REFERENCES sh4 (id_sh4),
    FOREIGN KEY (id_cgce_n3) REFERENCES cgce_n3 (id_n3),
    FOREIGN KEY (id_sh2) REFERENCES sh2 (id_sh2)
);

CREATE TABLE IF NOT EXISTS exportacao_estado (
    id_transacao SERIAL,
    ano INT,
    mes INT,
    id_produto INT,
    id_pais INT,
    id_estado INT,
    id_unidade_receita_federal INT,
    quantidade BIGINT,
    valor_fob DECIMAL(15,2),
    kg_liquido DECIMAL(15,2),
    valor_agregado DECIMAL(15,2),
    id_modal_transporte INT,
    FOREIGN KEY (id_modal_transporte) REFERENCES modal_transporte(id_modal_transporte),
    FOREIGN KEY (id_unidade_receita_federal) REFERENCES unidade_receita_federal (id_unidade),
    FOREIGN KEY (id_produto) REFERENCES produto (id_ncm),
    FOREIGN KEY (id_pais) REFERENCES pais (id_pais),
    FOREIGN KEY (id_estado) REFERENCES estado (id_estado)
) PARTITION BY RANGE (ano);

-- Adicionar a chave primária na tabela particionada
ALTER TABLE exportacao_estado ADD PRIMARY KEY (id_transacao, ano);

CREATE TABLE IF NOT EXISTS importacao_estado (
    id_transacao SERIAL,
    ano INT,
    mes INT,
    id_produto INT,
    id_pais INT,
    id_estado INT,
    id_unidade_receita_federal INT,
    quantidade BIGINT,
    valor_fob DECIMAL(15,2),
    kg_liquido DECIMAL(15,2),
    valor_agregado DECIMAL(15,2),
    valor_seguro DECIMAL(15,2),
    valor_frete DECIMAL(15,2),
    id_modal_transporte INT,
    FOREIGN KEY (id_modal_transporte) REFERENCES modal_transporte(id_modal_transporte),
    FOREIGN KEY (id_unidade_receita_federal) REFERENCES unidade_receita_federal (id_unidade),
    FOREIGN KEY (id_produto) REFERENCES produto (id_ncm),
    FOREIGN KEY (id_pais) REFERENCES pais (id_pais),
    FOREIGN KEY (id_estado) REFERENCES estado (id_estado)
) PARTITION BY RANGE (ano);

-- Adicionar a chave primária na tabela particionada
ALTER TABLE importacao_estado ADD PRIMARY KEY (id_transacao, ano);

-- Criar partições para os anos
DO $$
DECLARE
    ano_atual INT := EXTRACT(YEAR FROM CURRENT_DATE);
    ano_inicio INT := 2014;
BEGIN
    FOR ano IN ano_inicio..ano_atual LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS exportacao_estado_%s PARTITION OF exportacao_estado
            FOR VALUES FROM (%s) TO (%s);
        ', ano, ano, ano + 1);
        
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS importacao_estado_%s PARTITION OF importacao_estado
            FOR VALUES FROM (%s) TO (%s);
        ', ano, ano, ano + 1);
    END LOOP;
END $$;

CREATE TABLE IF NOT EXISTS importacao_municipio (
    id_transacao SERIAL PRIMARY KEY,
    ano INT,
    mes INT,
    id_sh4 VARCHAR(4),
    id_pais INT,
    id_municipio INT,
    valor_fob DECIMAL(15,2),
    kg_liquido DECIMAL(15,2),
    valor_agregado DECIMAL(15,2),
    valor_seguro DECIMAL(15,2),
    valor_frete DECIMAL(15,2),
    FOREIGN KEY (id_sh4) REFERENCES sh4 (id_sh4),
    FOREIGN KEY (id_pais) REFERENCES pais (id_pais),
    FOREIGN KEY (id_municipio) REFERENCES municipio (id_municipio)
);

CREATE TABLE IF NOT EXISTS exportacao_municipio (
    id_transacao SERIAL PRIMARY KEY,
    ano INT,
    mes INT,
    id_sh4 VARCHAR(4),
    id_pais INT,
    id_municipio INT,
    valor_fob DECIMAL(15,2),
    kg_liquido DECIMAL(15,2),
    valor_agregado DECIMAL(15,2),
    FOREIGN KEY (id_sh4) REFERENCES sh4 (id_sh4),
    FOREIGN KEY (id_pais) REFERENCES pais (id_pais),
    FOREIGN KEY (id_municipio) REFERENCES municipio (id_municipio)
);

CREATE INDEX IF NOT EXISTS idx_ano_id_produto ON exportacao_estado(ano, id_produto);
CREATE INDEX IF NOT EXISTS idx_ano_mes_estado ON exportacao_estado(ano, mes, id_estado);
CREATE INDEX IF NOT EXISTS idx_produto_ano_mes ON exportacao_estado(id_produto, ano, mes);
CREATE INDEX IF NOT EXISTS idx_ano_mes_pais ON exportacao_estado(ano, mes, id_pais);
CREATE INDEX IF NOT EXISTS idx_ano_mes_estado_imp ON importacao_estado(ano, mes, id_estado);
CREATE INDEX IF NOT EXISTS idx_ano_mes_pais_imp ON importacao_estado(ano, mes, id_pais);
CREATE INDEX IF NOT EXISTS idx_produto_ano_mes_imp ON importacao_estado(id_produto, ano, mes);
CREATE INDEX IF NOT EXISTS idx_produto_sh4 ON produto(id_sh4);
CREATE INDEX IF NOT EXISTS idx_produto_sh2 ON produto(id_sh2);
CREATE INDEX IF NOT EXISTS idx_municipio_estado ON municipio(id_estado);
CREATE INDEX IF NOT EXISTS idx_pais_bloco ON pais(id_bloco);
CREATE INDEX IF NOT EXISTS idx_exportacao_estado_ano_mes_tipo ON exportacao_estado (ano, mes, id_estado, id_pais, id_produto);
CREATE INDEX IF NOT EXISTS idx_importacao_estado_ano_mes_tipo ON importacao_estado (ano, mes, id_estado, id_pais, id_produto);

CREATE EXTENSION IF NOT EXISTS unaccent;
'''

cria_mv_exportacao_estado_anual = """
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_exportacao_estado_anual AS
SELECT 
    ano,
    id_estado,
    id_produto,
    id_pais,
    SUM(quantidade) as quantidade_total,
    SUM(valor_fob) as valor_fob_total,
    SUM(kg_liquido) as kg_liquido_total,
    SUM(valor_agregado) as valor_agregado_total
FROM exportacao_estado
GROUP BY ano, id_estado, id_produto, id_pais;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_exportacao_estado_anual ON mv_exportacao_estado_anual(ano, id_estado, id_produto, id_pais);
"""

cria_mv_importacao_estado_anual = """
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_importacao_estado_anual AS
SELECT 
    ano,
    id_estado,
    id_produto,
    id_pais,
    SUM(quantidade) as quantidade_total,
    SUM(valor_fob) as valor_fob_total,
    SUM(kg_liquido) as kg_liquido_total,
    SUM(valor_agregado) as valor_agregado_total,
    SUM(valor_seguro) as valor_seguro_total,
    SUM(valor_frete) as valor_frete_total
FROM importacao_estado
GROUP BY ano, id_estado, id_produto, id_pais;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_importacao_estado_anual ON mv_importacao_estado_anual(ano, id_estado, id_produto, id_pais);
"""

cria_mv_balanca_comercial = """
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_balanca_comercial AS
WITH exp AS (
    SELECT
        ano,
        mes,
        id_pais,
        id_estado,
        SUM(valor_fob) AS total_exportado
    FROM exportacao_estado
    GROUP BY ano, mes, id_pais, id_estado
),
imp AS (
    SELECT
        ano,
        mes,
        id_pais,
        id_estado,
        SUM(valor_fob) AS total_importado
    FROM importacao_estado
    GROUP BY ano, mes, id_pais, id_estado 
)
SELECT
    COALESCE(exp.ano, imp.ano) AS ano,
    COALESCE(exp.mes, imp.mes) AS mes,
    COALESCE(exp.id_pais, imp.id_pais) AS id_pais,
    COALESCE(exp.id_estado, imp.id_estado) AS id_estado,
    exp.total_exportado,
    imp.total_importado,
    COALESCE(exp.total_exportado, 0) - COALESCE(imp.total_importado, 0) AS balanca_comercial
FROM exp
FULL OUTER JOIN imp
    ON exp.ano = imp.ano
    AND exp.mes = imp.mes
    AND exp.id_pais = imp.id_pais
    AND exp.id_estado = imp.id_estado
ORDER BY ano, mes;

-- Índices para as views materializadas
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_exportacao_estado_anual ON mv_exportacao_estado_anual(ano, id_estado, id_produto, id_pais);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_importacao_estado_anual ON mv_importacao_estado_anual(ano, id_estado, id_produto, id_pais);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_balanca_comercial_unique ON mv_balanca_comercial (ano, mes, id_pais, id_estado);
"""

cria_mv_vlfob_setores = """
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vlfob_setores AS
WITH exportacoes AS (
    SELECT 
        s.id_sh4,
        e.ano,
        e.id_estado,
        SUM(e.valor_fob) AS valor_fob_exp,
        SUM(e.kg_liquido) AS kg_liquido_exp
    FROM produto p
    JOIN sh4 s ON s.id_sh4 = p.id_sh4
    JOIN exportacao_estado e ON e.id_produto = p.id_ncm
    GROUP BY s.id_sh4, ano, e.id_estado
),
importacoes AS (
    SELECT 
        s.id_sh4,
        i.ano,
        i.id_estado,
        SUM(i.valor_fob) AS valor_fob_imp,
        SUM(i.kg_liquido) AS kg_liquido_imp
    FROM produto p
    JOIN sh4 s ON s.id_sh4 = p.id_sh4
    JOIN importacao_estado i ON i.id_produto = p.id_ncm
    GROUP BY s.id_sh4, ano, i.id_estado
)
SELECT 
    COALESCE(e.id_sh4, i.id_sh4) AS id_sh4,
    COALESCE(e.ano, i.ano) AS ano,
    COALESCE(e.id_estado, i.id_estado) AS id_estado,
    COALESCE(e.valor_fob_exp, 0) AS valor_fob_exp,
    COALESCE(i.valor_fob_imp, 0) AS valor_fob_imp,
    COALESCE(e.kg_liquido_exp, 0) AS kg_liquido_exp,
    COALESCE(i.kg_liquido_imp, 0) AS kg_liquido_imp
FROM exportacoes e
FULL OUTER JOIN importacoes i
    ON e.id_sh4 = i.id_sh4 AND e.ano = i.ano AND e.id_estado = i.id_estado  ;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_vlfob_setores ON mv_vlfob_setores (id_sh4, ano, id_estado);
"""

cria_mv_tendencia_saldo_setores = """
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_tendencia_saldo_setores AS
WITH dados_mensais AS (
    SELECT 
        p.id_sh4,
        e.ano,
        e.mes,
        COALESCE(SUM(e.valor_fob), 0) AS valor_fob_exp,
        COALESCE(SUM(i.valor_fob), 0) AS valor_fob_imp
    FROM produto p
    LEFT JOIN exportacao_estado e ON e.id_produto = p.id_ncm
    LEFT JOIN importacao_estado i ON i.id_produto = p.id_ncm
    GROUP BY p.id_sh4, e.ano, e.mes
)
SELECT 
    id_sh4,
    ano,
    mes,
    valor_fob_exp - valor_fob_imp AS saldo
FROM dados_mensais
ORDER BY id_sh4, ano, mes;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_tendencia_saldo_setores ON mv_tendencia_saldo_setores (id_sh4, ano, mes);

"""

atualiza_mv_exportacao_estado_anual = """
CREATE OR REPLACE FUNCTION atualizar_mv_exportacao_estado_anual()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_exportacao_estado_anual;
END;
$$ LANGUAGE plpgsql;
"""

atualiza_mv_importacao_estado_anual = """
CREATE OR REPLACE FUNCTION atualizar_mv_importacao_estado_anual()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_importacao_estado_anual;
END;
$$ LANGUAGE plpgsql;
"""

atualiza_mv_balanca_comercial = """
CREATE OR REPLACE FUNCTION atualizar_mv_balanca_comercial()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_balanca_comercial;
END;
$$ LANGUAGE plpgsql;
"""

atualiza_mv_vlfob_setores = """
CREATE OR REPLACE FUNCTION atualizar_mv_vlfob_setores()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_vlfob_setores;

END;
$$ LANGUAGE plpgsql;
"""

atualiza_mv_tendencia_saldo_setores = """
CREATE OR REPLACE FUNCTION atualizar_mv_tendencia_saldo_setores()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_tendencia_saldo_setores;
END;
$$ LANGUAGE plpgsql;
"""

atualiza_views = """
-- Função para atualizar as views materializadas
CREATE OR REPLACE FUNCTION atualizar_views_materializadas()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_exportacao_estado_anual;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_importacao_estado_anual;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_balanca_comercial;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION atualizar_mv_vlfob_setores()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_vlfob_setores;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION atualizar_views_tendencias()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_tendencia_saldo_setores;
END;
$$ LANGUAGE plpgsql;
"""