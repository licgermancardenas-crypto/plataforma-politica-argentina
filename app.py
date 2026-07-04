"""
Plataforma Política PBA – Dashboard principal
Datos estáticos: JEPBA, INDEC Censo 2022, datos.gba.gob.ar
Datos en vivo:   HCDN (Congreso Nacional) · INDEC Series de Tiempo
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from core import loader, apis

st.set_page_config(
    page_title="Plataforma Política PBA",
    page_icon="🏛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personalizado ──────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #F8F9FA; }
[data-testid="stSidebar"] { background: #1F3864; }
[data-testid="stSidebar"] * { color: #FFFFFF !important; }
.metric-card {
    background: white; border-radius: 12px; padding: 20px 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 5px solid;
    margin-bottom: 8px;
}
.metric-value { font-size: 2.2rem; font-weight: 700; margin: 0; }
.metric-label { font-size: 0.85rem; color: #666; margin: 0; text-transform: uppercase; letter-spacing: .5px; }
.section-header {
    font-size: 1.1rem; font-weight: 600; color: #1F3864;
    border-bottom: 2px solid #1F3864; padding-bottom: 6px; margin: 24px 0 16px;
}
.live-badge {
    background: #E8F5E9; color: #1B5E20; font-size: 0.75rem;
    padding: 2px 8px; border-radius: 20px; font-weight: 600;
}
.static-badge {
    background: #E3F2FD; color: #1565C0; font-size: 0.75rem;
    padding: 2px 8px; border-radius: 20px; font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏛 Plataforma Política PBA")
    st.markdown("---")
    st.markdown("**Navegación**")
    st.markdown("""
    - 🏠 Dashboard *(esta página)*
    - 🗺 Municipios PBA
    - 🏛 Congreso Nacional
    - 📊 Legisladores PBA
    - 📈 Economía & Indicadores
    - 🏙 CABA – Capital Federal
    - 🏛 Legisladores CABA
    - 🔴 Seguridad CABA
    - 📐 Socioeconomía CABA
    - 💰 Presupuesto CABA
    - 🛍 Mapa Comercial CABA
    - 🚇 Movilidad CABA
    - 📚 Educación & Calidad CABA
    - 🏗 Obras Públicas CABA
    - 🔍 Fiscalizaciones CABA
    - 👥 Demografía CABA
    - ♀ Género & Violencia CABA
    - 🎭 Turismo & Cultura CABA
    - 🌿 Medio Ambiente CABA
    """)
    st.markdown("---")
    st.markdown("**Fuentes de datos**")
    st.markdown("""
    <span class='live-badge'>● LIVE</span> **HCDN** – Congreso Nación
    <span class='live-badge'>● LIVE</span> **INDEC** – Series económicas
    <span class='static-badge'>◉ 2023</span> **JEPBA** – Escrutinio definitivo
    <span class='static-badge'>◉ 2022</span> **INDEC** – Censo nacional
    """, unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🔄 Refrescar datos live"):
        st.cache_data.clear()
        st.rerun()

# ── Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div style='background: linear-gradient(135deg,#1F3864,#2E5BBA); padding:28px 32px; border-radius:12px; margin-bottom:24px;'>
<h1 style='color:white; margin:0; font-size:1.9rem;'>🏛 Plataforma Política – Provincia de Buenos Aires</h1>
<p style='color:#B0C4DE; margin:6px 0 0; font-size:0.95rem;'>
Período 2023-2027 · Datos en tiempo real del Congreso Nacional y el INDEC
</p>
</div>
""", unsafe_allow_html=True)

# ── Carga de datos ─────────────────────────────────────────────────────
with st.spinner("Cargando datasets..."):
    df_int  = loader.get_intendentes_df()
    df_conc = loader.get_concejales_df()
    df_dprov = loader.get_diputados_prov_df()
    df_sprov = loader.get_senadores_prov_df()
    df_dnac  = loader.get_diputados_nac_df()

# Live data
bloques_live = apis.get_bloques_camara()
ipc_df       = apis.get_ipc(months=13)
dolares_hoy  = apis.get_dolares_hoy()
rp_ultimo    = apis.get_riesgo_pais_ultimo()

# ── KPI Cards – fila política ───────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

cards = [
    (col1, len(df_int),            "Municipios PBA",            "#1F3864", "🏙"),
    (col2, len(df_conc),           "Concejales electos 2023",   "#1B5E20", "🗳"),
    (col3, len(df_dprov)+len(df_sprov), "Legisladores PBA",     "#6A1B9A", "📜"),
    (col4, len(df_dnac),           "Diputados Nacionales PBA",  "#1565C0", "🏛"),
    (col5, bloques_live['CANTIDAD'].sum() if bloques_live is not None else "–",
           "Diputados Nac. totales ●",                          "#E65100", "🔴"),
]

for col, val, label, color, icon in cards:
    with col:
        st.markdown(f"""
        <div class='metric-card' style='border-left-color:{color};'>
          <p class='metric-label'>{icon} {label}</p>
          <p class='metric-value' style='color:{color};'>{val}</p>
        </div>
        """, unsafe_allow_html=True)

# ── KPI Cards – fila económica (ArgentinaDatos) ─────────────────────────
ec1, ec2, ec3, ec4, ec5 = st.columns(5)

_blue  = dolares_hoy[dolares_hoy['casa']=='blue'].iloc[0]   if dolares_hoy is not None and 'blue'   in dolares_hoy['casa'].values else None
_ofic  = dolares_hoy[dolares_hoy['casa']=='oficial'].iloc[0] if dolares_hoy is not None and 'oficial' in dolares_hoy['casa'].values else None
_ccl   = dolares_hoy[dolares_hoy['casa']=='contadoconliqui'].iloc[0] if dolares_hoy is not None and 'contadoconliqui' in dolares_hoy['casa'].values else None
_tarj  = dolares_hoy[dolares_hoy['casa']=='tarjeta'].iloc[0] if dolares_hoy is not None and 'tarjeta' in dolares_hoy['casa'].values else None

eco_cards = [
    (ec1, f"${_blue['venta']:,.0f}"  if _blue  is not None else "–", "Dólar Blue ●",     "#1E40AF", "💵"),
    (ec2, f"${_ofic['venta']:,.0f}"  if _ofic  is not None else "–", "Dólar Oficial ●",  "#065F46", "🏦"),
    (ec3, f"${_ccl['venta']:,.0f}"   if _ccl   is not None else "–", "Dólar CCL ●",      "#7C3AED", "📊"),
    (ec4, f"${_tarj['venta']:,.0f}"  if _tarj  is not None else "–", "Dólar Tarjeta ●",  "#9A3412", "💳"),
    (ec5, f"{rp_ultimo['valor']:,} pb" if rp_ultimo else "–",        "Riesgo País ●",    "#B91C1C", "🌡"),
]

for col, val, label, color, icon in eco_cards:
    with col:
        st.markdown(f"""
        <div class='metric-card' style='border-left-color:{color};'>
          <p class='metric-label'>{icon} {label}</p>
          <p class='metric-value' style='color:{color};font-size:1.6rem;'>{val}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ── Fila de gráficos: composición política ─────────────────────────────
c_izq, c_der = st.columns([1, 1])

with c_izq:
    st.markdown("<p class='section-header'>Intendentes por bloque político <span class='static-badge'>◉ 2023</span></p>", unsafe_allow_html=True)
    bc_int = loader.bloque_counts(df_int)
    fig_int = px.pie(
        bc_int, values='cantidad', names='bloque',
        color='bloque', color_discrete_map=loader.BLOQUE_COLOR,
        hole=0.45,
    )
    fig_int.update_traces(textposition='outside', textinfo='label+percent')
    fig_int.update_layout(
        showlegend=False, margin=dict(t=10, b=10, l=10, r=10),
        height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    )
    st.plotly_chart(fig_int, use_container_width=True)

with c_der:
    st.markdown("<p class='section-header'>Cámara de Diputados – bloques actuales <span class='live-badge'>● LIVE</span></p>", unsafe_allow_html=True)
    if bloques_live is not None and not bloques_live.empty:
        bloc_col = 'BLOQUE' if 'BLOQUE' in bloques_live.columns else bloques_live.columns[0]
        cant_col = 'CANTIDAD' if 'CANTIDAD' in bloques_live.columns else bloques_live.columns[-1]
        top_bloques = bloques_live.nlargest(8, cant_col)
        fig_blq = px.bar(
            top_bloques, x=cant_col, y=bloc_col, orientation='h',
            color=cant_col, color_continuous_scale='Blues',
            text=cant_col,
        )
        fig_blq.update_traces(textposition='outside')
        fig_blq.update_layout(
            showlegend=False, coloraxis_showscale=False,
            yaxis=dict(categoryorder='total ascending'),
            margin=dict(t=10, b=10, l=10, r=10),
            height=300, paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_blq, use_container_width=True)
    else:
        st.info("No se pudo conectar con datos.hcdn.gob.ar en este momento.")

# ── Concejales por bloque ──────────────────────────────────────────────
st.markdown("<p class='section-header'>Concejales 2023 – composición por bloque <span class='static-badge'>◉ JEPBA</span></p>", unsafe_allow_html=True)
bc_conc = loader.bloque_counts(df_conc)
fig_conc = px.bar(
    bc_conc.sort_values('cantidad', ascending=True),
    x='cantidad', y='bloque', orientation='h',
    color='bloque', color_discrete_map=loader.BLOQUE_COLOR,
    text='cantidad',
)
fig_conc.update_traces(textposition='outside')
fig_conc.update_layout(
    showlegend=False, yaxis_title='', xaxis_title='Concejales',
    margin=dict(t=10, b=10, l=10, r=10), height=250,
    paper_bgcolor='rgba(0,0,0,0)',
)
st.plotly_chart(fig_conc, use_container_width=True)

# ── IPC Últimas tendencias ─────────────────────────────────────────────
if ipc_df is not None and not ipc_df.empty:
    st.markdown("<p class='section-header'>Inflación – IPC Nivel General últimos 12 meses <span class='live-badge'>● INDEC live</span></p>", unsafe_allow_html=True)
    ipc_plot = ipc_df.dropna(subset=['var_mensual_pct']).tail(12)
    fig_ipc = go.Figure()
    fig_ipc.add_trace(go.Bar(
        x=ipc_plot['fecha'].dt.strftime('%b %Y'),
        y=ipc_plot['var_mensual_pct'].round(1),
        marker_color=['#E53935' if v > 5 else '#FF7043' if v > 3 else '#66BB6A'
                      for v in ipc_plot['var_mensual_pct']],
        text=ipc_plot['var_mensual_pct'].round(1).astype(str) + '%',
        textposition='outside',
    ))
    fig_ipc.update_layout(
        yaxis_title='Variación mensual (%)', xaxis_title='',
        margin=dict(t=10, b=10, l=10, r=10), height=260,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(248,249,250,1)',
        yaxis=dict(gridcolor='#E0E0E0'),
    )
    st.plotly_chart(fig_ipc, use_container_width=True)

# ── Resumen rápido ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown("<p class='section-header'>Resumen político – Provincia de Buenos Aires 2023-2027</p>", unsafe_allow_html=True)

r1, r2 = st.columns(2)
with r1:
    st.markdown("**Intendentes por bloque**")
    bc_table = loader.bloque_counts(df_int).rename(columns={'cantidad': 'Municipios'})
    st.dataframe(bc_table[['bloque', 'Municipios']].rename(columns={'bloque': 'Bloque'}),
                 hide_index=True, use_container_width=True)

with r2:
    st.markdown("**Diputados nacionales PBA por bloque**")
    bc_dnac = loader.bloque_counts(df_dnac)
    st.dataframe(bc_dnac[['bloque', 'cantidad']].rename(columns={'bloque': 'Bloque', 'cantidad': 'Diputados'}),
                 hide_index=True, use_container_width=True)

st.caption("Datos legislativos estáticos: composición al 10/12/2023. Datos HCDN y INDEC: en tiempo real con actualización cada 30 minutos.")
