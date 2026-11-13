"""Gráficos do painel (Plotly) com a identidade visual do projeto."""
import json
from functools import lru_cache
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

VINHO = "#8C1D40"
VINHO_CLARO = "#D9A3B5"
CINZA = "#B9C0CB"
CINZA_CLARO = "#E3E7ED"
AZUL_REF = "#1F6F8B"
AMBAR = "#B7791F"
TEXTO = "#1B2333"
TEXTO_2 = "#5B6475"
GRADE = "#EDF0F4"
FONTE = "Inter, 'Segoe UI', Roboto, Arial, sans-serif"
ESCALA = [[0, "#F8EEF2"], [0.35, "#E2AFC0"], [0.7, "#B04A6E"], [1, "#5E0F2A"]]

GEOJSON = Path(__file__).parent / "assets" / "br_uf.geojson"


def num(v: float, casas: int = 1) -> str:
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _base(fig: go.Figure, altura: int, legenda: bool = False) -> go.Figure:
    fig.update_layout(
        height=altura,
        margin=dict(l=4, r=12, t=8, b=4),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONTE, size=12.5, color=TEXTO_2),
        separators=",.",
        showlegend=legenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=12)),
        hoverlabel=dict(bgcolor="white", bordercolor=CINZA, font=dict(family=FONTE, color=TEXTO, size=12.5)),
        barcornerradius=3,
        bargap=0.32,
        dragmode=False,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showline=False, ticks="", fixedrange=True)
    fig.update_yaxes(gridcolor=GRADE, zeroline=False, showline=False, ticks="", fixedrange=True)
    return fig


def barras_horizontais(df: pd.DataFrame, cat: str, val: str, sufixo: str = "", casas: int = 1,
                       ref: float | None = None, ref_rotulo: str = "", destaque: list | None = None,
                       poucos: str | None = None, hover_extra: str | None = None,
                       altura: int | None = None, ordenar: bool = True) -> go.Figure:
    df = (df.sort_values(val, ascending=True, kind="mergesort") if ordenar else df.iloc[::-1]).reset_index(drop=True)
    poucos = df[poucos].astype(bool) if poucos else pd.Series(False, index=df.index)
    cores = [
        CINZA_CLARO if p else (VINHO if destaque is None or c in destaque else CINZA)
        for c, p in zip(df[cat], poucos)
    ]
    textos = [num(v, casas) + sufixo for v in df[val]]
    avisos = ["<br><i>menos de 10 óbitos: taxa instável</i>" if p else "" for p in poucos]
    extra = list(df[hover_extra]) if hover_extra else [""] * len(df)
    fig = go.Figure(go.Bar(
        x=df[val], y=df[cat], orientation="h", marker_color=cores,
        text=textos, textposition="outside", cliponaxis=False,
        textfont=dict(color=TEXTO, size=12.5),
        customdata=list(zip(textos, extra, avisos)),
        hovertemplate="<b>%{y}</b><br>%{customdata[0]}%{customdata[1]}%{customdata[2]}<extra></extra>",
    ))
    maximo = max(df[val].max(), ref or 0)
    fig.update_xaxes(visible=False, range=[0, maximo * 1.22 if maximo else 1])
    fig.update_yaxes(showgrid=False, tickfont=dict(color=TEXTO, size=12.5))
    if ref is not None:
        fig.add_vline(x=ref, line=dict(color=AZUL_REF, width=1.5, dash="dot"))
        fig.add_annotation(x=ref, y=1.0, yref="paper", yanchor="bottom", text=ref_rotulo, showarrow=False,
                           font=dict(color=AZUL_REF, size=11.5), xanchor="left", xshift=4)
    fig = _base(fig, altura or max(180, 36 * len(df) + 40))
    if ref is not None:
        fig.update_layout(margin=dict(t=26))
    return fig


def colunas(df: pd.DataFrame, cat: str, val: str, sufixo: str = "", casas: int = 1,
            ref: float | None = None, ref_rotulo: str = "", poucos: str | None = None,
            altura: int = 260) -> go.Figure:
    poucos = df[poucos].astype(bool) if poucos else pd.Series(False, index=df.index)
    cores = [CINZA_CLARO if p else VINHO for p in poucos]
    fig = go.Figure(go.Bar(
        x=df[cat], y=df[val], marker_color=cores,
        text=[num(v, casas) + sufixo for v in df[val]], textposition="outside", cliponaxis=False,
        textfont=dict(color=TEXTO, size=12),
        hovertemplate="<b>%{x}</b><br>%{text}<extra></extra>",
    ))
    fig.update_yaxes(visible=False, range=[0, max(df[val].max(), ref or 0) * 1.25 or 1])
    fig.update_xaxes(type="category", tickfont=dict(color=TEXTO, size=11.5), tickangle=0)
    if ref is not None:
        fig.add_hline(y=ref, line=dict(color=AZUL_REF, width=1.5, dash="dot"))
    return _base(fig, altura)


def evolucao(df: pd.DataFrame, val: str, sufixo: str = "", casas: int = 1,
             metas: list[tuple[float, str]] = (), altura: int = 260) -> go.Figure:
    anos = df["ano"].astype(str)
    fig = go.Figure(go.Scatter(
        x=anos, y=df[val], mode="lines+markers+text",
        line=dict(color=VINHO, width=3), marker=dict(size=9, color=VINHO, line=dict(color="white", width=2)),
        text=[num(v, casas) + sufixo for v in df[val]], textposition="top center",
        textfont=dict(color=TEXTO, size=12.5),
        hovertemplate="<b>%{x}</b><br>%{text}<extra></extra>",
    ))
    topo = max([df[val].max()] + [m for m, _ in metas]) * 1.25
    for valor, rotulo in metas:
        fig.add_hline(y=valor, line=dict(color=AMBAR, width=1.5, dash="dash"))
        fig.add_annotation(x=1, xref="paper", y=valor, text=rotulo, showarrow=False, xanchor="right",
                           yanchor="bottom", font=dict(color=AMBAR, size=11.5))
    fig.update_xaxes(type="category", tickfont=dict(color=TEXTO), range=[-0.35, len(df) - 0.65])
    fig.update_yaxes(range=[0, topo], tickformat=",.0f")
    return _base(fig, altura)


@lru_cache(maxsize=1)
def _geojson() -> dict:
    return json.loads(GEOJSON.read_text(encoding="utf-8"))


def mapa(df: pd.DataFrame, val: str, rotulo: str, sufixo: str = "", casas: int = 1,
         hover_extra: str | None = None, altura: int = 420) -> go.Figure:
    extra = list(df[hover_extra]) if hover_extra else [""] * len(df)
    fig = go.Figure(go.Choropleth(
        geojson=_geojson(), featureidkey="properties.sigla",
        locations=df["uf_sigla"], z=df[val], colorscale=ESCALA,
        marker_line_color="white", marker_line_width=0.8,
        customdata=list(zip(df["uf_nome"], [num(v, casas) + sufixo for v in df[val]], extra)),
        hovertemplate="<b>%{customdata[0]}</b><br>" + rotulo + ": %{customdata[1]}%{customdata[2]}<extra></extra>",
        colorbar=dict(orientation="h", thickness=8, len=0.55, x=0.5, xanchor="center", y=-0.02,
                      outlinewidth=0, tickfont=dict(size=11, color=TEXTO_2), ticksuffix=sufixo),
    ))
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig = _base(fig, altura)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    return fig
