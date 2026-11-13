"""
Painel Epidemiológico de Mortalidade Materna e Violência Obstétrica

Execução local (na raiz do projeto):
    streamlit run dashboard/app.py
"""
import pandas as pd
import streamlit as st

import dados
import graficos as g
from dados import BancoIndisponivel

st.set_page_config(page_title="Saúde Materna | Painel Epidemiológico", layout="wide",
                   initial_sidebar_state="expanded")

LIMITE_POUCOS = 10          # óbitos no recorte abaixo disso: taxa instável
META_BRASIL, META_ODS = 30, 70
REPOSITORIO = "https://github.com/liviasves/painel-epidemiologico-saude-materna"

RACAS = ["Todas", "Negra (preta + parda)", "Preta", "Parda", "Branca", "Indígena", "Amarela"]

METRICAS_PARTO = {
    "Cesárea": ("cesareas", "partos_tipo_informado",
                "Partos cesáreos entre os partos com tipo informado", 15, "OMS: 10% a 15%"),
    "Cesárea em baixo risco": ("cesareas_robson_1a4", "partos_robson_1a4",
                               "Cesáreas nos grupos 1 a 4 de Robson (gestação única, cefálica, a termo, sem cesárea anterior)",
                               None, ""),
    "Cesárea antes do trabalho de parto": ("cesareas_antes_tp", "cesareas",
                                           "Cesáreas feitas antes de a mulher entrar em trabalho de parto", None, ""),
    "Parto induzido": ("partos_induzidos", "inducao_informada",
                       "Nascimentos com trabalho de parto induzido", None, ""),
    "Pré-natal adequado": ("prenatal_7_mais", "prenatal_informado",
                           "Nascidos vivos cujas mães fizeram 7 ou mais consultas de pré-natal", None, ""),
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, select { font-family: Inter, 'Segoe UI', Roboto, Arial, sans-serif; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1440px; }
[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E3E7ED; }
[data-testid="stSidebar"] .stSelectbox label, [data-testid="stSidebar"] .stSelectbox p { font-size: 13px; font-weight: 600; color: #1B2333; }
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [class*="st-key-cartao"]) {
    background: #FFFFFF; border-color: #E3E7ED; border-radius: 10px;
    box-shadow: 0 1px 2px rgba(16, 24, 40, .04);
}
[class*="st-key-cartao"] { gap: 0.4rem; }
.topo { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: 12px;
        padding-bottom: 14px; margin-bottom: 18px; border-bottom: 1px solid #E3E7ED; }
.topo .rotulo { font-size: 11.5px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: #8C1D40; }
.topo h1 { font-size: 26px; font-weight: 700; color: #1B2333; margin: 2px 0 2px; padding: 0; line-height: 1.2; }
.topo .sub { font-size: 13.5px; color: #5B6475; }
.topo .meta { font-size: 12.5px; color: #5B6475; text-align: right; line-height: 1.6; }
.topo .vivo { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #12B76A; margin-right: 6px; }
.kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-bottom: 8px; }
@media (max-width: 1100px) { .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.kpi { background: #FFFFFF; border: 1px solid #E3E7ED; border-radius: 10px; padding: 16px 18px 14px;
       box-shadow: 0 1px 2px rgba(16, 24, 40, .04); border-top: 3px solid #8C1D40; }
.kpi .t { font-size: 12.5px; font-weight: 600; color: #5B6475; text-transform: uppercase; letter-spacing: .04em; }
.kpi .v { font-size: 34px; font-weight: 700; color: #1B2333; line-height: 1.15; margin-top: 6px; font-variant-numeric: tabular-nums; }
.kpi .v small { font-size: 14px; font-weight: 500; color: #5B6475; margin-left: 4px; }
.kpi .d { font-size: 12.5px; font-weight: 600; margin-top: 2px; }
.kpi .d.ruim { color: #B42318; } .kpi .d.bom { color: #067647; } .kpi .d.neutro { color: #5B6475; }
.kpi .r { font-size: 12.5px; color: #5B6475; margin-top: 6px; }
.kpi .trilho { position: relative; height: 6px; background: #EDF0F4; border-radius: 3px; margin-top: 10px; }
.kpi .trilho i { position: absolute; left: 0; top: 0; bottom: 0; background: #8C1D40; border-radius: 3px; }
.kpi .trilho b { position: absolute; top: -3px; width: 2px; height: 12px; background: #B7791F; }
.card-titulo { font-size: 15px; font-weight: 600; color: #1B2333; margin: 2px 0 0; }
.card-sub { font-size: 12.5px; color: #5B6475; margin: 2px 0 6px; }
.trilha { font-size: 13px; color: #5B6475; margin-bottom: 4px; }
.trilha b { color: #1B2333; }
.faixa { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 0; }
@media (max-width: 1100px) { .faixa { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
.faixa > div { padding: 6px 14px; border-left: 1px solid #E3E7ED; }
.faixa > div:first-child { border-left: 0; }
.faixa .n { font-size: 24px; font-weight: 700; color: #1B2333; font-variant-numeric: tabular-nums; }
.faixa .l { font-size: 12.5px; color: #5B6475; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 1px solid #E3E7ED; }
.stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 14px; padding: 10px 6px; }
.nota { font-size: 12px; color: #5B6475; line-height: 1.5; margin: 2px 0 8px; }
</style>
"""


# ---------------------------------------------------------------------------
# utilidades
# ---------------------------------------------------------------------------
def razao(n, d, fator=100.0):
    return (n * fator / d) if d else 0.0


_CARTOES = [0]


def cartao(titulo: str, sub: str = ""):
    _CARTOES[0] += 1
    caixa = st.container(border=True, key=f"cartao_{_CARTOES[0]}")
    caixa.markdown(f'<div class="card-titulo">{titulo}</div><div class="card-sub">{sub}</div>',
                   unsafe_allow_html=True)
    return caixa


def plot(caixa, fig, **kw):
    caixa.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, **kw)


def delta(atual, anterior, unidade, maior_e_ruim=True, ano_ant=None):
    if anterior is None:
        return '<div class="d neutro">&nbsp;</div>'
    dif = atual - anterior
    if abs(dif) < 0.05:
        return f'<div class="d neutro">estável em relação a {ano_ant}</div>'
    classe = "ruim" if (dif > 0) == maior_e_ruim else "bom"
    seta = "▲" if dif > 0 else "▼"
    return f'<div class="d {classe}">{seta} {g.num(abs(dif))}{unidade} em relação a {ano_ant}</div>'


def poucos_casos(df: pd.DataFrame) -> pd.DataFrame:
    df["poucos"] = df["obitos_rmm"] < LIMITE_POUCOS
    df["hover"] = [f"<br>{o} óbitos · {g.num(n, 0)} nascidos" for o, n in zip(df["obitos_rmm"], df["nascidos_vivos"])]
    return df


def com_rmm(df: pd.DataFrame) -> pd.DataFrame:
    df["rmm"] = [razao(o, n, 1e5) for o, n in zip(df["obitos_rmm"], df["nascidos_vivos"])]
    return poucos_casos(df)


# ---------------------------------------------------------------------------
# filtros (barra lateral) e drill-down
# ---------------------------------------------------------------------------
def limpar_filtros():
    for k in ("f_ano", "f_regiao", "f_uf", "f_mun", "f_raca", "f_faixa", "f_esc"):
        st.session_state.pop(k, None)


def subir_nivel():
    if st.session_state.get("f_mun"):
        st.session_state["f_mun"] = ""
    elif st.session_state.get("f_uf", "Todas") != "Todas":
        st.session_state["f_uf"] = "Todas"
    else:
        st.session_state["f_regiao"] = "Brasil"


def descer_nivel():
    evento = st.session_state.get("graf_geo")
    pontos = (evento or {}).get("selection", {}).get("points", [])
    if not pontos:
        return
    indice = pontos[0].get("point_index", pontos[0].get("point_number"))
    chaves = st.session_state.get("_geo_chaves", [])
    if indice is None or indice >= len(chaves):
        return
    alvo = {"regiao": "f_regiao", "uf": "f_uf", "mun": "f_mun"}[st.session_state["_geo_nivel"]]
    st.session_state[alvo] = chaves[indice]


def barra_lateral(op: dict) -> dict:
    sb = st.sidebar
    sb.markdown('<div class="card-titulo" style="font-size:16px">Filtros</div>'
                '<div class="card-sub">Valem para todos os gráficos</div>', unsafe_allow_html=True)

    ano = sb.selectbox("Período", ["2022 a 2024", "2024", "2023", "2022"], key="f_ano")
    regiao = sb.selectbox("Região", ["Brasil"] + op["regioes"], key="f_regiao")

    ufs = op["ufs"] if regiao == "Brasil" else op["ufs"][op["ufs"]["regiao"] == regiao]
    nomes_uf = dict(zip(ufs["uf_sigla"], ufs["uf_nome"]))
    if st.session_state.get("f_uf", "Todas") not in ["Todas"] + list(nomes_uf):
        st.session_state["f_uf"] = "Todas"
    uf = sb.selectbox("Estado", ["Todas"] + list(nomes_uf), key="f_uf",
                      format_func=lambda s: "Todos" if s == "Todas" else nomes_uf[s])

    mun = ""
    if uf != "Todas":
        muns = dados.municipios(uf)
        nomes_mun = dict(zip(muns["cod_mun_res"], muns["municipio"]))
        if st.session_state.get("f_mun", "") not in [""] + list(nomes_mun):
            st.session_state["f_mun"] = ""
        mun = sb.selectbox("Município", [""] + list(nomes_mun), key="f_mun",
                           format_func=lambda c: "Todos" if c == "" else nomes_mun[c])
    else:
        st.session_state["f_mun"] = ""

    raca = sb.selectbox("Raça/cor da mulher", RACAS, key="f_raca")
    faixa = sb.selectbox("Faixa etária", ["Todas"] + op["faixas"], key="f_faixa")
    esc = sb.selectbox("Escolaridade", ["Todas"] + op["escolaridades"], key="f_esc")
    sb.button("Limpar filtros", on_click=limpar_filtros, use_container_width=True)
    sb.markdown(
        '<div class="nota" style="margin-top:14px">Óbito materno ocorre apenas em mulheres, por isso o painel '
        'não tem filtro de sexo. Os indicadores de parto vão até o nível de estado.</div>',
        unsafe_allow_html=True)

    return {
        "ano": None if ano.startswith("2022 a") else int(ano),
        "regiao": None if regiao == "Brasil" else regiao,
        "uf": None if uf == "Todas" else uf,
        "mun": mun or None,
        "raca": None if raca == "Todas" else raca,
        "faixa": None if faixa == "Todas" else faixa,
        "esc": None if esc == "Todas" else esc,
        "_uf_nome": nomes_uf.get(uf, ""),
        "_mun_nome": nomes_mun.get(mun, "") if mun else "",
    }


def descricao_recorte(f: dict) -> str:
    partes = [str(f["ano"]) if f["ano"] else "2022 a 2024"]
    lugar = f["_mun_nome"] or f["_uf_nome"] or f["regiao"] or "Brasil"
    partes.append(lugar)
    for k in ("raca", "faixa", "esc"):
        if f[k]:
            partes.append(f[k] + (" anos" if k == "faixa" else ""))
    return " · ".join(partes)


def chave_cache(f: dict) -> dict:
    return {k: v for k, v in f.items() if not k.startswith("_")}


# ---------------------------------------------------------------------------
# cabeçalho e KPIs
# ---------------------------------------------------------------------------
def cabecalho(f: dict):
    carga = dados.ultima_carga()
    carga_txt = carga.strftime("%d/%m/%Y") if carga is not None else "–"
    st.markdown(f"""
    <div class="topo">
      <div>
        <div class="rotulo">Painel epidemiológico · ODS 5 e ODS 18</div>
        <h1>Mortalidade materna e violência obstétrica no Brasil</h1>
        <div class="sub">{descricao_recorte(f)}</div>
      </div>
      <div class="meta">
        <span class="vivo"></span>Consulta ao banco em {dados.agora()}<br>
        Fonte: SIM e SINASC/DATASUS · carga de {carga_txt}
      </div>
    </div>""", unsafe_allow_html=True)


def kpis(f: dict):
    fc = chave_cache(f)
    m = dados.mortalidade(fc).iloc[0]
    p = dados.parto(fc).iloc[0]
    rmm = razao(m.obitos_rmm, m.nascidos_vivos, 1e5)

    ant_m = ant_p = None
    if f["ano"] and f["ano"] > 2022:
        fa = {**fc, "ano": f["ano"] - 1}
        ant_m, ant_p = dados.mortalidade(fa).iloc[0], dados.parto(fa).iloc[0]

    raca = com_rmm(dados.mortalidade(fc, ("raca_cor_agregada",), ("raca",))).set_index("raca_cor_agregada")
    branca = raca["rmm"].get("Branca", 0)
    rr_ind = razao(raca["rmm"].get("Indígena", 0), branca, 1)
    rr_neg = razao(raca["rmm"].get("Negra (preta + parda)", 0), branca, 1)
    aviso_ind = " · poucos casos" if raca["obitos_rmm"].get("Indígena", 0) < LIMITE_POUCOS else ""

    robson = razao(p.cesareas_robson_1a4, p.partos_robson_1a4)
    prenatal = razao(p.prenatal_7_mais, p.prenatal_informado)
    ano_ant = f["ano"] - 1 if f["ano"] else None
    nivel_parto = " · dado do estado" if f["mun"] else ""
    vezes_meta = razao(rmm, META_BRASIL, 1)
    pos_meta = min(100, META_BRASIL / max(rmm, META_BRASIL) * 100 / 1.15)
    pos_rmm = min(100, rmm / max(rmm, META_BRASIL) * 100 / 1.15)

    st.markdown(f"""
    <div class="kpis">
      <div class="kpi">
        <div class="t">Razão de mortalidade materna</div>
        <div class="v">{g.num(rmm)}<small>por 100 mil nascidos</small></div>
        {delta(rmm, razao(ant_m.obitos_rmm, ant_m.nascidos_vivos, 1e5) if ant_m is not None else None, "", True, ano_ant)}
        <div class="trilho"><i style="width:{pos_rmm:.0f}%"></i><b style="left:{pos_meta:.0f}%"></b></div>
        <div class="r">{g.num(m.obitos_rmm, 0)} óbitos · {g.num(vezes_meta)}x a meta de 2030 ({META_BRASIL})</div>
      </div>
      <div class="kpi">
        <div class="t">Risco das mulheres indígenas</div>
        <div class="v">{g.num(rr_ind)}<small>x o das brancas</small></div>
        <div class="d neutro">Mulheres negras: {g.num(rr_neg, 2)}x{aviso_ind}</div>
        <div class="r">Razão entre as RMM de cada grupo. 1,0 significa risco igual.</div>
      </div>
      <div class="kpi">
        <div class="t">Cesárea em baixo risco</div>
        <div class="v">{g.num(robson)}<small>%</small></div>
        {delta(robson, razao(ant_p.cesareas_robson_1a4, ant_p.partos_robson_1a4) if ant_p is not None else None, " p.p.", True, ano_ant)}
        <div class="r">Grupos 1 a 4 de Robson{nivel_parto}</div>
      </div>
      <div class="kpi">
        <div class="t">Pré-natal adequado</div>
        <div class="v">{g.num(prenatal)}<small>%</small></div>
        {delta(prenatal, razao(ant_p.prenatal_7_mais, ant_p.prenatal_informado) if ant_p is not None else None, " p.p.", False, ano_ant)}
        <div class="r">7 ou mais consultas{nivel_parto}</div>
      </div>
    </div>""", unsafe_allow_html=True)
    return m


# ---------------------------------------------------------------------------
# aba 1: mortalidade materna
# ---------------------------------------------------------------------------
def ranking_geografico(f: dict, caixa):
    fc = chave_cache(f)
    if f["uf"]:
        nivel, por, ignorar = "mun", ("cod_mun_res", "municipio"), ("mun",)
        pai = f["_uf_nome"]
    elif f["regiao"]:
        nivel, por, ignorar = "uf", ("uf_sigla", "uf_nome"), ("uf", "mun")
        pai = f["regiao"]
    else:
        nivel, por, ignorar = "regiao", ("regiao",), ("regiao", "uf", "mun")
        pai = "Brasil"

    df = com_rmm(dados.mortalidade(fc, por, ignorar))
    df = df[df["nascidos_vivos"] > 0]
    if nivel == "mun":
        df = df[df["municipio"] != "Município ignorado"].nlargest(15, "nascidos_vivos")
        cat, chave = "municipio", "cod_mun_res"
    elif nivel == "uf":
        cat, chave = "uf_nome", "uf_sigla"
    else:
        df = df[df["regiao"] != "Ignorada"]
        cat, chave = "regiao", "regiao"

    pai_df = dados.mortalidade(fc, (), ignorar).iloc[0]
    ref = razao(pai_df.obitos_rmm, pai_df.nascidos_vivos, 1e5)

    df = df.sort_values("rmm", kind="mergesort").reset_index(drop=True)
    st.session_state["_geo_nivel"] = nivel
    st.session_state["_geo_chaves"] = df[chave].tolist()

    trilha = ["Brasil"] + [x for x in (f["regiao"], f["_uf_nome"], f["_mun_nome"]) if x]
    col_a, col_b = caixa.columns([3, 1.4])
    col_a.markdown('<div class="trilha">' + " › ".join(
        f"<b>{t}</b>" if i == len(trilha) - 1 else t for i, t in enumerate(trilha)) + "</div>",
        unsafe_allow_html=True)
    if len(trilha) > 1:
        col_b.button("Voltar um nível", on_click=subir_nivel, use_container_width=True, key="btn_subir")

    destaque = None
    if nivel == "mun" and f["mun"]:
        destaque = [f["_mun_nome"]]
    fig = g.barras_horizontais(df, cat, "rmm", ref=ref, ref_rotulo=f"{pai} {g.num(ref)}",
                               poucos="poucos", hover_extra="hover", destaque=destaque)
    plot(caixa, fig, key="graf_geo", on_select=descer_nivel, selection_mode="points")
    dica = ("Clique em uma barra para descer de nível." if nivel != "mun"
            else "Os 15 municípios com mais nascimentos no recorte.")
    caixa.markdown(f'<div class="nota">{dica} Barras claras: menos de {LIMITE_POUCOS} óbitos, taxa instável.</div>',
                   unsafe_allow_html=True)


def aba_mortalidade(f: dict, total):
    fc = chave_cache(f)
    periodo = str(f["ano"]) if f["ano"] else "2022 a 2024"

    c1, c2 = st.columns([1.05, 1], gap="medium")
    mapa_df = com_rmm(dados.mortalidade(fc, ("uf_sigla", "uf_nome"), ("uf", "mun")))
    mapa_df = mapa_df[(mapa_df["uf_sigla"] != "IG") & (mapa_df["nascidos_vivos"] > 0)]
    with c1:
        caixa = cartao("RMM por estado", f"Óbitos maternos por 100 mil nascidos vivos · {periodo}")
        plot(caixa, g.mapa(mapa_df, "rmm", "RMM", hover_extra="hover", altura=380))
    with c2:
        caixa = cartao("Onde o risco é maior", "RMM por nível geográfico, comparada à média do nível acima")
        ranking_geografico(f, caixa)

    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="nota" style="margin:4px 0 6px">Perfil das mulheres. Barras claras indicam recortes '
                f'com menos de {LIMITE_POUCOS} óbitos, em que a taxa muda muito com um único caso.</div>',
                unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        caixa = cartao("RMM por raça/cor", "Linha pontilhada: mulheres brancas")
        separar = caixa.toggle("Separar pretas e pardas", key="t_separar")
        coluna = "raca_cor" if separar else "raca_cor_agregada"
        df = com_rmm(dados.mortalidade(fc, (coluna,), ("raca",)))
        df = df[df["nascidos_vivos"] > 0]
        branca = df.loc[df[coluna] == "Branca", "rmm"]
        topo = df[df[coluna] != "Ignorado"].nlargest(1, "rmm")[coluna].tolist()
        plot(caixa, g.barras_horizontais(df, coluna, "rmm", ref=branca.iloc[0] if len(branca) else None,
                                         ref_rotulo="Brancas", destaque=topo, poucos="poucos",
                                         hover_extra="hover", altura=250))
    with c2:
        caixa = cartao("RMM por faixa etária", "Idade da mulher, em anos · linha pontilhada: média do recorte")
        df = com_rmm(dados.mortalidade(fc, ("faixa_etaria", "faixa_ordem"), ("faixa",)))
        df = df[df["faixa_etaria"].isin(dados.opcoes()["faixas"])].sort_values("faixa_ordem")
        media = razao(total.obitos_rmm, total.nascidos_vivos, 1e5) if not f["faixa"] else None
        plot(caixa, g.barras_horizontais(df, "faixa_etaria", "rmm", poucos="poucos", hover_extra="hover",
                                         ref=media, ref_rotulo="Média" if media else "", ordenar=False,
                                         altura=288))
    with c3:
        caixa = cartao("RMM por escolaridade", "Escolaridade da mulher")
        df = com_rmm(dados.mortalidade(fc, ("escolaridade", "escolaridade_ordem"), ("esc",)))
        df = df[df["escolaridade"] != "Ignorado"].sort_values("escolaridade_ordem")
        df["escolaridade"] = df["escolaridade"].str.replace(r" \(.*\)", "", regex=True)
        plot(caixa, g.barras_horizontais(df, "escolaridade", "rmm", poucos="poucos", hover_extra="hover",
                                         ordenar=False, altura=288))

    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1], gap="medium")
    with c1:
        caixa = cartao("Evolução da RMM", "Linhas tracejadas: meta global (ODS) e meta do Brasil para 2030")
        df = com_rmm(dados.mortalidade(fc, ("ano",), ("ano",)))
        plot(caixa, g.evolucao(df, "rmm", metas=[(META_ODS, f"Meta ODS {META_ODS}"),
                                                  (META_BRASIL, f"Meta Brasil 2030: {META_BRASIL}")],
                               altura=300))
    with c2:
        caixa = cartao("Principais causas", "% dos óbitos maternos do recorte, por grupo de causa (CID-10)")
        df = dados.causas(fc)
        if df.empty:
            caixa.info("Nenhum óbito materno neste recorte.")
        else:
            df["pct"] = df["obitos"] / df["obitos"].sum() * 100
            df["hover"] = [f"<br>{o} óbitos" for o in df["obitos"]]
            plot(caixa, g.barras_horizontais(df, "grupo_causa", "pct", sufixo="%", hover_extra="hover",
                                             altura=300))

    caixa = cartao("Circunstâncias do óbito e violência",
                   f"{periodo} · óbitos tardios e associados a causas externas ficam fora da RMM oficial")
    fora = razao(total.obitos_fora_hospital, total.obitos_local_informado)
    sem = razao(total.obitos_sem_assistencia, total.obitos_assist_informada)
    caixa.markdown(f"""
    <div class="faixa">
      <div><div class="n">{g.num(fora)}%</div><div class="l">morreram fora do hospital (domicílio, via pública, aldeia)</div></div>
      <div><div class="n">{g.num(sem)}%</div><div class="l">sem assistência médica na doença que levou ao óbito</div></div>
      <div><div class="n">{g.num(total.obitos_tardios, 0)}</div><div class="l">óbitos maternos tardios (O96 e O97)</div></div>
      <div><div class="n">{g.num(total.obitos_causa_externa, 0)}</div><div class="l">óbitos de gestantes e puérperas por causa externa</div></div>
      <div><div class="n">{g.num(total.obitos_homicidio, 0)}</div><div class="l">homicídios (marcador O93.7)</div></div>
      <div><div class="n">{g.num(total.obitos_suicidio, 0)}</div><div class="l">suicídios (marcador O93.6)</div></div>
    </div>""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# aba 2: parto e violência obstétrica
# ---------------------------------------------------------------------------
def com_taxa(df: pd.DataFrame, num: str, den: str) -> pd.DataFrame:
    df["taxa"] = [razao(n, d) for n, d in zip(df[num], df[den])]
    df["hover"] = [f"<br>{g.num(n, 0)} de {g.num(d, 0)}" for n, d in zip(df[num], df[den])]
    df = df[df[den] > 0]
    return df


def aba_parto(f: dict):
    fc = chave_cache(f)
    if f["mun"]:
        st.info(f"Os dados de parto estão agregados por estado. Mostrando {f['_uf_nome']}.")

    escolha = st.segmented_control("Indicador", list(METRICAS_PARTO), default="Cesárea",
                                   key="f_metrica", label_visibility="collapsed") or "Cesárea"
    num, den, descricao, ref, ref_rotulo = METRICAS_PARTO[escolha]
    st.markdown(f'<div class="nota" style="margin:-4px 0 10px">{descricao}.</div>', unsafe_allow_html=True)

    total = dados.parto(fc).iloc[0]
    media = razao(total[num], total[den])

    c1, c2 = st.columns([1.05, 1], gap="medium")
    with c1:
        caixa = cartao(f"{escolha} por estado", "% em cada estado no recorte selecionado")
        df = com_taxa(dados.parto(fc, ("uf_sigla", "uf_nome"), ("uf",)), num, den)
        df = df[df["uf_sigla"] != "IG"]
        plot(caixa, g.mapa(df, "taxa", escolha, sufixo="%", hover_extra="hover", altura=380))
    with c2:
        caixa = cartao(f"{escolha} por raça/cor", "Linha pontilhada: média do recorte")
        df = com_taxa(dados.parto(fc, ("raca_cor",), ("raca",)), num, den)
        df = df[df["raca_cor"] != "Ignorado"]
        topo = df.nlargest(1, "taxa")["raca_cor"].tolist()
        plot(caixa, g.barras_horizontais(df, "raca_cor", "taxa", sufixo="%", ref=media,
                                         ref_rotulo=f"Média {g.num(media)}%", destaque=topo,
                                         hover_extra="hover", altura=380))

    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        caixa = cartao("Evolução", f"{escolha}, por ano" + (f" · {ref_rotulo}" if ref else ""))
        df = com_taxa(dados.parto(fc, ("ano",), ("ano",)), num, den)
        plot(caixa, g.evolucao(df, "taxa", sufixo="%", metas=[(ref, ref_rotulo)] if ref else [], altura=290))
    with c2:
        caixa = cartao("Por faixa etária", "Idade da mãe, em anos · linha pontilhada: média do recorte")
        df = com_taxa(dados.parto(fc, ("faixa_etaria", "faixa_ordem"), ("faixa",)), num, den)
        df = df[df["faixa_etaria"].isin(dados.opcoes()["faixas"])].sort_values("faixa_ordem")
        plot(caixa, g.colunas(df, "faixa_etaria", "taxa", sufixo="%", ref=media, altura=290))

    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        caixa = cartao("Por escolaridade", "Escolaridade da mãe")
        df = com_taxa(dados.parto(fc, ("escolaridade", "escolaridade_ordem"), ("esc",)), num, den)
        df = df[df["escolaridade"] != "Ignorado"].sort_values("escolaridade_ordem")
        df["escolaridade"] = df["escolaridade"].str.replace(r" \(.*\)", "", regex=True)
        plot(caixa, g.barras_horizontais(df, "escolaridade", "taxa", sufixo="%", hover_extra="hover",
                                         ordenar=False, altura=300))
    with c2:
        caixa = cartao("Gravidez até 14 anos",
                       "% dos nascidos vivos com mãe de 10 a 14 anos · os 10 estados com maior proporção")
        df = dados.parto(fc, ("uf_sigla", "uf_nome", "faixa_etaria"), ("faixa", "uf"))
        df = df[df["uf_sigla"] != "IG"]
        tab = df.pivot_table(index=["uf_sigla", "uf_nome"], columns="faixa_etaria",
                             values="nascidos_vivos", aggfunc="sum", fill_value=0)
        tab = pd.DataFrame({
            "meninas": tab.get("10-14", 0),
            "total": tab.sum(axis=1),
        }).reset_index()
        tab = tab[tab["total"] > 0]
        tab["pct"] = tab["meninas"] / tab["total"] * 100
        tab["hover"] = [f"<br>{g.num(n, 0)} nascidos de mães de 10 a 14 anos" for n in tab["meninas"]]
        caixa.markdown(f'<div class="nota" style="margin:0">{g.num(tab["meninas"].sum(), 0)} nascidos de mães '
                       f'de 10 a 14 anos no recorte. Toda gravidez antes dos 14 anos configura estupro de '
                       f'vulnerável.</div>', unsafe_allow_html=True)
        plot(caixa, g.barras_horizontais(tab.nlargest(10, "pct"), "uf_nome", "pct", sufixo="%", casas=2,
                                         hover_extra="hover", altura=300))


# ---------------------------------------------------------------------------
# aba 3: metodologia
# ---------------------------------------------------------------------------
def aba_metodologia():
    c1, c2 = st.columns([1.2, 1], gap="large")
    with c1:
        st.markdown("""
#### Como os indicadores são calculados

| Indicador | Fórmula |
|---|---|
| Razão de mortalidade materna (RMM) | óbitos maternos (CID-10 O00–O99, exceto O96 e O97) ÷ nascidos vivos × 100.000 |
| Risco racial | RMM do grupo ÷ RMM das mulheres brancas |
| Cesárea | cesáreas ÷ partos com tipo informado |
| Cesárea em baixo risco | cesáreas nos grupos 1 a 4 de Robson ÷ partos com tipo informado nesses grupos |
| Cesárea antes do trabalho de parto | cesáreas antes do trabalho de parto ÷ total de cesáreas |
| Parto induzido | partos induzidos ÷ nascimentos com o campo informado |
| Pré-natal adequado | nascidos com 7 ou mais consultas ÷ nascidos com consultas informadas |

**Regras gerais**

- Numerador e denominador sempre com o mesmo recorte de filtros.
- Em períodos somados, a taxa é soma dos óbitos ÷ soma dos nascidos, nunca a média das taxas anuais.
- Registros com campo ignorado ficam fora do denominador dos percentuais.
- Recortes com menos de 10 óbitos aparecem destacados: a taxa varia muito com um único caso.
- Óbitos tardios (O96, O97) e associados a causa externa (marcador O93) não entram na RMM e aparecem à parte.
- SIM e SINASC não se ligam por pessoa: os dois eixos são lidos lado a lado.
""")
    with c2:
        st.markdown(f"""
#### Dados

- **SIM** (Sistema de Informações sobre Mortalidade) e **SINASC** (Sistema de Informações sobre Nascidos Vivos), DATASUS, 2022 a 2024.
- Municípios e estados: API de Localidades do IBGE.
- Totais validados contra o Painel de Monitoramento da Mortalidade Materna do Ministério da Saúde e o TabNet.

#### Arquitetura

Scripts Python (ETL) → PostgreSQL na Aiven, criado com Terraform, em modelo estrela → views de indicadores → este painel, que consulta o banco com um usuário somente leitura.

Código e documentação: [{REPOSITORIO.split('/')[-1]}]({REPOSITORIO})
""")


# ---------------------------------------------------------------------------
def main():
    _CARTOES[0] = 0
    st.markdown(CSS, unsafe_allow_html=True)
    try:
        op = dados.opcoes()
        f = barra_lateral(op)
        cabecalho(f)
        total = kpis(f)
        aba1, aba2, aba3 = st.tabs(["Mortalidade materna", "Parto e violência obstétrica", "Metodologia"])
        with aba1:
            aba_mortalidade(f, total)
        with aba2:
            aba_parto(f)
        with aba3:
            aba_metodologia()
    except BancoIndisponivel as erro:
        st.error("Não foi possível consultar o banco de dados.")
        if "permission" in str(erro).lower() or "does not exist" in str(erro).lower():
            st.markdown("As views de indicadores ou as permissões do usuário do painel não estão no banco. "
                        "Rode `python etl/fase3/11_indicadores.py` e recarregue a página.")
        else:
            st.markdown(
                "O plano gratuito da Aiven desliga o serviço após um período sem uso. "
                "Ligue o serviço no console da Aiven (botão **Power on**) e recarregue a página em alguns minutos.")
        st.caption(f"Detalhe técnico: {erro}")


main()
