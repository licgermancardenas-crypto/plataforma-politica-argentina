"""
Página 5 – Búsqueda Global
Buscador unificado entre todos los políticos del dataset.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from core import loader

st.set_page_config(page_title="Búsqueda Global", page_icon="🔍", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #1F3864; }
[data-testid="stSidebar"] * { color: #FFF !important; }

.result-card {
    background: white;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    border-left: 5px solid;
    display: flex;
    align-items: flex-start;
    gap: 12px;
}
.result-name  { font-size: 1.05rem; font-weight: 700; color: #1F3864; margin: 0; }
.result-role  { font-size: 0.82rem; color: #555; margin: 2px 0; }
.result-party { font-size: 0.82rem; color: #333; margin: 0; }
.result-loc   { font-size: 0.78rem; color: #777; margin: 2px 0 0; }
.cat-badge    {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .4px; white-space: nowrap;
}
.result-icon  { font-size: 1.6rem; line-height: 1; flex-shrink: 0; }
.section-title {
    font-size: 0.9rem; font-weight: 700; color: #888; text-transform: uppercase;
    letter-spacing: 1px; margin: 22px 0 8px; padding-bottom: 4px;
    border-bottom: 1px solid #E0E0E0;
}
.no-results { text-align: center; color: #999; padding: 60px 0; font-size: 1.1rem; }
</style>
""", unsafe_allow_html=True)

# ── Colores por categoría ─────────────────────────────────────────────
CAT_META = {
    'Intendente':           {'icon': '🏙', 'color': '#1F3864', 'badge_bg': '#E3F2FD', 'badge_fg': '#1565C0'},
    'Secretario/a':         {'icon': '📋', 'color': '#4A148C', 'badge_bg': '#F3E5F5', 'badge_fg': '#6A1B9A'},
    'Concejal':             {'icon': '🗳', 'color': '#1B5E20', 'badge_bg': '#E8F5E9', 'badge_fg': '#2E7D32'},
    'Diputado/a Provincial':{'icon': '📜', 'color': '#E65100', 'badge_bg': '#FFF3E0', 'badge_fg': '#BF360C'},
    'Senador/a Provincial': {'icon': '🏛', 'color': '#880E4F', 'badge_bg': '#FCE4EC', 'badge_fg': '#880E4F'},
    'Diputado/a Nacional':  {'icon': '🇦🇷', 'color': '#006064', 'badge_bg': '#E0F7FA', 'badge_fg': '#00695C'},
    'Senador/a Nacional':   {'icon': '⭐', 'color': '#4E342E', 'badge_bg': '#EFEBE9', 'badge_fg': '#4E342E'},
}

# ── Construir índice unificado (solo una vez) ──────────────────────────
@st.cache_data(show_spinner=False)
def build_index():
    records = []

    # 1. Intendentes
    df_int = loader.get_intendentes_df()
    for _, r in df_int.iterrows():
        records.append({
            'nombre':    r['intendente'],
            'categoria': 'Intendente',
            'rol':       f"Intendente/a de {r['municipio']}",
            'partido':   r['partido'],
            'bloque':    r['bloque'],
            'lugar':     r['municipio'],
            'seccion':   r['seccion_nombre'],
            'extra':     f"Ganó con {r['ganador_pct']}% · margen {r['margen']}%",
        })

    # 2. Secretarios
    sec_dict = loader.get_secretarios()
    df_int_idx = {r['municipio']: r for _, r in df_int.iterrows()}
    for muni, items in sec_dict.items():
        bloque = df_int_idx.get(muni, {}).get('bloque', '')
        seccion = df_int_idx.get(muni, {}).get('seccion_nombre', '')
        for s in items:
            records.append({
                'nombre':    s['nombre'],
                'categoria': 'Secretario/a',
                'rol':       s['cargo'],
                'partido':   '',
                'bloque':    bloque,
                'lugar':     muni,
                'seccion':   seccion,
                'extra':     '',
            })

    # 3. Concejales
    df_conc = loader.get_concejales_df()
    for _, r in df_conc.iterrows():
        records.append({
            'nombre':    r['nombre'],
            'categoria': 'Concejal',
            'rol':       f"Concejal electo 2023 – {r['municipio']}",
            'partido':   r['partido'],
            'bloque':    r['bloque'],
            'lugar':     r['municipio'],
            'seccion':   r['seccion_nombre'],
            'extra':     f"Lista: {r['partido']}",
        })

    # 4. Diputados provinciales
    df_dp = loader.get_diputados_prov_df()
    for _, r in df_dp.iterrows():
        records.append({
            'nombre':    r['nombre'],
            'categoria': 'Diputado/a Provincial',
            'rol':       f"Diputado/a provincial – Sección {r['seccion']}",
            'partido':   r['bloque'],
            'bloque':    r['bloque'],
            'lugar':     f"Sección {r['seccion']}",
            'seccion':   str(r['seccion']),
            'extra':     '',
        })

    # 5. Senadores provinciales
    df_sp = loader.get_senadores_prov_df()
    for _, r in df_sp.iterrows():
        records.append({
            'nombre':    r['nombre'],
            'categoria': 'Senador/a Provincial',
            'rol':       f"Senador/a provincial – Sección {r['seccion']}",
            'partido':   r['bloque'],
            'bloque':    r['bloque'],
            'lugar':     f"Sección {r['seccion']}",
            'seccion':   str(r['seccion']),
            'extra':     '',
        })

    # 6. Diputados nacionales
    df_dn = loader.get_diputados_nac_df()
    for _, r in df_dn.iterrows():
        records.append({
            'nombre':    r['nombre'],
            'categoria': 'Diputado/a Nacional',
            'rol':       'Diputado/a nacional por Buenos Aires',
            'partido':   r['bloque'],
            'bloque':    r['bloque'],
            'lugar':     'Buenos Aires',
            'seccion':   '',
            'extra':     '',
        })

    # 7. Senadores nacionales
    df_sn = loader.get_senadores_nac_df()
    for _, r in df_sn.iterrows():
        records.append({
            'nombre':    r['nombre'],
            'categoria': 'Senador/a Nacional',
            'rol':       'Senador/a nacional por Buenos Aires',
            'partido':   r['bloque'],
            'bloque':    r['bloque'],
            'lugar':     'Buenos Aires',
            'seccion':   '',
            'extra':     '',
        })

    df = pd.DataFrame(records)
    df['_search'] = (
        df['nombre'].str.lower().fillna('') + ' ' +
        df['lugar'].str.lower().fillna('') + ' ' +
        df['partido'].str.lower().fillna('') + ' ' +
        df['bloque'].str.lower().fillna('') + ' ' +
        df['rol'].str.lower().fillna('')
    )
    return df


# ── Página ─────────────────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#1F3864,#2E5BBA);padding:28px 32px;border-radius:12px;margin-bottom:24px;'>
<h1 style='color:white;margin:0;font-size:1.9rem;'>🔍 Búsqueda Global de Políticos</h1>
<p style='color:#B0C4DE;margin:6px 0 0;font-size:0.95rem;'>
Buscá en tiempo real entre 2,248+ políticos: intendentes, secretarios, concejales, legisladores provinciales y nacionales
</p>
</div>
""", unsafe_allow_html=True)

df_index = build_index()
total_politicos = len(df_index)

# ── Barra de búsqueda principal ────────────────────────────────────────
query = st.text_input(
    label="",
    placeholder="🔍  Escribí un nombre, municipio, partido o cargo...",
    label_visibility="collapsed",
)

# ── Filtros secundarios ────────────────────────────────────────────────
with st.expander("Filtros avanzados", expanded=False):
    fa1, fa2, fa3 = st.columns(3)
    with fa1:
        cats = ['Todas las categorías'] + sorted(df_index['categoria'].unique().tolist())
        cat_sel = st.selectbox("Categoría", cats)
    with fa2:
        bloques_list = ['Todos los bloques'] + sorted(df_index['bloque'].dropna().unique().tolist())
        bloque_sel = st.selectbox("Bloque político", bloques_list)
    with fa3:
        secciones_list = ['Todas las secciones'] + sorted(
            [s for s in df_index['seccion'].dropna().unique() if s and not s.isdigit()], key=str
        )
        sec_sel = st.selectbox("Sección electoral", secciones_list)

# ── Lógica de búsqueda ─────────────────────────────────────────────────
results = df_index.copy()

if query.strip():
    q = query.lower().strip()
    mask = results['_search'].str.contains(q, na=False)
    results = results[mask]

if cat_sel    != 'Todas las categorías':  results = results[results['categoria']     == cat_sel]
if bloque_sel != 'Todos los bloques':     results = results[results['bloque']        == bloque_sel]
if sec_sel    != 'Todas las secciones':   results = results[results['seccion'] == sec_sel]

# ── Resumen ────────────────────────────────────────────────────────────
if not query.strip() and cat_sel == 'Todas las categorías' and bloque_sel == 'Todos los bloques' and sec_sel == 'Todas las secciones':
    # Estado vacío: mostrar estadísticas del índice
    st.markdown(f"**{total_politicos:,} políticos indexados** — escribí algo para buscar".replace(',', '.'))
    cols = st.columns(len(CAT_META))
    cat_counts = df_index['categoria'].value_counts()
    for col, (cat, meta) in zip(cols, CAT_META.items()):
        with col:
            st.markdown(f"""
            <div style='background:white;border-radius:10px;padding:14px;text-align:center;
                        box-shadow:0 1px 4px rgba(0,0,0,.07);border-top:4px solid {meta["color"]};'>
              <div style='font-size:1.6rem;'>{meta["icon"]}</div>
              <div style='font-size:1.5rem;font-weight:700;color:{meta["color"]};'>{cat_counts.get(cat, 0)}</div>
              <div style='font-size:0.72rem;color:#666;'>{cat}</div>
            </div>
            """, unsafe_allow_html=True)
    st.stop()

n = len(results)
if n == 0:
    st.markdown("<div class='no-results'>Sin resultados. Probá con otro término.</div>", unsafe_allow_html=True)
    st.stop()

st.markdown(f"**{n}** resultado{'s' if n != 1 else ''} encontrado{'s' if n != 1 else ''}")

# ── Renderizado de resultados ──────────────────────────────────────────
MAX_RESULTS = 200
show_all = n <= MAX_RESULTS
if not show_all:
    st.info(f"Mostrando los primeros {MAX_RESULTS} de {n} resultados. Refiná la búsqueda para ver más.")

CAT_ORDER = list(CAT_META.keys())
results_sorted = results.copy()
results_sorted['_cat_order'] = results_sorted['categoria'].map(
    {c: i for i, c in enumerate(CAT_ORDER)}
).fillna(99)
results_sorted = results_sorted.sort_values(['_cat_order', 'nombre']).head(MAX_RESULTS)

current_cat = None
for _, row in results_sorted.iterrows():
    cat = row['categoria']
    meta = CAT_META.get(cat, {'icon': '👤', 'color': '#546E7A', 'badge_bg': '#ECEFF1', 'badge_fg': '#546E7A'})

    if cat != current_cat:
        current_cat = cat
        cat_count = len(results[results['categoria'] == cat])
        st.markdown(
            f"<p class='section-title'>{meta['icon']} {cat}s &nbsp; <span style='font-weight:400;'>({cat_count})</span></p>",
            unsafe_allow_html=True
        )

    bloque_color = loader.BLOQUE_COLOR.get(row['bloque'], '#546E7A')
    badge_html = (
        f"<span class='cat-badge' style='background:{meta['badge_bg']};color:{meta['badge_fg']};'>{cat}</span>"
        if False else ""  # badge inside card optional
    )
    bloque_badge = f"<span class='cat-badge' style='background:{loader.BLOQUE_BG.get(row['bloque'], '#ECEFF1')};color:{bloque_color};'>{row['bloque']}</span>" if row['bloque'] else ""

    partido_html = ""
    if row['partido'] and row['partido'] != row['bloque']:
        partido_html = f"<span style='color:#555;'>{row['partido'][:60]}</span>"

    extra_html = f"<span style='color:#888;font-size:0.78rem;'> · {row['extra']}</span>" if row['extra'] else ""

    st.markdown(f"""
    <div class='result-card' style='border-left-color:{meta["color"]};'>
      <div class='result-icon'>{meta["icon"]}</div>
      <div style='flex:1;'>
        <p class='result-name'>{row['nombre']}</p>
        <p class='result-role'>{row['rol']}{extra_html}</p>
        <p class='result-party'>{bloque_badge} {partido_html}</p>
        <p class='result-loc'>📍 {row['lugar']}{('  ·  ' + row['seccion']) if (row['seccion'] and not str(row['seccion']).isdigit()) else ''}</p>
      </div>
    </div>
    """, unsafe_allow_html=True)
