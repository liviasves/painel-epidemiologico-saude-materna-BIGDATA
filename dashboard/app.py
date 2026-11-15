import pandas as pd
import streamlit as st

import dados
import graficos as g
from dados import BancoIndisponivel

st.set_page_config(page_title="Saúde Materna | Painel Epidemiológico", layout="wide",
                   initial_sidebar_state="expanded")

LIMITE_POUCOS = 10
META_BRASIL, META_ODS = 30, 70
REPOSITORIO = "https://github.com/liviasves/painel-epidemiologico-saude-materna-BIGDATA"

RACAS = ["Todas", "Preta", "Parda", "Branca", "Indígena", "Amarela"]

PLURAL = {"Indígena": "indígenas", "Preta": "pretas", "Parda": "pardas", "Branca": "brancas",
          "Amarela": "amarelas"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, select { font-family: Inter, 'Segoe UI', Roboto, Arial, sans-serif; }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
[data-testid="stHeader"] { background: transparent; }
.stApp { background: #F3F4F7; }
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1480px; }

[data-testid="stSidebar"] { background: #16202E; }
[data-testid="stSidebar"] * { color: #E7EAF0; }
[data-testid="stSidebar"] .stSelectbox label p { font-size: 11.5px; font-weight: 600; letter-spacing: .06em;
    text-transform: uppercase; color: #9AA4B5 !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div { background: #222D3D; border-color: #2F3B4D; }
[data-testid="stSidebar"] [data-baseweb="select"] div { color: #FFFFFF; }
[data-testid="stSidebar"] .stButton button { background: transparent; border: 1px solid #3A4659; color: #E7EAF0; }
[data-testid="stSidebar"] .stButton button:hover { border-color: #D46A8C; color: #FFFFFF; }
.marca { font-size: 12px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: #D46A8C !important;
         padding-bottom: 14px; margin-bottom: 14px; border-bottom: 1px solid #2F3B4D; }

.topo { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px;
        background: #16202E; border-radius: 12px; padding: 18px 24px; margin-bottom: 16px; }
.topo .rotulo { font-size: 11px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: #D46A8C; }
.topo h1 { font-size: 22px; font-weight: 700; color: #FFFFFF; margin: 4px 0 2px; padding: 0; line-height: 1.25; }
.topo .sub { font-size: 13px; color: #9AA4B5; }
.topo .meta { font-size: 12px; color: #9AA4B5; text-align: right; line-height: 1.7; }
.topo .vivo { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #32D583; margin-right: 6px; }

.kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 4px 0 14px; }
@media (max-width: 1000px) { .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.kpi { display: flex; align-items: center; gap: 14px; background: #FFFFFF; border-radius: 12px; padding: 14px 16px;
       box-shadow: 0 1px 3px rgba(16, 24, 40, .08); min-width: 0; }
.kpi > div:last-child { min-width: 0; }
.kpi .ic { flex: none; width: 46px; height: 46px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.kpi .ic svg { width: 22px; height: 22px; }
.kpi .t { font-size: 12px; color: #6B7385; }
.kpi .v { font-size: 24px; font-weight: 700; color: #16202E; line-height: 1.2; font-variant-numeric: tabular-nums; }
.kpi .r { font-size: 11.5px; color: #6B7385; margin-top: 1px; }

[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [class*="st-key-cartao"]) {
    background: #FFFFFF; border: none !important; border-radius: 12px;
    box-shadow: 0 1px 3px rgba(16, 24, 40, .08);
}
[class*="st-key-cartao"] { gap: 0.3rem; }
.card-titulo { font-size: 14px; font-weight: 700; color: #16202E; margin: 2px 0 0; letter-spacing: .01em; }
.card-sub { font-size: 12px; color: #6B7385; margin: 1px 0 4px; }
.trilha { font-size: 12.5px; color: #6B7385; margin: 6px 0 2px; }
.trilha b { color: #16202E; }

.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #DDE1E8; }
.stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 14px; padding: 10px 14px; color: #6B7385; }
.stTabs [aria-selected="true"] { color: #8C1D40; }
[data-testid="stExpander"] { background: #FFFFFF; border: none; border-radius: 12px; box-shadow: 0 1px 3px rgba(16, 24, 40, .08); }
.nota { font-size: 12px; color: #6B7385; line-height: 1.5; margin: 2px 0 8px; }
</style>
"""


def razao(n, d, fator=100.0):
    return (n * fator / d) if d else 0.0


_CARTOES = [0]


def cartao(titulo: str, sub: str = ""):
    _CARTOES[0] += 1
    caixa = st.container(border=True, key=f"cartao_{_CARTOES[0]}")
    caixa.markdown(f'<div class="card-titulo">{titulo}</div>'
                   + (f'<div class="card-sub">{sub}</div>' if sub else ''), unsafe_allow_html=True)
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
    sb.markdown('<div class="marca">Saúde materna · Brasil</div>', unsafe_allow_html=True)

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


def texto_negras(rr: float) -> str:
    dif = (rr - 1) * 100
    if abs(dif) < 1:
        return "Mulheres negras morrem na mesma proporção que as brancas."
    return f"Mulheres negras morrem {g.num(abs(dif), 0)}% {'a mais' if dif > 0 else 'a menos'} que as brancas."


ICONES = {
    "pulso": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "pessoas": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>'
               '<path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "local": '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
    "cruz": '<rect x="3" y="3" width="18" height="18" rx="3"/><line x1="12" y1="8" x2="12" y2="16"/>'
            '<line x1="8" y1="12" x2="16" y2="12"/>',
    "escudo": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "agenda": '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/>'
              '<line x1="8" y1="2" x2="8" y2="6"/><polyline points="9 15 11 17 15 13"/>',
    "grafico": '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>'
               '<line x1="6" y1="20" x2="6" y2="14"/>',
    "pessoa": '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
}


def card(titulo: str, valor: str, detalhe: str = "", icone: str = "pulso", cor: str = "#8C1D40") -> str:
    svg = (f'<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" '
           f'stroke-linejoin="round">{ICONES[icone]}</svg>')
    return (f'<div class="kpi"><div class="ic" style="background:{cor}">{svg}</div>'
            f'<div><div class="t">{titulo}</div><div class="v">{valor}</div>'
            + (f'<div class="r">{detalhe}</div>' if detalhe else "") + "</div></div>")


def variacao(serie: dict, ano, tipo: str = "rel", maior_ruim: bool = True) -> str:
    if ano:
        atual, base, rotulo = serie.get(ano), serie.get(ano - 1), f"vs. {ano - 1}"
    else:
        anos = sorted(serie)
        atual, base, rotulo = serie.get(anos[-1]), serie.get(anos[0]), f"{anos[-1]} vs. {anos[0]}"
    if atual is None or not base:
        return ""
    dif = (atual / base - 1) * 100 if tipo == "rel" else atual - base
    unidade = "%" if tipo == "rel" else " p.p."
    cor = "#B42318" if (dif > 0) == maior_ruim else "#067647"
    if abs(dif) < 0.05:
        cor, sinal = "#6B7385", ""
    else:
        sinal = "+" if dif > 0 else "−"
    return f'<b style="color:{cor}">{sinal}{g.num(abs(dif))}{unidade}</b> {rotulo}'


def linha_kpis(cards: list):
    st.markdown('<div class="kpis">' + "".join(cards) + "</div>", unsafe_allow_html=True)


def kpis_mortalidade(f: dict):
    fc = chave_cache(f)
    ano = f["ano"]
    m = dados.mortalidade(fc).iloc[0]
    m_ano = com_rmm(dados.mortalidade(fc, ("ano",), ("ano",)))
    mortes_ano = {int(a): v for a, v in zip(m_ano["ano"], m_ano["obitos_rmm"])}

    ufs = com_rmm(dados.mortalidade(fc, ("uf_sigla", "uf_nome"), ("regiao", "uf", "mun")))
    ufs = ufs[(ufs["uf_sigla"] != "IG") & (ufs["nascidos_vivos"] > 0)]
    sigla = f["uf"] or "BA"
    alvo = ufs[ufs["uf_sigla"] == sigla].iloc[0]
    uf_ano = com_rmm(dados.mortalidade({**fc, "regiao": None, "uf": sigla, "mun": None}, ("ano",), ("ano",)))
    rmm_uf_ano = {int(a): v for a, v in zip(uf_ano["ano"], uf_ano["rmm"])}

    raca = com_rmm(dados.mortalidade(fc, ("raca_cor",), ("raca",))).set_index("raca_cor")
    branca = raca["rmm"].get("Branca", 0)
    validos = raca[(raca.index != "Ignorado") & (raca.index != "Branca") & ~raca["poucos"]]
    if len(validos) and branca:
        grupo = validos["rmm"].idxmax()
        c_raca = card("Risco racial", f"{g.num(validos['rmm'].max() / branca)}x",
                      f"{PLURAL.get(grupo, grupo)} x brancas", "pessoas", "#6941C6")
    else:
        c_raca = card("Risco racial", "–", "poucos casos", "pessoas", "#6941C6")

    causas = dados.causas_detalhe(fc)
    if len(causas):
        pct = causas.iloc[0].obitos / causas["obitos"].sum() * 100
        c_causa = card("Principal causa", f"{g.num(pct)}%", rotulo_causa(causas.iloc[0].descricao, 200),
                       "cruz", "#B7791F")
    else:
        c_causa = card("Principal causa", "–", "", "cruz", "#B7791F")

    linha_kpis([
        card("Mortes maternas", g.num(m.obitos_rmm, 0), variacao(mortes_ano, ano), "pulso", "#8C1D40"),
        c_raca,
        card(f"{alvo.uf_nome} · a cada 100 mil", g.num(alvo.rmm), variacao(rmm_uf_ano, ano), "local", "#1F6F8B"),
        c_causa,
    ])


def kpis_parto(f: dict):
    fc = chave_cache(f)
    ano = f["ano"]
    p = dados.parto(fc).iloc[0]
    p_ano = dados.parto(fc, ("ano",), ("ano",))
    anos = [int(a) for a in p_ano["ano"]]

    def serie(num, den):
        return {a: razao(n, d) for a, n, d in zip(anos, p_ano[num], p_ano[den])}

    fx = dados.parto(fc, ("ano", "faixa_etaria"), ("ano", "faixa"))
    fx["adol"] = fx["faixa_etaria"].isin(["10-14", "15-19"]) * fx["nascidos_vivos"]
    tot = fx.groupby("ano")[["adol", "nascidos_vivos"]].sum()
    adol_ano = {int(a): razao(r.adol, r.nascidos_vivos) for a, r in tot.iterrows()}
    if ano:
        adol = adol_ano.get(ano, 0)
    else:
        adol = razao(tot["adol"].sum(), tot["nascidos_vivos"].sum())

    linha_kpis([
        card("Cesárea em baixo risco", f"{g.num(razao(p.cesareas_robson_1a4, p.partos_robson_1a4))}%",
             variacao(serie("cesareas_robson_1a4", "partos_robson_1a4"), ano, "pp"), "escudo", "#8C1D40"),
        card("Pré-natal completo", f"{g.num(razao(p.prenatal_7_mais, p.prenatal_informado))}%",
             variacao(serie("prenatal_7_mais", "prenatal_informado"), ano, "pp", maior_ruim=False),
             "agenda", "#1F6F8B"),
        card("Cesárea", f"{g.num(razao(p.cesareas, p.partos_tipo_informado))}%",
             variacao(serie("cesareas", "partos_tipo_informado"), ano, "pp"), "grafico", "#6941C6"),
        card("Mães adolescentes", f"{g.num(adol)}%", variacao(adol_ano, ano, "pp"), "pessoa", "#B7791F"),
    ])


METRICAS_PARTO = {
    "Cesárea em baixo risco": ("cesareas_robson_1a4", "partos_robson_1a4", "partos"),
    "Pré-natal completo": ("prenatal_7_mais", "prenatal_informado", "mães"),
    "Cesárea total": ("cesareas", "partos_tipo_informado", "partos"),
}


def ranking_geografico(f: dict, col: str, casas: int):
    fc = chave_cache(f)
    if f["uf"]:
        nivel, por, ignorar, pai = "mun", ("cod_mun_res", "municipio"), ("mun",), f["_uf_nome"]
    elif f["regiao"]:
        nivel, por, ignorar, pai = "uf", ("uf_sigla", "uf_nome"), ("uf", "mun"), f["regiao"]
    else:
        nivel, por, ignorar, pai = "regiao", ("regiao",), ("regiao", "uf", "mun"), "Brasil"

    df = com_rmm(dados.mortalidade(fc, por, ignorar))
    df = df[df["nascidos_vivos"] > 0]
    if nivel == "mun":
        df = df[df["municipio"] != "Município ignorado"].nlargest(10, "nascidos_vivos")
        cat, chave = "municipio", "cod_mun_res"
    elif nivel == "uf":
        cat, chave = "uf_nome", "uf_sigla"
    else:
        df = df[df["regiao"] != "Ignorada"]
        cat, chave = "regiao", "regiao"

    df = df.sort_values(col, kind="mergesort").reset_index(drop=True)
    st.session_state["_geo_nivel"] = nivel
    st.session_state["_geo_chaves"] = df[chave].tolist()

    nome_nivel = {"regiao": "Ranking das regiões", "uf": f"Ranking dos estados · {pai}",
                  "mun": f"Ranking dos municípios · {pai}"}[nivel]
    ref = None
    if col == "rmm":
        pai_df = dados.mortalidade(fc, (), ignorar).iloc[0]
        ref = razao(pai_df.obitos_rmm, pai_df.nascidos_vivos, 1e5)
    caixa = cartao(nome_nivel, "Os 10 municípios com mais nascimentos" if nivel == "mun" else "")

    trilha = ["Brasil"] + [x for x in (f["regiao"], f["_uf_nome"], f["_mun_nome"]) if x]
    if len(trilha) > 1:
        col_a, col_b = caixa.columns([3, 1.4])
        col_a.markdown('<div class="trilha">' + " › ".join(
            f"<b>{t}</b>" if i == len(trilha) - 1 else t for i, t in enumerate(trilha)) + "</div>",
            unsafe_allow_html=True)
        col_b.button("Voltar um nível", on_click=subir_nivel, use_container_width=True, key="btn_subir")

    destaque = [f["_mun_nome"]] if nivel == "mun" and f["mun"] else None
    fig = g.barras_horizontais(df, cat, col, casas=casas, ref=ref, ref_rotulo=f"{pai} {g.num(ref)}" if ref else "",
                               poucos="poucos" if col == "rmm" else None, hover_extra="hover",
                               destaque=destaque, altura=392)
    plot(caixa, fig, key="graf_geo", on_select=descer_nivel, selection_mode="points")


def rotulo_causa(texto: str, largura: int = 34) -> str:
    for trecho in (" complicando a gravidez, o parto e o puerpério", " complicando a gravidez, o parto e o puerpério"):
        texto = texto.replace(trecho, "")
    linhas, atual = [], ""
    for palavra in texto.split():
        if atual and len(atual) + len(palavra) + 1 > largura:
            linhas.append(atual)
            atual = palavra
        else:
            atual = f"{atual} {palavra}".strip()
    linhas.append(atual)
    return "<br>".join(linhas[:3])


def painel(f: dict):
    fc = chave_cache(f)

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        df = com_rmm(dados.mortalidade(fc, ("ano",), ("ano",)))
        df["ano"] = df["ano"].astype(int).astype(str)
        df["hover"] = [f"<br>{g.num(t)} a cada 100 mil nascimentos" for t in df["rmm"]]
        pior = df.nlargest(1, "obitos_rmm").iloc[0]
        caixa = cartao("Mortes maternas por ano", "Número de mortes")
        plot(caixa, g.colunas(df, "ano", "obitos_rmm", casas=0, destaque=[pior.ano],
                              hover_extra="hover", altura=340))
    with c2:
        df = com_rmm(dados.mortalidade(fc, ("raca_cor",), ("raca",)))
        df = df[df["nascidos_vivos"] > 0]
        branca = df.loc[df["raca_cor"] == "Branca", "rmm"]
        topo = df[(df["raca_cor"] != "Ignorado") & ~df["poucos"]].nlargest(1, "rmm")
        caixa = cartao("Risco racial: mortes por raça/cor", "A cada 100 mil nascimentos · linha pontilhada: brancas")
        plot(caixa, g.barras_horizontais(df, "raca_cor", "rmm", ref=branca.iloc[0] if len(branca) else None,
                                         ref_rotulo="Brancas", destaque=topo["raca_cor"].tolist(), poucos="poucos",
                                         hover_extra="hover", altura=340))

    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1.05, 1], gap="medium")
    with c1:
        df = com_rmm(dados.mortalidade(fc, ("uf_sigla", "uf_nome"), ("uf", "mun")))
        df = df[(df["uf_sigla"] != "IG") & (df["nascidos_vivos"] > 0)]
        caixa = cartao("Mortes por estado", "A cada 100 mil nascimentos")
        plot(caixa, g.mapa(df, "rmm", "Mortes a cada 100 mil nascimentos", hover_extra="hover", altura=420))
    with c2:
        ranking_geografico(f, "rmm", 1)

    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    df = dados.causas_detalhe(fc)
    if df.empty:
        cartao("Principais causas", "Nenhuma morte materna neste recorte.")
        return
    df["pct"] = df["obitos"] / df["obitos"].sum() * 100
    top = df.head(5).copy()
    top["causa"] = [rotulo_causa(c) for c in top["descricao"]]
    top["hover"] = [f"<br>{c}<br>{o} mortes" for c, o in zip(top["descricao"], top["obitos"])]
    caixa = cartao("5 principais causas", "% das mortes maternas")
    plot(caixa, g.barras_horizontais(top, "causa", "pct", sufixo="%", hover_extra="hover", altura=300))


def taxa_parto(df: pd.DataFrame, num: str, den: str) -> pd.DataFrame:
    df = df[df[den] > 0].copy()
    df["taxa"] = [razao(n, d) for n, d in zip(df[num], df[den])]
    df["hover"] = [f"<br>{g.num(n, 0)} de {g.num(d, 0)} partos" for n, d in zip(df[num], df[den])]
    return df


def aba_violencia(f: dict):
    fc = chave_cache(f)
    if f["mun"]:
        st.info(f"Os dados de parto estão agregados por estado. Mostrando {f['_uf_nome']}.")

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        caixa = st.container(border=True, key="cartao_parto_raca")
        escolha = caixa.segmented_control("Indicador", list(METRICAS_PARTO), default="Cesárea em baixo risco",
                                          key="f_metrica", label_visibility="collapsed") or "Cesárea em baixo risco"
        num, den, unidade = METRICAS_PARTO[escolha]
        df = taxa_parto(dados.parto(fc, ("raca_cor",), ("raca",)), num, den)
        df = df[df["raca_cor"] != "Ignorado"]
        df["hover"] = [h.replace("partos", unidade) for h in df["hover"]]
        total = dados.parto(fc, (), ("raca",)).iloc[0]
        media = razao(total[num], total[den])
        alvo = df.nsmallest(1, "taxa") if num == "prenatal_7_mais" else df.nlargest(1, "taxa")
        caixa.markdown(f'<div class="card-titulo">{escolha}, por raça/cor</div>'
                       f'<div class="card-sub">% de {unidade} · linha pontilhada: média de todas as mães</div>',
                       unsafe_allow_html=True)
        plot(caixa, g.barras_horizontais(df, "raca_cor", "taxa", sufixo="%", ref=media,
                                         ref_rotulo=f"Média {g.num(media)}%", destaque=alvo["raca_cor"].tolist(),
                                         hover_extra="hover", altura=330))
    with c2:
        df = taxa_parto(dados.parto(fc, ("ano",), ("ano",)), "cesareas", "partos_tipo_informado")
        caixa = cartao("Cesárea por ano", "% dos partos · linha tracejada: limite da OMS (15%)")
        plot(caixa, g.evolucao(df, "taxa", sufixo="%", metas=[(15, "OMS: até 15%")], altura=372))

    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    df = dados.parto(fc, ("uf_sigla", "uf_nome", "faixa_etaria"), ("faixa", "uf"))
    df = df[df["uf_sigla"] != "IG"]
    tab = df.pivot_table(index=["uf_sigla", "uf_nome"], columns="faixa_etaria",
                         values="nascidos_vivos", aggfunc="sum", fill_value=0)
    tab = pd.DataFrame({"m10": tab.get("10-14", 0), "m15": tab.get("15-19", 0),
                        "total": tab.sum(axis=1)}).reset_index()
    tab = tab[tab["total"] > 0]
    tab["p10"] = tab["m10"] / tab["total"] * 100
    tab["p15"] = tab["m15"] / tab["total"] * 100
    tab["pct"] = tab["p10"] + tab["p15"]
    caixa = cartao("Mães adolescentes: 5 estados com maior proporção", "% dos nascimentos com mãe de 10 a 19 anos")
    plot(caixa, g.barras_empilhadas(tab.nlargest(5, "pct"), "uf_nome", [("p10", "10 a 14 anos", "#5E0F2A"),
                                                                       ("p15", "15 a 19 anos", "#C76A8A")],
                                    altura=300))

def metodologia():
    with st.expander("Como os números são calculados"):
        st.markdown(f"""
- **Mortes maternas:** mortes por causas da gravidez, do parto ou do pós-parto até 42 dias (CID-10 O00–O99, exceto O96 e O97). Fonte: SIM/DATASUS.
- **Taxa a cada 100 mil nascimentos (RMM):** mortes maternas ÷ nascidos vivos × 100.000, sempre com o mesmo recorte de filtros nos dois números. Fonte dos nascimentos: SINASC/DATASUS.
- **Desigualdade racial:** taxa de cada grupo ÷ taxa das mulheres brancas.
- **Pré-natal completo:** mães com 7 ou mais consultas ÷ mães com o número de consultas informado.
- **Cesárea em baixo risco:** cesáreas nos grupos 1 a 4 da classificação de Robson ÷ partos desses grupos.
- **Taxa de cesárea:** cesáreas ÷ partos com o tipo informado.
- **Mães adolescentes:** nascidos de mães de 10 a 19 anos ÷ total de nascidos, separando 10 a 14 e 15 a 19 anos. Os dados de parto vão até o nível de estado.
- Recortes com menos de {LIMITE_POUCOS} mortes aparecem destacados, porque um único caso muda muito a taxa.
- Totais validados contra o Painel de Monitoramento da Mortalidade Materna do Ministério da Saúde e o TabNet.

Código e documentação: [{REPOSITORIO.split('/')[-1]}]({REPOSITORIO})
""")


def main():
    _CARTOES[0] = 0
    st.markdown(CSS, unsafe_allow_html=True)
    try:
        op = dados.opcoes()
        f = barra_lateral(op)
        cabecalho(f)
        aba1, aba2 = st.tabs(["Mortalidade materna", "Violência obstétrica"])
        with aba1:
            kpis_mortalidade(f)
            painel(f)
        with aba2:
            kpis_parto(f)
            aba_violencia(f)
        metodologia()
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