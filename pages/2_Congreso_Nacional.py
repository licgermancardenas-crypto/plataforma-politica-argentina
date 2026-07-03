"""
Página 2 – Congreso Nacional (datos en tiempo real via HCDN API)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from core import apis, loader

st.set_page_config(page_title="Congreso Nacional", page_icon="🏛", layout="wide")
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #1F3864; }
[data-testid="stSidebar"] * { color: #FFF !important; }
.live-pill { background:#E8F5E9; color:#1B5E20; padding:3px 12px; border-radius:20px; font-size:.8rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

st.title("🏛 Congreso Nacional")
st.markdown("<span class='live-pill'>● Datos en tiempo real desde datos.hcdn.gob.ar</span>", unsafe_allow_html=True)
st.caption(f"Fuente: Portal de Datos Abiertos HCDN · Actualización automática cada 30 min")

if st.button("🔄 Actualizar datos"):
    apis.get_bloques_camara.clear()
    apis.get_composicion_bloques.clear()
    apis.get_votaciones_recientes.clear()
    apis.get_diputados_pba_actual.clear()
    st.rerun()

# ══════════════════════════════════════════════════════════════════════
# COMPOSICIÓN DE LA CÁMARA
# ══════════════════════════════════════════════════════════════════════
st.markdown("## Composición actual – Cámara de Diputados")

with st.spinner("Consultando HCDN..."):
    bloques_df  = apis.get_bloques_camara()
    comp_df     = apis.get_composicion_bloques()
    dip_pba     = apis.get_diputados_pba_actual()
    votaciones  = apis.get_votaciones_recientes(n=40)

if bloques_df is not None and not bloques_df.empty:
    bloc_col = next((c for c in bloques_df.columns if 'BLOQUE' in c), bloques_df.columns[0])
    cant_col = next((c for c in bloques_df.columns if 'CANT' in c), bloques_df.columns[-1])

    total_bancas = int(bloques_df[cant_col].sum())
    st.metric("Total bancas ocupadas", total_bancas)

    c1, c2 = st.columns([1, 1])

    with c1:
        fig_bl = px.pie(
            bloques_df, values=cant_col, names=bloc_col, hole=0.42,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_bl.update_traces(textinfo='label+value')
        fig_bl.update_layout(showlegend=False, height=380, margin=dict(t=10,b=10,l=10,r=10),
                             paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bl, use_container_width=True)

    with c2:
        top = bloques_df.nlargest(10, cant_col)
        fig_bar = px.bar(
            top, x=cant_col, y=bloc_col, orientation='h', text=cant_col,
            color=cant_col, color_continuous_scale='Blues',
        )
        fig_bar.update_traces(textposition='outside')
        fig_bar.update_layout(
            coloraxis_showscale=False, yaxis=dict(categoryorder='total ascending'),
            yaxis_title='', xaxis_title='Bancas',
            height=380, margin=dict(t=10,b=10,l=10,r=10),
            paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Tabla completa de bloques
    with st.expander("📋 Ver tabla completa de bloques"):
        st.dataframe(
            bloques_df.rename(columns={bloc_col: 'Bloque', cant_col: 'Bancas'})
                      .sort_values('Bancas', ascending=False),
            use_container_width=True, hide_index=True
        )
else:
    st.error("No se pudo obtener la composición de bloques desde datos.hcdn.gob.ar")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════
# DIPUTADOS DE BUENOS AIRES
# ══════════════════════════════════════════════════════════════════════
st.markdown("## Diputados/as de Buenos Aires en mandato vigente")

if dip_pba is not None and not dip_pba.empty:
    # Show key columns
    show_cols = [c for c in ['APELLIDO', 'NOMBRE', 'BLOQUE', 'INICIO', 'FIN'] if c in dip_pba.columns]
    if 'INICIO' in show_cols:
        dip_pba['INICIO'] = pd.to_datetime(dip_pba['INICIO'], errors='coerce').dt.strftime('%d/%m/%Y')
    if 'FIN' in show_cols:
        dip_pba['FIN_DT'] = pd.to_datetime(dip_pba['FIN'], errors='coerce')
        dip_pba['FIN'] = dip_pba['FIN_DT'].dt.strftime('%d/%m/%Y')
        dip_pba = dip_pba.sort_values('FIN_DT', ascending=False)

    # Filter by bloc
    bloques_pba = ['Todos'] + sorted(dip_pba['BLOQUE'].dropna().unique().tolist()) if 'BLOQUE' in dip_pba.columns else ['Todos']
    blq_sel = st.selectbox("Filtrar por bloque", bloques_pba)
    df_show = dip_pba if blq_sel == 'Todos' else dip_pba[dip_pba['BLOQUE'] == blq_sel]

    st.dataframe(
        df_show[show_cols].rename(columns={
            'APELLIDO': 'Apellido', 'NOMBRE': 'Nombre',
            'BLOQUE': 'Bloque', 'INICIO': 'Inicio', 'FIN': 'Vencimiento'
        }),
        use_container_width=True, hide_index=True,
    )

    # Composition of PBA deputies
    if 'BLOQUE' in dip_pba.columns:
        bc_pba = dip_pba['BLOQUE'].value_counts().reset_index()
        bc_pba.columns = ['Bloque', 'Diputados']
        fig_pba = px.bar(bc_pba.sort_values('Diputados'), x='Diputados', y='Bloque',
                         orientation='h', text='Diputados',
                         color_discrete_sequence=['#1565C0'])
        fig_pba.update_layout(yaxis=dict(categoryorder='total ascending'), height=280,
                              yaxis_title='', margin=dict(t=5,b=5,l=5,r=5),
                              paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_pba, use_container_width=True)
else:
    st.warning("No se pudo obtener el listado de diputados desde HCDN en este momento.")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════
# COMPOSICIÓN POR INTEGRANTES
# ══════════════════════════════════════════════════════════════════════
if comp_df is not None and not comp_df.empty:
    st.markdown("## Integrantes por bloque")

    bloc_c = next((c for c in comp_df.columns if 'BLOQUE' in c), comp_df.columns[0])
    ap_c   = next((c for c in comp_df.columns if 'APELL' in c), None)
    nom_c  = next((c for c in comp_df.columns if 'NOMBRE' in c or 'NOM' in c), None)
    per_c  = next((c for c in comp_df.columns if 'PERIOD' in c), None)

    bloques_disp = ['Todos'] + sorted(comp_df[bloc_c].dropna().unique().tolist())
    sel_bloque = st.selectbox("Seleccioná un bloque", bloques_disp, key='bloque_integrantes')

    df_integ = comp_df if sel_bloque == 'Todos' else comp_df[comp_df[bloc_c] == sel_bloque]
    rename_map = {bloc_c: 'Bloque'}
    if ap_c:  rename_map[ap_c] = 'Apellido'
    if nom_c: rename_map[nom_c] = 'Nombre'
    if per_c: rename_map[per_c] = 'Período'

    st.dataframe(df_integ.rename(columns=rename_map), use_container_width=True, hide_index=True)
    st.caption(f"{len(df_integ)} diputados/as en la selección")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════
# ÚLTIMAS VOTACIONES NOMINALES
# ══════════════════════════════════════════════════════════════════════
st.markdown("## Últimas votaciones nominales – período 135")

if votaciones is not None and not votaciones.empty:
    # Detect key columns
    fecha_c  = next((c for c in votaciones.columns if 'FECHA' in c), None)
    tema_c   = next((c for c in votaciones.columns if 'ASUNTO' in c or 'TEMA' in c or 'DESCRIPCION' in c or 'TITULO' in c), None)
    afirm_c  = next((c for c in votaciones.columns if 'AFIRM' in c or 'SI' in c), None)
    neg_c    = next((c for c in votaciones.columns if 'NEGAT' in c or 'NO' in c), None)
    result_c = next((c for c in votaciones.columns if 'RESULT' in c), None)

    # Show columns available
    show = [c for c in [fecha_c, tema_c, afirm_c, neg_c, result_c] if c]
    if not show:
        show = votaciones.columns[:5].tolist()

    rename_v = {}
    if fecha_c:  rename_v[fecha_c]  = 'Fecha'
    if tema_c:   rename_v[tema_c]   = 'Asunto'
    if afirm_c:  rename_v[afirm_c]  = 'Afirmativos'
    if neg_c:    rename_v[neg_c]    = 'Negativos'
    if result_c: rename_v[result_c] = 'Resultado'

    st.dataframe(
        votaciones[show].rename(columns=rename_v),
        use_container_width=True, hide_index=True, height=400,
    )
else:
    st.info("Los datos de votaciones del período 135 no están disponibles en este momento. "
            "Podés consultarlos directamente en: datos.hcdn.gob.ar")

st.markdown("---")
st.caption("Todos los datos de esta página provienen del Portal de Datos Abiertos de la Honorable Cámara de Diputados de la Nación (datos.hcdn.gob.ar). Se actualiza automáticamente.")
