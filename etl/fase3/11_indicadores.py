"""
11 - Camada de indicadores (regras de negócio)

Cria as views materializadas e as views de indicadores (etl/sql/02_views_indicadores.sql),
concede leitura ao usuário do dashboard (etl/sql/03_permissoes.sql) e mostra
os valores dos indicadores, para conferência e para a documentação.

Rodar sempre depois do 09_carga_postgres.py: o 01_schema.sql recria as tabelas
e apaga as views que dependem delas.

Execução (a partir da raiz do projeto):
    python etl/fase3/11_indicadores.py
"""
from pathlib import Path

import pandas as pd
import psycopg

RAIZ = Path(__file__).resolve().parents[2]
SQL = RAIZ / "etl" / "sql"

INDICADORES_ANO = """
SELECT m.ano,
       m.obitos_rmm, m.nascidos_vivos,
       round(m.obitos_rmm * 1e5 / m.nascidos_vivos, 1)                        AS rmm,
       round(100.0 * p.cesareas / p.partos_tipo_informado, 1)                AS pct_cesarea,
       round(100.0 * p.cesareas_robson_1a4 / p.partos_robson_1a4, 1)         AS pct_cesarea_robson_1a4,
       round(100.0 * p.cesareas_antes_tp / p.cesareas, 1)                    AS pct_cesarea_antes_tp,
       round(100.0 * p.partos_induzidos / p.inducao_informada, 1)            AS pct_induzido,
       round(100.0 * p.prenatal_7_mais / p.prenatal_informado, 1)            AS pct_prenatal_adequado
FROM (SELECT ano, sum(obitos_rmm) obitos_rmm, sum(nascidos_vivos) nascidos_vivos
      FROM vw_ind_mortalidade GROUP BY ano) m
JOIN (SELECT ano, sum(cesareas) cesareas, sum(partos_tipo_informado) partos_tipo_informado,
             sum(cesareas_robson_1a4) cesareas_robson_1a4, sum(partos_robson_1a4) partos_robson_1a4,
             sum(cesareas_antes_tp) cesareas_antes_tp, sum(partos_induzidos) partos_induzidos,
             sum(inducao_informada) inducao_informada, sum(prenatal_7_mais) prenatal_7_mais,
             sum(prenatal_informado) prenatal_informado
      FROM vw_ind_parto GROUP BY ano) p USING (ano)
ORDER BY ano
"""

INDICADORES_RACA = """
SELECT m.raca_cor_agregada,
       m.obitos_rmm,
       round(m.obitos_rmm * 1e5 / nullif(m.nascidos_vivos, 0), 1)             AS rmm,
       round(100.0 * p.cesareas_robson_1a4 / nullif(p.partos_robson_1a4, 0), 1) AS pct_cesarea_robson_1a4,
       round(100.0 * p.prenatal_7_mais / nullif(p.prenatal_informado, 0), 1)  AS pct_prenatal_adequado
FROM (SELECT raca_cor_agregada, sum(obitos_rmm) obitos_rmm, sum(nascidos_vivos) nascidos_vivos
      FROM vw_ind_mortalidade GROUP BY 1) m
JOIN (SELECT raca_cor_agregada, sum(cesareas_robson_1a4) cesareas_robson_1a4,
             sum(partos_robson_1a4) partos_robson_1a4, sum(prenatal_7_mais) prenatal_7_mais,
             sum(prenatal_informado) prenatal_informado
      FROM vw_ind_parto GROUP BY 1) p USING (raca_cor_agregada)
ORDER BY rmm DESC
"""

OUTROS = """
SELECT sum(obitos_tardios)        AS obitos_tardios,
       sum(obitos_causa_externa)  AS obitos_causa_externa,
       sum(obitos_homicidio)      AS homicidios_o93_7,
       sum(obitos_suicidio)       AS suicidios_o93_6,
       round(100.0 * sum(obitos_fora_hospital) / sum(obitos_local_informado), 1)    AS pct_fora_hospital,
       round(100.0 * sum(obitos_sem_assistencia) / sum(obitos_assist_informada), 1) AS pct_sem_assistencia
FROM vw_ind_mortalidade
"""


def ler_database_url() -> str:
    for linha in (RAIZ / ".env").read_text(encoding="utf-8-sig").splitlines():
        if linha.startswith("DATABASE_URL="):
            return linha.split("=", 1)[1].strip()
    raise RuntimeError("DATABASE_URL não encontrada no arquivo .env")


def consultar(cur, sql: str) -> pd.DataFrame:
    cur.execute(sql)
    return pd.DataFrame(cur.fetchall(), columns=[c.name for c in cur.description])


def main() -> None:
    with psycopg.connect(ler_database_url()) as conn:
        conn.add_notice_handler(lambda n: print(" ", n.message_primary))
        with conn.cursor() as cur:
            print("Criando views de indicadores...")
            cur.execute((SQL / "02_views_indicadores.sql").read_text(encoding="utf-8"))
            cur.execute((SQL / "03_permissoes.sql").read_text(encoding="utf-8"))

            cur.execute("""
                SELECT relname, pg_size_pretty(pg_total_relation_size(oid))
                FROM pg_class WHERE relname IN ('mv_ind_mortalidade', 'mv_ind_parto')
            """)
            for nome, tamanho in cur.fetchall():
                print(f"  {nome}: {tamanho}")

            pd.set_option("display.width", 200)
            print("\n=== Indicadores por ano ===")
            print(consultar(cur, INDICADORES_ANO).to_string(index=False))
            print("\n=== Indicadores por raça/cor (2022 a 2024) ===")
            print(consultar(cur, INDICADORES_RACA).to_string(index=False))
            print("\n=== Circunstâncias e violência (2022 a 2024) ===")
            print(consultar(cur, OUTROS).to_string(index=False))


if __name__ == "__main__":
    main()
