"""
Página 15 – Obras Públicas CABA
BA Obras · AGC Obras Iniciadas · SOA
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Obras Públicas CABA", page_icon="🏗", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background:#0D1117; }
[data-testid="stSidebar"]          { background:#0A1628; border-right:1px solid #1E293B; }
[data-testid="stSidebar"] *        { color:#E2E8F0 !important; }
[data-testid="stHeader"]           { background:transparent; }
[data-testid="stStatusWidget"]     { display:none !important; }
[data-stale],[data-stale="true"],[aria-busy="true"],.stApp>*,iframe { opacity:1!important; transition:none!important; }
.stTabs [data-baseweb="tab"]       { color:#94A3B8!important; }
.stTabs [aria-selected="true"]     { color:#FB923C!important; border-bottom:2px solid #F97316!important; }
</style>""", unsafe_allow_html=True)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

@st.cache_data(show_spinner=False)
def load():
    with open(os.path.join(DATA_DIR, "obras_publicas_caba.json"), encoding="utf-8") as f:
        return json.load(f)

data = load()

obras_act    = data["obras_actuales"]
df_jur       = pd.DataFrame(data["obras_por_jurisdiccion"])
df_hist_anio = pd.DataFrame(data["historico_por_anio"])
df_hist_com  = pd.DataFrame(data["historico_por_comuna"])
df_hist_area = pd.DataFrame(data["historico_por_area"])
df_oi_com    = pd.DataFrame(data["obras_iniciadas_por_comuna"])

ESTADO_COLOR = {
    "En ejecución":  "#F59E0B",
    "En licitación": "#38BDF8",
    "Finalizada":    "#4ADE80",
    "Adjudicada":    "#A78BFA",
    "En proyecto":   "#94A3B8",
    "Paralizada":    "#EF4444",
    "Rescisión":     "#DC2626",
    "Habilitada al tránsito": "#22D3EE",
    "En armado de pliegos": "#64748B",
}

# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏗 Obras Públicas CABA")
    st.markdown("<span style='font-size:.73rem;color:#64748B;'>BA Obras · AGC · Sec. Desarrollo Urbano</span>", unsafe_allow_html=True)
    st.markdown("---")

    n_ejecucion = data["obras_por_estado"].get("En ejecución", 0)
    n_licitacion = data["obras_por_estado"].get("En licitación", 0)
    monto_M = data["monto_total_actual_M"]

    st.markdown(f"<div style='font-size:.62rem;color:#334155;text-transform:uppercase;'>Obras en ejecución</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:1.8rem;font-weight:800;color:#F59E0B;'>{n_ejecucion}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:.65rem;color:#475569;'>+ {n_licitacion} en licitación</div>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("**Por estado**")
    for estado, n in sorted(data["obras_por_estado"].items(), key=lambda x:-x[1]):
        clr = ESTADO_COLOR.get(estado, "#64748B")
        bw  = int(n / max(data["obras_por_estado"].values()) * 100)
        st.markdown(
            f"<div style='margin-bottom:5px;'>"
            f"<div style='display:flex;justify-content:space-between;font-size:.7rem;'>"
            f"<span style='color:{clr};'>{estado[:24]}</span><span style='color:{clr};font-weight:700;'>{n}</span></div>"
            f"<div style='background:#1E293B;border-radius:3px;height:3px;'>"
            f"<div style='background:{clr};height:3px;width:{bw}%;border-radius:3px;'></div></div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    # Filtro de estado para el mapa
    estados_lista = ["Todos"] + sorted(data["obras_por_estado"].keys())
    est_sel = st.selectbox("Filtrar mapa por estado", estados_lista)

# ── Header ──────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='background:linear-gradient(135deg,#0A1628,#1a0f00);padding:20px 28px;border-radius:12px;
            margin-bottom:20px;border:1px solid #7c2d1244;'>
  <h1 style='color:#fff;margin:0;font-size:1.7rem;'>🏗 Obras Públicas – Ciudad de Buenos Aires</h1>
  <p style='color:#64748B;margin:5px 0 0;font-size:.88rem;'>
    {data['n_obras_actuales']} obras registradas · ${data['monto_total_actual_M']:,.0f}M comprometidos · BA Obras + AGC
  </p>
</div>""", unsafe_allow_html=True)

# ── KPIs ────────────────────────────────────────────────────────────────
n_hist = len(data["obras_historicas"])
n_oi   = sum(r["n"] for r in data["obras_iniciadas_por_comuna"])
top_jur = df_jur.iloc[0] if len(df_jur) else {}

k1,k2,k3,k4,k5 = st.columns(5)
kpis = [
    (k1, str(n_ejecucion),          "En ejecución",         "#F59E0B", "obras activas"),
    (k2, f"${data['monto_total_actual_M']/1e6:,.1f}B", "Inversión total",  "#F97316", "miles de millones $"),
    (k3, str(data["obras_por_estado"].get("Finalizada",0)), "Finalizadas", "#4ADE80", "BA Obras actuales"),
    (k4, f"{n_hist:,}",             "Históricas (BA Obras)", "#38BDF8", "licitaciones 2010-2025"),
    (k5, f"{n_oi:,}",               "Obras privadas AGC",   "#A78BFA", "registradas en comunas"),
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

tab1, tab2, tab3 = st.tabs(["🗺 Mapa de Obras", "📊 Por Jurisdicción & Estado", "📈 Evolución Histórica"])

# ══════════════════════════════════════════════════════════════════════
# TAB 1 – MAPA
# ══════════════════════════════════════════════════════════════════════
with tab1:
    col_m, col_l = st.columns([3, 2])
    with col_m:
        m = folium.Map(location=[-34.615, -58.443], zoom_start=12, tiles=None)
        folium.TileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
                         attr="© CARTO", max_zoom=19).add_to(m)

        # Obras actuales con coords
        filt = obras_act if est_sel == "Todos" else [o for o in obras_act if o["estado"] == est_sel]
        for o in filt:
            if not o.get("lat"): continue
            clr = ESTADO_COLOR.get(o["estado"],"#64748B")
            av  = o.get("avance_pct") or 0
            tip = (f"<b>{o['nombre'][:50]}</b><br>"
                   f"{o['jurisdiccion']}<br>"
                   f"Estado: <b style='color:{clr}'>{o['estado']}</b><br>"
                   f"Avance: {av:.0f}%<br>"
                   f"Empresa: {o.get('empresa','')[:30]}")
            folium.CircleMarker(
                location=[o["lat"], o["lon"]],
                radius=6 if o["estado"]=="En ejecución" else 5,
                color=clr, fill=True, fill_color=clr, fill_opacity=0.85,
                tooltip=folium.Tooltip(tip, sticky=False),
            ).add_to(m)

        # Obras históricas (punto más pequeño)
        for o in data["obras_historicas"]:
            if not o.get("lat"): continue
            folium.CircleMarker(
                location=[o["lat"], o["lon"]],
                radius=3, color="#1E3A5F", fill=True, fill_color="#334155", fill_opacity=0.4,
                tooltip=folium.Tooltip(f"<b>{o['nombre'][:40]}</b><br>{o.get('area','')}<br>{o.get('estado','')}", sticky=False),
            ).add_to(m)

        st_folium(m, height=520, use_container_width=True,
                  returned_objects=[], key=f"obras_map_{est_sel}")

        st.markdown("<div style='font-size:.65rem;color:#334155;'>Puntos brillantes = obras actuales BA Obras · Puntos grises = históricas</div>",
                    unsafe_allow_html=True)

    with col_l:
        st.markdown("#### Obras en ejecución")
        obras_ej = sorted([o for o in obras_act if o["estado"]=="En ejecución" and o.get("lat")],
                          key=lambda x: -(x.get("avance_pct") or 0))
        for o in obras_ej[:18]:
            av  = o.get("avance_pct") or 0
            av_pct = min(int(av), 100)
            clr = "#4ADE80" if av>=75 else "#FBBF24" if av>=40 else "#F97316"
            jur_short = o["jurisdiccion"].replace("Ministerio de ","Min. ")[:22]
            st.markdown(
                f"<div style='margin-bottom:6px;padding:7px 10px;background:#0A1628;"
                f"border:1px solid #1E293B;border-radius:6px;'>"
                f"<div style='font-size:.72rem;color:#E2E8F0;font-weight:600;'>{o['nombre'][:44]}</div>"
                f"<div style='font-size:.62rem;color:#475569;margin-bottom:4px;'>{jur_short}</div>"
                f"<div style='display:flex;align-items:center;gap:8px;'>"
                f"<div style='flex:1;background:#1E293B;border-radius:3px;height:5px;'>"
                f"<div style='background:{clr};height:5px;width:{av_pct}%;border-radius:3px;'></div></div>"
                f"<span style='font-size:.68rem;color:{clr};font-weight:700;'>{av:.0f}%</span>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════════════════════════════
# TAB 2 – POR JURISDICCIÓN & ESTADO
# ══════════════════════════════════════════════════════════════════════
with tab2:
    c1, c2 = st.columns(2)
    with c1:
        fig_jur = go.Figure(go.Bar(
            y=[r["jurisdiccion"].replace("Ministerio de ","Min. ")[:30] for r in data["obras_por_jurisdiccion"]],
            x=[r["n"] for r in data["obras_por_jurisdiccion"]],
            orientation="h",
            marker_color="#F59E0B",
            text=[r["n"] for r in data["obras_por_jurisdiccion"]],
            textposition="outside", textfont=dict(color="#E2E8F0",size=9),
        ))
        fig_jur.update_layout(
            title=dict(text="Obras por jurisdicción (cantidad)",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B", categoryorder="total ascending"),
            margin=dict(t=35,b=5,l=5,r=50), height=400, showlegend=False,
        )
        st.plotly_chart(fig_jur, use_container_width=True)

    with c2:
        # Monto por jurisdicción
        df_jur_m = pd.DataFrame(data["obras_por_jurisdiccion"])
        df_jur_m = df_jur_m[df_jur_m["monto_M"].notna()].sort_values("monto_M", ascending=True)
        fig_mont = go.Figure(go.Bar(
            y=df_jur_m["jurisdiccion"].str.replace("Ministerio de ","Min. ").str[:30],
            x=df_jur_m["monto_M"],
            orientation="h",
            marker_color="#F97316",
            text=df_jur_m["monto_M"].apply(lambda x: f"${x:,.0f}M"),
            textposition="outside", textfont=dict(color="#E2E8F0",size=9),
        ))
        fig_mont.update_layout(
            title=dict(text="Monto comprometido por jurisdicción ($M)",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=35,b=5,l=5,r=70), height=400, showlegend=False,
        )
        st.plotly_chart(fig_mont, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        # Donut por estado
        est_data = data["obras_por_estado"]
        fig_est = go.Figure(go.Pie(
            labels=list(est_data.keys()), values=list(est_data.values()),
            hole=0.5,
            marker_colors=[ESTADO_COLOR.get(k,"#64748B") for k in est_data.keys()],
        ))
        fig_est.update_layout(
            title=dict(text="Distribución por estado",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=8)),
            margin=dict(t=35,b=5,l=5,r=5), height=300,
        )
        st.plotly_chart(fig_est, use_container_width=True)

    with c4:
        # Por tipo de procedimiento
        tp = data["obras_por_tipo_proc"]
        fig_tp = go.Figure(go.Bar(
            x=list(tp.keys()), y=list(tp.values()),
            marker_color="#38BDF8",
            text=list(tp.values()), textposition="outside",
            textfont=dict(color="#E2E8F0",size=10),
        ))
        fig_tp.update_layout(
            title=dict(text="Por tipo de procedimiento",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B", tickangle=20),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=35,b=5,l=5,r=5), height=300, showlegend=False,
        )
        st.plotly_chart(fig_tp, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 3 – EVOLUCIÓN HISTÓRICA
# ══════════════════════════════════════════════════════════════════════
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        fig_han = go.Figure()
        fig_han.add_trace(go.Bar(
            x=df_hist_anio["anio"].astype(str), y=df_hist_anio["n"],
            name="Nº licitaciones", marker_color="#38BDF8", opacity=0.7,
            text=df_hist_anio["n"], textposition="outside",
            textfont=dict(color="#E2E8F0",size=8),
        ))
        fig_han.add_trace(go.Scatter(
            x=df_hist_anio["anio"].astype(str), y=df_hist_anio["monto_M"],
            name="Monto ($M)", mode="lines+markers",
            line=dict(color="#F59E0B",width=2.5), marker=dict(size=6),
            yaxis="y2",
        ))
        fig_han.update_layout(
            title=dict(text="Licitaciones anuales y monto comprometido (histórico)",
                       font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B", title="Nº obras"),
            yaxis2=dict(title="Monto $M", side="right", overlaying="y", showgrid=False),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
            margin=dict(t=35,b=5,l=5,r=5), height=360,
        )
        st.plotly_chart(fig_han, use_container_width=True)

    with c2:
        # Por área (entorno)
        fig_area = go.Figure(go.Bar(
            y=[r["area"][:30] for r in data["historico_por_area"]],
            x=[r["monto_M"] for r in data["historico_por_area"]],
            orientation="h", marker_color="#F97316",
            text=[f"${r['monto_M']:,.0f}M" for r in data["historico_por_area"]],
            textposition="outside", textfont=dict(color="#E2E8F0",size=9),
        ))
        fig_area.update_layout(
            title=dict(text="Inversión histórica por área",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B", categoryorder="total ascending"),
            margin=dict(t=35,b=5,l=5,r=65), height=360, showlegend=False,
        )
        st.plotly_chart(fig_area, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        # Históricas por commune
        fig_com = go.Figure(go.Bar(
            x=[f"C{r['comuna']:02d}" for r in sorted(data["historico_por_comuna"], key=lambda x:x["comuna"])],
            y=[r["monto_M"] for r in sorted(data["historico_por_comuna"], key=lambda x:x["comuna"])],
            marker_color="#A78BFA",
            text=[f"${r['monto_M']:.0f}M" for r in sorted(data["historico_por_comuna"], key=lambda x:x["comuna"])],
            textposition="outside", textfont=dict(color="#E2E8F0",size=8),
        ))
        fig_com.update_layout(
            title=dict(text="Inversión histórica por commune ($M)",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=35,b=5,l=5,r=5), height=300, showlegend=False,
        )
        st.plotly_chart(fig_com, use_container_width=True)

    with c4:
        # Obras privadas iniciadas (AGC) por commune
        df_oi = df_oi_com.sort_values("n", ascending=False)
        fig_oi = go.Figure(go.Bar(
            x=df_oi["comuna"].apply(lambda c: f"C{int(c):02d}"),
            y=df_oi["n"],
            marker_color="#22D3EE",
            text=df_oi["n"], textposition="outside", textfont=dict(color="#E2E8F0",size=8),
        ))
        fig_oi.update_layout(
            title=dict(text="Obras privadas iniciadas (AGC) por commune",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=35,b=5,l=5,r=5), height=300, showlegend=False,
        )
        st.plotly_chart(fig_oi, use_container_width=True)

st.markdown("---")
st.caption("Fuente: BA Obras – Secretaría Legal y Técnica GCBA · "
           "AGC – Obras Iniciadas (registro de permisos) · "
           "Secretaría de Desarrollo Urbano – SOA (Seguimiento de Obras Adjudicadas).")
