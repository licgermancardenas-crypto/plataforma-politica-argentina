"""
Capital Federal (CABA) – Mapa político por Comunas
Fuente: Datos Abiertos GCBA · Elecciones 2023
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
import folium
from streamlit_folium import st_folium
from shapely.geometry import shape

st.set_page_config(
    page_title="CABA – Capital Federal",
    page_icon="🏙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background:#0D1117; }
[data-testid="stSidebar"]          { background:#0A1628; border-right:1px solid #1E293B; }
[data-testid="stSidebar"] *        { color:#E2E8F0 !important; }
[data-testid="stSidebar"] .stSelectbox label { color:#94A3B8 !important; }
[data-testid="stHeader"]           { background:transparent; }
div[data-testid="stMetric"]        { background:#0A1628; border:1px solid #1E293B; border-radius:8px; padding:12px 16px; }
[data-testid="stStatusWidget"]     { display: none !important; }
[data-stale="true"]                { opacity: 1 !important; transition: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Datos ──────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

@st.cache_data(show_spinner=False)
def load_comunas():
    with open(os.path.join(DATA_DIR, "comunas_caba.geojson"), encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(show_spinner=False)
def load_elecciones():
    with open(os.path.join(DATA_DIR, "elecciones_caba_2023.json"), encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(show_spinner=False)
def build_bounds_index(geojson):
    idx = {}
    for feat in geojson["features"]:
        c = feat["properties"]["comuna"]
        try:
            b = shape(feat["geometry"]).bounds
            idx[c] = [[b[1], b[0]], [b[3], b[2]]]
        except Exception:
            pass
    return idx

geojson_data = load_comunas()
elec_list    = load_elecciones()
elec_by_id   = {e["seccion_id"]: e for e in elec_list}
bounds_index = build_bounds_index(geojson_data)

# ── Constantes ────────────────────────────────────────────────────────
PARTIDO_COLOR = {
    "JUNTOS POR EL CAMBIO": "#1D4ED8",
    "UNION POR LA PATRIA":  "#DC2626",
    "LA LIBERTAD AVANZA":   "#7C3AED",
    "FRENTE DE IZQUIERDA Y DE TRABAJADORES - UNIDAD": "#F59E0B",
}
PARTIDO_SHORT = {
    "JUNTOS POR EL CAMBIO": "JxC",
    "UNION POR LA PATRIA":  "UxP",
    "LA LIBERTAD AVANZA":   "LLA",
    "FRENTE DE IZQUIERDA Y DE TRABAJADORES - UNIDAD": "FIT-U",
}

def margin_color(ganador, margen):
    base = PARTIDO_COLOR.get(ganador, "#64748B")
    # Lighten for small margins, darken for large
    if margen < 8:
        return base + "88"
    elif margen < 20:
        return base + "BB"
    elif margen < 35:
        return base + "DD"
    else:
        return base

# ── Session State ─────────────────────────────────────────────────────
if "sel_comuna" not in st.session_state:
    st.session_state.sel_comuna = None
if "zoomed_comuna" not in st.session_state:
    st.session_state.zoomed_comuna = None
if "map_center" not in st.session_state:
    st.session_state.map_center = [-34.615, -58.443]
if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = 11

# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏙 Capital Federal")
    st.markdown("<span style='font-size:.75rem;color:#64748B;'>CABA – 15 Comunas · 48 Barrios</span>", unsafe_allow_html=True)
    st.markdown("---")

    options = ["— ver todas —"] + [f"Comuna {e['seccion_id']:02d}" for e in sorted(elec_list, key=lambda x: x['seccion_id'])]
    sel_label = st.selectbox("Buscar comuna", options, key="search_caba")
    if sel_label != "— ver todas —":
        num = int(sel_label.split()[1])
        if st.session_state.sel_comuna != num:
            st.session_state.sel_comuna   = num
            st.session_state.zoomed_comuna = num  # búsqueda = zoom inmediato
            st.rerun()
    elif sel_label == "— ver todas —" and st.session_state.sel_comuna is not None:
        if st.button("Limpiar selección"):
            st.session_state.sel_comuna    = None
            st.session_state.zoomed_comuna = None
            st.rerun()

    st.markdown("---")

    # ── Panel intel ───────────────────────────────────────────────────
    sel = st.session_state.sel_comuna
    if sel is not None and sel in elec_by_id:
        e = elec_by_id[sel]
        props = next((f["properties"] for f in geojson_data["features"] if f["properties"]["comuna"] == sel), {})

        ganador  = e["ganador"]
        color    = PARTIDO_COLOR.get(ganador, "#64748B")
        short    = PARTIDO_SHORT.get(ganador, ganador)
        short2   = PARTIDO_SHORT.get(e["segundo"], e["segundo"])

        pct_g    = e["pct_ganador"]
        pct_s    = e["pct_segundo"]
        margen   = e["margen"]
        padron   = e["padron"]
        total_p  = e["total_positivos"]
        total_e  = e["total_emitidos"]

        # Participación
        part_pct = round(total_e / padron * 100, 1) if padron > 0 else 0

        # Header
        st.markdown(f"""
<div style="background:linear-gradient(150deg,{color}DD 0%,{color}44 100%);
            border:1px solid {color}66;border-radius:11px;padding:12px 14px 10px;margin-bottom:8px;">
  <div style="font-size:1.1rem;font-weight:800;color:#fff;">Comuna {sel:02d}</div>
  <div style="font-size:.65rem;color:rgba(255,255,255,.5);margin-bottom:6px;">{props.get('barrios','')}</div>
  <span style="background:{color}33;color:{color};border:1px solid {color}55;padding:2px 9px;border-radius:12px;font-size:.7rem;font-weight:700;">{short}</span>
</div>""", unsafe_allow_html=True)

        def stat_cell(clr, ico, label, val, sub=""):
            sub_h = f"<div style='font-size:.54rem;color:#475569;margin-top:2px;'>{sub}</div>" if sub else ""
            return (
                f"<div style='background:#0A1628;border:1px solid #1E293B;border-radius:7px;padding:7px 9px;'>"
                f"<div style='font-size:.58rem;color:#334155;margin-bottom:3px;'>{ico} {label}</div>"
                f"<div style='font-size:.85rem;font-weight:800;color:{clr};line-height:1.1;'>{val}</div>"
                f"{sub_h}</div>"
            )

        padron_s = f"{padron:,}".replace(",", ".")
        area_s   = f"{props.get('area_km2', 0):.1f}"
        cells = "".join([
            stat_cell("#6EE7B7", "🗳", "Padrón", padron_s, "Electores 2023"),
            stat_cell("#93C5FD", "✅", "Participación", f"{part_pct}%", f"{total_e:,} emitidos".replace(",",".")),
            stat_cell("#FCD34D", "📐", "Superficie", f"{area_s} km²", ""),
            stat_cell("#F9A8D4", "🏘", "Barrios", str(len(props.get("barrios","").split(","))), props.get("barrios","")[:35]+"…" if len(props.get("barrios",""))>35 else props.get("barrios","")),
        ])
        st.markdown(
            f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:7px;'>{cells}</div>",
            unsafe_allow_html=True,
        )

        # Electoral bars
        color2 = PARTIDO_COLOR.get(e["segundo"], "#64748B")
        bar_g  = min(pct_g, 100)
        bar_s  = min(pct_s, 100)
        cat_c  = "#6EE7B7" if margen > 15 else "#FCD34D" if margen > 5 else "#F87171"
        # CABA avg JxC = 47.5% (our data)
        delta  = round(pct_g - 47.5, 1)
        delta_m_vs_caba = round(margen - 18.3, 1)  # avg margin in CABA
        delta_s = f"{delta:+.1f}pp vs CABA"
        st.markdown(f"""
<div style="background:#0A1628;border:1px solid #1E293B;border-radius:9px;padding:10px 12px;margin-bottom:6px;">
  <div style="font-size:.58rem;font-weight:700;color:#334155;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;">Resultado 2023 – Jefe de Gobierno</div>
  <div style="display:flex;justify-content:space-between;font-size:.7rem;margin-bottom:3px;"><span style="color:#94A3B8;">{e['ganador'][:32]}</span><span style="color:{color};font-weight:700;">{pct_g:.1f}%</span></div>
  <div style="background:#1E293B;border-radius:4px;height:7px;margin-bottom:9px;"><div style="background:{color};height:7px;width:{bar_g:.0f}%;border-radius:4px;"></div></div>
  <div style="display:flex;justify-content:space-between;font-size:.7rem;margin-bottom:3px;"><span style="color:#94A3B8;">{e['segundo'][:32]}</span><span style="color:{color2};font-weight:700;">{pct_s:.1f}%</span></div>
  <div style="background:#1E293B;border-radius:4px;height:7px;margin-bottom:10px;"><div style="background:{color2};height:7px;width:{bar_s:.0f}%;border-radius:4px;"></div></div>
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <span style="background:{cat_c}22;color:{cat_c};border:1px solid {cat_c}55;padding:3px 10px;border-radius:20px;font-size:.7rem;font-weight:800;">+{margen:.1f} pp ventaja</span>
    <span style="font-size:.6rem;color:#475569;">{delta_s}</span>
  </div>
</div>""", unsafe_allow_html=True)

    else:
        # CABA summary
        total_padron = sum(e["padron"] for e in elec_list)
        total_emitidos = sum(e["total_emitidos"] for e in elec_list)
        jxc_total = sum(e["votos_ganador"] for e in elec_list if e["ganador"] == "JUNTOS POR EL CAMBIO")
        uxp_total = sum(e["votos_ganador"] for e in elec_list if e["ganador"] == "UNION POR LA PATRIA")
        total_pos_caba = sum(e["total_positivos"] for e in elec_list)

        st.markdown("**📊 Resumen CABA 2023**", unsafe_allow_html=False)

        def mini_card(clr, label, val):
            return (
                f"<div style='background:#0A1628;border:1px solid #1E293B;border-radius:7px;padding:8px 10px;margin-bottom:4px;'>"
                f"<div style='font-size:.58rem;color:#334155;'>{label}</div>"
                f"<div style='font-size:.9rem;font-weight:800;color:{clr};'>{val}</div></div>"
            )

        padron_s = f"{total_padron:,}".replace(",", ".")
        emitidos_s = f"{total_emitidos:,}".replace(",", ".")
        part = round(total_emitidos / total_padron * 100, 1)
        jxc_pct = round(jxc_total / total_pos_caba * 100, 1)
        uxp_pct = round(uxp_total / total_pos_caba * 100, 1)
        comunas_jxc = sum(1 for e in elec_list if e["ganador"] == "JUNTOS POR EL CAMBIO")
        comunas_uxp = sum(1 for e in elec_list if e["ganador"] == "UNION POR LA PATRIA")

        cards_html = "".join([
            mini_card("#6EE7B7", "Padrón total", padron_s),
            mini_card("#93C5FD", "Participación", f"{part}%"),
            mini_card("#1D4ED8", "JxC – Jorge Macri", f"{jxc_pct:.1f}% · {comunas_jxc}/15 comunas"),
            mini_card("#DC2626", "UxP – Leandro Santoro", f"{uxp_pct:.1f}% · {comunas_uxp}/15 comunas"),
        ])
        st.markdown(cards_html, unsafe_allow_html=True)

        st.markdown("<div style='font-size:.6rem;color:#334155;margin-top:8px;'>Hacé clic en una comuna para ver el detalle</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div style='font-size:.65rem;color:#334155;'>Fuente: Datos Abiertos GCBA<br>Elecciones Generales 2023</div>", unsafe_allow_html=True)

# ── Main content ───────────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#0A1628,#1E3A5F);padding:20px 28px;border-radius:12px;margin-bottom:20px;border:1px solid #1E293B;'>
<h1 style='color:#fff;margin:0;font-size:1.7rem;'>🏙 Ciudad Autónoma de Buenos Aires</h1>
<p style='color:#64748B;margin:5px 0 0;font-size:.88rem;'>Capital Federal · 15 Comunas · 48 Barrios · Resultados electorales 2023</p>
</div>
""", unsafe_allow_html=True)

# ── KPI row ───────────────────────────────────────────────────────────
total_padron = sum(e["padron"] for e in elec_list)
total_emitidos = sum(e["total_emitidos"] for e in elec_list)
total_pos_caba = sum(e["total_positivos"] for e in elec_list)
jxc_votos = sum(e["votos_ganador"] for e in elec_list if e["ganador"] == "JUNTOS POR EL CAMBIO") + \
            sum(e["votos_segundo"] for e in elec_list if e["segundo"] == "JUNTOS POR EL CAMBIO")
uxp_votos = sum(e["votos_ganador"] for e in elec_list if e["ganador"] == "UNION POR LA PATRIA") + \
            sum(e["votos_segundo"] for e in elec_list if e["segundo"] == "UNION POR LA PATRIA")
lla_votos = 246179  # from global total

k1, k2, k3, k4, k5 = st.columns(5)
kpi_cards = [
    (k1, f"{total_padron:,}".replace(",","."),          "Padrón electoral",          "#1E40AF", "🗳"),
    (k2, f"{round(total_emitidos/total_padron*100,1)}%", "Participación",             "#065F46", "✅"),
    (k3, f"{round(jxc_votos/total_pos_caba*100,1)}%",   "JxC (Jorge Macri)",         "#1D4ED8", "🔵"),
    (k4, f"{round(uxp_votos/total_pos_caba*100,1)}%",   "UxP (Leandro Santoro)",     "#DC2626", "🔴"),
    (k5, f"{round(lla_votos/total_pos_caba*100,1)}%",   "LLA (Ramiro Marra)",        "#7C3AED", "🟣"),
]
for col, val, label, color, icon in kpi_cards:
    with col:
        st.markdown(f"""
<div style='background:#0A1628;border:1px solid #1E293B;border-left:4px solid {color};border-radius:8px;padding:14px 18px;'>
  <div style='font-size:.72rem;color:#64748B;text-transform:uppercase;letter-spacing:.05em;'>{icon} {label}</div>
  <div style='font-size:1.6rem;font-weight:800;color:{color};margin-top:4px;'>{val}</div>
</div>""", unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Map ────────────────────────────────────────────────────────────────
sel         = st.session_state.sel_comuna
zoomed      = st.session_state.zoomed_comuna
fit_bounds  = bounds_index.get(zoomed) if zoomed else None

m = folium.Map(
    location=st.session_state.map_center,
    zoom_start=st.session_state.map_zoom,
    tiles=None,
    prefer_canvas=True,
)
folium.TileLayer(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attr="© CARTO", name="Dark", max_zoom=19,
).add_to(m)

if fit_bounds:
    m.fit_bounds(fit_bounds, padding=(60, 60))

# Draw comunas
for feat in geojson_data["features"]:
    props = feat["properties"]
    c_id  = props["comuna"]
    e     = elec_by_id.get(c_id, {})
    ganador = e.get("ganador", "")
    margen  = e.get("margen", 0)

    is_zoomed = (c_id == zoomed)
    fill      = margin_color(ganador, margen)
    border    = PARTIDO_COLOR.get(ganador, "#64748B")

    if zoomed:
        if is_zoomed:
            opacity, weight, border = 0.95, 4.0, "#FFFFFF"
        else:
            opacity, weight, border = 0.18, 0.5, "#FFFFFF22"
    else:
        opacity, weight = 0.58, 1.5

    short  = PARTIDO_SHORT.get(ganador, ganador)
    short2 = PARTIDO_SHORT.get(e.get("segundo",""), e.get("segundo",""))
    zoom_hint = "<br><span style='color:#6EE7B7;font-size:.65rem;'>🔍 Doble clic para hacer zoom</span>" if (c_id == sel and not is_zoomed) else ""
    tooltip = (
        f"<b>Comuna {c_id:02d}</b><br>"
        f"{props.get('barrios','')}<br><br>"
        f"<b>🏆 {short}</b> {e.get('pct_ganador',0):.1f}%<br>"
        f"2° {short2} {e.get('pct_segundo',0):.1f}%<br>"
        f"Margen: {margen:.1f} pp"
        + zoom_hint
    )

    folium.GeoJson(
        feat,
        style_function=lambda f, fc=fill, bc=border, op=opacity, wt=weight: {
            "fillColor": fc, "color": bc,
            "weight": wt, "fillOpacity": op,
        },
        highlight_function=lambda f: {"weight": 3, "fillOpacity": 0.85},
        tooltip=folium.Tooltip(tooltip, sticky=False),
    ).add_to(m)

    # Label
    try:
        centroid = shape(feat["geometry"]).centroid
        folium.Marker(
            location=[centroid.y, centroid.x],
            icon=folium.DivIcon(
                html=f"<div style='font-size:10px;font-weight:700;color:white;text-shadow:0 1px 3px #000;text-align:center;white-space:nowrap;'>C{c_id:02d}</div>",
                icon_size=(30, 16),
                icon_anchor=(15, 8),
            ),
        ).add_to(m)
    except Exception:
        pass

map_result = st_folium(
    m,
    height=620,
    use_container_width=True,
    returned_objects=["last_object_clicked_tooltip", "center", "zoom"],
    key=f"caba_map_{zoomed}",
)

# Guardar posición del mapa
if map_result:
    if map_result.get("center"):
        c = map_result["center"]
        st.session_state.map_center = [c["lat"], c["lng"]]
    if map_result.get("zoom"):
        st.session_state.map_zoom = map_result["zoom"]

# 1er clic → sidebar (key del mapa no cambia)
# Doble clic → zoom + resaltado exclusivo (key cambia)
if map_result and map_result.get("last_object_clicked_tooltip"):
    tip = map_result["last_object_clicked_tooltip"]
    if tip and "Comuna" in tip:
        try:
            import re
            match = re.search(r"Comuna (\d+)", tip)
            if match:
                clicked_id = int(match.group(1))
                if clicked_id == st.session_state.sel_comuna and st.session_state.zoomed_comuna != clicked_id:
                    # Doble clic → zoom
                    st.session_state.zoomed_comuna = clicked_id
                    st.rerun()
                elif clicked_id != st.session_state.sel_comuna:
                    # 1er clic → solo sidebar
                    st.session_state.sel_comuna    = clicked_id
                    st.session_state.zoomed_comuna = None
                    st.rerun()
        except Exception:
            pass

# ── Tabla resumen ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 Resultados por Comuna – Jefe de Gobierno 2023")

import pandas as pd
rows = []
for e in sorted(elec_list, key=lambda x: x["seccion_id"]):
    props = next((f["properties"] for f in geojson_data["features"] if f["properties"]["comuna"] == e["seccion_id"]), {})
    rows.append({
        "Comuna": f"C{e['seccion_id']:02d}",
        "Barrios": props.get("barrios", "")[:45],
        "Ganador": PARTIDO_SHORT.get(e["ganador"], e["ganador"]),
        "% Ganador": f"{e['pct_ganador']:.1f}%",
        "2° lugar": PARTIDO_SHORT.get(e["segundo"], e["segundo"]),
        "% 2°": f"{e['pct_segundo']:.1f}%",
        "Margen": f"{e['margen']:.1f} pp",
        "Padrón": f"{e['padron']:,}".replace(",","."),
        "Participación": f"{round(e['total_emitidos']/e['padron']*100,1)}%",
    })

df_res = pd.DataFrame(rows)

def color_ganador(val):
    if val == "JxC":
        return "background-color: #1D4ED822; color: #93C5FD"
    elif val == "UxP":
        return "background-color: #DC262622; color: #FCA5A5"
    return ""

st.dataframe(
    df_res,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Margen": st.column_config.TextColumn("Margen", width="small"),
        "% Ganador": st.column_config.TextColumn("% Ganador", width="small"),
    },
)

st.caption("Fuente: Datos Abiertos GCBA · datos.buenosaires.gob.ar · Elecciones Generales 2023 (escrutinio definitivo)")
