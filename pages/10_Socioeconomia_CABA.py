"""
Página 10 – Socioeconomía CABA
Indicadores sociales y habitacionales por comuna
Fuentes: GCBA Datos Abiertos · IVC · DGEyC · Censo INDEC 2010
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import loader

import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from shapely.geometry import shape

st.set_page_config(
    page_title="Socioeconomía CABA",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background:#0D1117; }
[data-testid="stSidebar"]          { background:#0A1628; border-right:1px solid #1E293B; }
[data-testid="stSidebar"] *        { color:#E2E8F0 !important; }
[data-testid="stHeader"]           { background:transparent; }
[data-testid="stStatusWidget"]     { display:none !important; }
[data-stale="true"]                { opacity:1 !important; transition:none !important; }
[data-stale]                       { opacity:1 !important; }
[aria-busy="true"]                 { opacity:1 !important; }
.stApp > *                         { opacity:1 !important; transition:none !important; }
iframe                             { opacity:1 !important; }
.stTabs [data-baseweb="tab"]       { color:#94A3B8 !important; }
.stTabs [aria-selected="true"]     { color:#6EE7B7 !important; border-bottom:2px solid #10B981 !important; }
</style>
""", unsafe_allow_html=True)

# ── Data ───────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

@st.cache_data(show_spinner=False)
def load_data():
    with open(os.path.join(DATA_DIR, "socioeconomia_caba.json"), encoding="utf-8") as f:
        return json.load(f)

data    = load_data()
geojson = loader.get_comunas_geojson()
df      = pd.DataFrame(data["por_comuna"])
df_pob  = pd.DataFrame(data["pobreza_serie"])

NIVEL_COLOR = {"Alta": "#EF4444", "Media": "#F97316", "Baja": "#6EE7B7"}
INDICADORES = {
    "idx_vulnerabilidad":    ("🔴 Índice de vulnerabilidad",  "higher_worse", "#EF4444"),
    "nbi_pct":               ("📊 Hogares con NBI (%)",       "higher_worse", "#F97316"),
    "deficit_cuantitativo":  ("🏚 Déficit habitacional cuant.", "higher_worse", "#FBBF24"),
    "hacinamiento_critico_pct": ("👥 Hacinamiento crítico (%)", "higher_worse", "#A78BFA"),
    "poblacion_2010":        ("👥 Población (Censo 2010)",     "neutral",     "#93C5FD"),
}

# ── Session state ──────────────────────────────────────────────────────
if "soc_comuna" not in st.session_state:
    st.session_state.soc_comuna = None
if "soc_indicador" not in st.session_state:
    st.session_state.soc_indicador = "idx_vulnerabilidad"

# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📐 Socioeconomía CABA")
    st.markdown("<span style='font-size:.75rem;color:#64748B;'>IVC · DGEyC · Censo INDEC 2010</span>", unsafe_allow_html=True)
    st.markdown("---")

    ind_sel = st.selectbox(
        "Ver en el mapa",
        list(INDICADORES.keys()),
        format_func=lambda k: INDICADORES[k][0],
        key="ind_mapa_sel",
    )
    st.session_state.soc_indicador = ind_sel

    st.markdown("---")
    com_opts = ["— todas —"] + [f"Comuna {i:02d}" for i in range(1, 16)]
    com_sel  = st.selectbox("Filtrar comuna", com_opts, key="com_sel_soc")
    if com_sel != "— todas —":
        st.session_state.soc_comuna = int(com_sel.split()[1])
    else:
        st.session_state.soc_comuna = None

    sel = st.session_state.soc_comuna
    if sel:
        row  = df[df["comuna"] == sel].iloc[0]
        gj_p = next((f["properties"] for f in geojson["features"] if f["properties"]["comuna"]==sel), {})
        niv  = row["nivel_vulnerabilidad"]
        clr  = NIVEL_COLOR[niv]
        st.markdown(f"""
<div style='background:#050d1a;border:1px solid {clr}44;border-radius:10px;padding:12px 14px;'>
  <div style='font-size:1rem;font-weight:800;color:#fff;margin-bottom:2px;'>📍 Comuna {sel:02d}</div>
  <div style='font-size:.65rem;color:#64748B;margin-bottom:8px;'>{gj_p.get("barrios","")}</div>
  <span style='background:{clr}22;color:{clr};border:1px solid {clr}44;padding:2px 10px;
        border-radius:12px;font-size:.7rem;font-weight:700;'>
    Vulnerabilidad {niv}
  </span>
""", unsafe_allow_html=True)

        def mini(lbl, val, clr2="#E2E8F0"):
            return (f"<div style='display:flex;justify-content:space-between;padding:5px 0;"
                    f"border-bottom:1px solid #0F172A;font-size:.78rem;'>"
                    f"<span style='color:#64748B;'>{lbl}</span>"
                    f"<span style='color:{clr2};font-weight:700;'>{val}</span></div>")

        pob_s = f"{int(row['poblacion_2010']):,}".replace(",",".")
        hog_s = f"{int(row['hogares']):,}".replace(",",".")
        st.markdown(
            mini("Población (2010)", pob_s, "#93C5FD") +
            mini("Hogares", hog_s, "#93C5FD") +
            mini("Índice vulnerabilidad", f"{row['idx_vulnerabilidad']}/100", clr) +
            mini("Hogares NBI", f"{row['nbi_pct']}%", "#F97316") +
            mini("Déficit hab. cuant.", f"{row['deficit_cuantitativo']}%", "#FBBF24") +
            mini("Hacinamiento crítico", f"{row['hacinamiento_critico_pct']}%", "#A78BFA") +
            mini("Agua de red pública", f"{row['agua_red_pct']}%", "#6EE7B7") +
            mini("Electricidad de red", f"{row['elec_red_pct']}%", "#6EE7B7"),
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div style='font-size:.6rem;color:#1E293B;'>IVC · Datos Abiertos GCBA · Censo INDEC 2010</div>", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#0A1628,#064e3b);padding:20px 28px;border-radius:12px;
            margin-bottom:20px;border:1px solid #065f4655;'>
  <h1 style='color:#fff;margin:0;font-size:1.7rem;'>📐 Socioeconomía – Ciudad de Buenos Aires</h1>
  <p style='color:#64748B;margin:5px 0 0;font-size:.88rem;'>
    NBI · Déficit habitacional · Hacinamiento · Infraestructura · Pobreza e indigencia · por comunas
  </p>
</div>
""", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────────────
tot_pob    = data["total_poblacion_2010"]
pct_nbi    = round(df["nbi_pct"].mean(), 1)
com_alta   = (df["nivel_vulnerabilidad"] == "Alta").sum()
com_media  = (df["nivel_vulnerabilidad"] == "Media").sum()
pct_def    = round(df["deficit_cuantitativo"].mean(), 1)
com_max_vul = int(df.loc[df["idx_vulnerabilidad"].idxmax(), "comuna"])

k1,k2,k3,k4,k5,k6 = st.columns(6)
kpis = [
    (k1, f"{tot_pob:,}".replace(",","."),   "Población total (2010)", "#3B82F6",  "CABA"),
    (k2, f"{pct_nbi}%",                     "NBI promedio CABA",      "#F97316",  "hogares"),
    (k3, str(com_alta),                      "Comunas alta vulnerab.", "#EF4444",  "C1, C4, C8"),
    (k4, str(com_media),                     "Comunas media vulnerab.","#F97316",  "C3, C7"),
    (k5, f"{pct_def}%",                      "Déficit hab. promedio",  "#FBBF24",  "cuantitativo"),
    (k6, f"C{com_max_vul:02d}",              "Mayor vulnerabilidad",   "#EF4444",  "índice más alto"),
]
for col, val, label, color, sub in kpis:
    with col:
        st.markdown(f"""
<div style='background:#0A1628;border:1px solid #1E293B;border-left:4px solid {color};
            border-radius:8px;padding:12px 16px;'>
  <div style='font-size:.65rem;color:#64748B;text-transform:uppercase;letter-spacing:.04em;'>{label}</div>
  <div style='font-size:1.45rem;font-weight:800;color:{color};margin:3px 0;'>{val}</div>
  <div style='font-size:.6rem;color:#334155;'>{sub}</div>
</div>""", unsafe_allow_html=True)

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# ── Tabs ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🗺 Mapa Temático", "📊 Indicadores por Comuna", "🏚 Vivienda e Infraestructura", "📈 Pobreza CABA"
])

# ══════════════════════════════════════════════════════════════════════
# TAB 1 – MAPA
# ══════════════════════════════════════════════════════════════════════
with tab1:
    ind_key   = st.session_state.soc_indicador
    ind_label, ind_dir, ind_color = INDICADORES[ind_key]

    max_val = df[ind_key].max()
    min_val = df[ind_key].min()

    def choro_color(val):
        if max_val == min_val:
            return "#6EE7B766"
        ratio = (val - min_val) / (max_val - min_val)
        if ind_dir == "higher_worse":
            r = int(239 * ratio + 16  * (1 - ratio))
            g = int(68  * ratio + 185 * (1 - ratio))
            b = int(68  * ratio + 129 * (1 - ratio))
        else:
            r = int(16  * ratio + 30  * (1 - ratio))
            g = int(185 * ratio + 100 * (1 - ratio))
            b = int(129 * ratio + 200 * (1 - ratio))
        alpha = int(50 + ratio * 170)
        return f"#{r:02X}{g:02X}{b:02X}{alpha:02X}"

    m = folium.Map(location=[-34.615, -58.443], zoom_start=12, tiles=None, prefer_canvas=True)
    folium.TileLayer(
        "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="© CARTO", max_zoom=19,
    ).add_to(m)

    for feat in geojson["features"]:
        cid  = feat["properties"]["comuna"]
        row  = df[df["comuna"] == cid]
        if row.empty: continue
        row  = row.iloc[0]
        val  = row[ind_key]
        fill = choro_color(val)
        is_sel  = (cid == st.session_state.soc_comuna)
        border  = "#FFFFFF" if is_sel else ind_color
        weight  = 3.5 if is_sel else 1.2
        opacity = 0.92 if is_sel else 0.78

        niv   = row["nivel_vulnerabilidad"]
        tooltip = (
            f"<b>Comuna {cid:02d}</b><br>"
            f"{feat['properties'].get('barrios','')}<br><br>"
            f"<b>{ind_label}:</b> {val:.1f}<br>"
            f"Vulnerabilidad: <b>{niv}</b><br>"
            f"NBI: {row['nbi_pct']}% · Déficit: {row['deficit_cuantitativo']}%"
        )
        folium.GeoJson(
            feat,
            style_function=lambda f, fc=fill, bc=border, op=opacity, wt=weight: {
                "fillColor": fc, "color": bc, "weight": wt, "fillOpacity": op,
            },
            highlight_function=lambda f: {"weight": 3, "fillOpacity": 0.95},
            tooltip=folium.Tooltip(tooltip, sticky=False),
        ).add_to(m)

        try:
            centroid = shape(feat["geometry"]).centroid
            folium.Marker(
                location=[centroid.y, centroid.x],
                icon=folium.DivIcon(
                    html=(f"<div style='font-size:9px;font-weight:800;color:white;"
                          f"text-shadow:0 1px 3px #000;text-align:center;'>"
                          f"C{cid:02d}<br>{val:.0f}</div>"),
                    icon_size=(32, 22), icon_anchor=(16, 11),
                ),
            ).add_to(m)
        except Exception:
            pass

    col_map, col_leg = st.columns([3, 1])
    with col_map:
        st_folium(m, height=560, use_container_width=True,
                  returned_objects=[], key=f"soc_map_{ind_key}_{st.session_state.soc_comuna}")

    with col_leg:
        st.markdown(f"<div style='font-size:.7rem;color:#64748B;font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;'>Ranking</div>", unsafe_allow_html=True)
        df_rank = df[["comuna", ind_key, "nivel_vulnerabilidad"]].sort_values(ind_key, ascending=(ind_dir != "higher_worse"))
        for _, r in df_rank.iterrows():
            niv   = r["nivel_vulnerabilidad"]
            clr   = NIVEL_COLOR[niv]
            val_n = r[ind_key]
            bar_w = int((val_n - min_val) / (max_val - min_val) * 100) if max_val != min_val else 50
            st.markdown(
                f"<div style='margin-bottom:6px;'>"
                f"<div style='display:flex;justify-content:space-between;font-size:.72rem;color:#94A3B8;margin-bottom:2px;'>"
                f"<span>C{int(r['comuna']):02d}</span>"
                f"<span style='color:{clr};font-weight:700;'>{val_n:.1f}</span></div>"
                f"<div style='background:#1E293B;border-radius:3px;height:5px;'>"
                f"<div style='background:{clr};height:5px;width:{bar_w}%;border-radius:3px;'></div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════════════════════════════
# TAB 2 – INDICADORES
# ══════════════════════════════════════════════════════════════════════
with tab2:
    col_i1, col_i2 = st.columns(2)

    with col_i1:
        df_nbi_c = df[["comuna","nbi_pct","nivel_vulnerabilidad"]].sort_values("nbi_pct", ascending=True)
        colors_nbi = [NIVEL_COLOR[n] for n in df_nbi_c["nivel_vulnerabilidad"]]
        fig_nbi = go.Figure(go.Bar(
            y=[f"C{int(c):02d}" for c in df_nbi_c["comuna"]],
            x=df_nbi_c["nbi_pct"],
            orientation="h",
            marker_color=colors_nbi,
            text=df_nbi_c["nbi_pct"].apply(lambda x: f"{x}%"),
            textposition="outside",
            textfont=dict(color="#E2E8F0", size=10),
        ))
        fig_nbi.add_vline(x=df["nbi_pct"].mean(), line_dash="dot", line_color="#475569",
                          annotation_text="promedio", annotation_font_color="#475569")
        fig_nbi.update_layout(
            title=dict(text="Hogares con NBI (%)", font=dict(color="#E2E8F0", size=13)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B", range=[0, 22]),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=35, b=5, l=5, r=40), height=370,
        )
        st.plotly_chart(fig_nbi, use_container_width=True)

    with col_i2:
        df_def_c = df[["comuna","deficit_cuantitativo","deficit_cualitativo","nivel_vulnerabilidad"]].sort_values("deficit_cuantitativo", ascending=True)
        fig_def = go.Figure()
        fig_def.add_trace(go.Bar(
            y=[f"C{int(c):02d}" for c in df_def_c["comuna"]],
            x=df_def_c["deficit_cuantitativo"],
            name="Cuantitativo", orientation="h",
            marker_color="#EF4444",
        ))
        fig_def.add_trace(go.Bar(
            y=[f"C{int(c):02d}" for c in df_def_c["comuna"]],
            x=df_def_c["deficit_cualitativo"],
            name="Cualitativo I", orientation="h",
            marker_color="#FBBF24",
        ))
        fig_def.update_layout(
            title=dict(text="Déficit habitacional (%)", font=dict(color="#E2E8F0", size=13)),
            barmode="group",
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
            xaxis=dict(gridcolor="#1E293B", range=[0, 22]),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=35, b=5, l=5, r=5), height=370,
        )
        st.plotly_chart(fig_def, use_container_width=True)

    # Scatter NBI vs Tasa delictiva
    st.markdown("---")
    st.markdown("#### 🔗 Correlación: NBI vs Tasa delictiva (2024)")

    @st.cache_data(show_spinner=False)
    def load_delitos():
        with open(os.path.join(DATA_DIR, "delitos_caba_stats.json"), encoding="utf-8") as f:
            return json.load(f)

    delitos = load_delitos()
    df_del  = pd.DataFrame(delitos["por_comuna"])
    df_cross = df.merge(df_del[["comuna","tasa_por_1000","total"]], on="comuna", how="left")
    df_cross["label"] = df_cross["comuna"].apply(lambda c: f"C{int(c):02d}")

    fig_sc = px.scatter(
        df_cross, x="nbi_pct", y="tasa_por_1000",
        color="nivel_vulnerabilidad",
        color_discrete_map=NIVEL_COLOR,
        text="label", size="poblacion_2010",
        labels={"nbi_pct": "NBI (%)", "tasa_por_1000": "Hechos delictivos cada 1.000 electores"},
        hover_data={"label": False, "nbi_pct": True, "tasa_por_1000": True, "nivel_vulnerabilidad": True},
    )
    fig_sc.update_traces(textposition="top center", textfont_size=9)
    fig_sc.update_layout(
        paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
        font=dict(color="#94A3B8"),
        xaxis=dict(gridcolor="#1E293B"),
        yaxis=dict(gridcolor="#1E293B"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=10, b=10, l=10, r=10), height=320,
    )
    st.plotly_chart(fig_sc, use_container_width=True)

    # Tabla completa
    st.markdown("---")
    df_t = df.copy()
    df_t["comuna"] = df_t["comuna"].apply(lambda x: f"C{int(x):02d}")
    df_t["Población"] = df_t["poblacion_2010"].apply(lambda x: f"{int(x):,}".replace(",","."))
    st.dataframe(df_t[[
        "comuna","Población","nbi_pct","deficit_cuantitativo",
        "hacinamiento_critico_pct","agua_red_pct","elec_red_pct",
        "idx_vulnerabilidad","nivel_vulnerabilidad"
    ]].rename(columns={
        "comuna":"Comuna","nbi_pct":"NBI %","deficit_cuantitativo":"Déficit cuant. %",
        "hacinamiento_critico_pct":"Hacinamiento crít. %","agua_red_pct":"Agua red %",
        "elec_red_pct":"Electricidad red %","idx_vulnerabilidad":"Índ. Vulnerab.",
        "nivel_vulnerabilidad":"Nivel",
    }), hide_index=True, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 3 – VIVIENDA
# ══════════════════════════════════════════════════════════════════════
with tab3:
    col_v1, col_v2 = st.columns(2)

    with col_v1:
        # Hacinamiento crítico
        df_hac_c = df[["comuna","hacinamiento_critico_pct","sin_hacinamiento_pct"]].sort_values("hacinamiento_critico_pct", ascending=True)
        fig_hac = go.Figure()
        fig_hac.add_trace(go.Bar(
            y=[f"C{int(c):02d}" for c in df_hac_c["comuna"]],
            x=df_hac_c["hacinamiento_critico_pct"],
            name="Crítico", orientation="h",
            marker_color="#EF4444",
            text=df_hac_c["hacinamiento_critico_pct"].apply(lambda x: f"{x:.1f}%"),
            textposition="outside",
        ))
        fig_hac.update_layout(
            title=dict(text="Hacinamiento crítico por comuna (%)", font=dict(color="#E2E8F0", size=13)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B", range=[0, 9]),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=35, b=5, l=5, r=45), height=370, showlegend=False,
        )
        st.plotly_chart(fig_hac, use_container_width=True)

    with col_v2:
        # Acceso a agua
        df_agua_c = df[["comuna","agua_red_pct"]].sort_values("agua_red_pct")
        colors_agua = ["#EF4444" if v < 98.5 else "#6EE7B7" for v in df_agua_c["agua_red_pct"]]
        fig_agua = go.Figure(go.Bar(
            y=[f"C{int(c):02d}" for c in df_agua_c["comuna"]],
            x=df_agua_c["agua_red_pct"],
            orientation="h",
            marker_color=colors_agua,
            text=df_agua_c["agua_red_pct"].apply(lambda x: f"{x:.1f}%"),
            textposition="outside",
        ))
        fig_agua.update_layout(
            title=dict(text="Acceso a agua de red pública (%)", font=dict(color="#E2E8F0", size=13)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B", range=[97, 100.3]),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=35, b=5, l=5, r=45), height=370, showlegend=False,
        )
        st.plotly_chart(fig_agua, use_container_width=True)

    # Radar comparativo
    st.markdown("---")
    st.markdown("#### Radar de vulnerabilidad — comunas extremas")
    radar_cats = ["NBI %","Déficit cuant. %","Hacin. crít. %","Sin agua red %","Sin electricidad %"]
    df_radar = df.copy()
    df_radar["sin_agua_pct"]  = 100 - df_radar["agua_red_pct"]
    df_radar["sin_elec_pct"]  = 100 - df_radar["elec_red_pct"]

    comunas_radar = [
        int(df.loc[df["idx_vulnerabilidad"].idxmax(), "comuna"]),  # más vulnerable
        int(df.loc[df["idx_vulnerabilidad"].idxmin(), "comuna"]),  # menos vulnerable
    ]
    radar_colors = ["#EF4444", "#6EE7B7"]
    fig_radar = go.Figure()
    for cid, clr in zip(comunas_radar, radar_colors):
        r = df_radar[df_radar["comuna"] == cid].iloc[0]
        vals = [r["nbi_pct"], r["deficit_cuantitativo"], r["hacinamiento_critico_pct"],
                r["sin_agua_pct"], r["sin_elec_pct"]]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=radar_cats + [radar_cats[0]],
            fill="toself", fillcolor=f"{clr}22",
            line=dict(color=clr, width=2),
            name=f"C{int(cid):02d}",
        ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="#0A1628",
            radialaxis=dict(visible=True, gridcolor="#1E293B", color="#475569"),
            angularaxis=dict(gridcolor="#1E293B", color="#94A3B8"),
        ),
        paper_bgcolor="#0A1628", font=dict(color="#94A3B8"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=20, b=20, l=20, r=20), height=320,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 4 – POBREZA CABA
# ══════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("#### Evolución de pobreza e indigencia – CABA (2015–2019)")
    st.markdown("<div style='font-size:.75rem;color:#475569;margin-bottom:12px;'>EAH – Encuesta Anual de Hogares · GCBA. Datos disponibles hasta 2019.</div>", unsafe_allow_html=True)

    fig_pob = go.Figure()
    fig_pob.add_trace(go.Scatter(
        x=df_pob["trimestre"], y=df_pob["En situación de indigencia"],
        name="Indigencia", mode="lines+markers",
        line=dict(color="#7F1D1D", width=2), marker=dict(size=5),
        fill="tozeroy", fillcolor="rgba(127,29,29,0.1)",
    ))
    fig_pob.add_trace(go.Scatter(
        x=df_pob["trimestre"], y=df_pob["En situación de pobreza no indigente"],
        name="Pobreza no indigente", mode="lines+markers",
        line=dict(color="#EF4444", width=2), marker=dict(size=5),
        fill="tozeroy", fillcolor="rgba(239,68,68,0.1)",
    ))
    fig_pob.add_trace(go.Scatter(
        x=df_pob["trimestre"], y=df_pob["No pobres"],
        name="No pobres", mode="lines",
        line=dict(color="#6EE7B7", width=1.5, dash="dot"),
        visible="legendonly",
    ))
    fig_pob.update_layout(
        paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
        font=dict(color="#94A3B8"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="#1E293B", tickangle=45),
        yaxis=dict(gridcolor="#1E293B", title="% de hogares"),
        margin=dict(t=10, b=10, l=10, r=10), height=320,
    )
    st.plotly_chart(fig_pob, use_container_width=True)

    # Stats de la serie
    col_p1, col_p2, col_p3 = st.columns(3)
    ultimo = df_pob.iloc[-1]
    minimo = df_pob.loc[df_pob["En situación de indigencia"].idxmin()]
    maximo = df_pob.loc[df_pob["En situación de indigencia"].idxmax()]
    for col, label, row, color in [
        (col_p1, "Último dato disponible", ultimo, "#6EE7B7"),
        (col_p2, "Mejor trimestre", minimo,  "#6EE7B7"),
        (col_p3, "Peor trimestre",  maximo,  "#EF4444"),
    ]:
        with col:
            st.markdown(f"""
<div style='background:#0A1628;border:1px solid #1E293B;border-radius:8px;padding:12px;'>
  <div style='font-size:.6rem;color:#64748B;margin-bottom:6px;'>{label} · {row['trimestre']}</div>
  <div style='font-size:.82rem;color:#EF4444;'>Indigencia: <b>{row['En situación de indigencia']}%</b></div>
  <div style='font-size:.82rem;color:#F97316;'>Pobreza: <b>{row['En situación de pobreza no indigente']}%</b></div>
  <div style='font-size:.82rem;color:{color};'>Total pobre: <b>{round(row['En situación de indigencia']+row['En situación de pobreza no indigente'],1)}%</b></div>
</div>""", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Fuentes: Instituto de Vivienda de la Ciudad (IVC) · Dirección General de Estadísticas y Censos (DGEyC) · "
    "INDEC Censo Nacional 2010 · EAH GCBA. Indicadores de hacinamiento: Encuesta Anual de Hogares 2018. "
    "Índice de vulnerabilidad: elaboración propia con ponderación NBI (30%), déficit (25%), "
    "hacinamiento (25%), infraestructura (20%)."
)
