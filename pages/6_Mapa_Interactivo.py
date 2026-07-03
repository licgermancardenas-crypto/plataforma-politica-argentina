"""
Página 6 – Mapa Estratégico PBA  (Power BI / OSINT mode)
Mapa político con filtros dinámicos, panel de inteligencia y analytics.
"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import MiniMap, Fullscreen
from streamlit_folium import st_folium
from shapely.geometry import Point, shape
from core import loader

st.set_page_config(
    page_title="Mapa Estratégico PBA",
    page_icon="🛰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════
# ESTILOS
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ═══════════════════════════════════════════
   MAPA FULL-SCREEN
═══════════════════════════════════════════ */
header[data-testid="stHeader"]  { display: none !important; }
[data-testid="stToolbar"]        { display: none !important; }
footer                           { display: none !important; }

.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}
/* Iframe del mapa ocupa toda la altura disponible */
[data-testid="stIFrame"] > iframe,
iframe[title*="folium"],
iframe[title*="streamlit_folium"] {
    height: calc(100vh - 48px) !important;
    min-height: 500px !important;
}
[data-testid="stIFrame"] {
    height: calc(100vh - 48px) !important;
}

/* ═══════════════════════════════════════════
   SIDEBAR – REDISEÑO ELEGANTE
═══════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: #070D1A !important;
    border-right: 1px solid #1E293B !important;
}
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
[data-testid="stSidebarNav"] {
    background: #070D1A !important;
    padding-bottom: 4px !important;
    border-bottom: 1px solid #1E293B !important;
}
[data-testid="stSidebarNav"] a {
    font-size: .78rem !important;
    padding: 4px 12px !important;
}
[data-testid="stSidebarNav"] a[aria-selected="true"] {
    background: #1E293B !important;
    border-radius: 6px !important;
}

/* inputs y selects */
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] input { color: #1e293b !important; }
[data-testid="stSidebar"] .stSlider > div > div { background: #1E3A5F !important; }
[data-testid="stSidebar"] [data-testid="stSlider"] div[role="slider"] {
    background: #3B82F6 !important;
}

/* expanders */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: #0F172A !important;
    border: 1px solid #1E293B !important;
    border-radius: 8px !important;
    margin-bottom: 6px !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    font-size: .78rem !important;
    font-weight: 600 !important;
    letter-spacing: .04em !important;
    padding: 8px 12px !important;
}

/* botones */
[data-testid="stSidebar"] .stButton > button {
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    color: #94A3B8 !important;
    font-size: .75rem !important;
    border-radius: 6px !important;
    padding: 4px 0 !important;
    transition: all .15s !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #334155 !important;
    color: #E2E8F0 !important;
    border-color: #475569 !important;
}

/* radio */
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    font-size: .78rem !important;
    padding: 2px 0 !important;
}

/* intel-row tabla */
.intel-row {
    display:flex; justify-content:space-between;
    padding: 4px 0; border-bottom: 1px solid #1E293B; font-size: .78rem;
}
.intel-key { color: #475569; }
.intel-val { color: #E2E8F0; font-weight: 600; text-align:right; max-width:58%; }

/* section-label para analytics */
.section-label {
    font-size:.72rem; font-weight:700; color:#475569; text-transform:uppercase;
    letter-spacing:.1em; margin:12px 0 6px; padding-bottom:4px;
    border-bottom:1px solid #1E293B;
}

/* categorías */
.cat-batalla     { background:#7F1D1D; color:#FCA5A5; }
.cat-competitivo { background:#78350F; color:#FCD34D; }
.cat-dominio     { background:#1E3A5F; color:#93C5FD; }
.cat-fortaleza   { background:#14532D; color:#86EFAC; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════
BLOQUE_HEX = {
    'Unión por la Patria':  '#3B82F6',
    'Juntos por el Cambio': '#EAB308',
    'Vecinal':              '#22C55E',
}
SECCION_HEX = {
    '1ª – Norte Conurbano':  '#0EA5E9',
    '2ª – Norte PBA':        '#06B6D4',
    '3ª – Sur Conurbano':    '#8B5CF6',
    '4ª – Noroeste PBA':     '#10B981',
    '5ª – Costa Atlántica':  '#F59E0B',
    '6ª – Sudoeste PBA':     '#EF4444',
    '7ª – Centro PBA':       '#F97316',
    '8ª – Capital (La Plata)': '#EC4899',
}
DEFAULT_CLR = '#475569'
BORDER_CLR  = '#FFFFFF'

def cat_estrategica(margen):
    if margen is None or margen == 0: return 'Sin datos'
    if margen <= 3:   return 'Batalla'
    if margen <= 8:   return 'Competitivo'
    if margen <= 20:  return 'Dominio'
    return 'Fortaleza'

CAT_HEX = {
    'Batalla':     '#EF4444',
    'Competitivo': '#F59E0B',
    'Dominio':     '#3B82F6',
    'Fortaleza':   '#22C55E',
    'Sin datos':   '#475569',
}
CAT_CSS = {
    'Batalla': 'cat-batalla', 'Competitivo': 'cat-competitivo',
    'Dominio': 'cat-dominio', 'Fortaleza': 'cat-fortaleza',
}

# ═══════════════════════════════════════════════════════════════════════════
# CARGA DE DATOS
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def load_all():
    _dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    with open(os.path.join(_dir, 'data', 'municipios_pba.geojson')) as f:
        gj = json.load(f)

    rows = []
    for feat in gj['features']:
        p = feat['properties']
        rows.append({**p,
            'categoria': cat_estrategica(p.get('margen') or 0),
            'zona': 'GBA' if p.get('seccion_nombre','') in (
                '1ª – Norte Conurbano', '3ª – Sur Conurbano', '8ª – Capital (La Plata)'
            ) else 'Interior',
            '_geom_type': feat['geometry']['type'] if feat.get('geometry') else 'None',
        })
    df = pd.DataFrame(rows)

    with open(os.path.join(_dir, 'data', 'concejales_flat.json')) as f:
        conc_flat = json.load(f)
    conc_df = pd.DataFrame(conc_flat)

    with open(os.path.join(_dir, 'data', 'secretarios.json')) as f:
        sec_dict = json.load(f)

    return gj, df, conc_df, sec_dict

@st.cache_data(show_spinner=False)
def load_radios_by_partido(partido_nombre):
    """Carga solo los radios censales del partido seleccionado."""
    _dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(_dir, 'data', 'radios_censales_2022.geojson')
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        gj = json.load(f)
    nombre_up = partido_nombre.upper()
    features = [
        feat for feat in gj['features']
        if feat['properties'].get('PARTIDO','').upper() == nombre_up
    ]
    return {'type': 'FeatureCollection', 'features': features}

with st.spinner("Cargando datos..."):
    geojson_data, df_all, conc_df, sec_dict = load_all()

# Índice espacial: lista de (nombre, shapely_geometry) para point-in-polygon
@st.cache_data(show_spinner=False)
def build_spatial_index():
    index = []
    for feat in geojson_data['features']:
        geom = feat.get('geometry')
        if geom and geom['type'] in ('Polygon', 'MultiPolygon'):
            try:
                index.append((feat['properties']['municipio'], shape(geom)))
            except Exception:
                pass
    return index

spatial_index = build_spatial_index()

def find_muni_by_point(lat, lng):
    pt = Point(lng, lat)  # shapely usa (x=lng, y=lat)
    for muni_name, geom in spatial_index:
        if geom.contains(pt):
            return muni_name
    # Si no hay match exacto, buscar el más cercano (para puntos cerca del borde)
    min_dist, closest = float('inf'), None
    for muni_name, geom in spatial_index:
        d = pt.distance(geom)
        if d < min_dist:
            min_dist, closest = d, muni_name
    return closest if min_dist < 0.05 else None

# ═══════════════════════════════════════════════════════════════════════════
# ÍNDICE DE CENTROIDES (para zoom al buscar)
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def build_centroid_index():
    index = {}
    for feat in geojson_data['features']:
        geom = feat.get('geometry')
        muni = feat['properties'].get('municipio', '')
        if not geom or geom['type'] not in ('Polygon', 'MultiPolygon'):
            continue
        try:
            c = shape(geom).centroid
            index[muni] = [c.y, c.x]
        except Exception:
            pass
    return index

centroid_index = build_centroid_index()

# ═══════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════
if 'selected_muni' not in st.session_state:
    st.session_state.selected_muni = None
if 'map_center' not in st.session_state:
    st.session_state.map_center = [-36.5, -60.0]
if 'map_zoom' not in st.session_state:
    st.session_state.map_zoom = 7

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR – FILTROS DINÁMICOS
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:14px 4px 8px;">
      <div style="font-size:.62rem;font-weight:700;color:#334155;letter-spacing:.16em;
                  text-transform:uppercase;margin-bottom:2px;">Provincia de Buenos Aires</div>
      <div style="font-size:1.05rem;font-weight:800;color:#E2E8F0;letter-spacing:-.01em;">
        Mapa Estratégico
      </div>
      <div style="width:28px;height:2px;background:linear-gradient(90deg,#3B82F6,#8B5CF6);
                  border-radius:2px;margin-top:6px;"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI placeholder (se rellena después del filtrado) ───────────────────
    kpi_placeholder = st.empty()

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    st.markdown("### BUSCAR MUNICIPIO")
    all_munis_sorted = [""] + sorted(df_all['municipio'].dropna().tolist())
    muni_search = st.selectbox(
        "Ir a municipio",
        all_munis_sorted,
        format_func=lambda x: "🔍 Escribí un municipio..." if x == "" else x,
        label_visibility="collapsed",
        key="muni_search_box",
    )
    if muni_search and muni_search != st.session_state.selected_muni:
        st.session_state.selected_muni = muni_search
        if muni_search in centroid_index:
            st.session_state.map_center = centroid_index[muni_search]
            st.session_state.map_zoom = 13
        st.rerun()

    st.markdown("---")
    st.markdown("### CAPA TEMÁTICA")
    capa = st.radio(
        "", ["Bloque político", "Categoría estratégica", "Sección electoral",
             "% de victoria", "Población 2022"],
        label_visibility="collapsed",
    )

    with st.expander("⚙ Filtros", expanded=False):
        all_bloques = sorted(df_all['bloque'].dropna().unique())
        bloque_sel = st.multiselect("Bloque político", all_bloques, placeholder="Todos los bloques")

        all_secciones = sorted(df_all['seccion_nombre'].dropna().unique())
        sec_sel = st.multiselect("Sección electoral", all_secciones, placeholder="Todas las secciones")

        all_cats = ['Batalla', 'Competitivo', 'Dominio', 'Fortaleza']
        cat_sel = st.multiselect("Categoría estratégica", all_cats, placeholder="Todas")

        zona_sel = st.selectbox("Zona", ["GBA + Interior", "Solo GBA", "Solo Interior"])

        margen_range = st.slider(
            "Margen electoral (pp)", 0.0, 50.0, (0.0, 50.0), step=0.5,
            help="Diferencia de puntos entre 1° y 2° lugar"
        )

        padron_range = st.slider(
            "Padrón electoral", 2000, 1200000, (2000, 1200000), step=1000,
            format="%d",
        )

    with st.expander("🔧 Opciones", expanded=False):
        show_labels = st.checkbox("Mostrar nombre en mapa", False)
        show_disputes = st.checkbox("Resaltar disputados (<3pp)", True)
        show_radios = st.checkbox("Radios censales 2022", False,
                                  help="Muestra los radios del municipio seleccionado")

    if st.button("🔄 Resetear", use_container_width=True):
        st.session_state.selected_muni = None
        st.session_state.map_center = [-36.5, -60.0]
        st.session_state.map_zoom = 7
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# FILTRADO DEL DATAFRAME
# ═══════════════════════════════════════════════════════════════════════════
df = df_all.copy()
if bloque_sel:    df = df[df['bloque'].isin(bloque_sel)]
if sec_sel:       df = df[df['seccion_nombre'].isin(sec_sel)]
if cat_sel:       df = df[df['categoria'].isin(cat_sel)]
if zona_sel == "Solo GBA":      df = df[df['zona'] == 'GBA']
elif zona_sel == "Solo Interior": df = df[df['zona'] == 'Interior']
df = df[(df['margen'] >= margen_range[0]) & (df['margen'] <= margen_range[1])]
df = df[(df['padron'] >= padron_range[0]) & (df['padron'] <= padron_range[1])]

visible_munis = set(df['municipio'].tolist())

# ── KPIs calculados → se inyectan en el sidebar placeholder ─────────────
total_munis  = len(df)
n_batalla    = len(df[df['categoria'] == 'Batalla'])
n_compet     = len(df[df['categoria'] == 'Competitivo'])
n_fortal     = len(df[df['categoria'] == 'Fortaleza'])
pob_total    = df['poblacion_2022'].sum()
margen_prom  = df['margen'].mean()

kpi_placeholder.markdown(f"""
<div style="padding:10px 0 6px;">
  <div style="font-size:.62rem;font-weight:700;color:#334155;text-transform:uppercase;
              letter-spacing:.12em;margin-bottom:8px;padding-left:2px;">
    Resumen · filtro activo
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:3px;">
    <div style="background:linear-gradient(135deg,#0F172A,#1E293B);border:1px solid #1E3A5F;
                border-left:3px solid #3B82F6;border-radius:7px;padding:7px 10px;">
      <div style="font-size:1.25rem;font-weight:800;color:#3B82F6;line-height:1;">{total_munis}</div>
      <div style="font-size:.58rem;color:#475569;text-transform:uppercase;letter-spacing:.06em;margin-top:2px;">Municipios</div>
    </div>
    <div style="background:linear-gradient(135deg,#0F172A,#1E293B);border:1px solid #3B1E1E;
                border-left:3px solid #EF4444;border-radius:7px;padding:7px 10px;">
      <div style="font-size:1.25rem;font-weight:800;color:#EF4444;line-height:1;">{n_batalla}</div>
      <div style="font-size:.58rem;color:#475569;text-transform:uppercase;letter-spacing:.06em;margin-top:2px;">En disputa</div>
    </div>
    <div style="background:linear-gradient(135deg,#0F172A,#1E293B);border:1px solid #2D1E0F;
                border-left:3px solid #F59E0B;border-radius:7px;padding:7px 10px;">
      <div style="font-size:1.25rem;font-weight:800;color:#F59E0B;line-height:1;">{n_compet}</div>
      <div style="font-size:.58rem;color:#475569;text-transform:uppercase;letter-spacing:.06em;margin-top:2px;">Competitivos</div>
    </div>
    <div style="background:linear-gradient(135deg,#0F172A,#1E293B);border:1px solid #14532D22;
                border-left:3px solid #22C55E;border-radius:7px;padding:7px 10px;">
      <div style="font-size:1.25rem;font-weight:800;color:#22C55E;line-height:1;">{n_fortal}</div>
      <div style="font-size:.58rem;color:#475569;text-transform:uppercase;letter-spacing:.06em;margin-top:2px;">Fortalezas</div>
    </div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:3px;margin-top:3px;">
    <div style="background:#0F172A;border:1px solid #1E293B;border-radius:7px;
                padding:5px 10px;display:flex;align-items:center;gap:6px;">
      <span style="font-size:.9rem;font-weight:700;color:#8B5CF6;">{margen_prom:.1f}pp</span>
      <span style="font-size:.56rem;color:#334155;text-transform:uppercase;">margen</span>
    </div>
    <div style="background:#0F172A;border:1px solid #1E293B;border-radius:7px;
                padding:5px 10px;display:flex;align-items:center;gap:6px;">
      <span style="font-size:.9rem;font-weight:700;color:#06B6D4;">{pob_total/1e6:.1f}M</span>
      <span style="font-size:.56rem;color:#334155;text-transform:uppercase;">hab.</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# FUNCIÓN DE COLOR POR CAPA
# ═══════════════════════════════════════════════════════════════════════════
def get_color(props, capa_mode):
    if capa_mode == "Bloque político":
        return BLOQUE_HEX.get(props.get('bloque', ''), DEFAULT_CLR)
    if capa_mode == "Categoría estratégica":
        return CAT_HEX.get(cat_estrategica(props.get('margen') or 0), DEFAULT_CLR)
    if capa_mode == "Sección electoral":
        return SECCION_HEX.get(props.get('seccion_nombre', ''), DEFAULT_CLR)
    if capa_mode == "% de victoria":
        pct = props.get('ganador_pct') or 0
        if pct >= 60: return '#1D4ED8'
        if pct >= 50: return '#3B82F6'
        if pct >= 45: return '#93C5FD'
        if pct >= 40: return '#BFDBFE'
        return '#DBEAFE'
    if capa_mode == "Población 2022":
        pop = props.get('poblacion_2022') or 0
        if pop >= 500000: return '#7C3AED'
        if pop >= 200000: return '#8B5CF6'
        if pop >= 100000: return '#A78BFA'
        if pop >= 50000:  return '#C4B5FD'
        if pop >= 20000:  return '#DDD6FE'
        return '#EDE9FE'
    return DEFAULT_CLR

# ═══════════════════════════════════════════════════════════════════════════
# POPUP HTML
# ═══════════════════════════════════════════════════════════════════════════
def make_popup(props):
    muni   = props.get('municipio', '')
    intend = props.get('intendente', 'N/D')
    pdo    = props.get('partido', '')
    bloque = props.get('bloque', '')
    sec    = props.get('seccion_nombre', '')
    pct    = props.get('ganador_pct') or 0
    marg   = props.get('margen') or 0
    seg    = props.get('segundo', '')
    spct   = props.get('segundo_pct') or 0
    conc   = props.get('concejales_electos') or 0
    pop    = props.get('poblacion_2022') or 0
    km2    = props.get('superficie_km2') or 0
    padron = props.get('padron') or 0
    cat    = cat_estrategica(marg)
    color  = get_color(props, "Bloque político")
    cat_c  = CAT_HEX.get(cat, DEFAULT_CLR)

    pop_s  = f"{pop:,}".replace(',', '.')
    dens   = f"{pop/km2:.0f} hab/km²" if km2 else 'S/D'
    padron_s = f"{padron:,}".replace(',', '.')

    return f"""
<div style="font-family:system-ui,sans-serif;width:310px;background:#0F172A;color:#E2E8F0;border-radius:10px;overflow:hidden;" id="popup-{muni.replace(' ','_')}" data-muni="{muni}">
  <!-- Encabezado -->
  <div style="background:{color};padding:12px 16px;">
    <div style="font-size:1.1rem;font-weight:800;color:white;letter-spacing:-.01em;">{muni}</div>
    <div style="font-size:.75rem;opacity:.85;color:white;margin-top:1px;">{sec}</div>
    <div style="margin-top:6px;">
      <span style="background:rgba(0,0,0,.25);color:white;padding:2px 8px;border-radius:10px;font-size:.7rem;font-weight:700;">{bloque}</span>
      <span style="background:{cat_c};color:white;padding:2px 8px;border-radius:10px;font-size:.7rem;font-weight:700;margin-left:4px;">{cat}</span>
    </div>
  </div>

  <div style="padding:12px 16px;">
    <!-- Intendente -->
    <div style="font-size:.82rem;margin-bottom:10px;">
      <div style="color:#64748B;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px;">Intendente/a</div>
      <div style="font-weight:700;font-size:.95rem;color:#F1F5F9;">{intend}</div>
      <div style="color:#94A3B8;font-size:.75rem;">{pdo[:45]}</div>
    </div>

    <!-- Resultado electoral -->
    <div style="font-size:.78rem;color:#64748B;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;">Resultado 2023</div>
    <div style="background:#1E293B;border-radius:8px;padding:8px 10px;margin-bottom:8px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
        <span style="font-weight:600;font-size:.82rem;color:#E2E8F0;">{pdo[:30]}</span>
        <span style="color:{color};font-weight:800;font-size:.9rem;">{pct:.1f}%</span>
      </div>
      <div style="background:#334155;border-radius:3px;height:5px;margin-bottom:6px;">
        <div style="background:{color};height:5px;border-radius:3px;width:{min(pct,100):.0f}%;"></div>
      </div>
      <div style="color:#475569;font-size:.72rem;">2° {seg[:25]} · {spct:.1f}% · margen <b style="color:#E2E8F0;">+{marg:.1f}pp</b></div>
    </div>

    <!-- Stats grid -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;font-size:.75rem;">
      <div style="background:#1E293B;border-radius:6px;padding:6px 8px;">
        <div style="color:#475569;">Concejales</div>
        <div style="font-weight:700;color:#93C5FD;">{conc}</div>
      </div>
      <div style="background:#1E293B;border-radius:6px;padding:6px 8px;">
        <div style="color:#475569;">Padrón</div>
        <div style="font-weight:700;color:#86EFAC;">{padron_s}</div>
      </div>
      <div style="background:#1E293B;border-radius:6px;padding:6px 8px;">
        <div style="color:#475569;">Población 2022</div>
        <div style="font-weight:700;color:#FCD34D;">{pop_s}</div>
      </div>
      <div style="background:#1E293B;border-radius:6px;padding:6px 8px;">
        <div style="color:#475569;">Densidad</div>
        <div style="font-weight:700;color:#F9A8D4;">{dens}</div>
      </div>
    </div>

    <!-- Seleccionar para análisis -->
    <div style="margin-top:10px;text-align:center;font-size:.72rem;color:#475569;">
      ☝ Clic en el panel derecho para análisis completo
    </div>
  </div>
  <!-- Municipio name marker for JS extraction -->
  <span id="muni-marker" data-muni="{muni}" style="display:none;"></span>
</div>"""

# ═══════════════════════════════════════════════════════════════════════════
# CONSTRUIR MAPA FOLIUM
# ═══════════════════════════════════════════════════════════════════════════
def build_map(visible_munis_tuple, capa_mode, show_labels_, show_disputes_, center=None, zoom=7, radios_gj=None):
    visible = set(visible_munis_tuple)

    m = folium.Map(
        location=center or [-36.5, -60.0],
        zoom_start=zoom,
        tiles=None,
        prefer_canvas=True,
    )

    # Base tiles
    folium.TileLayer(
        'CartoDB.DarkMatter',
        name='🌑 Dark (OSINT)',
        attr='© CartoDB',
        max_zoom=19,
    ).add_to(m)
    folium.TileLayer(
        'CartoDB.Positron',
        name='⬜ Claro (calles)',
        attr='© CartoDB',
        max_zoom=19,
    ).add_to(m)
    folium.TileLayer(
        'OpenStreetMap',
        name='🗺 OpenStreetMap',
        attr='© OpenStreetMap contributors',
        max_zoom=19,
    ).add_to(m)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        name='🛰 Satélite (Esri)',
        attr='Tiles © Esri — Maxar, Earthstar Geographics',
        max_zoom=19,
    ).add_to(m)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        name='🏙 Esri Calles',
        attr='Tiles © Esri',
        max_zoom=19,
    ).add_to(m)
    folium.TileLayer(
        tiles='https://wms.ign.gob.ar/geoserver/gwc/service/tms/1.0.0/capabaseargenmap@EPSG:3857@png/{z}/{x}/{y}.png',
        name='📍 IGN Argentina (manzanas)',
        attr='© IGN Argentina',
        max_zoom=18,
        tms=True,
    ).add_to(m)

    Fullscreen(position='topleft').add_to(m)
    MiniMap(tile_layer='CartoDB.DarkMatter', toggle_display=True, position='bottomright', width=130, height=90).add_to(m)

    layer_poly  = folium.FeatureGroup(name="Municipios", show=True)
    layer_pt    = folium.FeatureGroup(name="Sin polígono (puntos)", show=True)
    layer_disp  = folium.FeatureGroup(name="⚠️ En disputa (<3pp)", show=show_disputes_)

    for feat in geojson_data['features']:
        props = feat['properties']
        muni  = props.get('municipio', '')
        geom  = feat.get('geometry')

        if not geom:
            continue

        is_visible = muni in visible
        fill  = get_color(props, capa_mode) if is_visible else '#1E293B'
        opac  = 0.75 if is_visible else 0.18
        w_    = 1.2 if is_visible else 0.5
        popup = folium.Popup(make_popup(props), max_width=340) if is_visible else None
        tip   = folium.Tooltip(
            f"<b style='color:{'#F1F5F9' if is_visible else '#475569'};'>{muni}</b>"
            + (f"<br><span style='color:{fill};font-size:.78rem;'>{props.get('bloque','')}</span>"
               + f"<br><span style='font-size:.72rem;color:#94A3B8;'>Margen: {props.get('margen',0):.1f}pp</span>" if is_visible else ""),
            sticky=True,
        )

        geo_style  = {'fillColor': fill, 'color': BORDER_CLR, 'weight': w_, 'fillOpacity': opac}
        geo_hi     = {'weight': 3, 'color': '#F1F5F9', 'fillOpacity': 0.9}
        disp_style = {'fillColor': 'transparent', 'color': '#EF4444',
                      'weight': 2.5, 'fillOpacity': 0, 'dashArray': '5 4'}

        if geom['type'] == 'Point':
            if is_visible:
                folium.CircleMarker(
                    location=[geom['coordinates'][1], geom['coordinates'][0]],
                    radius=9, color=fill, fill=True,
                    fill_color=fill, fill_opacity=0.85, weight=2,
                    popup=popup, tooltip=tip,
                ).add_to(layer_pt)
        else:
            folium.GeoJson(
                {'type': 'Feature', 'geometry': geom, 'properties': props},
                style_function=lambda x, s=geo_style: s,
                highlight_function=lambda x, h=geo_hi: h,
                popup=popup, tooltip=tip,
            ).add_to(layer_poly)

        # Dispute overlay
        if is_visible and (props.get('margen') or 0) <= 3 and geom['type'] != 'Point':
            folium.GeoJson(
                {'type': 'Feature', 'geometry': geom, 'properties': props},
                style_function=lambda x, d=disp_style: d,
            ).add_to(layer_disp)

        # Labels
        if show_labels_ and is_visible and geom['type'] != 'Point':
            try:
                coords = geom['coordinates']
                if geom['type'] == 'Polygon':
                    ring = coords[0]
                else:
                    ring = max(coords, key=lambda p: len(p[0]))[0]
                cx = sum(c[0] for c in ring) / len(ring)
                cy = sum(c[1] for c in ring) / len(ring)
                short = muni.split()[-1] if len(muni) > 12 else muni
                folium.Marker(
                    [cy, cx],
                    icon=folium.DivIcon(
                        html=f"<div style='font-size:.6rem;color:#E2E8F0;font-weight:600;"
                             f"text-shadow:0 0 3px #000,0 0 3px #000;white-space:nowrap;"
                             f"transform:translate(-50%,-50%);'>{short}</div>",
                        icon_size=(80, 16), icon_anchor=(40, 8),
                    ),
                ).add_to(layer_poly)
            except Exception:
                pass

    layer_poly.add_to(m)
    layer_pt.add_to(m)
    layer_disp.add_to(m)

    # Capa de radios censales (solo si se activa y hay municipio seleccionado)
    if radios_gj and radios_gj.get('features'):
        n = len(radios_gj['features'])
        layer_radios = folium.FeatureGroup(name=f"🔲 Radios censales 2022 ({n})", show=True)
        folium.GeoJson(
            radios_gj,
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': '#F59E0B',
                'weight': 0.8,
                'fillOpacity': 0,
                'dashArray': '3 2',
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['CRO', 'FRACCION', 'RADIO', 'TRO'],
                aliases=['Código:', 'Fracción:', 'Radio:', 'Tipo:'],
                style='background:#0F172A;color:#E2E8F0;font-size:.75rem;border:1px solid #334155;',
            ),
        ).add_to(layer_radios)
        layer_radios.add_to(m)

    folium.LayerControl(position='topright', collapsed=False).add_to(m)

    return m

with st.spinner("Renderizando mapa..."):
    radios_data = None
    sel_muni = st.session_state.selected_muni
    if show_radios and sel_muni:
        with st.spinner(f"Cargando radios de {sel_muni}..."):
            radios_data = load_radios_by_partido(sel_muni)

    folium_map = build_map(
        tuple(sorted(visible_munis)),
        capa,
        show_labels,
        show_disputes,
        center=st.session_state.map_center,
        zoom=st.session_state.map_zoom,
        radios_gj=radios_data,
    )

# ═══════════════════════════════════════════════════════════════════════════
# MAPA – FULL WIDTH / FULL HEIGHT
# ═══════════════════════════════════════════════════════════════════════════
map_result = st_folium(
    folium_map,
    width="100%",
    height=920,
    returned_objects=["last_object_clicked_popup", "last_object_clicked"],
    key=f"map_{capa}_{tuple(sorted(visible_munis))}_{show_labels}_{show_disputes}_{show_radios}_{sel_muni}_{st.session_state.map_center[0]:.4f}_{st.session_state.map_zoom}",
)

# Detectar municipio clickeado via lat/lng → point-in-polygon
clicked = map_result.get("last_object_clicked") if map_result else None
if clicked and isinstance(clicked, dict):
    lat = clicked.get("lat")
    lng = clicked.get("lng")
    if lat is not None and lng is not None:
        found = find_muni_by_point(lat, lng)
        if found and found != st.session_state.selected_muni:
            st.session_state.selected_muni = found
            st.rerun()

# ─────────────────────────────────────────────
# PANEL INTELIGENCIA → SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    sel = st.session_state.selected_muni
    sel_row = df_all[df_all['municipio'] == sel].iloc[0] if sel and sel in df_all['municipio'].values else None

    st.markdown("""
    <div style="font-size:.6rem;font-weight:700;color:#1E3A5F;text-transform:uppercase;
                letter-spacing:.14em;margin:12px 0 6px;padding-bottom:5px;
                border-bottom:1px solid #0F172A;">Municipio seleccionado</div>
    """, unsafe_allow_html=True)

    if sel_row is None:
        st.markdown("""
        <div style="background:#0F172A;border:1px dashed #1E293B;border-radius:10px;
                    padding:24px 16px;text-align:center;margin-top:4px;">
          <div style="font-size:1.4rem;opacity:.4;margin-bottom:8px;">🗺</div>
          <div style="color:#334155;font-size:.75rem;line-height:1.5;">
            Hacé click en un municipio<br>o buscalo arriba
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        color  = BLOQUE_HEX.get(sel_row['bloque'], DEFAULT_CLR)
        cat    = sel_row['categoria']
        cat_c  = CAT_HEX.get(cat, DEFAULT_CLR)
        pct_gd = sel_row['ganador_pct'] or 0
        marg   = sel_row['margen'] or 0
        pop    = sel_row['poblacion_2022'] or 0
        km2    = sel_row['superficie_km2'] or 0

        # Header del municipio
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{color}CC,{color}88);
                    border:1px solid {color}66;border-radius:10px;
                    padding:12px 14px;margin-bottom:8px;">
          <div style="font-size:1rem;font-weight:800;color:white;letter-spacing:-.01em;">{sel}</div>
          <div style="font-size:.7rem;color:rgba(255,255,255,.6);margin-top:1px;">{sel_row['seccion_nombre']}</div>
          <div style="margin-top:8px;display:flex;gap:4px;flex-wrap:wrap;">
            <span style="background:rgba(0,0,0,.35);color:rgba(255,255,255,.85);
                         padding:2px 8px;border-radius:20px;font-size:.62rem;font-weight:700;
                         letter-spacing:.03em;">{sel_row['bloque']}</span>
            <span style="background:{cat_c}33;color:{cat_c};border:1px solid {cat_c}66;
                         padding:2px 8px;border-radius:20px;font-size:.62rem;font-weight:700;
                         letter-spacing:.03em;">{cat}</span>
          </div>
        </div>""", unsafe_allow_html=True)

        # Datos clave
        dens = f"{pop/km2:.0f}" if km2 else "S/D"
        rows_intel = [
            ("Intendente",   sel_row['intendente']),
            ("Partido",      sel_row['partido'][:35] + ('…' if len(sel_row['partido']) > 35 else '')),
            ("Padrón",       f"{sel_row['padron']:,}".replace(',','.')),
            ("Población",    f"{pop:,}".replace(',','.')),
            ("Densidad",     f"{dens} hab/km²"),
            ("Superficie",   f"{km2:,.0f} km²".replace(',','.')),
            ("Concejales",   str(sel_row['concejales_electos'])),
        ]
        items_html = "".join(
            f"<div class='intel-row'><span class='intel-key'>{k}</span><span class='intel-val'>{v}</span></div>"
            for k, v in rows_intel
        )
        st.markdown(f"<div class='intel-card'>{items_html}</div>", unsafe_allow_html=True)

        # Gráfico resultado electoral (mini donut)
        seg_pct = sel_row.get('segundo_pct') or 0
        otros_pct = max(0, 100 - pct_gd - seg_pct)
        fig_elec = go.Figure(go.Pie(
            values=[pct_gd, seg_pct, otros_pct],
            labels=[sel_row['partido'][:20], (sel_row.get('segundo','') or '')[:20], 'Otros'],
            hole=.55,
            marker_colors=[color, '#475569', '#1E293B'],
            textinfo='percent',
            textfont=dict(size=10, color='white'),
            showlegend=False,
        ))
        fig_elec.update_layout(
            height=160, margin=dict(t=4,b=4,l=4,r=4),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            annotations=[dict(text=f"<b>{pct_gd:.0f}%</b>", x=.5, y=.5,
                              font_size=16, font_color='white', showarrow=False)],
        )
        st.plotly_chart(fig_elec, use_container_width=True, config={'displayModeBar': False})

        # Vs promedio provincial
        prom_marg = df_all['margen'].mean()
        prom_pct  = df_all['ganador_pct'].mean()

        delta_marg = marg - prom_marg
        delta_pct  = pct_gd - prom_pct

        c1, c2 = st.columns(2)
        c1.metric("Margen", f"{marg:.1f}pp",
                  f"{delta_marg:+.1f}pp vs prom.",
                  delta_color="normal")
        c2.metric("% ganador", f"{pct_gd:.1f}%",
                  f"{delta_pct:+.1f}pp vs prom.",
                  delta_color="normal")

        # Concejales del municipio
        muni_conc = conc_df[conc_df['municipio'] == sel]
        if not muni_conc.empty:
            with st.expander(f"Concejales 2023 ({len(muni_conc)})", expanded=False):
                for _, row in muni_conc.iterrows():
                    st.markdown(
                        f"<div style='font-size:.75rem;padding:3px 0;border-bottom:1px solid #1E293B;color:#E2E8F0;'>"
                        f"<b>{row['nombre']}</b><br>"
                        f"<span style='color:#64748B;'>{row.get('partido','')[:40]}</span></div>",
                        unsafe_allow_html=True,
                    )

        # Secretarios del municipio
        muni_secs = sec_dict.get(sel, [])
        if muni_secs:
            with st.expander(f"Gabinete ({len(muni_secs)} secretarías)", expanded=False):
                for s in muni_secs:
                    nm = s.get('nombre','') if isinstance(s, dict) else s[0]
                    cg = s.get('cargo','') if isinstance(s, dict) else s[1]
                    st.markdown(
                        f"<div style='font-size:.75rem;padding:3px 0;border-bottom:1px solid #1E293B;color:#E2E8F0;'>"
                        f"<b>{nm}</b><br><span style='color:#64748B;'>{cg}</span></div>",
                        unsafe_allow_html=True,
                    )

# ═══════════════════════════════════════════════════════════════════════════
# SECCIÓN DE ANALYTICS (DEBAJO DEL MAPA)
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.markdown("<div class='section-label'>Analytics de los municipios filtrados</div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Distribución de poder",
    "🎯 Mapa de competitividad",
    "🔥 Matriz estratégica",
    "⚠️ Territorios en disputa",
    "📋 Tabla detallada",
])

# ── Tab 1: Distribución de poder ─────────────────────────────────────────
with tab1:
    a1, a2 = st.columns(2)
    with a1:
        fig_b = px.bar(
            df.groupby('bloque').size().reset_index(name='municipios').sort_values('municipios'),
            x='municipios', y='bloque', orientation='h',
            color='bloque', color_discrete_map=BLOQUE_HEX,
            title="Municipios por bloque",
            text='municipios',
        )
        fig_b.update_layout(
            height=220, margin=dict(t=30,b=10,l=10,r=10),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,23,42,1)',
            showlegend=False, font_color='#E2E8F0',
            xaxis=dict(gridcolor='#1E293B', color='#64748B'),
            yaxis=dict(gridcolor='#1E293B', color='#E2E8F0'),
            title_font=dict(color='#94A3B8', size=13),
        )
        fig_b.update_traces(textfont=dict(color='white'))
        st.plotly_chart(fig_b, use_container_width=True, config={'displayModeBar': False})

    with a2:
        bloque_pop = df.groupby('bloque')['poblacion_2022'].sum().reset_index()
        bloque_pop.columns = ['bloque', 'poblacion']
        fig_p = px.pie(
            bloque_pop, values='poblacion', names='bloque',
            color='bloque', color_discrete_map=BLOQUE_HEX,
            title="Población representada por bloque",
            hole=.45,
        )
        fig_p.update_layout(
            height=220, margin=dict(t=30,b=10,l=10,r=10),
            paper_bgcolor='rgba(0,0,0,0)', font_color='#E2E8F0',
            legend=dict(font=dict(color='#E2E8F0'), bgcolor='rgba(0,0,0,0)'),
            title_font=dict(color='#94A3B8', size=13),
        )
        st.plotly_chart(fig_p, use_container_width=True, config={'displayModeBar': False})

# ── Tab 2: Mapa de competitividad (scatter) ───────────────────────────────
with tab2:
    fig_sc = px.scatter(
        df,
        x='padron', y='margen',
        color='bloque', color_discrete_map=BLOQUE_HEX,
        size='poblacion_2022',
        hover_name='municipio',
        hover_data={'partido': True, 'ganador_pct': ':.1f', 'seccion_nombre': True,
                    'padron': ':,', 'poblacion_2022': ':,', 'bloque': False},
        title="Competitividad electoral vs Padrón electoral · tamaño = Población 2022",
        labels={'padron': 'Padrón electoral', 'margen': 'Margen 1° vs 2° (pp)',
                'ganador_pct': '% ganador'},
    )
    # Zona de disputa
    fig_sc.add_hrect(y0=0, y1=3, fillcolor='#EF4444', opacity=0.08,
                     annotation_text="⚠️ Zona de disputa (<3pp)",
                     annotation_font=dict(color='#EF4444', size=10))
    fig_sc.add_hrect(y0=3, y1=8, fillcolor='#F59E0B', opacity=0.05,
                     annotation_text="Competitivo (3-8pp)",
                     annotation_font=dict(color='#F59E0B', size=10))
    fig_sc.update_layout(
        height=400, margin=dict(t=40,b=20,l=20,r=20),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,23,42,1)',
        font_color='#E2E8F0',
        xaxis=dict(gridcolor='#1E293B', color='#64748B', type='log',
                   title='Padrón (escala log)'),
        yaxis=dict(gridcolor='#1E293B', color='#64748B'),
        legend=dict(bgcolor='rgba(15,23,42,.8)', font=dict(color='#E2E8F0')),
        title_font=dict(color='#94A3B8', size=13),
    )
    st.plotly_chart(fig_sc, use_container_width=True, config={'displayModeBar': False})

# ── Tab 3: Matriz estratégica ─────────────────────────────────────────────
with tab3:
    mat = df.groupby(['seccion_nombre', 'bloque']).size().reset_index(name='n')
    mat_pivot = mat.pivot(index='seccion_nombre', columns='bloque', values='n').fillna(0)
    fig_hm = px.imshow(
        mat_pivot,
        color_continuous_scale=[[0,'#0F172A'],[.5,'#1E3A5F'],[1,'#3B82F6']],
        title="Sección × Bloque — cantidad de municipios",
        text_auto=True,
        aspect='auto',
    )
    fig_hm.update_layout(
        height=320, margin=dict(t=40,b=10,l=10,r=10),
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#E2E8F0',
        title_font=dict(color='#94A3B8', size=13),
        coloraxis_showscale=False,
    )
    fig_hm.update_xaxes(color='#64748B')
    fig_hm.update_yaxes(color='#E2E8F0')
    st.plotly_chart(fig_hm, use_container_width=True, config={'displayModeBar': False})

    # Barras apiladas por sección
    fig_stk = px.bar(
        mat, x='seccion_nombre', y='n', color='bloque',
        color_discrete_map=BLOQUE_HEX,
        title="Municipios por sección y bloque",
        labels={'n': 'Municipios', 'seccion_nombre': ''},
    )
    fig_stk.update_layout(
        height=300, margin=dict(t=30,b=60,l=10,r=10),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,23,42,1)',
        font_color='#E2E8F0',
        xaxis=dict(gridcolor='#1E293B', color='#64748B', tickangle=-30),
        yaxis=dict(gridcolor='#1E293B', color='#64748B'),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#E2E8F0')),
        title_font=dict(color='#94A3B8', size=13),
        barmode='stack',
    )
    st.plotly_chart(fig_stk, use_container_width=True, config={'displayModeBar': False})

# ── Tab 4: Territorios en disputa ─────────────────────────────────────────
with tab4:
    swing = df[df['margen'] <= 5].sort_values('margen').head(30)
    if swing.empty:
        st.info("No hay municipios en disputa con los filtros actuales.")
    else:
        st.markdown(f"**{len(swing)} municipios con margen ≤ 5pp** (más competitivos)")
        for _, row in swing.iterrows():
            cat_   = row['categoria']
            c_b    = BLOQUE_HEX.get(row['bloque'], DEFAULT_CLR)
            c_cat  = CAT_HEX.get(cat_, DEFAULT_CLR)
            bar_w  = int(row['margen'] / 5 * 100)
            seg_b  = BLOQUE_HEX.get('Juntos por el Cambio' if row['bloque'] == 'Unión por la Patria' else 'Unión por la Patria', '#475569')

            st.markdown(f"""
            <div style="background:#1E293B;border-radius:8px;padding:10px 14px;margin-bottom:6px;
                        border-left:4px solid {c_cat};">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <span style="font-weight:700;color:#F1F5F9;font-size:.9rem;">{row['municipio']}</span>
                  <span style="background:{c_b}22;color:{c_b};padding:1px 8px;border-radius:10px;
                               font-size:.68rem;font-weight:700;margin-left:6px;">{row['bloque']}</span>
                  <span style="background:{c_cat}22;color:{c_cat};padding:1px 8px;border-radius:10px;
                               font-size:.68rem;font-weight:700;margin-left:4px;">{cat_}</span>
                </div>
                <div style="text-align:right;">
                  <span style="font-size:1.1rem;font-weight:800;color:{c_cat};">+{row['margen']:.1f}pp</span>
                </div>
              </div>
              <div style="font-size:.75rem;color:#64748B;margin-top:4px;">
                {row['intendente']} · {row['seccion_nombre']} · Padrón: {int(row['padron']):,}
              </div>
              <div style="background:#334155;border-radius:3px;height:4px;margin-top:6px;">
                <div style="background:{c_cat};height:4px;border-radius:3px;width:{bar_w}%;"></div>
              </div>
            </div>""".replace(',', '.'), unsafe_allow_html=True)

# ── Tab 5: Tabla detallada ────────────────────────────────────────────────
with tab5:
    table_df = df[[
        'municipio','intendente','partido','bloque','seccion_nombre',
        'zona','categoria','ganador_pct','margen','poblacion_2022','padron','concejales_electos',
    ]].copy()
    table_df.columns = [
        'Municipio','Intendente','Partido','Bloque','Sección',
        'Zona','Categoría','% Ganador','Margen (pp)','Población','Padrón','Concejales',
    ]
    table_df = table_df.sort_values('Margen (pp)')

    csv_data = table_df.to_csv(index=False).encode('utf-8')
    dl1, dl2 = st.columns([3,1])
    with dl2:
        st.download_button(
            "⬇ Descargar CSV",
            csv_data, "municipios_pba_filtrado.csv", "text/csv",
            use_container_width=True,
        )

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        height=380,
        column_config={
            '% Ganador':    st.column_config.ProgressColumn("% Ganador", min_value=0, max_value=100, format="%.1f%%"),
            'Margen (pp)':  st.column_config.NumberColumn("Margen", format="%.1f pp"),
            'Población':    st.column_config.NumberColumn("Población", format="%d"),
            'Padrón':       st.column_config.NumberColumn("Padrón", format="%d"),
        }
    )
    st.caption(f"{len(table_df)} municipios · filtros activos")
