"""
Página 12 – Mapa Comercial / MOC CABA
Fuente: GCBA – Mapa de Oportunidades Comerciales + AGC Habilitaciones Aprobadas
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Mapa Comercial CABA",
    page_icon="🛍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background:#0D1117; }
[data-testid="stSidebar"]          { background:#0A1628; border-right:1px solid #1E293B; }
[data-testid="stSidebar"] *        { color:#E2E8F0 !important; }
[data-testid="stHeader"]           { background:transparent; }
[data-testid="stStatusWidget"]     { display:none !important; }
[data-stale="true"]                { opacity:1 !important; transition:none !important; }
[data-stale]                       { opacity:1 !important; }
[aria-busy="true"]                 { opacity:1 !important; }
.stApp > *                         { opacity:1 !important; transition:none !important; }
iframe                             { opacity:1 !important; }
.stTabs [data-baseweb="tab"]       { color:#94A3B8 !important; }
.stTabs [aria-selected="true"]     { color:#FBBF24 !important; border-bottom:2px solid #F59E0B !important; }
</style>
""", unsafe_allow_html=True)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

@st.cache_data(show_spinner=False)
def load_data():
    with open(os.path.join(DATA_DIR, "mapa_comercial_caba.json"), encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(show_spinner=False)
def load_geojson():
    with open(os.path.join(DATA_DIR, "moc_zonas.geojson"), encoding="utf-8") as f:
        return json.load(f)

data   = load_data()
geo    = load_geojson()

zona_by_id = {r["zona_id"]: r for r in data["por_zona"]}
rub_by_zona = data["rubros_por_zona"]  # str(zona_id) → list of rubro dicts

# DataFrames
df_zonas = pd.DataFrame(data["por_zona"])
df_rub   = pd.DataFrame(data["rubros_resumen"])
df_ape   = pd.DataFrame(data["apertura_por_rubro_anio"])
df_hab_cat = pd.DataFrame(data["habilitaciones_categorias"])
df_hab_tot = pd.DataFrame(data["habilitaciones_totales"])

RUBRO_COLORS = {
    "BARES Y CAFES":              "#F59E0B",
    "RESTAURANTES":               "#EF4444",
    "COMIDA AL PASO":             "#FB923C",
    "PANADERIAS":                 "#FCD34D",
    "HELADERIAS":                 "#38BDF8",
    "FIAMBRERIAS Y DIETETICAS":   "#86EFAC",
    "CARNES Y VERDURAS":          "#4ADE80",
    "KIOSCOS Y LOTERIAS":         "#C084FC",
    "INDUMENTARIA":               "#E879F9",
    "INSUMOS PARA EL HOGAR":      "#94A3B8",
    "FERRETERIA Y CONSTRUCCION":  "#78716C",
    "OPTICA Y JOYERIAS":          "#67E8F9",
    "MUSICA Y LIBRERIA":          "#A78BFA",
    "SALUD Y COSMETICA":          "#34D399",
    "INSTITUCIONES DEPORTIVAS":   "#60A5FA",
    "VETERINARIA":                "#FCA5A5",
}

IND_OPTIONS = {
    "Supervivencia (%)":  ("supervivencia_prom",  True,  "#22D3EE", "#EF4444"),
    "Apertura (índice)":  ("apertura_prom",        True,  "#4ADE80", "#1E293B"),
    "Cierre (índice)":    ("cierre_prom",          False, "#EF4444", "#1E293B"),
    "Precio alquiler ($)":("alquiler_prom",        True,  "#FBBF24", "#1E293B"),
    "Riesgo comercial":   ("riesgo_prom",          False, "#F97316", "#1E293B"),
}

# ── Session state ─────────────────────────────────────────────────────
if "mc_zona"    not in st.session_state: st.session_state.mc_zona    = None
if "mc_ind"     not in st.session_state: st.session_state.mc_ind     = "Supervivencia (%)"
if "mc_rub_sel" not in st.session_state: st.session_state.mc_rub_sel = "Todos"

# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛍 Mapa Comercial CABA")
    st.markdown(f"<span style='font-size:.73rem;color:#64748B;'>{data['n_zonas']} zonas · {data['n_rubros']} rubros<br>MOC 2016-2017 + Habilitaciones 2022-2024</span>", unsafe_allow_html=True)
    st.markdown("---")

    ind_sel = st.selectbox("Indicador en el mapa", list(IND_OPTIONS.keys()),
                            index=list(IND_OPTIONS.keys()).index(st.session_state.mc_ind))
    if ind_sel != st.session_state.mc_ind:
        st.session_state.mc_ind = ind_sel
        st.rerun()

    rubros_lista = ["Todos"] + sorted(df_rub["rubro"].tolist())
    rub_sel = st.selectbox("Filtrar por rubro", rubros_lista,
                            index=rubros_lista.index(st.session_state.mc_rub_sel)
                                  if st.session_state.mc_rub_sel in rubros_lista else 0)
    if rub_sel != st.session_state.mc_rub_sel:
        st.session_state.mc_rub_sel = rub_sel
        st.rerun()

    st.markdown("---")

    # Panel de zona seleccionada
    sel_z = st.session_state.mc_zona
    if sel_z and str(sel_z) in rub_by_zona:
        z     = zona_by_id.get(sel_z, {})
        rubros = sorted(rub_by_zona[str(sel_z)],
                        key=lambda r: r["ind_supervivencia"] or 0, reverse=True)
        st.markdown(f"### Zona {sel_z}")
        st.markdown(f"<div style='font-size:.75rem;color:#94A3B8;'>Rubro predominante: <b style='color:#FBBF24;'>{z.get('rubro_predominante','—')}</b></div>", unsafe_allow_html=True)
        if z.get("alquiler_prom"):
            st.markdown(f"<div style='font-size:.7rem;color:#64748B;'>Alquiler prom: ${z['alquiler_prom']:,.0f}/mes</div>", unsafe_allow_html=True)
        st.markdown("**Rubros activos:**")
        for r in rubros[:8]:
            sv = r.get("ind_supervivencia")
            if sv is None: continue
            clr = "#4ADE80" if sv >= 90 else "#FBBF24" if sv >= 70 else "#EF4444"
            rg  = r.get("nivel_riesgo") or "?"
            st.markdown(
                f"<div style='margin-bottom:5px;padding:5px 8px;background:#0F172A;"
                f"border-radius:5px;font-size:.7rem;'>"
                f"<span style='color:{clr};'>{'▲' if sv>=90 else '▶' if sv>=70 else '▼'} </span>"
                f"<span style='color:#E2E8F0;'>{r['rubro'][:20]}</span> "
                f"<span style='float:right;color:{clr};font-weight:700;'>{sv:.0f}%</span><br>"
                f"<span style='color:#334155;'>Riesgo: {rg} · Apertura: {r.get('ind_apertura','?')}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown("<div style='font-size:.7rem;color:#334155;'>Hacé click en una zona del mapa para ver el detalle.</div>", unsafe_allow_html=True)

        # Ranking top rubros CABA
        st.markdown("#### Top rubros CABA")
        for r in df_rub.head(8).itertuples():
            sv  = r.supervivencia or 0
            clr = RUBRO_COLORS.get(r.rubro, "#64748B")
            bw  = int(sv)
            st.markdown(
                f"<div style='margin-bottom:5px;'>"
                f"<div style='display:flex;justify-content:space-between;font-size:.7rem;'>"
                f"<span style='color:{clr};'>{r.rubro[:22]}</span>"
                f"<span style='color:{clr};font-weight:700;'>{sv:.0f}%</span></div>"
                f"<div style='background:#1E293B;border-radius:3px;height:3px;'>"
                f"<div style='background:{clr};height:3px;width:{bw}%;border-radius:3px;'></div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

# ── Header ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='background:linear-gradient(135deg,#0A1628,#0f1f04);padding:20px 28px;border-radius:12px;
            margin-bottom:20px;border:1px solid #1a3a0a44;'>
  <h1 style='color:#fff;margin:0;font-size:1.7rem;'>🛍 Mapa Comercial – Ciudad de Buenos Aires</h1>
  <p style='color:#64748B;margin:5px 0 0;font-size:.88rem;'>
    Mapa de Oportunidades Comerciales (MOC) · {data['n_zonas']} zonas · {data['n_rubros']} rubros
    &nbsp;·&nbsp; MOC 2016-2017 + Habilitaciones AGC 2022-2024
  </p>
</div>
""", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────────────
best_rub = df_rub.iloc[0]
worst_rub = df_rub[df_rub["supervivencia"].notna()].iloc[-1]
hab24 = df_hab_tot[df_hab_tot["anio"]==2024]["total"].iloc[0]
ps = data["precio_stats"]

k1,k2,k3,k4,k5 = st.columns(5)
kpis = [
    (k1, f"{data['n_zonas']}", "Zonas MOC",                    "#F59E0B", "unidades comerciales"),
    (k2, f"{best_rub['supervivencia']:.0f}%", f"Mejor supervivencia", "#4ADE80", best_rub["rubro"][:22]),
    (k3, f"{df_rub['supervivencia'].mean():.0f}%", "Supervivencia media", "#38BDF8", "promedio CABA"),
    (k4, f"{hab24:,}", "Habilitaciones 2024",         "#C084FC", "nuevos locales AGC"),
    (k5, f"${ps['alquiler_prom_caba']:,.0f}", "Alquiler prom. local",  "#EF4444", "$/mes · base 2017"),
]
for col, val, label, color, sub in kpis:
    with col:
        st.markdown(f"""
<div style='background:#0A1628;border:1px solid #1E293B;border-left:4px solid {color};
            border-radius:8px;padding:12px 16px;'>
  <div style='font-size:.62rem;color:#64748B;text-transform:uppercase;letter-spacing:.04em;'>{label}</div>
  <div style='font-size:1.35rem;font-weight:800;color:{color};margin:3px 0;'>{val}</div>
  <div style='font-size:.6rem;color:#334155;'>{sub}</div>
</div>""", unsafe_allow_html=True)

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# ── Tabs ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🗺 Mapa de Zonas", "📊 Índices por Rubro", "📈 Evolución Temporal", "🏢 Habilitaciones"
])

# ══════════════════════════════════════════════════════════════════════
# TAB 1 – MAPA DE ZONAS MOC
# ══════════════════════════════════════════════════════════════════════
with tab1:
    ind_col, ind_good, clr_hi, clr_lo = IND_OPTIONS[st.session_state.mc_ind]

    # Calcular rango para colorear
    vals = [zona_by_id.get(feat["properties"]["zone_id"]
                           if isinstance(feat["properties"].get("zone_id"), int)
                           else int(feat["properties"]["zone_id"]), {}).get(ind_col)
            for feat in geo["features"]]
    vals_clean = [v for v in vals if v is not None]
    vmin = min(vals_clean) if vals_clean else 0
    vmax = max(vals_clean) if vals_clean else 1

    def interp_color(val, vmin, vmax, good_high):
        if val is None: return "#1E293B"
        ratio = (val - vmin) / (vmax - vmin) if vmax > vmin else 0.5
        if not good_high: ratio = 1 - ratio
        # verde → amarillo → rojo (invertido si good_high)
        if ratio > 0.66:
            r_, g_, b_ = 34, 197, 94    # verde
        elif ratio > 0.33:
            r_, g_, b_ = 251, 191, 36   # amarillo
        else:
            r_, g_, b_ = 239, 68,  68   # rojo
        alpha = int(80 + ratio * 140)
        return f"#{r_:02X}{g_:02X}{b_:02X}{alpha:02X}"

    col_m1, col_m2 = st.columns([3, 1])
    with col_m1:
        m = folium.Map(location=[-34.615, -58.443], zoom_start=12,
                       tiles=None, prefer_canvas=True)
        folium.TileLayer(
            "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
            attr="© CARTO", max_zoom=19,
        ).add_to(m)

        for feat in geo["features"]:
            zid = int(feat["properties"]["zone_id"])
            z   = zona_by_id.get(zid, {})
            val = z.get(ind_col)
            fill = interp_color(val, vmin, vmax, ind_good)

            alq   = z.get("alquiler_prom")
            rub_p = z.get("rubro_predominante","—") or "—"
            sv    = z.get("supervivencia_prom")
            ap    = z.get("apertura_prom")
            cl    = z.get("cierre_prom")

            tip_lines = [
                f"<b>Zona {zid}</b><br>",
                f"Rubro predominante: <b>{rub_p}</b><br>",
            ]
            if sv is not None: tip_lines.append(f"Supervivencia: <b>{sv:.0f}%</b><br>")
            if ap is not None: tip_lines.append(f"Apertura: {ap:.1f} · Cierre: {cl:.1f}<br>")
            if alq:            tip_lines.append(f"Alquiler prom: ${alq:,.0f}/mes")

            folium.GeoJson(
                feat,
                style_function=lambda f, fc=fill: {
                    "fillColor": fc, "color": "#334155",
                    "weight": 0.8, "fillOpacity": 0.85,
                },
                highlight_function=lambda f: {
                    "weight": 2.5, "color": "#FBBF24", "fillOpacity": 0.95,
                },
                tooltip=folium.Tooltip("".join(tip_lines), sticky=False),
            ).add_to(m)

        st_folium(m, height=500, use_container_width=True,
                  returned_objects=[], key=f"moc_map_{st.session_state.mc_ind}")

    with col_m2:
        # Leyenda
        st.markdown("#### Escala de color")
        lev_labels = (["Alto", "Medio", "Bajo"] if ind_good else ["Alto", "Medio", "Bajo"])
        lev_colors = (["#22C55E","#FBBF24","#EF4444"] if ind_good else ["#EF4444","#FBBF24","#22C55E"])
        for lbl, clr in zip(lev_labels, lev_colors):
            st.markdown(
                f"<div style='display:flex;align-items:center;margin-bottom:5px;'>"
                f"<div style='width:16px;height:16px;background:{clr};border-radius:3px;margin-right:8px;'></div>"
                f"<span style='font-size:.75rem;color:#94A3B8;'>{lbl}</span></div>",
                unsafe_allow_html=True,
            )
        st.markdown("---")

        # Top 10 zonas por indicador seleccionado
        st.markdown(f"#### Top 10 zonas · {ind_col.replace('_prom','').replace('_',' ').title()}")
        df_top = df_zonas[df_zonas[ind_col].notna()].nlargest(10, ind_col)[
            ["zona_id", ind_col, "rubro_predominante"]
        ]
        for _, r in df_top.iterrows():
            zid  = int(r["zona_id"])
            val  = r[ind_col]
            rp   = (r["rubro_predominante"] or "—")[:18]
            ratio = (val - vmin) / (vmax - vmin) if vmax > vmin else 0.5
            if not ind_good: ratio = 1 - ratio
            clr_ = "#22C55E" if ratio > 0.66 else "#FBBF24" if ratio > 0.33 else "#EF4444"
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;padding:4px 0;"
                f"border-bottom:1px solid #0F172A;font-size:.72rem;'>"
                f"<span style='color:#94A3B8;'>Z{zid:03d} <span style='color:#475569;font-size:.6rem;'>{rp}</span></span>"
                f"<span style='color:{clr_};font-weight:700;'>{val:.1f}</span></div>",
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════════════════════════════
# TAB 2 – ÍNDICES POR RUBRO
# ══════════════════════════════════════════════════════════════════════
with tab2:
    col_r1, col_r2 = st.columns(2)

    with col_r1:
        # Bubble chart: supervivencia vs apertura, size = n_zonas
        fig_bub = px.scatter(
            df_rub, x="apertura", y="supervivencia",
            size="n_zonas_activas",
            color="riesgo_prom",
            color_continuous_scale="RdYlGn_r",
            text="rubro",
            hover_data={"rubro":True,"apertura":True,"supervivencia":True,
                        "cierre":True,"n_zonas_activas":True},
            size_max=40,
        )
        fig_bub.update_traces(
            textposition="top center", textfont=dict(size=8, color="#94A3B8"),
        )
        fig_bub.update_layout(
            title=dict(text="Supervivencia vs Apertura por rubro (tamaño = zonas activas)",
                       font=dict(color="#E2E8F0", size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B", title="Índice de apertura"),
            yaxis=dict(gridcolor="#1E293B", title="% Supervivencia"),
            coloraxis_colorbar=dict(title="Riesgo", tickfont=dict(color="#64748B")),
            margin=dict(t=35, b=10, l=10, r=10), height=420,
        )
        st.plotly_chart(fig_bub, use_container_width=True)

    with col_r2:
        # Bar horizontal supervivencia
        df_rs = df_rub.sort_values("supervivencia")
        colors_rs = [RUBRO_COLORS.get(r, "#64748B") for r in df_rs["rubro"]]
        fig_sv = go.Figure(go.Bar(
            y=df_rs["rubro"],
            x=df_rs["supervivencia"],
            orientation="h",
            marker_color=colors_rs,
            text=df_rs["supervivencia"].apply(lambda x: f"{x:.0f}%" if x else ""),
            textposition="outside",
            textfont=dict(size=10, color="#E2E8F0"),
        ))
        fig_sv.add_vline(x=df_rub["supervivencia"].mean(), line_dash="dot",
                         line_color="#475569",
                         annotation_text=f"Media: {df_rub['supervivencia'].mean():.0f}%",
                         annotation_font_color="#64748B", annotation_font_size=9)
        fig_sv.update_layout(
            title=dict(text="Índice de supervivencia por rubro", font=dict(color="#E2E8F0", size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B", range=[0, 115]),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=35, b=5, l=5, r=50), height=420, showlegend=False,
        )
        st.plotly_chart(fig_sv, use_container_width=True)

    # Tabla resumen
    st.markdown("#### Tabla completa de índices por rubro")
    df_show = df_rub[["rubro","supervivencia","apertura","cierre","crecimiento","riesgo_prom","n_zonas_activas"]].copy()
    df_show.columns = ["Rubro","Supervivencia%","Apertura","Cierre","Crecimiento","Riesgo","Zonas activas"]
    st.dataframe(df_show.style.format({
        "Supervivencia%":"  {:.1f}",
        "Apertura":"  {:.1f}",
        "Cierre":"  {:.1f}",
        "Crecimiento":"  {:.1f}",
        "Riesgo":"  {:.1f}",
    }), use_container_width=True, hide_index=True, height=350)

# ══════════════════════════════════════════════════════════════════════
# TAB 3 – EVOLUCIÓN TEMPORAL
# ══════════════════════════════════════════════════════════════════════
with tab3:
    col_e1, col_e2 = st.columns(2)

    with col_e1:
        # Aperturas por rubro y año (multi-line)
        df_ape_p = df_ape.copy()
        df_ape_p["periodo"] = df_ape_p["anio"].astype(str)
        fig_ape = px.bar(
            df_ape_p.sort_values(["anio","n_registros"], ascending=[True,False]),
            x="anio", y="n_registros", color="rubro",
            barmode="stack",
            color_discrete_map=RUBRO_COLORS,
        )
        fig_ape.update_layout(
            title=dict(text="Aperturas por rubro · MOC 2016-2017", font=dict(color="#E2E8F0", size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B", title="Año", tickvals=[2016,2017]),
            yaxis=dict(gridcolor="#1E293B", title="Registros de apertura"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=8)),
            margin=dict(t=35, b=10, l=10, r=10), height=380,
        )
        st.plotly_chart(fig_ape, use_container_width=True)

    with col_e2:
        # Comparación apertura vs cierre por rubro
        df_a = df_ape.groupby("rubro")["n_registros"].sum().reset_index().rename(columns={"n_registros":"aperturas"})
        df_c = pd.DataFrame(data["cierre_serie"])
        if not df_c.empty:
            df_c2 = df_c.groupby("rubro")["total_zonas"].sum().reset_index().rename(columns={"total_zonas":"cierres"})
            df_ac = df_a.merge(df_c2, on="rubro", how="outer").fillna(0)
            df_ac["balance"] = df_ac["aperturas"] - df_ac["cierres"]
            df_ac = df_ac.sort_values("balance", ascending=True)
            colors_bal = ["#EF4444" if b < 0 else "#4ADE80" for b in df_ac["balance"]]
            fig_bal = go.Figure(go.Bar(
                y=df_ac["rubro"],
                x=df_ac["balance"],
                orientation="h",
                marker_color=colors_bal,
                text=df_ac["balance"].apply(lambda x: f"+{x:.0f}" if x >= 0 else f"{x:.0f}"),
                textposition="outside",
                textfont=dict(size=9, color="#E2E8F0"),
            ))
            fig_bal.add_vline(x=0, line_color="#475569", line_width=1)
            fig_bal.update_layout(
                title=dict(text="Balance aperturas − cierres por rubro (2016-2017)",
                           font=dict(color="#E2E8F0", size=12)),
                paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
                font=dict(color="#94A3B8"),
                xaxis=dict(gridcolor="#1E293B"),
                yaxis=dict(gridcolor="#1E293B"),
                margin=dict(t=35, b=5, l=5, r=55), height=380, showlegend=False,
            )
            st.plotly_chart(fig_bal, use_container_width=True)
        else:
            st.info("Sin datos de cierre disponibles.")

    # Cuatrimestres (granularidad fina)
    df_ape_q = pd.DataFrame(data["apertura_serie"])
    if not df_ape_q.empty:
        df_ape_q["periodo"] = df_ape_q["anio"].astype(str) + "-C" + df_ape_q["cuatrimestre"].astype(str)
        rub_sel = st.session_state.mc_rub_sel
        df_q_filt = df_ape_q if rub_sel == "Todos" else df_ape_q[df_ape_q["rubro"] == rub_sel]
        fig_q = px.line(
            df_q_filt.sort_values(["anio","cuatrimestre"]),
            x="periodo", y="total_zonas", color="rubro",
            color_discrete_map=RUBRO_COLORS,
            markers=True,
            title="Evolución por cuatrimestre",
        )
        fig_q.update_layout(
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B", title="Zonas con apertura"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=8)),
            margin=dict(t=35, b=10, l=10, r=10), height=300,
            title=dict(font=dict(color="#E2E8F0", size=12)),
        )
        st.plotly_chart(fig_q, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 4 – HABILITACIONES AGC (2022-2024)
# ══════════════════════════════════════════════════════════════════════
with tab4:
    col_h1, col_h2 = st.columns(2)

    with col_h1:
        # Totales por año
        fig_tot = go.Figure(go.Bar(
            x=df_hab_tot["anio"].astype(str),
            y=df_hab_tot["total"],
            marker_color=["#3B82F6","#8B5CF6","#EC4899"],
            text=df_hab_tot["total"].apply(lambda x: f"{x:,}"),
            textposition="outside",
            textfont=dict(color="#E2E8F0", size=13),
        ))
        fig_tot.update_layout(
            title=dict(text="Total de habilitaciones aprobadas por año (AGC)",
                       font=dict(color="#E2E8F0", size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B", range=[0, df_hab_tot["total"].max()*1.15]),
            margin=dict(t=35, b=10, l=10, r=10), height=300, showlegend=False,
        )
        st.plotly_chart(fig_tot, use_container_width=True)

        # Nota sobre variación
        t22 = int(df_hab_tot[df_hab_tot["anio"]==2022]["total"])
        t23 = int(df_hab_tot[df_hab_tot["anio"]==2023]["total"])
        t24 = int(df_hab_tot[df_hab_tot["anio"]==2024]["total"])
        d23 = round((t23-t22)/t22*100,1)
        d24 = round((t24-t23)/t23*100,1)
        st.info(
            f"📌 2022→2023: {d23:+.1f}% · 2023→2024: {d24:+.1f}%  |  "
            f"El volumen de 2022 puede incluir habilitaciones atrasadas post-pandemia."
        )

    with col_h2:
        # Categorías apiladas
        fig_cat = px.bar(
            df_hab_cat, x="anio", y="cantidad", color="categoria",
            barmode="stack",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_cat.update_layout(
            title=dict(text="Habilitaciones por categoría · 2022-2024",
                       font=dict(color="#E2E8F0", size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B", tickvals=[2022,2023,2024]),
            yaxis=dict(gridcolor="#1E293B"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9)),
            margin=dict(t=35, b=10, l=10, r=10), height=300,
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    # Top 15 rubros recientes
    st.markdown("#### Top rubros en habilitaciones recientes")
    df_hr = pd.DataFrame(data["habilitaciones_recientes"])
    df_hr_pivot = df_hr.pivot_table(index="rubro", columns="anio", values="cantidad", fill_value=0)
    df_hr_pivot.columns = [str(c) for c in df_hr_pivot.columns]
    df_hr_pivot = df_hr_pivot.fillna(0).astype(int)
    if "2024" in df_hr_pivot.columns:
        df_hr_pivot = df_hr_pivot.nlargest(15, "2024")
    st.dataframe(df_hr_pivot.reset_index().rename(columns={"rubro":"Rubro"}),
                 use_container_width=True, hide_index=True, height=420)

# ── Footer ─────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Fuente: Mapa de Oportunidades Comerciales (MOC) – GCBA / Innovación y Transformación Digital (2016-2017) · "
    "Habilitaciones Aprobadas – Agencia Gubernamental de Control (AGC) 2022-2024. "
    "Precios de alquiler en $ corrientes de 2017. Los índices de supervivencia miden el porcentaje de locales "
    "que permanecen activos al cabo de cada período."
)
