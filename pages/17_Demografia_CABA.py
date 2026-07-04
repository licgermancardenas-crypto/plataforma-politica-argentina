"""
Demografía CABA – Página 17
Fuentes: DGEyC GCBA · Censo 2010 · Encuesta Anual Hogares · Registro Civil
"""
import json, os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import loader
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Demografía CABA", page_icon="👥", layout="wide")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@st.cache_data
def load():
    with open(os.path.join(BASE, "data", "demografia_caba.json"), encoding="utf-8") as f:
        return json.load(f)



d   = load()
geo = loader.get_comunas_geojson()

ACCENT = "#A78BFA"   # violet
ACCENT2 = "#7C3AED"
LIGHT  = "#EDE9FE"

st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#F8F7FF;}
[data-testid="stSidebar"]{background:#1E1B4B;}
[data-testid="stSidebar"] *{color:#fff!important;}
</style>""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#1E1B4B,#4C1D95);
     padding:24px 32px;border-radius:12px;margin-bottom:20px;'>
  <h1 style='color:white;margin:0;font-size:1.8rem;'>👥 Demografía CABA</h1>
  <p style='color:#C4B5FD;margin:4px 0 0;font-size:.9rem;'>
    Población · Estructura etaria · Vivienda & vulnerabilidad · Estadísticas vitales
  </p>
</div>""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────────
res = d["resumen"]
ev  = d["esperanza_vida_ultimo"]
k1, k2, k3, k4, k5 = st.columns(5)

def kpi(col, val, label, color):
    col.markdown(f"""
    <div style='background:white;border-radius:10px;padding:16px 20px;
         border-left:5px solid {color};box-shadow:0 2px 6px rgba(0,0,0,.08);'>
      <p style='margin:0;font-size:.8rem;color:#666;text-transform:uppercase;letter-spacing:.5px;'>{label}</p>
      <p style='margin:0;font-size:1.8rem;font-weight:700;color:{color};'>{val}</p>
    </div>""", unsafe_allow_html=True)

kpi(k1, f"{res['poblacion_total']:,}".replace(",","."), "Habitantes (Censo 2010)", "#7C3AED")
kpi(k2, f"{ev['total']} años", f"Esp. de vida ({ev['anio']})", "#0EA5E9")
kpi(k3, f"{ev['mujer']} / {ev['varon']}", "Mujer / Varón", "#EC4899")
kpi(k4, f"{res['fecundidad_ultima']}", "Hijos prom. por mujer", "#10B981")
kpi(k5, f"{res['nbi_promedio']:.1f}%", "NBI promedio por comuna", "#F59E0B")

st.markdown("<br>", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 👥 Demografía CABA")
    st.markdown("---")
    st.markdown("**Población total**")
    st.metric("Censo 2010", f"{res['poblacion_total']:,}".replace(",","."))
    st.markdown("**Esperanza de vida**")
    st.metric(f"Año {ev['anio']}", f"{ev['total']} años")
    st.caption("Mujer: " + str(ev['mujer']) + " · Varón: " + str(ev['varon']))
    st.markdown("---")
    st.markdown("**Filtros**")
    comunas_sel = st.multiselect("Comunas", list(range(1,16)), default=list(range(1,16)), format_func=lambda x: f"C{x}", key="demo_comunas")
    if not comunas_sel:
        comunas_sel = list(range(1, 16))
    indicador_viv = st.radio("Indicador vivienda", ["NBI", "Déficit habitacional", "Hacinamiento"], key="demo_ind")
    st.markdown("---")

    st.markdown("**Top 10 barrios por población**")
    barrios = sorted(d["pob_por_barrio"], key=lambda x: x["poblacion"], reverse=True)[:10]
    for b in barrios:
        st.markdown(f"<div style='display:flex;justify-content:space-between;font-size:.83rem;'>"
                    f"<span>{b['barrio'].title()}</span><b>{b['poblacion']:,}</b></div>",
                    unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "🗺 Población & Mapa",
    "📊 Estructura Etaria",
    "🏠 Vivienda & Vulnerabilidad",
    "❤️ Estadísticas Vitales",
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 – Población & Mapa
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    col_m, col_r = st.columns([2, 1])

    with col_m:
        st.markdown("#### Población por comuna (Censo 2010)")
        pob_dict = {r["comuna"]: r["poblacion"] for r in d["pob_por_comuna"]}
        for feat in geo["features"]:
            c = feat["properties"].get("comuna", 0)
            feat["properties"]["pob"] = pob_dict.get(c, 0)

        m = folium.Map(location=[-34.615, -58.437], zoom_start=11,
                       tiles="CartoDB positron")
        folium.Choropleth(
            geo_data=geo,
            data=d["pob_por_comuna"],
            columns=["comuna", "poblacion"],
            key_on="feature.properties.comuna",
            fill_color="BuPu",
            fill_opacity=0.75,
            line_opacity=0.4,
            legend_name="Población",
            nan_fill_color="#eee",
        ).add_to(m)
        folium.GeoJson(
            geo,
            style_function=lambda x: {"fillOpacity": 0, "weight": 0.5, "color": "#555"},
            tooltip=folium.GeoJsonTooltip(
                fields=["comuna", "barrios", "pob"],
                aliases=["Comuna", "Barrios", "Población"],
                localize=True,
            ),
        ).add_to(m)
        if len(comunas_sel) < 15:
            sel_features = {"type":"FeatureCollection","features":[
                f for f in geo["features"] if f["properties"].get("comuna") in comunas_sel
            ]}
            folium.GeoJson(sel_features, style_function=lambda x: {
                "fillOpacity": 0, "weight": 3, "color": "#A78BFA"
            }).add_to(m)
        st_folium(m, width=None, height=440, returned_objects=[], key="demo_map")

    with col_r:
        st.markdown("#### Ranking comunas")
        pob_df = pd.DataFrame(d["pob_por_comuna"]).sort_values("poblacion", ascending=False)
        pob_df = pob_df[pob_df["comuna"].isin(comunas_sel)]
        max_pob = pob_df["poblacion"].max() if not pob_df.empty else 1
        for _, row in pob_df.iterrows():
            pct = row["poblacion"] / max_pob
            st.markdown(
                f"<div style='margin-bottom:6px;'>"
                f"<div style='display:flex;justify-content:space-between;font-size:.82rem;'>"
                f"<span>Comuna {int(row['comuna'])}</span>"
                f"<b>{int(row['poblacion']):,}</b></div>"
                f"<div style='background:#E9D5FF;border-radius:4px;height:6px;'>"
                f"<div style='width:{pct*100:.0f}%;background:#7C3AED;height:6px;border-radius:4px;'></div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("#### Población por barrio (top 30)")
    barrios_df = pd.DataFrame(d["pob_por_barrio"]).sort_values("poblacion", ascending=False).head(30)
    barrios_df["barrio"] = barrios_df["barrio"].str.title()
    fig_b = px.bar(
        barrios_df, x="poblacion", y="barrio", orientation="h",
        color="poblacion", color_continuous_scale="Purples",
        labels={"poblacion": "Población", "barrio": ""},
    )
    fig_b.update_layout(
        height=500, showlegend=False, coloraxis_showscale=False,
        yaxis={"categoryorder": "total ascending"},
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_b, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 – Estructura Etaria
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    col_p, col_gg = st.columns([1, 1])

    with col_p:
        st.markdown(f"#### Pirámide de edad (Censo {d['piramide_anio']})")
        pir = pd.DataFrame(d["piramide"])
        fig_pir = go.Figure()
        fig_pir.add_trace(go.Bar(
            y=pir["grupo"],
            x=[-v for v in pir["mujer"]],
            name="Mujer",
            orientation="h",
            marker_color="#EC4899",
            hovertemplate="%{y}: %{customdata:,}<extra>Mujer</extra>",
            customdata=pir["mujer"],
        ))
        fig_pir.add_trace(go.Bar(
            y=pir["grupo"],
            x=pir["varon"],
            name="Varón",
            orientation="h",
            marker_color="#3B82F6",
            hovertemplate="%{y}: %{x:,}<extra>Varón</extra>",
        ))
        fig_pir.update_layout(
            barmode="overlay",
            xaxis=dict(
                tickvals=[-300000, -200000, -100000, 0, 100000, 200000, 300000],
                ticktext=["300k", "200k", "100k", "0", "100k", "200k", "300k"],
                title="Población",
            ),
            yaxis_title="Grupo de edad",
            legend=dict(orientation="h", y=1.05),
            margin=dict(t=30, b=30, l=10, r=10),
            height=450,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,247,255,1)",
        )
        st.plotly_chart(fig_pir, use_container_width=True)

    with col_gg:
        st.markdown("#### Evolución de grandes grupos de edad (%)")
        gg = pd.DataFrame(d["grandes_grupos"])
        grupos = [c for c in gg.columns if c != "anio"]
        colors = {"0 - 14": "#F59E0B", "15 - 64": "#7C3AED", "65 y más": "#10B981"}
        fig_gg = go.Figure()
        for g in grupos:
            if g in gg.columns:
                fig_gg.add_trace(go.Scatter(
                    x=gg["anio"], y=gg[g],
                    name=g,
                    mode="lines+markers",
                    marker_size=6,
                    line=dict(color=colors.get(g, "#888")),
                ))
        fig_gg.update_layout(
            yaxis_title="% de la población",
            xaxis_title="Año censal",
            legend=dict(orientation="h", y=-0.25),
            margin=dict(t=10, b=10, l=10, r=10),
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,247,255,1)",
            yaxis=dict(gridcolor="#E9D5FF"),
        )
        st.plotly_chart(fig_gg, use_container_width=True)

        st.markdown("#### Adultos mayores: tipo de hogar")
        am = pd.DataFrame(d["adultos_mayores_hogar"])
        fig_am = px.bar(
            am, x="anio", y="pct", color="tipo",
            barmode="group",
            color_discrete_sequence=["#7C3AED", "#EC4899", "#F59E0B"],
            labels={"anio": "Año", "pct": "%", "tipo": "Tipo de hogar"},
        )
        fig_am.update_layout(
            height=220, margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=-0.35),
        )
        st.plotly_chart(fig_am, use_container_width=True)

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Jefatura femenina de hogares (%)")
        jf = pd.DataFrame(d["jefatura_femenina"])
        fig_jf = go.Figure(go.Scatter(
            x=jf["anio"], y=jf["pct"],
            mode="lines+markers+text",
            text=[f"{v:.1f}%" for v in jf["pct"]],
            textposition="top center",
            marker=dict(size=8, color=ACCENT2),
            line=dict(color=ACCENT2, width=2),
            fill="tozeroy",
            fillcolor="rgba(124,58,237,0.1)",
        ))
        fig_jf.update_layout(
            yaxis_title="% hogares con jefa mujer",
            height=260,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,247,255,1)",
            yaxis=dict(gridcolor="#E9D5FF"),
        )
        st.plotly_chart(fig_jf, use_container_width=True)

    with col_b:
        st.markdown("#### Esperanza de vida por sexo")
        ev_df = pd.DataFrame(d["esperanza_vida"])
        ev_df = ev_df[ev_df["anio"] >= 1950]
        fig_ev = go.Figure()
        for col_name, color, name in [("mujer","#EC4899","Mujer"),("varon","#3B82F6","Varón"),("total","#7C3AED","Total")]:
            if col_name in ev_df.columns:
                fig_ev.add_trace(go.Scatter(
                    x=ev_df["anio"], y=ev_df[col_name],
                    name=name, mode="lines+markers",
                    marker=dict(size=5, color=color),
                    line=dict(color=color, width=2),
                ))
        fig_ev.update_layout(
            yaxis_title="Años",
            height=260,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,247,255,1)",
            yaxis=dict(gridcolor="#E9D5FF"),
            legend=dict(orientation="h", y=-0.35),
        )
        st.plotly_chart(fig_ev, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 – Vivienda & Vulnerabilidad
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    col_nbi, col_def = st.columns(2)

    with col_nbi:
        st.markdown("#### NBI por comuna (%)")
        nbi_df = pd.DataFrame(d["nbi_por_comuna"])
        nbi_df = nbi_df[nbi_df["comuna"].isin(comunas_sel)].sort_values("nbi_pct", ascending=True)
        if indicador_viv == "NBI":
            colors_nbi = [ACCENT] * len(nbi_df)
        else:
            colors_nbi = ["#EF4444" if v > 10 else "#F59E0B" if v > 5 else "#10B981"
                          for v in nbi_df["nbi_pct"]]
        fig_nbi = go.Figure(go.Bar(
            y=[f"C{c}" for c in nbi_df["comuna"]],
            x=nbi_df["nbi_pct"],
            orientation="h",
            marker_color=colors_nbi,
            text=[f"{v:.1f}%" for v in nbi_df["nbi_pct"]],
            textposition="outside",
        ))
        fig_nbi.add_vline(x=float(nbi_df["nbi_pct"].mean()), line_dash="dash",
                          line_color="#888", annotation_text=f"Prom: {nbi_df['nbi_pct'].mean():.1f}%")
        fig_nbi.update_layout(
            height=380,
            margin=dict(t=10, b=10, l=40, r=60),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,247,255,1)",
            xaxis=dict(gridcolor="#E9D5FF"),
        )
        st.plotly_chart(fig_nbi, use_container_width=True)
        st.caption("Rojo > 10% · Amarillo 5-10% · Verde < 5%")

    with col_def:
        st.markdown("#### Déficit habitacional por comuna")
        dh_df = pd.DataFrame(d["deficit_habitacional"])
        dh_df = dh_df[dh_df["comuna"].isin(comunas_sel)]
        dh_highlight = indicador_viv == "Déficit habitacional"
        fig_dh = go.Figure()
        for col_name, color, name in [
            ("cuantitativo", "#7C3AED" if dh_highlight else "#EF4444", "Cuantitativo"),
            ("cualitativo_i", "#A78BFA" if dh_highlight else "#F59E0B", "Cualitativo I"),
            ("cualitativo_ii", "#DDD6FE" if dh_highlight else "#10B981", "Cualitativo II"),
        ]:
            fig_dh.add_trace(go.Bar(
                x=[f"C{c}" for c in dh_df["comuna"]],
                y=dh_df[col_name],
                name=name,
                marker_color=color,
            ))
        fig_dh.update_layout(
            barmode="group",
            height=380,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,247,255,1)",
            yaxis=dict(gridcolor="#E9D5FF", title="%"),
            legend=dict(orientation="h", y=-0.25),
        )
        st.plotly_chart(fig_dh, use_container_width=True)

    st.markdown("---")
    col_cs, col_rt = st.columns(2)

    with col_cs:
        st.markdown("#### Calidad de conexión a servicios básicos (%)")
        cs_df = pd.DataFrame(d["calidad_servicios"])
        cs_df = cs_df[cs_df["comuna"].isin(comunas_sel)]
        fig_cs = go.Figure()
        for col_name, color, name in [
            ("satisfactoria","#10B981","Satisfactoria"),
            ("basica","#F59E0B","Básica"),
            ("insuficiente","#EF4444","Insuficiente"),
        ]:
            fig_cs.add_trace(go.Bar(
                x=[f"C{c}" for c in cs_df["comuna"]],
                y=cs_df[col_name],
                name=name, marker_color=color,
            ))
        fig_cs.update_layout(
            barmode="stack", height=300,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,247,255,1)",
            yaxis=dict(gridcolor="#E9D5FF"),
            legend=dict(orientation="h", y=-0.3),
        )
        st.plotly_chart(fig_cs, use_container_width=True)

    with col_rt:
        st.markdown("#### Régimen de tenencia de la vivienda (%)")
        rt_df = pd.DataFrame(d["regimen_tenencia"])
        years = rt_df.iloc[:,1].unique() if len(rt_df.columns) > 2 else []
        cols_ten = [c for c in rt_df.columns if c not in [rt_df.columns[0], rt_df.columns[1], "NS/NC "]]
        if cols_ten:
            year_col = rt_df.columns[1]
            com_col = rt_df.columns[0]
            latest_year = rt_df[year_col].max()
            latest = rt_df[rt_df[year_col] == latest_year]
            avg_latest = latest[cols_ten].mean()
            fig_rt = go.Figure(go.Pie(
                labels=avg_latest.index.tolist(),
                values=avg_latest.values.tolist(),
                hole=0.4,
                marker_colors=["#7C3AED", "#0EA5E9", "#F59E0B", "#EF4444"],
            ))
            fig_rt.update_layout(
                height=300,
                title=dict(text=f"Promedio CABA ({latest_year})", font=dict(size=12)),
                margin=dict(t=40, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_rt, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Hogares en situación de pobreza e indigencia (% – CABA)")
    pob_t = pd.DataFrame(d["pobreza_trimestre"])
    pob_t["total_pobres"] = pob_t["indigencia"] + pob_t["pobreza_no_indigente"]
    fig_pob = go.Figure()
    fig_pob.add_trace(go.Scatter(
        x=pob_t["trimestre"], y=pob_t["total_pobres"],
        name="Pobreza total", mode="lines",
        line=dict(color="#EF4444", width=2),
        fill="tozeroy", fillcolor="rgba(239,68,68,0.1)",
    ))
    fig_pob.add_trace(go.Scatter(
        x=pob_t["trimestre"], y=pob_t["indigencia"],
        name="Indigencia", mode="lines",
        line=dict(color="#F59E0B", width=2),
        fill="tozeroy", fillcolor="rgba(245,158,11,0.15)",
    ))
    fig_pob.update_layout(
        height=280,
        margin=dict(t=10, b=60, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,247,255,1)",
        yaxis=dict(gridcolor="#E9D5FF", title="%"),
        xaxis=dict(tickangle=45),
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig_pob, use_container_width=True)

    col_hac, _ = st.columns([1, 1])
    with col_hac:
        st.markdown("#### Hacinamiento: viviendas con 2+ hogares (%)")
        hac_df = pd.DataFrame(d["hacinamiento"])
        hac_df = hac_df[hac_df["comuna"].isin(comunas_sel)].sort_values("dos_mas_hogares", ascending=True)
        hac_scale = "Purples" if indicador_viv == "Hacinamiento" else "Reds"
        fig_hac = px.bar(
            hac_df, x="dos_mas_hogares", y=hac_df["comuna"].apply(lambda c: f"C{c}"),
            orientation="h",
            color="dos_mas_hogares", color_continuous_scale=hac_scale,
            labels={"x": "%", "y": ""},
            text=[f"{v:.1f}%" for v in hac_df["dos_mas_hogares"]],
        )
        fig_hac.update_traces(textposition="outside")
        fig_hac.update_layout(
            height=380, showlegend=False, coloraxis_showscale=False,
            margin=dict(t=10, b=10, l=40, r=60),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_hac, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 – Estadísticas Vitales
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    col_d, col_f = st.columns(2)

    with col_d:
        st.markdown("#### Defunciones anuales (2012-2024)")
        def_df = pd.DataFrame(d["defunciones_anual"])
        def_df["color"] = def_df["anio"].apply(
            lambda y: "#EF4444" if y in (2020, 2021) else "#A78BFA"
        )
        fig_def = go.Figure(go.Bar(
            x=def_df["anio"],
            y=def_df["total"],
            marker_color=def_df["color"],
            text=def_df["total"].apply(lambda v: f"{v:,}"),
            textposition="outside",
        ))
        fig_def.add_vrect(x0=2019.5, x1=2021.5, fillcolor="rgba(239,68,68,0.1)",
                          layer="below", line_width=0,
                          annotation_text="COVID", annotation_position="top left")
        fig_def.update_layout(
            height=320,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,247,255,1)",
            yaxis=dict(gridcolor="#E9D5FF"),
            xaxis=dict(tickmode="linear", dtick=1),
        )
        st.plotly_chart(fig_def, use_container_width=True)

    with col_f:
        st.markdown("#### Fecundidad: hijos promedio por mujer (CABA)")
        fec_df = pd.DataFrame(d["fecundidad"])
        fig_fec = go.Figure(go.Scatter(
            x=fec_df["anio"], y=fec_df["tasa"],
            mode="lines+markers",
            marker=dict(size=6, color=ACCENT2),
            line=dict(color=ACCENT2, width=2),
            fill="tozeroy",
            fillcolor="rgba(124,58,237,0.08)",
        ))
        fig_fec.add_hline(y=2.1, line_dash="dash", line_color="#EF4444",
                          annotation_text="Reemplazo 2.1")
        fig_fec.update_layout(
            height=320,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,247,255,1)",
            yaxis=dict(gridcolor="#E9D5FF", title="Hijos por mujer"),
        )
        st.plotly_chart(fig_fec, use_container_width=True)
        st.caption(f"Último dato: {d['fecundidad'][-1]['anio']} → {d['fecundidad'][-1]['tasa']} hijos/mujer (por debajo del nivel de reemplazo)")

    st.markdown("---")
    col_e, col_t = st.columns(2)

    with col_e:
        st.markdown("#### Edad promedio de las madres al dar a luz")
        em_df = pd.DataFrame(d["edad_promedio_madres"])
        fig_em = go.Figure(go.Scatter(
            x=em_df["anio"], y=em_df["edad"],
            mode="lines+markers",
            marker=dict(size=6, color="#EC4899"),
            line=dict(color="#EC4899", width=2),
        ))
        fig_em.update_layout(
            height=280, yaxis_title="Edad (años)",
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,247,255,1)",
            yaxis=dict(gridcolor="#E9D5FF"),
        )
        st.plotly_chart(fig_em, use_container_width=True)

    with col_t:
        st.markdown("#### Defunciones por tipo de registro (2012-2022)")
        dt_df = pd.DataFrame(d["defunciones_por_tipo"])
        fig_dt = px.pie(
            dt_df, values="n", names="tipo",
            color_discrete_sequence=px.colors.sequential.Purples_r,
            hole=0.35,
        )
        fig_dt.update_traces(textposition="inside", textinfo="percent+label")
        fig_dt.update_layout(
            height=280,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig_dt, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Esperanza de vida histórica desde 1887")
    ev_full = pd.DataFrame(d["esperanza_vida"])
    fig_ev2 = go.Figure()
    for col_ev, color, name in [("mujer","#EC4899","Mujer"),("varon","#3B82F6","Varón"),("total","#7C3AED","Total")]:
        if col_ev in ev_full.columns:
            valid = ev_full[ev_full[col_ev] > 0]
            fig_ev2.add_trace(go.Scatter(
                x=valid["anio"], y=valid[col_ev],
                name=name, mode="lines+markers",
                marker=dict(size=5, color=color),
                line=dict(color=color, width=2),
            ))
    fig_ev2.update_layout(
        height=300, yaxis_title="Años de vida",
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,247,255,1)",
        yaxis=dict(gridcolor="#E9D5FF"),
        legend=dict(orientation="h", y=-0.25),
    )
    st.plotly_chart(fig_ev2, use_container_width=True)
    st.caption("Fuente: DGEyC GCBA · Esperanza de vida al nacer por sexo. Serie desde 1887.")
