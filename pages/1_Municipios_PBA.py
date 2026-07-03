"""
Página 1 – Municipios PBA
Intendentes, secretarios y concejales de los 135 municipios.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.express as px
import pandas as pd
from core import loader

st.set_page_config(page_title="Municipios PBA", page_icon="🗺", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #1F3864; }
[data-testid="stSidebar"] * { color: #FFF !important; }
.tag {
    display:inline-block; padding:2px 10px; border-radius:20px;
    font-size:0.78rem; font-weight:600; margin:2px;
}
</style>
""", unsafe_allow_html=True)

st.title("🗺 Municipios de la Provincia de Buenos Aires")
st.caption("135 municipios · período 2023-2027 · fuente: JEPBA, datos.gba.gob.ar")

df = loader.get_intendentes_df()
secretarios = loader.get_secretarios()
df_conc = loader.get_concejales_df()

# ── Filtros ────────────────────────────────────────────────────────────
with st.expander("🔍 Filtros", expanded=True):
    fc1, fc2, fc3 = st.columns(3)
    secciones = ['Todas'] + sorted(df['seccion_nombre'].dropna().unique().tolist())
    bloques   = ['Todos'] + sorted(df['bloque'].dropna().unique().tolist())
    with fc1:
        sec_sel = st.selectbox("Sección electoral", secciones)
    with fc2:
        bloque_sel = st.selectbox("Bloque político", bloques)
    with fc3:
        buscar = st.text_input("Buscar municipio o intendente", "")

filtered = df.copy()
if sec_sel    != 'Todas': filtered = filtered[filtered['seccion_nombre'] == sec_sel]
if bloque_sel != 'Todos': filtered = filtered[filtered['bloque'] == bloque_sel]
if buscar:
    q = buscar.lower()
    filtered = filtered[
        filtered['municipio'].str.lower().str.contains(q) |
        filtered['intendente'].str.lower().str.contains(q)
    ]

st.markdown(f"**{len(filtered)}** municipios encontrados")

# ── Tabla principal ────────────────────────────────────────────────────
display_cols = {
    'municipio':     'Municipio',
    'intendente':    'Intendente/a',
    'partido':       'Partido',
    'bloque':        'Bloque',
    'seccion_nombre':'Sección',
    'ganador_pct':   '% Ganó',
    'margen':        'Margen %',
    'n_concejales':  'Concejales',
    'n_secretarios': 'Secretarios',
}
st.dataframe(
    filtered[list(display_cols.keys())].rename(columns=display_cols),
    use_container_width=True, hide_index=True,
    column_config={
        '% Ganó':   st.column_config.NumberColumn(format="%.1f%%"),
        'Margen %': st.column_config.NumberColumn(format="%.1f%%"),
    }
)

# ── Gráficos ───────────────────────────────────────────────────────────
st.markdown("---")
gc1, gc2 = st.columns(2)

with gc1:
    st.subheader("Por sección electoral")
    sec_counts = filtered.groupby('seccion_nombre').size().reset_index(name='municipios')
    fig = px.bar(sec_counts.sort_values('municipios'), x='municipios', y='seccion_nombre',
                 orientation='h', text='municipios', color_discrete_sequence=['#1F3864'])
    fig.update_layout(yaxis_title='', xaxis_title='Municipios', height=300, margin=dict(t=5,b=5,l=5,r=5))
    st.plotly_chart(fig, use_container_width=True)

with gc2:
    st.subheader("Por bloque político")
    bc = loader.bloque_counts(filtered)
    fig2 = px.pie(bc, values='cantidad', names='bloque', hole=0.4,
                  color='bloque', color_discrete_map=loader.BLOQUE_COLOR)
    fig2.update_traces(textinfo='label+percent')
    fig2.update_layout(showlegend=False, height=300, margin=dict(t=5,b=5,l=5,r=5))
    st.plotly_chart(fig2, use_container_width=True)

# ── Detalle por municipio ──────────────────────────────────────────────
st.markdown("---")
st.subheader("🔎 Detalle de municipio")

municipios_lista = filtered['municipio'].sort_values().tolist()
if not municipios_lista:
    st.warning("No hay municipios que coincidan con los filtros.")
    st.stop()

muni_sel = st.selectbox("Seleccioná un municipio", municipios_lista)
row = filtered[filtered['municipio'] == muni_sel].iloc[0]

d1, d2, d3, d4 = st.columns(4)
d1.metric("Intendente/a", row['intendente'])
d2.metric("Partido", row['partido'][:30] + ('…' if len(row['partido']) > 30 else ''))
d3.metric("% votos 2023", f"{row['ganador_pct']}%")
d4.metric("Margen victoria", f"{row['margen']}%")

tab1, tab2, tab3 = st.tabs(["📋 Secretarios", "🗳 Concejales 2023", "📊 Resultado electoral"])

with tab1:
    secs = secretarios.get(muni_sel, [])
    if secs:
        st.dataframe(
            pd.DataFrame(secs)[['cargo', 'nombre']].rename(columns={'cargo': 'Cargo', 'nombre': 'Nombre'}),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Sin datos de secretarios para este municipio.")

with tab2:
    conc_muni = df_conc[df_conc['municipio'] == muni_sel].copy()
    if not conc_muni.empty:
        st.dataframe(
            conc_muni[['n_orden', 'nombre', 'partido', 'bloque']].rename(columns={
                'n_orden': '#', 'nombre': 'Concejal', 'partido': 'Partido/Lista', 'bloque': 'Bloque'
            }),
            use_container_width=True, hide_index=True
        )
        # Mini composición
        bc_c = loader.bloque_counts(conc_muni)
        fig_c = px.bar(bc_c, x='bloque', y='cantidad', color='bloque',
                       color_discrete_map=loader.BLOQUE_COLOR, text='cantidad')
        fig_c.update_layout(showlegend=False, height=220, xaxis_title='', yaxis_title='',
                            margin=dict(t=5,b=5,l=5,r=5))
        st.plotly_chart(fig_c, use_container_width=True)
    else:
        st.info("Sin datos de concejales.")

with tab3:
    col_a, col_b = st.columns(2)
    col_a.metric("Ganador 2023", row['ganador_2023'][:50] if pd.notna(row.get('ganador_2023')) else '–')
    col_a.metric("Votos %", f"{row['ganador_pct']}%")
    col_b.metric("2do lugar", row['segundo'][:50] if pd.notna(row.get('segundo')) else '–')
    col_b.metric("Votos % 2do", f"{row['segundo_pct']}%")
    if pd.notna(row.get('padron')) and row['padron'] > 0:
        st.metric("Padrón electoral 2023", f"{int(row['padron']):,}".replace(',', '.'))
