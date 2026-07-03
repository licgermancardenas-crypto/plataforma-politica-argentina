"""
Página 4 – Economía e Indicadores (INDEC – datos en tiempo real)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from core import apis

st.set_page_config(page_title="Economía & Indicadores", page_icon="📈", layout="wide")
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #1F3864; }
[data-testid="stSidebar"] * { color: #FFF !important; }
.live-pill { background:#E8F5E9; color:#1B5E20; padding:3px 12px; border-radius:20px; font-size:.8rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

st.title("📈 Economía & Indicadores")
st.markdown("<span class='live-pill'>● Datos en tiempo real desde apis.datos.gob.ar (INDEC)</span>", unsafe_allow_html=True)
st.caption("Contexto económico nacional · fuente: INDEC Series de Tiempo · actualización automática cada hora")

if st.button("🔄 Refrescar indicadores"):
    apis.get_ipc.clear()
    apis.get_ipc_alimentos.clear()
    apis.get_dolar_oficial.clear()
    apis.get_emae.clear()
    st.rerun()

# ── Carga de datos ─────────────────────────────────────────────────────
with st.spinner("Consultando INDEC..."):
    ipc_df   = apis.get_ipc(months=25)
    alim_df  = apis.get_ipc_alimentos(months=25)
    dolar_df = apis.get_dolar_oficial(months=25)
    emae_df  = apis.get_emae(months=37)

# ── KPIs principales ───────────────────────────────────────────────────
if ipc_df is not None and not ipc_df.empty:
    ipc_clean = ipc_df.dropna(subset=['var_mensual_pct'])
    last_row = ipc_clean.iloc[-1]
    prev_row = ipc_clean.iloc[-2] if len(ipc_clean) > 1 else None

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        f"IPC Mensual – {last_row['fecha'].strftime('%b %Y')}",
        f"{last_row['var_mensual_pct']:.1f}%",
        delta=f"{last_row['var_mensual_pct'] - prev_row['var_mensual_pct']:.1f}pp" if prev_row is not None else None,
        delta_color="inverse",
    )
    if pd.notna(last_row.get('var_interanual_pct')):
        k2.metric("IPC Interanual", f"{last_row['var_interanual_pct']:.1f}%")

    if dolar_df is not None and not dolar_df.empty:
        d_last = dolar_df.iloc[-1]
        d_prev = dolar_df.iloc[-2] if len(dolar_df) > 1 else None
        k3.metric(
            f"Tipo de cambio – {d_last['fecha'].strftime('%b %Y')}",
            f"$ {d_last['valor']:,.0f}",
            delta=f"{d_last['valor'] - d_prev['valor']:,.0f}" if d_prev is not None else None,
            delta_color="inverse",
        )

    if alim_df is not None and not alim_df.empty:
        alim_clean = alim_df.copy()
        alim_clean['var'] = alim_clean['valor'].pct_change() * 100
        a_last = alim_clean.dropna(subset=['var']).iloc[-1]
        k4.metric(f"IPC Alimentos – {a_last['fecha'].strftime('%b %Y')}", f"{a_last['var']:.1f}%")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════
# IPC – INFLACIÓN MENSUAL
# ══════════════════════════════════════════════════════════════════════
st.subheader("Inflación mensual – IPC Nivel General")
n_meses = st.slider("Meses a mostrar", 6, 24, 12, key='ipc_slider')

if ipc_df is not None and not ipc_df.empty:
    plot_df = ipc_df.dropna(subset=['var_mensual_pct']).tail(n_meses)

    fig_ipc = go.Figure()
    colors = ['#E53935' if v > 6 else '#FF7043' if v > 4 else '#FFA726' if v > 2 else '#66BB6A'
              for v in plot_df['var_mensual_pct']]
    fig_ipc.add_trace(go.Bar(
        x=plot_df['fecha'].dt.strftime('%b %Y'),
        y=plot_df['var_mensual_pct'].round(1),
        marker_color=colors,
        text=plot_df['var_mensual_pct'].round(1).astype(str) + '%',
        textposition='outside',
        name='Variación mensual',
    ))
    # Trend line
    fig_ipc.add_trace(go.Scatter(
        x=plot_df['fecha'].dt.strftime('%b %Y'),
        y=plot_df['var_mensual_pct'].rolling(3, min_periods=1).mean().round(1),
        mode='lines', name='Media móvil 3M',
        line=dict(color='#1F3864', width=2, dash='dash'),
    ))
    fig_ipc.update_layout(
        yaxis_title='Variación mensual (%)', xaxis_title='',
        height=380, margin=dict(t=10,b=10,l=10,r=10),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(248,249,250,1)',
        yaxis=dict(gridcolor='#E0E0E0'),
        legend=dict(orientation='h', y=1.05),
    )
    st.plotly_chart(fig_ipc, use_container_width=True)
else:
    st.error("No se pudo obtener datos del IPC desde INDEC en este momento.")

# ══════════════════════════════════════════════════════════════════════
# COMPARACIÓN IPC vs IPC ALIMENTOS
# ══════════════════════════════════════════════════════════════════════
if ipc_df is not None and alim_df is not None:
    st.subheader("IPC General vs. Alimentos y Bebidas")

    alim_df = alim_df.copy()
    alim_df['var_mensual_pct'] = alim_df['valor'].pct_change() * 100
    ipc_last = ipc_df.dropna(subset=['var_mensual_pct']).tail(n_meses)
    alim_last = alim_df.dropna(subset=['var_mensual_pct']).tail(n_meses)

    if not alim_last.empty:
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Scatter(
            x=ipc_last['fecha'].dt.strftime('%b %Y'),
            y=ipc_last['var_mensual_pct'].round(1),
            mode='lines+markers', name='IPC General',
            line=dict(color='#1565C0', width=2.5),
        ))
        fig_comp.add_trace(go.Scatter(
            x=alim_last['fecha'].dt.strftime('%b %Y'),
            y=alim_last['var_mensual_pct'].round(1),
            mode='lines+markers', name='Alimentos y Bebidas',
            line=dict(color='#E53935', width=2.5),
        ))
        fig_comp.update_layout(
            yaxis_title='Variación mensual (%)', xaxis_title='',
            height=320, margin=dict(t=10,b=10,l=10,r=10),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(248,249,250,1)',
            yaxis=dict(gridcolor='#E0E0E0'),
            legend=dict(orientation='h', y=1.1),
        )
        st.plotly_chart(fig_comp, use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════
# TIPO DE CAMBIO
# ══════════════════════════════════════════════════════════════════════
if dolar_df is not None and not dolar_df.empty:
    st.subheader("Tipo de cambio oficial ($/USD)")
    dolar_plot = dolar_df.tail(24)
    fig_tc = px.line(dolar_plot, x='fecha', y='valor',
                     labels={'valor': 'Pesos por USD', 'fecha': ''},
                     color_discrete_sequence=['#1B5E20'])
    fig_tc.update_traces(line_width=2.5)
    fig_tc.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10),
                         paper_bgcolor='rgba(0,0,0,0)',
                         plot_bgcolor='rgba(248,249,250,1)',
                         yaxis=dict(gridcolor='#E0E0E0'))
    st.plotly_chart(fig_tc, use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════
# EMAE – ACTIVIDAD ECONÓMICA
# ══════════════════════════════════════════════════════════════════════
if emae_df is not None and not emae_df.empty:
    st.subheader("EMAE – Estimador Mensual de Actividad Económica")
    emae_plot = emae_df.tail(36)
    fig_emae = px.area(emae_plot, x='fecha', y='valor',
                       labels={'valor': 'Índice (base 2004=100)', 'fecha': ''},
                       color_discrete_sequence=['#6A1B9A'])
    fig_emae.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10),
                           paper_bgcolor='rgba(0,0,0,0)',
                           plot_bgcolor='rgba(248,249,250,1)',
                           yaxis=dict(gridcolor='#E0E0E0'))
    st.plotly_chart(fig_emae, use_container_width=True)

st.markdown("---")
st.caption("Todos los indicadores provienen del INDEC a través de la API pública apis.datos.gob.ar · Se actualizan automáticamente")
