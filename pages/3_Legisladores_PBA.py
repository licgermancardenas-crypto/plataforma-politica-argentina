"""
Página 3 – Legisladores de la Provincia de Buenos Aires
Diputados y senadores provinciales (Honorable Cámara de Diputados y Senado PBA)
"""
import sys, os, json, base64, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.express as px
import pandas as pd
from core import loader

@st.cache_data(show_spinner=False)
def load_fotos_legisladores():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "data", "fotos_legisladores.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _initials(nombre):
    words = nombre.split()
    return (words[0][0] + (words[-1][0] if len(words) > 1 else "")).upper()

def _bloque_color(bloque):
    b = bloque.lower()
    if "libertad" in b: return "#8B5CF6"
    if "patria" in b or "kirchner" in b or "peronist" in b: return "#3B82F6"
    if "radical" in b or "ucr" in b: return "#EF4444"
    if "juntos" in b or "cambio" in b or "pro" in b: return "#F59E0B"
    return "#6B7280"

def foto_legislador_html(tipo, nombre, bloque=""):
    """Retorna <img> con foto real o <div> con iniciales."""
    key = f"{tipo}::{nombre}"
    fotos = load_fotos_legisladores()
    if key in fotos:
        return f'<img src="{fotos[key]}" style="width:80px;height:80px;border-radius:50%;object-fit:cover;">'
    color = _bloque_color(bloque)
    ini = _initials(nombre)
    return f'<div style="width:80px;height:80px;border-radius:50%;background:{color};display:flex;align-items:center;justify-content:center;font-size:1.4rem;font-weight:700;color:white;">{ini}</div>'

fotos_legs = load_fotos_legisladores()

st.set_page_config(page_title="Legisladores PBA", page_icon="📊", layout="wide")
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #1F3864; }
[data-testid="stSidebar"] * { color: #FFF !important; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Legisladores – Provincia de Buenos Aires")
st.caption("Honorable Cámara de Diputados y Senado de la Provincia de Buenos Aires · período 2023-2027")

df_dp = loader.get_diputados_prov_df()
df_sp = loader.get_senadores_prov_df()

# ── KPIs ────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Diputados provinciales", len(df_dp))
k2.metric("Senadores provinciales", len(df_sp))
k3.metric("Total legisladores PBA", len(df_dp) + len(df_sp))
k4.metric("Secciones electorales", 8)

tab1, tab2, tab3, tab4 = st.tabs(["🏛 Diputados Provinciales", "📜 Senadores Provinciales", "📈 Análisis comparativo", "📸 Diputados Nacionales (PBA)"])

# ══════════════════════════════════════════════════════════════════════
# TAB 1: DIPUTADOS PROVINCIALES
# ══════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Honorable Cámara de Diputados de la Provincia de Buenos Aires")

    c_filt1, c_filt2 = st.columns(2)
    with c_filt1:
        sec_opts = ['Todas'] + sorted(df_dp['seccion'].dropna().unique().astype(str).tolist())
        sec_sel = st.selectbox("Sección electoral", sec_opts, key='dp_sec')
    with c_filt2:
        bl_opts = ['Todos'] + sorted(df_dp['bloque'].dropna().unique().tolist())
        bl_sel = st.selectbox("Bloque", bl_opts, key='dp_bl')

    df_dp_f = df_dp.copy()
    if sec_sel  != 'Todas': df_dp_f = df_dp_f[df_dp_f['seccion'].astype(str) == sec_sel]
    if bl_sel   != 'Todos': df_dp_f = df_dp_f[df_dp_f['bloque'] == bl_sel]

    st.markdown(f"**{len(df_dp_f)}** diputados/as en la selección")

    st.dataframe(
        df_dp_f.rename(columns={'nombre': 'Nombre', 'seccion': 'Sección', 'bloque': 'Bloque'}),
        use_container_width=True, hide_index=True,
    )

    # Charts
    col_a, col_b = st.columns(2)
    with col_a:
        bc_dp = loader.bloque_counts(df_dp_f)
        fig = px.pie(bc_dp, values='cantidad', names='bloque', hole=0.4,
                     color='bloque', color_discrete_map=loader.BLOQUE_COLOR,
                     title='Por bloque')
        fig.update_traces(textinfo='label+value')
        fig.update_layout(showlegend=False, height=300, margin=dict(t=30,b=5,l=5,r=5))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        sc_dp = df_dp_f.groupby('seccion').size().reset_index(name='diputados')
        fig2 = px.bar(sc_dp.sort_values('diputados'), x='diputados', y=sc_dp['seccion'].astype(str),
                      orientation='h', text='diputados', title='Por sección',
                      color_discrete_sequence=['#6A1B9A'])
        fig2.update_layout(yaxis_title='Sección', height=300, margin=dict(t=30,b=5,l=5,r=5))
        st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 2: SENADORES PROVINCIALES
# ══════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Honorable Senado de la Provincia de Buenos Aires")

    cs1, cs2 = st.columns(2)
    with cs1:
        sec_opts_s = ['Todas'] + sorted(df_sp['seccion'].dropna().unique().astype(str).tolist())
        sec_sel_s = st.selectbox("Sección electoral", sec_opts_s, key='sp_sec')
    with cs2:
        bl_opts_s = ['Todos'] + sorted(df_sp['bloque'].dropna().unique().tolist())
        bl_sel_s = st.selectbox("Bloque", bl_opts_s, key='sp_bl')

    df_sp_f = df_sp.copy()
    if sec_sel_s != 'Todas': df_sp_f = df_sp_f[df_sp_f['seccion'].astype(str) == sec_sel_s]
    if bl_sel_s  != 'Todos': df_sp_f = df_sp_f[df_sp_f['bloque'] == bl_sel_s]

    st.markdown(f"**{len(df_sp_f)}** senadores/as en la selección")

    st.dataframe(
        df_sp_f.rename(columns={'nombre': 'Nombre', 'seccion': 'Sección', 'bloque': 'Bloque'}),
        use_container_width=True, hide_index=True,
    )

    col_c, col_d = st.columns(2)
    with col_c:
        bc_sp = loader.bloque_counts(df_sp_f)
        fig3 = px.pie(bc_sp, values='cantidad', names='bloque', hole=0.4,
                      color='bloque', color_discrete_map=loader.BLOQUE_COLOR,
                      title='Por bloque')
        fig3.update_traces(textinfo='label+value')
        fig3.update_layout(showlegend=False, height=300, margin=dict(t=30,b=5,l=5,r=5))
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        sc_sp = df_sp_f.groupby('seccion').size().reset_index(name='senadores')
        fig4 = px.bar(sc_sp.sort_values('senadores'), x='senadores', y=sc_sp['seccion'].astype(str),
                      orientation='h', text='senadores', title='Por sección',
                      color_discrete_sequence=['#1B5E20'])
        fig4.update_layout(yaxis_title='Sección', height=300, margin=dict(t=30,b=5,l=5,r=5))
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 3: ANÁLISIS COMPARATIVO
# ══════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Análisis comparativo – bloques en ambas cámaras")

    dp_bc = df_dp.groupby('bloque').size().rename('Diputados')
    sp_bc = df_sp.groupby('bloque').size().rename('Senadores')
    compare = pd.concat([dp_bc, sp_bc], axis=1).fillna(0).astype(int).reset_index()
    compare.columns = ['Bloque', 'Diputados', 'Senadores']
    compare['Total'] = compare['Diputados'] + compare['Senadores']
    compare = compare.sort_values('Total', ascending=False)

    st.dataframe(compare, use_container_width=True, hide_index=True)

    fig5 = px.bar(
        compare.melt(id_vars='Bloque', value_vars=['Diputados', 'Senadores']),
        x='Bloque', y='value', color='variable', barmode='group',
        text='value', labels={'value': 'Legisladores', 'variable': 'Cámara'},
        color_discrete_map={'Diputados': '#6A1B9A', 'Senadores': '#1B5E20'},
    )
    fig5.update_layout(xaxis_tickangle=-30, height=360, margin=dict(t=10,b=10,l=10,r=10))
    st.plotly_chart(fig5, use_container_width=True)

    # Cross-reference: bloque controls intendencias?
    st.subheader("Control político por bloque: intendencias vs. escaños legislativos")
    df_int = loader.get_intendentes_df()
    int_bc = df_int.groupby('bloque').size().rename('Intendencias')
    summary = pd.concat([int_bc, dp_bc, sp_bc], axis=1).fillna(0).astype(int).reset_index()
    summary.columns = ['Bloque', 'Intendencias', 'Dip.Prov.', 'Sen.Prov.']
    summary = summary.sort_values('Intendencias', ascending=False)
    st.dataframe(summary, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 4: DIPUTADOS NACIONALES CON FOTOS
# ══════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Diputados Nacionales por Buenos Aires – 70 representantes")
    dip_nac = loader.get_diputados_nac_df().to_dict("records")
    n_con_foto = sum(1 for p in dip_nac if f"diputados_nac::{p['nombre']}" in fotos_legs)
    st.caption(f"Fotos reales disponibles: {n_con_foto}/{len(dip_nac)} · Resto: avatares por bloque")

    # Group by bloque
    bloques = {}
    for p in dip_nac:
        b = p.get("bloque", "Sin bloque")
        bloques.setdefault(b, []).append(p)

    for bloque, personas in sorted(bloques.items(), key=lambda x: -len(x[1])):
        color = _bloque_color(bloque)
        st.markdown(f"""
<div style="margin:16px 0 8px;padding:6px 14px;background:{color}22;border-left:3px solid {color};
     border-radius:4px;font-weight:600;color:{color};font-size:0.9rem;">
  {bloque} ({len(personas)})
</div>""", unsafe_allow_html=True)

        cards_html = '<div style="display:flex;flex-wrap:wrap;gap:12px;margin-bottom:8px;">'
        for p in personas:
            foto_html = foto_legislador_html("diputados_nac", p["nombre"], p.get("bloque",""))
            nombre_corto = p["nombre"]
            cards_html += f"""
<div style="width:110px;text-align:center;background:#1E293B;border-radius:10px;padding:12px 6px 8px;
     border:1px solid #334155;">
  <div style="display:flex;justify-content:center;margin-bottom:8px;">{foto_html}</div>
  <div style="font-size:0.65rem;color:#CBD5E1;line-height:1.3;word-break:break-word;">{nombre_corto}</div>
</div>"""
        cards_html += "</div>"
        st.markdown(cards_html, unsafe_allow_html=True)
