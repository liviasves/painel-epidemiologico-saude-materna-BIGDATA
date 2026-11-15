import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import psycopg
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
FUSO = ZoneInfo("America/Bahia")
TTL = 300

AGRUPAVEIS = {
    "ano", "regiao", "uf_sigla", "uf_nome", "cod_mun_res", "municipio",
    "raca_cor", "raca_cor_agregada", "faixa_etaria", "faixa_ordem",
    "escolaridade", "escolaridade_ordem",
}

SOMAS_MORTALIDADE = [
    "nascidos_vivos", "obitos_rmm", "obitos_tardios", "obitos_causa_externa",
    "obitos_homicidio", "obitos_suicidio", "obitos_fora_hospital",
    "obitos_local_informado", "obitos_sem_assistencia", "obitos_assist_informada",
]
SOMAS_PARTO = [
    "nascidos_vivos", "partos_tipo_informado", "cesareas", "partos_robson_1a4",
    "cesareas_robson_1a4", "cesareas_antes_tp", "partos_induzidos",
    "inducao_informada", "prenatal_7_mais", "prenatal_informado",
]


class BancoIndisponivel(Exception):
    pass


def _url() -> str:
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    arquivos = [RAIZ / ".streamlit" / "secrets.toml", Path.home() / ".streamlit" / "secrets.toml"]
    if any(a.exists() for a in arquivos) and "DATABASE_URL" in st.secrets:
        return st.secrets["DATABASE_URL"]
    env = RAIZ / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8-sig").splitlines():
            if linha.startswith("DATABASE_URL="):
                return linha.split("=", 1)[1].strip()
    raise BancoIndisponivel("A conexão com o banco não foi configurada (DATABASE_URL).")


@st.cache_resource(show_spinner=False)
def _conexao() -> psycopg.Connection:
    return psycopg.connect(_url(), autocommit=True, connect_timeout=10)


def consultar(sql: str, params: tuple = ()) -> pd.DataFrame:
    for tentativa in range(2):
        try:
            conn = _conexao()
            if conn.closed or conn.broken:
                raise psycopg.OperationalError("conexão encerrada")
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return pd.DataFrame(cur.fetchall(), columns=[c.name for c in cur.description])
        except psycopg.OperationalError as erro:
            _conexao.clear()
            if tentativa == 1:
                raise BancoIndisponivel(str(erro)) from erro
        except psycopg.Error as erro:
            raise BancoIndisponivel(str(erro)) from erro
    raise BancoIndisponivel("sem resposta")


def _where(f: dict, ignorar: set, com_municipio: bool) -> tuple[str, list]:
    cond, params = [], []
    if f.get("ano") and "ano" not in ignorar:
        cond.append("ano = %s"); params.append(f["ano"])
    if f.get("regiao") and "regiao" not in ignorar:
        cond.append("regiao = %s"); params.append(f["regiao"])
    if f.get("uf") and "uf" not in ignorar:
        cond.append("uf_sigla = %s"); params.append(f["uf"])
    if com_municipio and f.get("mun") and "mun" not in ignorar:
        cond.append("cod_mun_res = %s"); params.append(f["mun"])
    if f.get("raca") and "raca" not in ignorar:
        if f["raca"].startswith("Negra"):
            cond.append("raca_cor_agregada = %s")
        else:
            cond.append("raca_cor = %s")
        params.append(f["raca"])
    if f.get("faixa") and "faixa" not in ignorar:
        cond.append("faixa_etaria = %s"); params.append(f["faixa"])
    if f.get("esc") and "esc" not in ignorar:
        cond.append("escolaridade = %s"); params.append(f["esc"])
    return ("WHERE " + " AND ".join(cond)) if cond else "", params


def _agrupado(view: str, somas: list, f: dict, por: tuple, ignorar: tuple, com_municipio: bool) -> pd.DataFrame:
    por = tuple(c for c in por if c in AGRUPAVEIS)
    where, params = _where(f, set(ignorar), com_municipio)
    colunas = ", ".join(f"sum({c})::bigint AS {c}" for c in somas)
    if por:
        grupo = ", ".join(por)
        sql = f"SELECT {grupo}, {colunas} FROM {view} {where} GROUP BY {grupo} ORDER BY {grupo}"
    else:
        sql = f"SELECT {colunas} FROM {view} {where}"
    df = consultar(sql, tuple(params))
    for c in somas:
        df[c] = df[c].fillna(0).astype("int64")
    return df


@st.cache_data(ttl=TTL, show_spinner=False)
def mortalidade(f: dict, por: tuple = (), ignorar: tuple = ()) -> pd.DataFrame:
    return _agrupado("vw_ind_mortalidade", SOMAS_MORTALIDADE, f, por, ignorar, True)


@st.cache_data(ttl=TTL, show_spinner=False)
def parto(f: dict, por: tuple = (), ignorar: tuple = ()) -> pd.DataFrame:
    return _agrupado("vw_ind_parto", SOMAS_PARTO, f, por, ignorar, False)


@st.cache_data(ttl=TTL, show_spinner=False)
def causas(f: dict) -> pd.DataFrame:
    where, params = _where(f, set(), True)
    sql = f"SELECT grupo_causa, count(*) AS obitos FROM vw_ind_causas {where} GROUP BY grupo_causa ORDER BY obitos DESC"
    return consultar(sql, tuple(params))


@st.cache_data(ttl=TTL, show_spinner=False)
def causas_detalhe(f: dict) -> pd.DataFrame:
    where, params = _where(f, set(), True)
    sql = (f"SELECT cod_causa, descricao, count(*) AS obitos FROM vw_ind_causas {where} "
           f"GROUP BY cod_causa, descricao ORDER BY obitos DESC")
    return consultar(sql, tuple(params))


@st.cache_data(ttl=3600, show_spinner=False)
def opcoes() -> dict:
    ufs = consultar("SELECT uf_sigla, uf_nome, regiao FROM dim_uf WHERE uf_sigla <> 'IG' ORDER BY uf_nome")
    faixas = consultar("SELECT faixa_etaria FROM dim_faixa_etaria WHERE faixa_etaria NOT IN ('<10', '50+', 'Ignorada') ORDER BY ordem")
    esc = consultar("SELECT escolaridade FROM dim_escolaridade WHERE escolaridade <> 'Ignorado' ORDER BY ordem")
    return {
        "ufs": ufs,
        "regioes": sorted(ufs["regiao"].unique()),
        "faixas": faixas["faixa_etaria"].tolist(),
        "escolaridades": esc["escolaridade"].tolist(),
    }


@st.cache_data(ttl=3600, show_spinner=False)
def municipios(uf: str) -> pd.DataFrame:
    return consultar(
        "SELECT m.cod_mun_res, m.municipio FROM dim_municipio m JOIN dim_uf u USING (cod_uf) "
        "WHERE u.uf_sigla = %s AND NOT m.municipio_ignorado ORDER BY m.municipio", (uf,))


@st.cache_data(ttl=TTL, show_spinner=False)
def ultima_carga() -> datetime | None:
    df = consultar("SELECT max(carregado_em) AS carga FROM controle_carga")
    valor = df["carga"].iloc[0]
    return None if pd.isna(valor) else valor


def agora() -> str:
    return datetime.now(FUSO).strftime("%d/%m/%Y %H:%M")