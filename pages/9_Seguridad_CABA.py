"""
Página 9 – Seguridad CABA
Datos reales del Ministerio de Justicia y Seguridad GCBA
Fuente: data.buenosaires.gob.ar · delitos_2024.csv (158.838 hechos)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from shapely.geometry import shape

st.set_page_config(
    page_title="Seguridad CABA",
    page_icon="🔴",
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
.stTabs [aria-selected="true"]     { color:#F87171 !important; border-bottom:2px solid #EF4444 !important; }
</style>
""", unsafe_allow_html=True)

# ── Data ───────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

@st.cache_data(show_spinner=False)
def load_stats():
    with open(os.path.join(DATA_DIR, "delitos_caba_stats.json"), encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(show_spinner=False)
def load_comunas():
    with open(os.path.join(DATA_DIR, "comunas_caba.geojson"), encoding="utf-8") as f:
        return json.load(f)

stats     = load_stats()
geojson   = load_comunas()
df_com    = pd.DataFrame(stats["por_comuna"])
df_mes    = pd.DataFrame(stats["por_mes_2024"])
df_hora   = pd.DataFrame(stats["por_hora_2024"])
evol_anual = stats["evolucion_anual"]
evol_com   = {int(k): v for k, v in stats["evolucion_por_comuna"].items()}

MESES_LABEL = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
               7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
TIPO_COLOR = {
    "Robo":       "#EF4444",
    "Hurto":      "#F97316",
    "Lesiones":   "#FBBF24",
    "Amenazas":   "#A78BFA",
    "Homicidios": "#7F1D1D",
    "Vialidad":   "#64748B",
}

# ── Session state ──────────────────────────────────────────────────────
if "seg_comuna" not in st.session_state:
    st.session_state.seg_comuna = None
if "seg_tipo"   not in st.session_state:
    st.session_state.seg_tipo   = "total"

# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔴 Seguridad CABA")
    st.markdown("<span style='font-size:.75rem;color:#64748B;'>Ministerio de Justicia y Seguridad GCBA<br>Datos 2022–2024</span>", unsafe_allow_html=True)
    st.markdown("---")

    tipo_opts = {"total": "🔴 Todos los delitos", "robos": "👜 Robo", "hurtos": "🎒 Hurto",
                 "lesiones": "🩹 Lesiones", "homicidios": "💀 Homicidios",
                 "amenazas": "⚠️ Amenazas", "vialidad": "🚗 Vialidad"}
    tipo_sel = st.selectbox("Ver en el mapa", list(tipo_opts.keys()),
                            format_func=lambda k: tipo_opts[k], key="tipo_mapa")
    st.session_state.seg_tipo = tipo_sel

    st.markdown("---")
    com_opts = ["— todas —"] + [f"Comuna {i:02d}" for i in range(1, 16)]
    com_sel  = st.selectbox("Filtrar comuna", com_opts, key="com_sel_seg")
    if com_sel != "— todas —":
        st.session_state.seg_comuna = int(com_sel.split()[1])
    else:
        st.session_state.seg_comuna = None

    sel = st.session_state.seg_comuna
    if sel:
        row  = df_com[df_com["comuna"] == sel].iloc[0]
        gj_p = next((f["properties"] for f in geojson["features"] if f["properties"]["comuna"]==sel), {})
        color_nivel = "#EF4444" if row["tasa_por_1000"] > 80 else "#F97316" if row["tasa_por_1000"] > 55 else "#FBBF24"
        st.markdown(f"""
<div style='background:#150a0a;border:1px solid #7F1D1D55;border-radius:10px;padding:12px 14px;'>
  <div style='font-size:1rem;font-weight:800;color:#fff;margin-bottom:4px;'>📍 Comuna {sel:02d}</div>
  <div style='font-size:.65rem;color:#64748B;margin-bottom:10px;'>{gj_p.get("barrios","")}</div>
  <div style='font-size:.58rem;color:#334155;margin-bottom:6px;text-transform:uppercase;letter-spacing:.1em;'>Hechos delictivos 2024</div>
""", unsafe_allow_html=True)
        def mini(lbl, val, clr="#E2E8F0"):
            return (f"<div style='display:flex;justify-content:space-between;padding:4px 0;"
                    f"border-bottom:1px solid #1E293B;font-size:.78rem;'>"
                    f"<span style='color:#94A3B8;'>{lbl}</span>"
                    f"<span style='color:{clr};font-weight:700;'>{val}</span></div>")
        st.markdown(
            mini("Total hechos", f"{int(row['total']):,}".replace(",","."), color_nivel) +
            mini("Tasa / 1.000", f"{row['tasa_por_1000']}", color_nivel) +
            mini("Robos", f"{int(row['robos']):,}".replace(",","."), "#EF4444") +
            mini("Hurtos", f"{int(row['hurtos']):,}".replace(",","."), "#F97316") +
            mini("Lesiones", f"{int(row['lesiones']):,}".replace(",","."), "#FBBF24") +
            mini("Homicidios", f"{int(row['homicidios'])}", "#7F1D1D") +
            mini("Amenazas", f"{int(row['amenazas']):,}".replace(",","."), "#A78BFA"),
            unsafe_allow_html=True,
        )
        # Sparkline evolución 2022→2024
        c_evol = evol_com.get(sel, {})
        if c_evol:
            yrs = sorted(c_evol.keys())
            vals = [c_evol[y] for y in yrs]
            delta_pct = round((vals[-1]-vals[0])/vals[0]*100, 1) if vals[0] else 0
            delta_color = "#EF4444" if delta_pct > 0 else "#6EE7B7"
            delta_s = f"{delta_pct:+.1f}% 2022→2024"
            fig_spark = go.Figure(go.Scatter(
                x=[str(y) for y in yrs], y=vals, mode="lines+markers",
                line=dict(color="#EF4444", width=2),
                marker=dict(size=5, color="#EF4444"),
                fill="tozeroy", fillcolor="rgba(239,68,68,0.1)",
            ))
            fig_spark.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=8, b=4, l=0, r=0), height=70,
                xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=9, color="#475569")),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                showlegend=False,
            )
            st.markdown(f"<div style='font-size:.58rem;color:{delta_color};padding:8px 0 2px;'>{delta_s}</div>", unsafe_allow_html=True)
            st.plotly_chart(fig_spark, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        total_24 = int(df_com["total"].sum())
        hom_24   = int(df_com["homicidios"].sum())
        arma_pct = stats["uso_arma_pct_2024"]
        moto_pct = stats["uso_moto_pct_2024"]
        st.markdown(f"""
<div style='font-size:.7rem;color:#64748B;'>
  <b style='color:#F87171;'>{total_24:,}</b> hechos en 2024<br>
  <b style='color:#7F1D1D;'>{hom_24}</b> homicidios dolosos<br>
  <b style='color:#F97316;'>{arma_pct}%</b> con arma<br>
  <b style='color:#A78BFA;'>{moto_pct}%</b> en moto
</div>""".replace(",", "."), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div style='font-size:.6rem;color:#1E293B;'>Fuente: GCBA · Ministerio de Justicia y Seguridad</div>", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#150a0a,#450a0a);padding:20px 28px;border-radius:12px;
            margin-bottom:20px;border:1px solid #7F1D1D55;'>
  <h1 style='color:#fff;margin:0;font-size:1.7rem;'>🔴 Seguridad – Ciudad de Buenos Aires</h1>
  <p style='color:#64748B;margin:5px 0 0;font-size:.88rem;'>
    158.838 hechos delictivos 2024 · Homicidios, Robos, Hurtos, Lesiones · datos oficiales GCBA
  </p>
</div>
""", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────────────
total_24 = int(df_com["total"].sum())
hom_24   = int(df_com["homicidios"].sum())
rob_24   = int(df_com["robos"].sum())
hur_24   = int(df_com["hurtos"].sum())
arma_pct = stats["uso_arma_pct_2024"]
moto_pct = stats["uso_moto_pct_2024"]

# Variación vs 2022
total_22 = sum(v.get("total",0) for v in [evol_anual.get("2022",{})])
total_22 = evol_anual.get("2022",{}).get("total", 0)
total_24_raw = evol_anual.get("2024",{}).get("total", 0)
delta_pct = round((total_24_raw - total_22) / total_22 * 100, 1) if total_22 else 0

k1,k2,k3,k4,k5,k6 = st.columns(6)
kpis = [
    (k1, f"{total_24:,}".replace(",","."),  "Total hechos 2024",    "#EF4444",  f"{delta_pct:+.1f}% vs 2022"),
    (k2, str(hom_24),                       "Homicidios dolosos",   "#7F1D1D",  "2024"),
    (k3, f"{rob_24:,}".replace(",","."),    "Robos",                "#F97316",  "con/sin arma"),
    (k4, f"{hur_24:,}".replace(",","."),    "Hurtos",               "#FBBF24",  "sin violencia"),
    (k5, f"{arma_pct}%",                    "Hechos con arma",      "#A78BFA",  "del total"),
    (k6, f"{moto_pct}%",                    "Participación en moto","#64748B",  "del total"),
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
    "🗺 Mapa de Calor", "📊 Ranking por Comuna", "📈 Tendencias", "🕐 Análisis Temporal"
])

# ══════════════════════════════════════════════════════════════════════
# TAB 1 – MAPA
# ══════════════════════════════════════════════════════════════════════
with tab1:
    tipo_col = st.session_state.seg_tipo  # 'total','robos','hurtos', etc.

    max_val = df_com[tipo_col].max()
    min_val = df_com[tipo_col].min()

    def intensity_color(val):
        if max_val == min_val:
            return "#EF444488"
        ratio = (val - min_val) / (max_val - min_val)
        r = int(239 * ratio + 30 * (1 - ratio))
        g = int(68  * ratio + 40 * (1 - ratio))
        b = int(68  * ratio + 80 * (1 - ratio))
        alpha = int(40 + ratio * 180)
        return f"#{r:02X}{g:02X}{b:02X}{alpha:02X}"

    m = folium.Map(location=[-34.615, -58.443], zoom_start=12, tiles=None, prefer_canvas=True)
    folium.TileLayer(
        "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="© CARTO", max_zoom=19,
    ).add_to(m)

    for feat in geojson["features"]:
        cid   = feat["properties"]["comuna"]
        row   = df_com[df_com["comuna"] == cid]
        if row.empty:
            continue
        row = row.iloc[0]
        val      = int(row[tipo_col])
        fill     = intensity_color(val)
        is_sel   = (cid == st.session_state.seg_comuna)
        border   = "#FFFFFF" if is_sel else "#EF4444"
        weight   = 3.5 if is_sel else 1.2
        opacity  = 0.92 if is_sel else 0.75

        tipo_label = tipo_opts[tipo_col].split(" ",1)[1] if tipo_col != "total" else "Total"
        tooltip = (
            f"<b>Comuna {cid:02d}</b><br>"
            f"{feat['properties'].get('barrios','')}<br><br>"
            f"<b>🔴 {tipo_label}:</b> {val:,}<br>"
            f"Tasa / 1.000: {row['tasa_por_1000']}<br>"
            f"Total hechos: {int(row['total']):,}"
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
                          f"text-shadow:0 1px 3px #000;text-align:center;white-space:nowrap;'>"
                          f"C{cid:02d}<br>{val:,}</div>"),
                    icon_size=(40, 24), icon_anchor=(20, 12),
                ),
            ).add_to(m)
        except Exception:
            pass

    col_map, col_rank = st.columns([3, 1])
    with col_map:
        st_folium(m, height=560, use_container_width=True,
                  returned_objects=[], key=f"seg_map_{tipo_col}_{st.session_state.seg_comuna}")

    with col_rank:
        st.markdown(f"<div style='font-size:.7rem;color:#64748B;font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;'>Ranking comunas</div>", unsafe_allow_html=True)
        df_rank = df_com[["comuna", tipo_col, "tasa_por_1000"]].sort_values(tipo_col, ascending=False)
        for _, r in df_rank.iterrows():
            bar_pct = int(r[tipo_col] / max_val * 100) if max_val else 0
            is_top  = int(r[tipo_col]) == int(max_val)
            clr     = "#EF4444" if is_top else "#7F1D1D"
            st.markdown(
                f"<div style='margin-bottom:6px;'>"
                f"<div style='display:flex;justify-content:space-between;font-size:.72rem;"
                f"color:#94A3B8;margin-bottom:2px;'>"
                f"<span>C{int(r['comuna']):02d}</span>"
                f"<span style='color:{clr};font-weight:700;'>{int(r[tipo_col]):,}</span></div>"
                f"<div style='background:#1E293B;border-radius:3px;height:5px;'>"
                f"<div style='background:{clr};height:5px;width:{bar_pct}%;border-radius:3px;'></div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════════════════════════════
# TAB 2 – RANKING
# ══════════════════════════════════════════════════════════════════════
with tab2:
    col_r1, col_r2 = st.columns([1, 1])

    with col_r1:
        st.markdown("#### Por volumen total")
        df_s = df_com.sort_values("total", ascending=True)
        fig_vol = go.Figure()
        for tipo in ["Robo", "Hurto", "Lesiones", "Amenazas", "Vialidad", "Homicidios"]:
            col_k = tipo.lower() + "s" if tipo != "Vialidad" else "vialidad"
            col_k = col_k.replace("robos","robos").replace("hurtos","hurtos")
            # map tipo → col
            col_map_d = {"Robo":"robos","Hurto":"hurtos","Lesiones":"lesiones",
                         "Amenazas":"amenazas","Vialidad":"vialidad","Homicidios":"homicidios"}
            ck = col_map_d[tipo]
            if ck not in df_s.columns: continue
            fig_vol.add_trace(go.Bar(
                y=[f"C{int(c):02d}" for c in df_s["comuna"]],
                x=df_s[ck],
                name=tipo, orientation="h",
                marker_color=TIPO_COLOR.get(tipo, "#64748B"),
                hovertemplate=f"<b>%{{y}}</b><br>{tipo}: %{{x:,}}<extra></extra>",
            ))
        fig_vol.update_layout(
            barmode="stack",
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=10, b=10, l=10, r=10),
            height=400,
        )
        st.plotly_chart(fig_vol, use_container_width=True)

    with col_r2:
        st.markdown("#### Por tasa cada 1.000 electores")
        df_t = df_com.sort_values("tasa_por_1000", ascending=True)
        colors = ["#EF4444" if v > 80 else "#F97316" if v > 55 else "#FBBF24"
                  for v in df_t["tasa_por_1000"]]
        fig_tasa = go.Figure(go.Bar(
            y=[f"C{int(c):02d}" for c in df_t["comuna"]],
            x=df_t["tasa_por_1000"],
            orientation="h",
            marker_color=colors,
            text=df_t["tasa_por_1000"].astype(str),
            textposition="outside",
            textfont=dict(color="#E2E8F0", size=10),
            hovertemplate="<b>%{y}</b><br>Tasa: %{x}<extra></extra>",
        ))
        fig_tasa.add_vline(x=df_com["tasa_por_1000"].mean(), line_dash="dot",
                           line_color="#475569", annotation_text="promedio",
                           annotation_font_color="#475569")
        fig_tasa.update_layout(
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B", range=[0, 135]),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=10, b=10, l=10, r=50),
            height=400,
        )
        st.plotly_chart(fig_tasa, use_container_width=True)

    # Tabla completa
    st.markdown("---")
    df_table = df_com.sort_values("total", ascending=False).copy()
    df_table["comuna"] = df_table["comuna"].apply(lambda x: f"C{int(x):02d}")
    df_table = df_table.rename(columns={
        "comuna":"Comuna","total":"Total","robos":"Robos","hurtos":"Hurtos",
        "lesiones":"Lesiones","homicidios":"Homicidios","amenazas":"Amenazas",
        "vialidad":"Vialidad","tasa_por_1000":"Tasa/1.000",
    })
    st.dataframe(df_table[["Comuna","Total","Robos","Hurtos","Lesiones","Homicidios","Amenazas","Vialidad","Tasa/1.000"]],
                 hide_index=True, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 3 – TENDENCIAS
# ══════════════════════════════════════════════════════════════════════
with tab3:
    col_t1, col_t2 = st.columns([2, 1])

    with col_t1:
        st.markdown("#### Evolución mensual 2024")
        df_mes["mes_label"] = df_mes["mes"].map(MESES_LABEL)
        fig_mes = go.Figure()
        for tipo in ["Robo","Hurto","Lesiones","Amenazas","Vialidad"]:
            if tipo not in df_mes.columns: continue
            fig_mes.add_trace(go.Scatter(
                x=df_mes["mes_label"], y=df_mes[tipo],
                name=tipo, mode="lines+markers",
                line=dict(color=TIPO_COLOR.get(tipo, "#64748B"), width=2),
                marker=dict(size=5),
                hovertemplate=f"<b>{tipo}</b> %{{x}}: %{{y:,}}<extra></extra>",
            ))
        fig_mes.update_layout(
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=10, b=10, l=10, r=10),
            height=320,
        )
        st.plotly_chart(fig_mes, use_container_width=True)

    with col_t2:
        st.markdown("#### Variación anual (CABA total)")
        tipos_cmp = ["Robo","Hurto","Lesiones","Amenazas","Homicidios"]
        rows_cmp = []
        for t in tipos_cmp:
            v22 = evol_anual.get("2022",{}).get(t, 0)
            v24 = evol_anual.get("2024",{}).get(t, 0)
            delta = round((v24 - v22) / v22 * 100, 1) if v22 else 0
            rows_cmp.append({"tipo": t, "2022": v22, "2024": v24, "delta": delta})
        df_cmp = pd.DataFrame(rows_cmp)
        fig_cmp = go.Figure(go.Bar(
            x=df_cmp["tipo"], y=df_cmp["delta"],
            marker_color=["#EF4444" if v > 0 else "#6EE7B7" for v in df_cmp["delta"]],
            text=[f"{v:+.1f}%" for v in df_cmp["delta"]],
            textposition="outside",
            textfont=dict(color="#E2E8F0", size=10),
            hovertemplate="<b>%{x}</b><br>%{y:+.1f}% vs 2022<extra></extra>",
        ))
        fig_cmp.add_hline(y=0, line_color="#334155")
        fig_cmp.update_layout(
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B", title="Δ% vs 2022"),
            margin=dict(t=10, b=10, l=10, r=10),
            height=320, showlegend=False,
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

    # Evolución por comuna
    st.markdown("#### Tendencia 2022–2024 por comuna")
    evol_rows = []
    for cid, data in evol_com.items():
        for yr, total in data.items():
            evol_rows.append({"comuna": f"C{int(cid):02d}", "año": str(yr), "total": total})
    df_evol = pd.DataFrame(evol_rows)
    fig_evol = px.line(
        df_evol, x="año", y="total", color="comuna",
        markers=True,
        color_discrete_sequence=px.colors.qualitative.Dark24,
        labels={"total": "Hechos", "año": "Año"},
    )
    fig_evol.update_layout(
        paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
        font=dict(color="#94A3B8"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9)),
        xaxis=dict(gridcolor="#1E293B"),
        yaxis=dict(gridcolor="#1E293B"),
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
    )
    st.plotly_chart(fig_evol, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 4 – ANÁLISIS TEMPORAL
# ══════════════════════════════════════════════════════════════════════
with tab4:
    col_h1, col_h2 = st.columns([2, 1])

    with col_h1:
        st.markdown("#### Distribución horaria de hechos (2024)")
        df_hora["periodo"] = df_hora["hora"].apply(
            lambda h: "🌙 Noche" if h < 6 else "🌅 Mañana" if h < 12 else "☀️ Tarde" if h < 19 else "🌆 Noche"
        )
        period_color = {"🌙 Noche": "#1E3A5F", "🌅 Mañana": "#78350F", "☀️ Tarde": "#78350F", "🌆 Noche": "#1E3A5F"}
        fig_hora = go.Figure(go.Bar(
            x=df_hora["hora"],
            y=df_hora["total"],
            marker_color=["#EF4444" if 17 <= h <= 21 else
                          "#7F1D1D" if 0  <= h <= 5  else
                          "#F97316" for h in df_hora["hora"]],
            hovertemplate="<b>%{x}hs</b><br>%{y:,} hechos<extra></extra>",
        ))
        fig_hora.update_layout(
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B", title="Hora del día",
                       tickmode="array", tickvals=list(range(0,24,2))),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=10, b=10, l=10, r=10),
            height=280,
        )
        fig_hora.add_annotation(x=19, y=df_hora[df_hora["hora"]==19]["total"].values[0],
                                text="Pico vespertino", showarrow=True, arrowcolor="#F97316",
                                font=dict(color="#F97316", size=10), ax=40, ay=-30)
        st.plotly_chart(fig_hora, use_container_width=True)

    with col_h2:
        st.markdown("#### Composición por tipo")
        tipos_total = {
            "Robo":      evol_anual.get("2024",{}).get("Robo", 0),
            "Hurto":     evol_anual.get("2024",{}).get("Hurto", 0),
            "Lesiones":  evol_anual.get("2024",{}).get("Lesiones", 0),
            "Amenazas":  evol_anual.get("2024",{}).get("Amenazas", 0),
            "Vialidad":  evol_anual.get("2024",{}).get("Vialidad", 0),
            "Homicidios":evol_anual.get("2024",{}).get("Homicidios", 0),
        }
        fig_donut = go.Figure(go.Pie(
            labels=list(tipos_total.keys()),
            values=list(tipos_total.values()),
            hole=0.55,
            marker_colors=[TIPO_COLOR[t] for t in tipos_total],
            textinfo="label+percent",
            textfont_size=10,
            hovertemplate="<b>%{label}</b><br>%{value:,} hechos<br>%{percent}<extra></extra>",
        ))
        fig_donut.update_layout(
            paper_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            showlegend=False, height=280,
            margin=dict(t=10, b=10, l=5, r=5),
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    # Stats adicionales
    col_s1, col_s2, col_s3 = st.columns(3)
    hora_pico = int(df_hora.loc[df_hora["total"].idxmax(), "hora"])
    hora_baja  = int(df_hora.loc[df_hora["total"].idxmin(), "hora"])
    with col_s1:
        st.markdown(f"""
<div style='background:#0A1628;border:1px solid #1E293B;border-radius:8px;padding:14px;'>
  <div style='font-size:.6rem;color:#64748B;'>🕐 Hora pico</div>
  <div style='font-size:1.6rem;font-weight:800;color:#EF4444;'>{hora_pico}:00 hs</div>
  <div style='font-size:.65rem;color:#475569;'>{int(df_hora[df_hora["hora"]==hora_pico]["total"].values[0]):,} hechos</div>
</div>""", unsafe_allow_html=True)
    with col_s2:
        st.markdown(f"""
<div style='background:#0A1628;border:1px solid #1E293B;border-radius:8px;padding:14px;'>
  <div style='font-size:.6rem;color:#64748B;'>🕐 Hora más segura</div>
  <div style='font-size:1.6rem;font-weight:800;color:#6EE7B7;'>{hora_baja}:00 hs</div>
  <div style='font-size:.65rem;color:#475569;'>{int(df_hora[df_hora["hora"]==hora_baja]["total"].values[0]):,} hechos</div>
</div>""", unsafe_allow_html=True)
    with col_s3:
        pct_noche = round(
            df_hora[df_hora["hora"].isin(range(20,24))]["total"].sum() /
            df_hora["total"].sum() * 100, 1)
        st.markdown(f"""
<div style='background:#0A1628;border:1px solid #1E293B;border-radius:8px;padding:14px;'>
  <div style='font-size:.6rem;color:#64748B;'>🌙 Hechos nocturnos</div>
  <div style='font-size:1.6rem;font-weight:800;color:#A78BFA;'>{pct_noche}%</div>
  <div style='font-size:.65rem;color:#475569;'>entre las 20 y 23 hs</div>
</div>""", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Fuente: Ministerio de Justicia y Seguridad · Gobierno de la Ciudad de Buenos Aires · "
    "data.buenosaires.gob.ar · Homicidios dolosos, hurtos, robos, lesiones dolosas, amenazas "
    "y hechos viales 2022–2024."
)
