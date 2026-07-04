"""
Página 20 – Medio Ambiente CABA
Calidad del aire · GEI · Residuos & Reciclaje · Arbolado & Ruido
"""
import json
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

st.set_page_config(page_title="Medio Ambiente CABA", page_icon="🌿", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #F0FDF4; }
[data-testid="stSidebar"] { background: #14532D; }
[data-testid="stSidebar"] * { color: #FFFFFF !important; }
.metric-card {
    background: white; border-radius: 12px; padding: 18px 22px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 5px solid;
    margin-bottom: 8px;
}
.metric-value { font-size: 2rem; font-weight: 700; margin: 0; }
.metric-label { font-size: 0.82rem; color: #555; margin: 0; text-transform: uppercase; letter-spacing: .5px; }
</style>
""", unsafe_allow_html=True)

GREEN = "#16A34A"
DARK_GREEN = "#15803D"
TEAL = "#0D9488"
LIME = "#84CC16"
AMBER = "#F59E0B"
RED = "#EF4444"
BLUE = "#3B82F6"

# ── Carga ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    with open("data/medioambiente_caba.json", encoding="utf-8") as f:
        return json.load(f)

data = load_data()

# ── Sidebar ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌿 Medio Ambiente")
    st.markdown("---")
    st.markdown("### Filtros")
    anio_aire_desde = st.slider("Calidad del aire – desde", 2009, 2024, 2015, key="ma_aire_desde")
    anio_aire_hasta = st.slider("Calidad del aire – hasta", 2009, 2026, 2026, key="ma_aire_hasta")
    estaciones_sel = st.multiselect(
        "Estaciones de monitoreo",
        ["Centenario", "Córdoba", "La Boca", "Palermo"],
        default=["Centenario", "Córdoba", "La Boca", "Palermo"],
        key="ma_estaciones"
    )
    contaminante = st.selectbox("Contaminante", ["CO (ppm)", "NO₂ (ppb)", "PM10 (µg/m³)"], key="ma_cont")
    anio_gei_desde = st.slider("GEI – desde año", 2000, 2023, 2010, key="ma_gei_desde")
    sectores_gei = data["gei_sectores"]
    gei_sel = st.multiselect("Sectores GEI", sectores_gei, default=sectores_gei, key="ma_gei_sects")
    top_arbol = st.slider("Top N especies (arbolado)", 5, 20, 10, key="ma_top_arbol")

# ── Header ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='background:linear-gradient(135deg,#14532D,#16A34A);
     padding:24px 32px; border-radius:12px; margin-bottom:20px;'>
  <h1 style='color:white; margin:0; font-size:1.8rem;'>🌿 Medio Ambiente – CABA</h1>
  <p style='color:#BBF7D0; margin:6px 0 0; font-size:0.9rem;'>
    Calidad del aire · Gases de efecto invernadero · Residuos · Arbolado · Ruido urbano
  </p>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards ──────────────────────────────────────────────────────────
res = data["resumen"]
kpi_cols = st.columns(5)
kpis = [
    (kpi_cols[0], f"{res['total_arboles']:,}", "Árboles en espacios verdes", GREEN, "🌳"),
    (kpi_cols[1], f"{res['puntos_verdes_total']}", "Puntos Verdes reciclaje", TEAL, "♻"),
    (kpi_cols[2], f"{res['techos_solares_total']:,}", "Techos solares registrados", AMBER, "☀"),
    (kpi_cols[3], f"{res['estaciones_aire']}", "Estaciones calidad del aire", BLUE, "🏭"),
    (kpi_cols[4], f"{res['precipitacion_promedio_mm']:.0f} mm", "Precipitación prom. anual", "#7C3AED", "🌧"),
]
for col, val, label, color, icon in kpis:
    with col:
        st.markdown(f"""
        <div class='metric-card' style='border-left-color:{color};'>
          <p class='metric-label'>{icon} {label}</p>
          <p class='metric-value' style='color:{color};'>{val}</p>
        </div>""", unsafe_allow_html=True)

st.markdown("---")

# ── Tabs ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "💨 Calidad del Aire",
    "🌡 Gases de Efecto Invernadero",
    "♻ Residuos & Reciclaje",
    "🌳 Arbolado, Ruido & Solar",
])

# ════════════════════════════════════════════════════════════════════════
# TAB 1 – Calidad del Aire
# ════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### 💨 Red de Monitoreo de Calidad del Aire – CABA")

    col_mapa, col_info = st.columns([1.1, 1])

    with col_mapa:
        st.markdown("**Estaciones de monitoreo**")
        m = folium.Map(location=[-34.614, -58.41], zoom_start=12, tiles="CartoDB positron")
        for e in data["estaciones_monitoreo"]:
            folium.CircleMarker(
                location=[e["lat"], e["lon"]],
                radius=14,
                color=GREEN,
                fill=True,
                fill_color=GREEN,
                fill_opacity=0.8,
                tooltip=f"<b>{e['nombre']}</b><br>{e['parametros']}<br>Desde {e['inicio']}",
            ).add_to(m)
            folium.Marker(
                location=[e["lat"], e["lon"]],
                icon=folium.DivIcon(
                    html=f"<div style='font-size:9px;font-weight:bold;color:white;margin-top:-3px;margin-left:-18px;width:36px;text-align:center;'>{e['nombre'][:4]}</div>",
                    icon_size=(36, 14),
                ),
            ).add_to(m)
        st_folium(m, width=520, height=340, returned_objects=[], key="ma_estaciones_map")

    with col_info:
        st.markdown("**Parámetros medidos**")
        for e in data["estaciones_monitoreo"]:
            st.markdown(f"""
            <div style='background:white;border-radius:8px;padding:10px 14px;margin-bottom:8px;border-left:4px solid {GREEN};'>
              <b>{e['nombre']}</b><br>
              <span style='color:#555;font-size:0.85rem;'>{e['parametros']}</span><br>
              <span style='color:#888;font-size:0.8rem;'>Activa desde {e['inicio']}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Evolución anual de contaminantes por estación")

    estaciones_opciones = ["centenario", "cordoba", "la_boca", "palermo"]
    est_label = {"centenario": "Centenario", "cordoba": "Córdoba", "la_boca": "La Boca", "palermo": "Palermo"}

    col_key = {"CO (ppm)": "co", "NO₂ (ppb)": "no2", "PM10 (µg/m³)": "pm10"}[contaminante]

    # Mapping sidebar station selections to data keys
    est_map = {"Centenario": "centenario", "Córdoba": "cordoba", "La Boca": "la_boca", "Palermo": "palermo"}
    est_filtradas = [est_map[e] for e in estaciones_sel if e in est_map]

    air_data = [r for r in data["calidad_aire_anual"] if anio_aire_desde <= r["year"] <= anio_aire_hasta]
    años = [r["year"] for r in air_data]

    fig_air = go.Figure()
    colors_est = [GREEN, TEAL, AMBER, "#7C3AED"]
    for i, est in enumerate(estaciones_opciones):
        if est not in est_filtradas:
            continue
        key = f"{col_key}_{est}"
        vals = [r.get(key) for r in air_data]
        fig_air.add_trace(go.Scatter(
            x=años, y=vals,
            name=est_label[est],
            mode="lines+markers",
            line=dict(color=colors_est[i], width=2),
            marker=dict(size=5),
            connectgaps=True,
        ))

    fig_air.add_vrect(x0=2020, x1=2021, fillcolor="rgba(239,68,68,0.1)",
                      line_width=0, annotation_text="COVID", annotation_position="top left")
    fig_air.update_layout(
        height=380, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFAFA",
        legend=dict(orientation="h", y=1.1),
        yaxis=dict(gridcolor="#E5E7EB"),
        xaxis_title="Año", yaxis_title=contaminante,
        margin=dict(t=20, b=40, l=60, r=20),
    )
    st.plotly_chart(fig_air, use_container_width=True)

    st.info("**CO**: Monóxido de carbono — límite OMS 4 ppm (8h) · **NO₂**: Dióxido de nitrógeno — límite OMS 25 ppb · **PM10**: Material particulado — límite OMS 45 µg/m³")

# ════════════════════════════════════════════════════════════════════════
# TAB 2 – GEI
# ════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 🌡 Gases de Efecto Invernadero – CABA (2000–2023)")

    gei_data = [r for r in data["gei_anual_por_sector"] if r["año"] >= anio_gei_desde]
    sectores = [s for s in data["gei_sectores"] if s in gei_sel]
    años_gei = [r["año"] for r in gei_data]

    sector_colors = {
        "Energía": AMBER,
        "Transporte": BLUE,
        "Residuos": GREEN,
        "IPPU": "#7C3AED",
        "AFOLU": TEAL,
    }

    # Stacked area chart
    fig_gei = go.Figure()
    for s in sectores:
        vals = [r.get(s) for r in gei_data]
        color = sector_colors.get(s, "#999")
        fig_gei.add_trace(go.Scatter(
            x=años_gei, y=vals, name=s,
            mode="lines", stackgroup="one",
            line=dict(width=0.5, color=color),
            fillcolor=color.replace("#", "rgba(").replace(")", ",0.6)") if False else color,
            fill="tonexty" if s != sectores[0] else "tozeroy",
            connectgaps=True,
        ))

    # Simpler version: grouped bar
    fig_gei = go.Figure()
    for s in sectores:
        vals = [r.get(s) for r in gei_data]
        color = sector_colors.get(s, "#999")
        fig_gei.add_trace(go.Bar(
            x=años_gei, y=vals, name=s,
            marker_color=color,
        ))
    fig_gei.update_layout(
        barmode="stack",
        height=420, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFAFA",
        legend=dict(orientation="h", y=1.08),
        yaxis=dict(gridcolor="#E5E7EB", title="Toneladas CO₂eq"),
        xaxis_title="Año",
        margin=dict(t=30, b=40, l=80, r=20),
    )
    st.plotly_chart(fig_gei, use_container_width=True)

    # Metas 2030
    st.markdown("---")
    st.markdown("### Metas de reducción de emisiones al 2030")

    metas_data = data["gei_metas"]
    años_meta = sorted(set(m["año"] for m in metas_data))
    sectores_meta = sorted(set(m["sector"] for m in metas_data))

    col_m1, col_m2 = st.columns(2)
    for i, anio_m in enumerate(años_meta):
        rows = [m for m in metas_data if m["año"] == anio_m]
        col = col_m1 if i == 0 else col_m2
        with col:
            st.markdown(f"**Año {int(anio_m)}**")
            total = sum(r["meta"] for r in rows)
            fig_m = go.Figure(go.Pie(
                labels=[r["sector"] for r in rows],
                values=[r["meta"] for r in rows],
                hole=0.5,
                marker_colors=[sector_colors.get(r["sector"], "#999") for r in rows],
            ))
            fig_m.update_layout(
                height=260, paper_bgcolor="rgba(0,0,0,0)",
                annotations=[dict(text=f"<b>{total/1e6:.1f}M</b><br>tCO₂eq", x=0.5, y=0.5, font_size=13, showarrow=False)],
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=True, legend=dict(orientation="v"),
            )
            st.plotly_chart(fig_m, use_container_width=True)

    # Compare 2015 vs 2030
    if len(años_meta) >= 2:
        st.markdown("**Reducción meta 2015 → 2030 por sector**")
        metas_2015 = {m["sector"]: m["meta"] for m in metas_data if m["año"] == años_meta[0]}
        metas_2030 = {m["sector"]: m["meta"] for m in metas_data if m["año"] == años_meta[-1]}
        sects_comunes = [s for s in sectores_meta if s in metas_2015 and s in metas_2030]
        reduc = [(s, metas_2015[s], metas_2030[s], (metas_2030[s]-metas_2015[s])/metas_2015[s]*100) for s in sects_comunes]
        fig_red = go.Figure()
        fig_red.add_trace(go.Bar(x=[r[0] for r in reduc], y=[r[1]/1e6 for r in reduc], name=f"{años_meta[0]}", marker_color=AMBER))
        fig_red.add_trace(go.Bar(x=[r[0] for r in reduc], y=[r[2]/1e6 for r in reduc], name=f"{años_meta[-1]}", marker_color=GREEN))
        fig_red.update_layout(
            barmode="group", height=320,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFAFA",
            yaxis=dict(gridcolor="#E5E7EB", title="MtCO₂eq"),
            margin=dict(t=10, b=40, l=60, r=20),
        )
        st.plotly_chart(fig_red, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════
# TAB 3 – Residuos & Reciclaje
# ════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### ♻ Gestión de Residuos – CABA")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Toneladas recuperadas vs. dispuestas por año**")
        rec = {r["año"]: r["ton"] for r in data["residuos_recuperados_anual"]}
        dis = {r["año"]: r["ton"] for r in data["residuos_dispuestos_anual"]}
        años_res = sorted(set(list(rec.keys()) + list(dis.keys())))

        fig_res = go.Figure()
        fig_res.add_trace(go.Bar(
            x=[a for a in años_res if a in dis],
            y=[dis[a]/1000 for a in años_res if a in dis],
            name="Dispuestas (ton × 1000)", marker_color=RED,
        ))
        fig_res.add_trace(go.Bar(
            x=[a for a in años_res if a in rec],
            y=[rec[a]/1000 for a in años_res if a in rec],
            name="Recuperadas (ton × 1000)", marker_color=GREEN,
        ))
        fig_res.update_layout(
            barmode="group", height=320,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFAFA",
            yaxis=dict(gridcolor="#E5E7EB", title="Miles de toneladas"),
            legend=dict(orientation="h", y=1.08),
            margin=dict(t=30, b=40, l=60, r=20),
        )
        st.plotly_chart(fig_res, use_container_width=True)

    with c2:
        st.markdown("**Recuperación por centro de procesamiento**")
        centros = data["residuos_por_centro"]
        fig_cent = go.Figure(go.Bar(
            x=[c["ton"]/1000 for c in centros],
            y=[c["centro"] for c in centros],
            orientation="h",
            marker_color=[GREEN, TEAL, LIME, AMBER, BLUE][:len(centros)],
            text=[f"{c['ton']/1000:.0f}K" for c in centros],
            textposition="outside",
        ))
        fig_cent.update_layout(
            height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFAFA",
            xaxis=dict(title="Miles de ton"),
            yaxis=dict(autorange="reversed"),
            margin=dict(t=10, b=40, l=200, r=80),
        )
        st.plotly_chart(fig_cent, use_container_width=True)

    st.markdown("---")
    c3, c4 = st.columns(2)

    with c3:
        st.markdown("**Monitor de Reciclado – % bolsas que separan por comuna**")
        mr = sorted(data["reciclado_por_comuna"], key=lambda x: x["pct_separa"], reverse=True)
        colors_mr = [GREEN if r["pct_separa"] >= 30 else AMBER if r["pct_separa"] >= 20 else RED for r in mr]
        fig_mr = go.Figure(go.Bar(
            x=[f"C{r['comuna']}" for r in mr],
            y=[r["pct_separa"] for r in mr],
            marker_color=colors_mr,
            text=[f"{r['pct_separa']:.1f}%" for r in mr],
            textposition="outside",
        ))
        fig_mr.add_hline(y=30, line_dash="dot", line_color=DARK_GREEN,
                         annotation_text="Meta 30%", annotation_position="right")
        fig_mr.update_layout(
            height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFAFA",
            yaxis=dict(gridcolor="#E5E7EB", title="% bolsas que separan"),
            margin=dict(t=10, b=40, l=60, r=80),
        )
        st.plotly_chart(fig_mr, use_container_width=True)

    with c4:
        st.markdown("**Clasificación de bolsas analizadas**")
        clasif = data["reciclado_por_clasificacion"]
        total_bol = sum(c["bolsas"] for c in clasif)
        fig_class = go.Figure(go.Pie(
            labels=[c["clasificacion"] for c in clasif],
            values=[c["bolsas"] for c in clasif],
            hole=0.55,
            marker_colors=[GREEN, RED],
            textinfo="percent+label",
        ))
        fig_class.update_layout(
            height=320, paper_bgcolor="rgba(0,0,0,0)",
            annotations=[dict(text=f"<b>{total_bol:,}</b><br>bolsas", x=0.5, y=0.5, font_size=13, showarrow=False)],
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_class, use_container_width=True)

    # Puntos Verdes mapa
    st.markdown("---")
    st.markdown("### 📍 Puntos Verdes de Reciclaje")
    m_pv = folium.Map(location=[-34.614, -58.41], zoom_start=12, tiles="CartoDB positron")
    mc_pv = MarkerCluster().add_to(m_pv)
    for pv in data["puntos_verdes"]:
        folium.CircleMarker(
            location=[pv["lat"], pv["lon"]],
            radius=9,
            color=GREEN,
            fill=True,
            fill_color=GREEN,
            fill_opacity=0.85,
            tooltip=f"<b>{pv['nombre']}</b><br>{pv['barrio']}<br><i>{pv['tipo']}</i>",
        ).add_to(mc_pv)
    st_folium(m_pv, width=900, height=380, returned_objects=[], key="ma_pv_map")
    st.caption(f"Total: {len(data['puntos_verdes'])} Puntos Verdes activos en CABA")

# ════════════════════════════════════════════════════════════════════════
# TAB 4 – Arbolado, Ruido & Solar
# ════════════════════════════════════════════════════════════════════════
with tab4:
    # ── Arbolado ────────────────────────────────────────────────────────
    st.markdown("### 🌳 Arbolado Urbano – Espacios Verdes CABA")

    c_esp, c_orig = st.columns(2)

    with c_esp:
        st.markdown(f"**Top {top_arbol} especies más frecuentes**")
        esp = data["arbolado_top_especies"][:top_arbol]
        fig_esp = go.Figure(go.Bar(
            x=[e["cantidad"] for e in esp],
            y=[e["especie"] for e in esp],
            orientation="h",
            marker_color=GREEN,
            text=[f"{e['cantidad']:,}" for e in esp],
            textposition="outside",
        ))
        fig_esp.update_layout(
            height=460, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFAFA",
            xaxis=dict(title="Árboles"),
            yaxis=dict(autorange="reversed", tickfont=dict(size=10)),
            margin=dict(t=10, b=40, l=240, r=90),
        )
        st.plotly_chart(fig_esp, use_container_width=True)

    with c_orig:
        st.markdown("**Origen de las especies**")
        orig = data["arbolado_origen"]
        fig_orig = go.Figure(go.Pie(
            labels=[o["origen"] for o in orig],
            values=[o["cantidad"] for o in orig],
            hole=0.5,
            marker_colors=[GREEN, AMBER, TEAL, RED, BLUE, "#7C3AED"],
        ))
        fig_orig.update_layout(
            height=240, paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_orig, use_container_width=True)

        st.markdown("**Tipos de espacio verde**")
        espacios = data["arbolado_espacios"]
        fig_esp2 = go.Figure(go.Bar(
            x=[e["cantidad"] for e in espacios[:8]],
            y=[e["espacio"][:30] for e in espacios[:8]],
            orientation="h",
            marker_color=TEAL,
        ))
        fig_esp2.update_layout(
            height=240, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFAFA",
            xaxis=dict(title="Árboles"),
            yaxis=dict(autorange="reversed"),
            margin=dict(t=10, b=40, l=200, r=30),
        )
        st.plotly_chart(fig_esp2, use_container_width=True)

    st.markdown("---")

    # ── Ruido Urbano ─────────────────────────────────────────────────────
    st.markdown("### 🔊 Mapa de Ruido Urbano por Comuna")

    c_r1, c_r2 = st.columns(2)
    with c_r1:
        st.markdown("**Ruido Diurno (dBA promedio por comuna)**")
        rd = sorted(data["ruido_diurno_por_comuna"], key=lambda x: x["avg_dba"], reverse=True)
        colors_rd = [RED if r["avg_dba"] >= 70 else AMBER if r["avg_dba"] >= 65 else GREEN for r in rd]
        fig_rd = go.Figure(go.Bar(
            x=[f"C{r['comuna']}" for r in rd],
            y=[r["avg_dba"] for r in rd],
            marker_color=colors_rd,
            text=[f"{r['avg_dba']:.1f}" for r in rd],
            textposition="outside",
        ))
        fig_rd.add_hline(y=65, line_dash="dot", line_color=AMBER,
                         annotation_text="65 dBA límite diurno", annotation_position="right")
        fig_rd.update_layout(
            height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFAFA",
            yaxis=dict(gridcolor="#E5E7EB", title="dBA promedio", range=[40, 90]),
            margin=dict(t=10, b=40, l=60, r=120),
        )
        st.plotly_chart(fig_rd, use_container_width=True)

    with c_r2:
        st.markdown("**Ruido Nocturno (dBA promedio por comuna)**")
        rn = sorted(data["ruido_nocturno_por_comuna"], key=lambda x: x["avg_dba"], reverse=True)
        colors_rn = [RED if r["avg_dba"] >= 60 else AMBER if r["avg_dba"] >= 55 else GREEN for r in rn]
        fig_rn = go.Figure(go.Bar(
            x=[f"C{r['comuna']}" for r in rn],
            y=[r["avg_dba"] for r in rn],
            marker_color=colors_rn,
            text=[f"{r['avg_dba']:.1f}" for r in rn],
            textposition="outside",
        ))
        fig_rn.add_hline(y=55, line_dash="dot", line_color=AMBER,
                         annotation_text="55 dBA límite nocturno", annotation_position="right")
        fig_rn.update_layout(
            height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFAFA",
            yaxis=dict(gridcolor="#E5E7EB", title="dBA promedio", range=[40, 90]),
            margin=dict(t=10, b=40, l=60, r=120),
        )
        st.plotly_chart(fig_rn, use_container_width=True)

    st.markdown("---")

    # ── Precipitaciones ──────────────────────────────────────────────────
    st.markdown("### 🌧 Precipitaciones Anuales (1991–2020)")
    prec = data["precipitaciones_anual"]
    avg_mm = sum(p["mm"] for p in prec) / len(prec)
    fig_prec = go.Figure(go.Bar(
        x=[p["año"] for p in prec],
        y=[p["mm"] for p in prec],
        marker_color=[BLUE if p["mm"] >= avg_mm else AMBER for p in prec],
        text=[f"{p['mm']:.0f}" for p in prec],
        textposition="outside",
    ))
    fig_prec.add_hline(y=avg_mm, line_dash="dot", line_color=DARK_GREEN,
                       annotation_text=f"Promedio {avg_mm:.0f} mm", annotation_position="right")
    fig_prec.update_layout(
        height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFAFA",
        yaxis=dict(gridcolor="#E5E7EB", title="Precipitación (mm)"),
        margin=dict(t=10, b=40, l=60, r=120),
    )
    st.plotly_chart(fig_prec, use_container_width=True)

    # ── Techos Solares ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ☀ Techos Solares – Potencial Energético CABA")

    c_sol1, c_sol2 = st.columns(2)

    with c_sol1:
        st.markdown("**Por tipo de sistema**")
        ts_tipo = data["techos_solares_tipo"]
        fig_ts = go.Figure(go.Bar(
            x=[t["tipo"] for t in ts_tipo],
            y=[t["cantidad"] for t in ts_tipo],
            marker_color=[GREEN, AMBER],
            text=[f"{t['cantidad']} techos" for t in ts_tipo],
            textposition="outside",
        ))
        fig_ts.update_layout(
            height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFAFA",
            yaxis=dict(gridcolor="#E5E7EB", title="Cantidad"),
            margin=dict(t=10, b=40, l=60, r=20),
        )
        st.plotly_chart(fig_ts, use_container_width=True)

    with c_sol2:
        st.markdown("**Por tipo de edificio (público / privado)**")
        ts_pp = data["techos_solares_pub_priv"]
        fig_pp = go.Figure(go.Pie(
            labels=[t["tipo"] for t in ts_pp],
            values=[t["cantidad"] for t in ts_pp],
            hole=0.5,
            marker_colors=[BLUE, GREEN, AMBER],
        ))
        gen_total = sum(t["gen_mwh"] or 0 for t in ts_pp)
        fig_pp.update_layout(
            height=280, paper_bgcolor="rgba(0,0,0,0)",
            annotations=[dict(text=f"<b>{gen_total:.0f}</b><br>MWh/año", x=0.5, y=0.5, font_size=12, showarrow=False)],
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_pp, use_container_width=True)

    # Info cards
    ts_total = res["techos_solares_total"]
    gen_total_on = next((t["gen_mwh"] for t in data["techos_solares_tipo"] if t["tipo"] == "On-Grid"), 0) or 0
    cols_info = st.columns(3)
    info_items = [
        (cols_info[0], f"{ts_total}", "techos solares registrados", AMBER),
        (cols_info[1], f"{gen_total_on:.0f} MWh", "generación anual On-Grid", GREEN),
        (cols_info[2], f"{ts_total/15:.0f}", "techos por comuna (promedio)", TEAL),
    ]
    for col, val, label, color in info_items:
        with col:
            st.markdown(f"""
            <div style='background:white;border-radius:10px;padding:16px;border-left:4px solid {color};text-align:center;'>
              <p style='font-size:1.6rem;font-weight:700;color:{color};margin:0;'>{val}</p>
              <p style='font-size:0.8rem;color:#666;margin:0;'>{label}</p>
            </div>""", unsafe_allow_html=True)

# ── Footer ──────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Fuente: Portal de Datos Abiertos CABA (data.buenosaires.gob.ar) · Calidad del aire 2009–2025 · GEI 2000–2023 · Arbolado espacios verdes · Residuos y reciclaje 2015–2023")
