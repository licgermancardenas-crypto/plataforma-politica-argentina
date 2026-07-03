"""
Página 4 – Economía & Indicadores
Fuentes: INDEC (series de tiempo) + ArgentinaDatos (dólar, riesgo país, inflación BCRA)
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
.live-pill  { background:#E8F5E9; color:#1B5E20; padding:3px 10px; border-radius:20px; font-size:.78rem; font-weight:600; }
.src-pill   { background:#E3F2FD; color:#1565C0; padding:3px 10px; border-radius:20px; font-size:.78rem; font-weight:600; margin-left:6px; }
.dolar-card {
    background: #0F172A; border: 1px solid #1E293B; border-radius: 10px;
    padding: 12px 14px; text-align: center;
}
.dolar-label { font-size:.65rem; color:#475569; text-transform:uppercase; letter-spacing:.1em; }
.dolar-venta { font-size:1.3rem; font-weight:800; color:#E2E8F0; line-height:1.1; }
.dolar-compra { font-size:.75rem; color:#64748B; margin-top:2px; }
.dolar-fecha  { font-size:.6rem;  color:#334155; margin-top:3px; }
</style>
""", unsafe_allow_html=True)

st.title("📈 Economía & Indicadores")

if st.button("🔄 Refrescar datos"):
    st.cache_data.clear()
    st.rerun()

# ═══════════════════════════════════════════════════════════════════════
# CARGA DE DATOS
# ═══════════════════════════════════════════════════════════════════════
with st.spinner("Cargando indicadores..."):
    dolares_df      = apis.get_dolares_hoy()
    rp_df           = apis.get_riesgo_pais(dias=365)
    rp_ultimo       = apis.get_riesgo_pais_ultimo()
    inf_bcra        = apis.get_inflacion_bcra(meses=36)
    inf_interanual  = apis.get_inflacion_interanual_bcra()
    ipc_df          = apis.get_ipc(months=25)
    alim_df         = apis.get_ipc_alimentos(months=25)
    dolar_oficial_df= apis.get_dolar_oficial(months=25)
    emae_df         = apis.get_emae(months=37)

# ═══════════════════════════════════════════════════════════════════════
# KPIs SUPERIORES
# ═══════════════════════════════════════════════════════════════════════
kpi_cols = st.columns(5)

# IPC último
if ipc_df is not None and not ipc_df.empty:
    ipc_clean = ipc_df.dropna(subset=['var_mensual_pct'])
    last_ipc  = ipc_clean.iloc[-1]
    prev_ipc  = ipc_clean.iloc[-2] if len(ipc_clean) > 1 else None
    kpi_cols[0].metric(
        f"IPC Mensual ({last_ipc['fecha'].strftime('%b %Y')})",
        f"{last_ipc['var_mensual_pct']:.1f}%",
        delta=f"{last_ipc['var_mensual_pct'] - prev_ipc['var_mensual_pct']:.1f}pp" if prev_ipc is not None else None,
        delta_color="inverse",
    )
    if pd.notna(last_ipc.get('var_interanual_pct')):
        kpi_cols[1].metric("IPC Interanual", f"{last_ipc['var_interanual_pct']:.1f}%")
elif inf_bcra is not None and not inf_bcra.empty:
    last_inf = inf_bcra.iloc[-1]
    kpi_cols[0].metric(f"Inflación BCRA ({last_inf['fecha'].strftime('%b %Y')})", f"{last_inf['var_mensual_pct']:.1f}%")
    if inf_interanual is not None:
        kpi_cols[1].metric("Inflación interanual", f"{inf_interanual['valor']:.1f}%")

# Riesgo país
if rp_ultimo:
    rp_df_tail = rp_df.tail(2) if rp_df is not None and len(rp_df) >= 2 else None
    delta_rp = f"{rp_ultimo['valor'] - rp_df_tail.iloc[-2]['valor']:+.0f}" if rp_df_tail is not None else None
    kpi_cols[2].metric("Riesgo País", f"{rp_ultimo['valor']:,.0f} pb",
                       delta=delta_rp, delta_color="inverse")

# Dólar blue y oficial hoy
if dolares_df is not None and not dolares_df.empty:
    blue = dolares_df[dolares_df['casa'] == 'blue']
    ofic = dolares_df[dolares_df['casa'] == 'oficial']
    if not blue.empty:
        kpi_cols[3].metric("Dólar Blue (venta)", f"${blue.iloc[0]['venta']:,.0f}")
    if not ofic.empty:
        kpi_cols[4].metric("Dólar Oficial (venta)", f"${ofic.iloc[0]['venta']:,.0f}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
# PANEL DÓLAR – TODOS LOS TIPOS HOY
# ═══════════════════════════════════════════════════════════════════════
st.markdown("### 💵 Dólar · cotizaciones del día")
st.markdown("<span class='live-pill'>● LIVE</span><span class='src-pill'>ArgentinaDatos</span>", unsafe_allow_html=True)

ORDEN_DOLAR = ['oficial', 'blue', 'bolsa', 'contadoconliqui', 'mayorista', 'tarjeta', 'cripto']
COLORES = {
    'oficial':        '#22C55E',
    'blue':           '#3B82F6',
    'bolsa':          '#8B5CF6',
    'contadoconliqui':'#F59E0B',
    'mayorista':      '#06B6D4',
    'tarjeta':        '#EF4444',
    'cripto':         '#A78BFA',
}

if dolares_df is not None and not dolares_df.empty:
    ordered = [dolares_df[dolares_df['casa'] == c] for c in ORDEN_DOLAR if c in dolares_df['casa'].values]
    ordered = [x.iloc[0] for x in ordered if not x.empty]

    cols_d = st.columns(len(ordered))
    for col, row in zip(cols_d, ordered):
        clr = COLORES.get(row['casa'], '#475569')
        fecha_str = row['fecha'].strftime('%d/%m') if pd.notna(row['fecha']) else ''
        col.markdown(f"""
<div class="dolar-card" style="border-top:3px solid {clr};">
  <div class="dolar-label">{row['label']}</div>
  <div class="dolar-venta" style="color:{clr};">${row['venta']:,.0f}</div>
  <div class="dolar-compra">Compra ${row['compra']:,.0f}</div>
  <div class="dolar-fecha">{fecha_str}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráfico histórico comparativo: blue vs oficial vs CCL
    st.markdown("#### Evolución histórica")
    casas_hist = st.multiselect(
        "Tipos a comparar",
        options=['blue', 'oficial', 'bolsa', 'contadoconliqui', 'mayorista', 'tarjeta', 'cripto'],
        default=['blue', 'oficial', 'bolsa'],
        format_func=lambda x: {'oficial': 'Oficial', 'blue': 'Blue', 'bolsa': 'Bolsa (MEP)',
                                'contadoconliqui': 'CCL', 'mayorista': 'Mayorista',
                                'tarjeta': 'Tarjeta', 'cripto': 'Cripto'}.get(x, x),
    )
    dias_hist = st.slider("Días a mostrar", 30, 730, 365, key='dolar_dias')

    fig_dol = go.Figure()
    for casa in casas_hist:
        hist = apis.get_dolares_historico(casa, dias_hist)
        if hist is not None and not hist.empty:
            fig_dol.add_trace(go.Scatter(
                x=hist['fecha'], y=hist['venta'],
                name={'oficial': 'Oficial', 'blue': 'Blue', 'bolsa': 'Bolsa (MEP)',
                      'contadoconliqui': 'CCL', 'mayorista': 'Mayorista',
                      'tarjeta': 'Tarjeta', 'cripto': 'Cripto'}.get(casa, casa),
                line=dict(color=COLORES.get(casa, '#888'), width=2),
                mode='lines',
            ))
    fig_dol.update_layout(
        yaxis_title='Pesos por USD (venta)',
        height=360, margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(248,249,250,1)',
        yaxis=dict(gridcolor='#E0E0E0'),
        legend=dict(orientation='h', y=1.08),
        hovermode='x unified',
    )
    st.plotly_chart(fig_dol, use_container_width=True)
else:
    st.warning("No se pudieron obtener cotizaciones del dólar.")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
# RIESGO PAÍS
# ═══════════════════════════════════════════════════════════════════════
st.markdown("### 🌡 Riesgo País (EMBI Argentina)")
st.markdown("<span class='live-pill'>● LIVE</span><span class='src-pill'>ArgentinaDatos · Ámbito</span>", unsafe_allow_html=True)

if rp_df is not None and not rp_df.empty:
    dias_rp = st.slider("Días a mostrar", 30, 365, 180, key='rp_dias')
    rp_plot = rp_df.tail(dias_rp)

    ultimo_val = rp_plot.iloc[-1]['valor']
    min_val    = rp_plot['valor'].min()
    max_val    = rp_plot['valor'].max()
    color_rp   = '#EF4444' if ultimo_val > 1000 else '#F59E0B' if ultimo_val > 600 else '#22C55E'

    fig_rp = go.Figure()
    fig_rp.add_trace(go.Scatter(
        x=rp_plot['fecha'], y=rp_plot['valor'],
        fill='tozeroy', fillcolor=f'{color_rp}22',
        line=dict(color=color_rp, width=2.5),
        name='Riesgo País',
        hovertemplate='%{x|%d/%m/%Y}: <b>%{y:,.0f} pb</b><extra></extra>',
    ))
    fig_rp.add_hline(y=ultimo_val, line_dash='dot', line_color=color_rp, opacity=0.6,
                     annotation_text=f"Hoy: {ultimo_val:,.0f} pb",
                     annotation_position='bottom right')
    fig_rp.update_layout(
        yaxis_title='Puntos básicos (pb)',
        height=320, margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(248,249,250,1)',
        yaxis=dict(gridcolor='#E0E0E0'),
        showlegend=False,
        hovermode='x unified',
    )
    st.plotly_chart(fig_rp, use_container_width=True)
    st.caption(f"Mín: {min_val:,.0f} pb · Máx: {max_val:,.0f} pb · Promedio: {rp_plot['valor'].mean():,.0f} pb (último período)")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
# INFLACIÓN MENSUAL
# ═══════════════════════════════════════════════════════════════════════
st.markdown("### 📊 Inflación mensual")

tab_inf1, tab_inf2 = st.tabs(["BCRA (ArgentinaDatos)", "INDEC (Series de tiempo)"])

with tab_inf1:
    st.markdown("<span class='live-pill'>● LIVE</span><span class='src-pill'>BCRA vía ArgentinaDatos</span>", unsafe_allow_html=True)
    if inf_bcra is not None and not inf_bcra.empty:
        n = st.slider("Meses a mostrar", 6, 36, 24, key='inf_bcra_n')
        plot = inf_bcra.tail(n)
        colors_inf = ['#E53935' if v > 6 else '#FF7043' if v > 4 else '#FFA726' if v > 2 else '#66BB6A'
                      for v in plot['var_mensual_pct']]
        fig_inf = go.Figure()
        fig_inf.add_trace(go.Bar(
            x=plot['fecha'].dt.strftime('%b %Y'), y=plot['var_mensual_pct'].round(1),
            marker_color=colors_inf,
            text=plot['var_mensual_pct'].round(1).astype(str) + '%', textposition='outside',
        ))
        fig_inf.add_trace(go.Scatter(
            x=plot['fecha'].dt.strftime('%b %Y'),
            y=plot['var_mensual_pct'].rolling(3, min_periods=1).mean().round(1),
            mode='lines', name='Media móvil 3M',
            line=dict(color='#1F3864', width=2, dash='dash'),
        ))
        fig_inf.update_layout(
            yaxis_title='Variación mensual (%)',
            height=360, margin=dict(t=10,b=10,l=10,r=10),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(248,249,250,1)',
            yaxis=dict(gridcolor='#E0E0E0'), showlegend=False,
        )
        st.plotly_chart(fig_inf, use_container_width=True)
        if inf_interanual is not None:
            st.caption(f"Inflación interanual (BCRA): **{inf_interanual['valor']:.1f}%** · {pd.to_datetime(inf_interanual['fecha']).strftime('%b %Y')}")

with tab_inf2:
    st.markdown("<span class='live-pill'>● LIVE</span><span class='src-pill'>INDEC Series de Tiempo</span>", unsafe_allow_html=True)
    if ipc_df is not None and not ipc_df.empty:
        n2 = st.slider("Meses a mostrar", 6, 24, 12, key='ipc_n')
        plot2 = ipc_df.dropna(subset=['var_mensual_pct']).tail(n2)
        colors2 = ['#E53935' if v > 6 else '#FF7043' if v > 4 else '#FFA726' if v > 2 else '#66BB6A'
                   for v in plot2['var_mensual_pct']]
        fig_ipc = go.Figure()
        fig_ipc.add_trace(go.Bar(
            x=plot2['fecha'].dt.strftime('%b %Y'), y=plot2['var_mensual_pct'].round(1),
            marker_color=colors2,
            text=plot2['var_mensual_pct'].round(1).astype(str) + '%', textposition='outside',
        ))
        fig_ipc.add_trace(go.Scatter(
            x=plot2['fecha'].dt.strftime('%b %Y'),
            y=plot2['var_mensual_pct'].rolling(3, min_periods=1).mean().round(1),
            mode='lines', name='Media móvil 3M',
            line=dict(color='#1F3864', width=2, dash='dash'),
        ))
        fig_ipc.update_layout(
            yaxis_title='Variación mensual (%)',
            height=360, margin=dict(t=10,b=10,l=10,r=10),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(248,249,250,1)',
            yaxis=dict(gridcolor='#E0E0E0'), showlegend=False,
        )
        st.plotly_chart(fig_ipc, use_container_width=True)

        # Comparación IPC General vs Alimentos
        if alim_df is not None:
            alim_df2 = alim_df.copy()
            alim_df2['var_mensual_pct'] = alim_df2['valor'].pct_change() * 100
            ipc_c  = ipc_df.dropna(subset=['var_mensual_pct']).tail(n2)
            alim_c = alim_df2.dropna(subset=['var_mensual_pct']).tail(n2)
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Scatter(
                x=ipc_c['fecha'].dt.strftime('%b %Y'), y=ipc_c['var_mensual_pct'].round(1),
                mode='lines+markers', name='IPC General', line=dict(color='#1565C0', width=2.5),
            ))
            fig_comp.add_trace(go.Scatter(
                x=alim_c['fecha'].dt.strftime('%b %Y'), y=alim_c['var_mensual_pct'].round(1),
                mode='lines+markers', name='Alimentos y Bebidas', line=dict(color='#E53935', width=2.5),
            ))
            fig_comp.update_layout(
                yaxis_title='Variación mensual (%)', height=300,
                margin=dict(t=10,b=10,l=10,r=10),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(248,249,250,1)',
                yaxis=dict(gridcolor='#E0E0E0'), legend=dict(orientation='h', y=1.1),
            )
            st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("INDEC no disponible en este momento.")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
# TIPO DE CAMBIO OFICIAL (INDEC) + EMAE
# ═══════════════════════════════════════════════════════════════════════
c_tc, c_emae = st.columns(2)

with c_tc:
    st.markdown("#### Tipo de cambio oficial – INDEC")
    st.markdown("<span class='src-pill'>INDEC</span>", unsafe_allow_html=True)
    if dolar_oficial_df is not None and not dolar_oficial_df.empty:
        fig_tc = px.line(dolar_oficial_df.tail(24), x='fecha', y='valor',
                         labels={'valor': 'Pesos por USD', 'fecha': ''},
                         color_discrete_sequence=['#1B5E20'])
        fig_tc.update_traces(line_width=2.5)
        fig_tc.update_layout(height=280, margin=dict(t=10,b=10,l=10,r=10),
                             paper_bgcolor='rgba(0,0,0,0)',
                             plot_bgcolor='rgba(248,249,250,1)',
                             yaxis=dict(gridcolor='#E0E0E0'))
        st.plotly_chart(fig_tc, use_container_width=True)

with c_emae:
    st.markdown("#### EMAE – Actividad Económica")
    st.markdown("<span class='src-pill'>INDEC</span>", unsafe_allow_html=True)
    if emae_df is not None and not emae_df.empty:
        fig_emae = px.area(emae_df.tail(36), x='fecha', y='valor',
                           labels={'valor': 'Índice (base 2004=100)', 'fecha': ''},
                           color_discrete_sequence=['#6A1B9A'])
        fig_emae.update_layout(height=280, margin=dict(t=10,b=10,l=10,r=10),
                               paper_bgcolor='rgba(0,0,0,0)',
                               plot_bgcolor='rgba(248,249,250,1)',
                               yaxis=dict(gridcolor='#E0E0E0'))
        st.plotly_chart(fig_emae, use_container_width=True)

st.markdown("---")
st.caption("Fuentes: ArgentinaDatos (api.argentinadatos.com) · INDEC (apis.datos.gob.ar) · BCRA · Ámbito · Actualización automática")
