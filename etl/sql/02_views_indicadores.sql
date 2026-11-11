-- Camada de indicadores (etapa 5: regras de negócio)
--
-- mv_*: views materializadas, pré-agregadas a partir das tabelas fato.
--       Guardam numeradores e denominadores separados, para que o painel
--       sempre calcule soma(numerador) / soma(denominador) no recorte filtrado.
-- vw_*: as mesmas tabelas com os rótulos das dimensões, consultadas pelo dashboard.
--
-- Rodar depois da carga (09_carga_postgres.py), pelo script etl/fase3/11_indicadores.py.

DROP MATERIALIZED VIEW IF EXISTS mv_ind_mortalidade, mv_ind_parto CASCADE;
DROP VIEW IF EXISTS vw_ind_mortalidade, vw_ind_parto, vw_ind_causas CASCADE;

-- Eixo 1: mortalidade materna -----------------------------------------------
-- Grão: ano x município de residência x faixa etária x raça/cor x escolaridade
CREATE MATERIALIZED VIEW mv_ind_mortalidade AS
WITH obitos AS (
    SELECT ano, cod_mun_res, faixa_etaria, cod_raca_cor, cod_escolaridade,
           count(*) FILTER (WHERE entra_rmm)                                   AS obitos_rmm,
           count(*) FILTER (WHERE tipo_obito = 'Materno tardio')               AS obitos_tardios,
           count(*) FILTER (WHERE tipo_obito = 'Associado a causa externa')    AS obitos_causa_externa,
           count(*) FILTER (WHERE cod_causa_externa LIKE 'O937%')              AS obitos_homicidio,
           count(*) FILTER (WHERE cod_causa_externa LIKE 'O936%')              AS obitos_suicidio,
           count(*) FILTER (WHERE entra_rmm AND cod_local_ocorrencia IN ('3', '4', '6')) AS obitos_fora_hospital,
           count(*) FILTER (WHERE entra_rmm AND cod_local_ocorrencia <> '9')   AS obitos_local_informado,
           count(*) FILTER (WHERE entra_rmm AND assistencia_medica = '2')      AS obitos_sem_assistencia,
           count(*) FILTER (WHERE entra_rmm AND assistencia_medica IN ('1', '2')) AS obitos_assist_informada
    FROM fato_obito_materno
    GROUP BY ano, cod_mun_res, faixa_etaria, cod_raca_cor, cod_escolaridade
)
SELECT ano, m.cod_uf, cod_mun_res, faixa_etaria, cod_raca_cor, cod_escolaridade,
       coalesce(n.qtd_nascidos, 0)            AS nascidos_vivos,
       coalesce(o.obitos_rmm, 0)              AS obitos_rmm,
       coalesce(o.obitos_tardios, 0)          AS obitos_tardios,
       coalesce(o.obitos_causa_externa, 0)    AS obitos_causa_externa,
       coalesce(o.obitos_homicidio, 0)        AS obitos_homicidio,
       coalesce(o.obitos_suicidio, 0)         AS obitos_suicidio,
       coalesce(o.obitos_fora_hospital, 0)    AS obitos_fora_hospital,
       coalesce(o.obitos_local_informado, 0)  AS obitos_local_informado,
       coalesce(o.obitos_sem_assistencia, 0)  AS obitos_sem_assistencia,
       coalesce(o.obitos_assist_informada, 0) AS obitos_assist_informada
FROM fato_nascidos_municipio n
FULL JOIN obitos o USING (ano, cod_mun_res, faixa_etaria, cod_raca_cor, cod_escolaridade)
JOIN dim_municipio m USING (cod_mun_res);

CREATE INDEX ix_mv_mort_ano_uf ON mv_ind_mortalidade (ano, cod_uf);

-- Eixo 2: parto e violência obstétrica --------------------------------------
-- Grão: ano x UF x faixa etária x raça/cor x escolaridade
CREATE MATERIALIZED VIEW mv_ind_parto AS
SELECT ano, cod_uf, faixa_etaria, cod_raca_cor, cod_escolaridade,
       sum(qtd_nascidos) AS nascidos_vivos,
       sum(qtd_nascidos) FILTER (WHERE cod_parto IN ('1', '2'))                   AS partos_tipo_informado,
       sum(qtd_nascidos) FILTER (WHERE cod_parto = '2')                           AS cesareas,
       sum(qtd_nascidos) FILTER (WHERE grupo_robson BETWEEN 1 AND 4 AND cod_parto IN ('1', '2')) AS partos_robson_1a4,
       sum(qtd_nascidos) FILTER (WHERE grupo_robson BETWEEN 1 AND 4 AND cod_parto = '2')         AS cesareas_robson_1a4,
       sum(qtd_nascidos) FILTER (WHERE cod_parto = '2' AND cod_cesarea_antes_tp = '1')           AS cesareas_antes_tp,
       sum(qtd_nascidos) FILTER (WHERE cod_tp_induzido = '1')                     AS partos_induzidos,
       sum(qtd_nascidos) FILTER (WHERE cod_tp_induzido IN ('1', '2', '3'))        AS inducao_informada,
       sum(qtd_nascidos) FILTER (WHERE faixa_prenatal = '7 ou mais')              AS prenatal_7_mais,
       sum(qtd_nascidos) FILTER (WHERE faixa_prenatal <> 'Ignorado')              AS prenatal_informado
FROM fato_nascidos_parto
GROUP BY ano, cod_uf, faixa_etaria, cod_raca_cor, cod_escolaridade;

CREATE INDEX ix_mv_parto_ano_uf ON mv_ind_parto (ano, cod_uf);

-- Views com rótulos (consultadas pelo dashboard) ---------------------------
CREATE VIEW vw_ind_mortalidade AS
SELECT i.*, u.uf_sigla, u.uf_nome, u.regiao,
       m.municipio, m.municipio_ignorado,
       r.raca_cor, r.raca_cor_agregada,
       e.escolaridade, e.ordem AS escolaridade_ordem,
       f.ordem AS faixa_ordem
FROM mv_ind_mortalidade i
JOIN dim_uf u USING (cod_uf)
JOIN dim_municipio m USING (cod_mun_res)
JOIN dim_raca_cor r USING (cod_raca_cor)
JOIN dim_escolaridade e USING (cod_escolaridade)
JOIN dim_faixa_etaria f USING (faixa_etaria);

CREATE VIEW vw_ind_parto AS
SELECT i.*, u.uf_sigla, u.uf_nome, u.regiao,
       r.raca_cor, r.raca_cor_agregada,
       e.escolaridade, e.ordem AS escolaridade_ordem,
       f.ordem AS faixa_ordem
FROM mv_ind_parto i
JOIN dim_uf u USING (cod_uf)
JOIN dim_raca_cor r USING (cod_raca_cor)
JOIN dim_escolaridade e USING (cod_escolaridade)
JOIN dim_faixa_etaria f USING (faixa_etaria);

-- Causas dos óbitos que entram na RMM, em grupos de leitura rápida
CREATE VIEW vw_ind_causas AS
SELECT o.ano, m.cod_uf, u.uf_sigla, u.regiao, o.cod_mun_res, o.faixa_etaria,
       r.raca_cor, r.raca_cor_agregada, e.escolaridade,
       c.cod_causa, c.descricao, c.grupo_cid,
       CASE
           WHEN c.categoria BETWEEN 'O00' AND 'O08' THEN 'Aborto'
           WHEN c.categoria BETWEEN 'O10' AND 'O16' THEN 'Hipertensão'
           WHEN c.categoria IN ('O20', 'O44', 'O45', 'O46', 'O67', 'O72') THEN 'Hemorragia'
           WHEN c.categoria IN ('O85', 'O86') THEN 'Infecção puerperal'
           WHEN c.categoria IN ('O98', 'O99') THEN 'Doenças que complicam a gestação (O98–O99)'
           WHEN c.categoria = 'O95' THEN 'Causa não especificada'
           ELSE 'Outras causas obstétricas'
       END AS grupo_causa
FROM fato_obito_materno o
JOIN dim_causa_obito c ON c.cod_causa = o.cod_causa_basica
JOIN dim_municipio m USING (cod_mun_res)
JOIN dim_uf u ON u.cod_uf = m.cod_uf
JOIN dim_raca_cor r USING (cod_raca_cor)
JOIN dim_escolaridade e USING (cod_escolaridade)
WHERE o.entra_rmm;
