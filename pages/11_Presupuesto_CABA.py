"""
Página 11 – Presupuesto Ejecutado CABA
Ministerio de Hacienda y Finanzas GCBA · 2024 Trimestre 2
Fuente: data.buenosaires.gob.ar
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
    page_title="Presupuesto CABA",
    page_icon="💰",
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
.stTabs [aria-selected="true"]     { color:#FCD34D !important; border-bottom:2px solid #F59E0B !important; }
</style>
""", unsafe_allow_html=True)

# ── Data ───────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

@st.cache_data(show_spinner=False)
def load_data():
    with open(os.path.join(DATA_DIR, "presupuesto_caba.json"), encoding="utf-8") as f:
        return json.load(f)


data    = load_data()
geojson = loader.get_comunas_geojson()

df_jur  = pd.DataFrame(data["por_jurisdiccion"])
df_fun  = pd.DataFrame(data["por_funcion"])
df_inc  = pd.DataFrame(data["por_inciso"])
df_com  = pd.DataFrame(data["por_comuna"])
eco_d   = data["corriente_vs_capital"]

# Colores por función
FUN_COLORS = {
    "Educación":               "#3B82F6",
    "Salud":                   "#10B981",
    "Seguridad Interior":      "#EF4444",
    "Promoción Y Acción Social": "#F97316",
    "Servicios Urbanos":       "#8B5CF6",
    "Judicial":                "#64748B",
    "Vivienda Y Urbanismo":    "#F59E0B",
    "Dirección Ejecutiva":     "#475569",
    "Ecología":                "#6EE7B7",
    "Cultura":                 "#E879F9",
    "Transporte":              "#38BDF8",
    "Trabajo":                 "#FCD34D",
}

# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 Presupuesto CABA")
    st.markdown(f"<span style='font-size:.75rem;color:#64748B;'>{data['periodo']}<br>Ministerio de Hacienda y Finanzas</span>", unsafe_allow_html=True)
    st.markdown("---")

    # Gauge ejecución
    ejec = data["ejecucion_pct"]
    ejec_color = "#6EE7B7" if ejec >= 45 else "#FCD34D" if ejec >= 30 else "#EF4444"
    st.markdown(f"""
<div style='background:#0A1628;border:1px solid #1E293B;border-radius:10px;padding:14px;margin-bottom:12px;'>
  <div style='font-size:.6rem;color:#334155;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;'>Ejecución presupuestaria</div>
  <div style='font-size:2rem;font-weight:800;color:{ejec_color};'>{ejec}%</div>
  <div style='background:#1E293B;border-radius:6px;height:8px;margin:8px 0;'>
    <div style='background:{ejec_color};height:8px;width:{min(ejec,100):.0f}%;border-radius:6px;'></div>
  </div>
  <div style='font-size:.65rem;color:#475569;'>Devengado / Crédito Vigente · Trim. 2</div>
</div>""", unsafe_allow_html=True)

    # Top 5 funciones
    st.markdown("<div style='font-size:.6rem;color:#334155;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px;'>Top áreas de gasto</div>", unsafe_allow_html=True)
    total_dev = data["total_devengado_b"]
    for r in df_fun.head(5).itertuples():
        pct  = round(r.devengado / total_dev * 100, 1)
        clr  = FUN_COLORS.get(r.nombre, "#64748B")
        bar  = int(pct / df_fun.iloc[0]["devengado"] * total_dev / total_dev * 100)
        bar  = int(r.devengado / df_fun.iloc[0]["devengado"] * 100)
        st.markdown(
            f"<div style='margin-bottom:7px;'>"
            f"<div style='display:flex;justify-content:space-between;font-size:.7rem;color:#94A3B8;margin-bottom:2px;'>"
            f"<span style='color:{clr};'>{r.nombre[:22]}</span>"
            f"<span style='color:{clr};font-weight:700;'>${r.devengado:.0f}B</span></div>"
            f"<div style='background:#1E293B;border-radius:3px;height:4px;'>"
            f"<div style='background:{clr};height:4px;width:{bar}%;border-radius:3px;'></div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(f"<div style='font-size:.6rem;color:#334155;'>Total sancionado: ${data['total_sancion_b']:.0f} B<br>Total vigente: ${data['total_vigente_b']:.0f} B</div>", unsafe_allow_html=True)
    st.markdown("---")
    top_n = st.slider("Top N jurisdicciones", 5, 22, 10, key="pres_topn")
    vista = st.radio("Vista de monto", ["Devengado", "Vigente", "Sanción"], key="pres_vista")

# ── Header ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='background:linear-gradient(135deg,#0A1628,#1c1506);padding:20px 28px;border-radius:12px;
            margin-bottom:20px;border:1px solid #78350f44;'>
  <h1 style='color:#fff;margin:0;font-size:1.7rem;'>💰 Presupuesto Ejecutado – Ciudad de Buenos Aires</h1>
  <p style='color:#64748B;margin:5px 0 0;font-size:.88rem;'>
    {data['periodo']} · ${data['total_devengado_b']:.0f} mil millones ejecutados · {data['ejecucion_pct']}% de ejecución
  </p>
</div>
""", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────────────
corriente = eco_d.get("Gastos Corrientes", 0)
capital   = eco_d.get("Gastos De Capital", 0)
pct_cap   = round(capital / data["total_devengado_b"] * 100, 1)
min_jur   = df_jur[df_jur["devengado"] > 0].nsmallest(1, "devengado").iloc[0]

k1,k2,k3,k4,k5,k6 = st.columns(6)
kpis = [
    (k1, f"${data['total_devengado_b']:.0f} B",  "Total devengado",       "#F59E0B", f"de ${data['total_vigente_b']:.0f} B vigente"),
    (k2, f"{data['ejecucion_pct']}%",             "Ejecución presup.",     "#6EE7B7", "devengado / vigente"),
    (k3, f"${corriente:.0f} B",                   "Gasto corriente",       "#3B82F6", f"{round(corriente/data['total_devengado_b']*100,1)}% del total"),
    (k4, f"${capital:.0f} B",                     "Inversión (capital)",   "#10B981", f"{pct_cap}% del total"),
    (k5, f"${df_fun.iloc[0]['devengado']:.0f} B", f"Mayor área: {df_fun.iloc[0]['nombre'].split()[0]}",  "#EF4444", "primer área de gasto"),
    (k6, str(len(df_jur)),                        "Jurisdicciones",        "#8B5CF6", "ministerios y organismos"),
]
for col, val, label, color, sub in kpis:
    with col:
        st.markdown(f"""
<div style='background:#0A1628;border:1px solid #1E293B;border-left:4px solid {color};
            border-radius:8px;padding:12px 16px;'>
  <div style='font-size:.62rem;color:#64748B;text-transform:uppercase;letter-spacing:.04em;'>{label}</div>
  <div style='font-size:1.35rem;font-weight:800;color:{color};margin:3px 0;'>{val}</div>
  <div style='font-size:.6rem;color:#334155;'>{sub}</div>
</div>""", unsafe_allow_html=True)

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

col_monto = {"Devengado": "devengado", "Vigente": "vigente", "Sanción": "sancion"}[vista]
# por_funcion no tiene columna "sancion" → fallback a devengado
col_fun = col_monto if col_monto in df_fun.columns else "devengado"

# ── Tabs ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🌳 Por Área / Función", "🏛 Por Ministerio", "💳 Tipo de Gasto", "🗺 Por Comuna"
])

# ══════════════════════════════════════════════════════════════════════
# TAB 1 – TREEMAP POR FUNCIÓN
# ══════════════════════════════════════════════════════════════════════
with tab1:
    col_t1, col_t2 = st.columns([3, 2])

    with col_t1:
        df_fun_tree = df_fun[df_fun[col_fun] > 5].copy()
        df_fun_tree["color"] = df_fun_tree["nombre"].map(FUN_COLORS).fillna("#334155")
        df_fun_tree["pct"]   = (df_fun_tree[col_fun] / df_fun_tree[col_fun].sum() * 100).round(1)
        df_fun_tree["label"] = df_fun_tree.apply(
            lambda r: f"{r['nombre']}<br>${r[col_fun]:.0f}B ({r['pct']}%)", axis=1
        )

        fig_tree = px.treemap(
            df_fun_tree,
            path=["nombre"], values=col_fun,
            color="nombre",
            color_discrete_map=FUN_COLORS,
            custom_data=["devengado","pct"],
        )
        fig_tree.update_traces(
            texttemplate="<b>%{label}</b><br>$%{customdata[0]:.0f}B<br>%{customdata[1]:.1f}%",
            hovertemplate="<b>%{label}</b><br>$%{customdata[0]:.1f} B<extra></extra>",
            textfont=dict(size=12),
        )
        fig_tree.update_layout(
            paper_bgcolor="#0A1628", margin=dict(t=10, b=5, l=5, r=5), height=420,
        )
        st.plotly_chart(fig_tree, use_container_width=True)

    with col_t2:
        st.markdown("#### Ranking por área")
        df_fun_sorted = df_fun.sort_values(col_fun, ascending=False)
        total_fun = df_fun_sorted[col_fun].sum()
        max_fun   = df_fun_sorted[col_fun].max() if not df_fun_sorted.empty else 1
        for _, r in df_fun_sorted.iterrows():
            if r[col_fun] <= 0: continue
            pct_f = round(r[col_fun] / total_fun * 100, 1) if total_fun > 0 else 0
            clr   = FUN_COLORS.get(r["nombre"], "#64748B")
            bar_w = int(r[col_fun] / max_fun * 100) if max_fun > 0 else 0
            ejec_f= round(r["devengado"] / r["vigente"] * 100, 1) if r["vigente"] > 0 else 0
            ejec_c= "#6EE7B7" if ejec_f >= 45 else "#FCD34D" if ejec_f >= 25 else "#EF4444"
            st.markdown(
                f"<div style='margin-bottom:8px;padding:8px 10px;background:#0A1628;"
                f"border:1px solid #1E293B;border-radius:7px;'>"
                f"<div style='display:flex;justify-content:space-between;margin-bottom:4px;'>"
                f"<span style='font-size:.75rem;color:{clr};font-weight:600;'>{r['nombre'][:26]}</span>"
                f"<span style='font-size:.72rem;color:{clr};font-weight:800;'>${r[col_fun]:.0f}B</span></div>"
                f"<div style='background:#1E293B;border-radius:3px;height:5px;margin-bottom:4px;'>"
                f"<div style='background:{clr};height:5px;width:{bar_w}%;border-radius:3px;'></div>"
                f"</div>"
                f"<div style='display:flex;justify-content:space-between;font-size:.6rem;color:#334155;'>"
                f"<span>{pct_f}% del total</span>"
                f"<span style='color:{ejec_c};'>Ejec: {ejec_f}%</span></div>"
                f"</div>",
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════════════════════════════
# TAB 2 – POR MINISTERIO
# ══════════════════════════════════════════════════════════════════════
with tab2:
    col_m1, col_m2 = st.columns([2, 1])

    with col_m1:
        df_j = (df_jur[df_jur[col_monto] > 0]
                .sort_values(col_monto, ascending=False)
                .head(top_n)
                .sort_values(col_monto, ascending=True))
        # Escortar nombres largos
        df_j["nombre_short"] = df_j["nombre"].str.replace("Ministerio De ", "Min. ").str.replace("Ministerio ", "Min. ")
        ejec_jur = (df_j["devengado"] / df_j["vigente"] * 100).clip(0, 100)
        colors_jur = ["#6EE7B7" if e >= 45 else "#FCD34D" if e >= 25 else "#EF4444" for e in ejec_jur]

        fig_jur = go.Figure()
        fig_jur.add_trace(go.Bar(
            y=df_j["nombre_short"],
            x=df_j["vigente"],
            name="Crédito vigente",
            orientation="h",
            marker_color="#1E293B",
            hovertemplate="<b>%{y}</b><br>Vigente: $%{x:.1f}B<extra></extra>",
        ))
        fig_jur.add_trace(go.Bar(
            y=df_j["nombre_short"],
            x=df_j[col_monto],
            name=vista,
            orientation="h",
            marker_color=colors_jur,
            text=df_j[col_monto].apply(lambda x: f"${x:.0f}B"),
            textposition="outside",
            textfont=dict(color="#E2E8F0", size=9),
            hovertemplate=f"<b>%{{y}}</b><br>{vista}: $%{{x:.1f}}B<extra></extra>",
        ))
        fig_jur.update_layout(
            barmode="overlay",
            title=dict(text="Devengado vs Crédito Vigente por jurisdicción", font=dict(color="#E2E8F0", size=13)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
            xaxis=dict(gridcolor="#1E293B", title="Miles de millones $"),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=35, b=10, l=10, r=60),
            height=480,
        )
        st.plotly_chart(fig_jur, use_container_width=True)

    with col_m2:
        st.markdown("#### % Ejecución por ministerio")
        df_j2 = df_jur[df_jur[col_monto] > 0].copy()
        df_j2["ejec_pct"] = (df_j2["devengado"] / df_j2["vigente"] * 100).clip(0, 100).round(1)
        df_j2 = df_j2.sort_values(col_monto, ascending=False).head(top_n)
        df_j2 = df_j2.sort_values("ejec_pct", ascending=False)
        for _, r in df_j2.iterrows():
            e    = r["ejec_pct"]
            clr  = "#6EE7B7" if e >= 45 else "#FCD34D" if e >= 25 else "#EF4444"
            nom  = r["nombre"].replace("Ministerio De ","").replace("Ministerio ","")[:22]
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;padding:4px 0;"
                f"border-bottom:1px solid #0F172A;font-size:.72rem;'>"
                f"<span style='color:#94A3B8;'>{nom}</span>"
                f"<span style='color:{clr};font-weight:700;'>{e:.0f}%</span></div>",
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════════════════════════════
# TAB 3 – TIPO DE GASTO
# ══════════════════════════════════════════════════════════════════════
with tab3:
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        # Donut corriente vs capital
        eco_labels = list(eco_d.keys())
        eco_vals   = list(eco_d.values())
        eco_colors = {"Gastos Corrientes": "#3B82F6", "Gastos De Capital": "#10B981",
                      "Aplicaciones Financieras": "#64748B"}
        fig_eco = go.Figure(go.Pie(
            labels=eco_labels, values=eco_vals, hole=0.55,
            marker_colors=[eco_colors.get(l, "#334155") for l in eco_labels],
            textinfo="label+percent",
            textfont_size=11,
            hovertemplate="<b>%{label}</b><br>$%{value:.1f}B<br>%{percent}<extra></extra>",
        ))
        fig_eco.update_layout(
            title=dict(text="Corriente vs Capital", font=dict(color="#E2E8F0", size=13)),
            paper_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            showlegend=False, height=300,
            margin=dict(t=35, b=5, l=5, r=5),
            annotations=[dict(text=f"${data['total_devengado_b']:.0f}B", x=0.5, y=0.5,
                              font=dict(size=16, color="#E2E8F0"), showarrow=False)],
        )
        st.plotly_chart(fig_eco, use_container_width=True)

    with col_g2:
        # Inciso (tipo objeto del gasto)
        INC_COLORS = {
            "Gastos En Personal":           "#EF4444",
            "Servicios No Personales":      "#F97316",
            "Transferencias":               "#FBBF24",
            "Bienes De Uso":                "#10B981",
            "Bienes De Consumo":            "#3B82F6",
            "Servicio De La Deuda Y Disminución De Otros Pasivos": "#64748B",
            "Activos Financieros":          "#475569",
        }
        df_i = df_inc[df_inc["devengado"] > 0].sort_values("devengado", ascending=True)
        fig_inc = go.Figure(go.Bar(
            y=df_i["nombre"].str.replace("Servicio De La Deuda.*", "Serv. Deuda", regex=True),
            x=df_i["devengado"],
            orientation="h",
            marker_color=[INC_COLORS.get(n, "#334155") for n in df_i["nombre"]],
            text=df_i["devengado"].apply(lambda x: f"${x:.0f}B"),
            textposition="outside",
            textfont=dict(color="#E2E8F0", size=10),
        ))
        fig_inc.update_layout(
            title=dict(text="Por objeto del gasto (Inciso)", font=dict(color="#E2E8F0", size=13)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B", range=[0, 2000]),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=35, b=5, l=5, r=55), height=300, showlegend=False,
        )
        st.plotly_chart(fig_inc, use_container_width=True)

    # Nota sobre personal
    pct_personal = round(df_inc[df_inc["nombre"]=="Gastos En Personal"]["devengado"].sum()
                         / data["total_devengado_b"] * 100, 1)
    st.info(f"💡 **{pct_personal}% del presupuesto** está destinado a Gastos en Personal (sueldos y cargas sociales) — el ítem más grande del gasto público porteño.")

# ══════════════════════════════════════════════════════════════════════
# TAB 4 – POR COMUNA
# ══════════════════════════════════════════════════════════════════════
with tab4:
    df_com_s = df_com.sort_values("devengado_b", ascending=False)
    max_dev  = df_com_s["devengado_b"].max()
    min_dev  = df_com_s["devengado_b"].min()

    col_map, col_info = st.columns([3, 2])

    with col_map:
        m = folium.Map(location=[-34.615, -58.443], zoom_start=12, tiles=None, prefer_canvas=True)
        folium.TileLayer(
            "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
            attr="© CARTO", max_zoom=19,
        ).add_to(m)

        for feat in geojson["features"]:
            cid  = feat["properties"]["comuna"]
            row  = df_com[df_com["comuna"] == cid]
            if row.empty: continue
            row  = row.iloc[0]
            val  = row["devengado_b"]
            ratio = (val - min_dev) / (max_dev - min_dev) if max_dev != min_dev else 0.5
            r_ = int(245 * ratio + 16  * (1 - ratio))
            g_ = int(158 * ratio + 185 * (1 - ratio))
            b_ = int(11  * ratio + 129 * (1 - ratio))
            alpha = int(60 + ratio * 160)
            fill = f"#{r_:02X}{g_:02X}{b_:02X}{alpha:02X}"

            per_cap_m = row["per_capita"] / 1_000_000
            top_funs  = data["por_funcion_por_comuna"].get(str(cid), [])[:3]
            fun_str   = " · ".join(f"{r['funcion'][:12]}" for r in top_funs)

            tooltip = (
                f"<b>Comuna {cid:02d}</b><br>"
                f"{feat['properties'].get('barrios','')}<br><br>"
                f"<b>💰 Devengado:</b> ${val:.2f}B<br>"
                f"Per cápita: ${per_cap_m:.2f}M<br>"
                f"Top: {fun_str}"
            )
            folium.GeoJson(
                feat,
                style_function=lambda f, fc=fill: {
                    "fillColor": fc, "color": "#F59E0B", "weight": 1.2, "fillOpacity": 0.8,
                },
                highlight_function=lambda f: {"weight": 3, "fillOpacity": 0.95},
                tooltip=folium.Tooltip(tooltip, sticky=False),
            ).add_to(m)
            try:
                centroid = shape(feat["geometry"]).centroid
                folium.Marker(
                    location=[centroid.y, centroid.x],
                    icon=folium.DivIcon(
                        html=f"<div style='font-size:9px;font-weight:800;color:white;text-shadow:0 1px 3px #000;text-align:center;'>C{cid:02d}<br>${val:.1f}B</div>",
                        icon_size=(40, 22), icon_anchor=(20, 11),
                    ),
                ).add_to(m)
            except Exception:
                pass

        st_folium(m, height=480, use_container_width=True,
                  returned_objects=[], key="presup_map")

    with col_info:
        st.markdown("#### Gasto devengado por comuna")
        st.markdown("<div style='font-size:.7rem;color:#64748B;margin-bottom:8px;'>Solo gasto georreferenciado a comunas (excluye central/genérico)</div>", unsafe_allow_html=True)
        for _, r in df_com_s.iterrows():
            cid  = int(r["comuna"])
            val  = r["devengado_b"]
            bar_w = int(val / max_dev * 100)
            pc_m  = r["per_capita"] / 1_000_000
            top3  = data["por_funcion_por_comuna"].get(str(cid), [])[:3]
            top_s = ", ".join(t["funcion"][:14] for t in top3)
            ratio = (val - min_dev) / (max_dev - min_dev) if max_dev != min_dev else 0.5
            clr   = f"#{int(245*ratio+16*(1-ratio)):02X}{int(158*ratio+185*(1-ratio)):02X}{int(11*ratio+129*(1-ratio)):02X}"
            st.markdown(
                f"<div style='margin-bottom:8px;padding:8px 10px;background:#0A1628;"
                f"border:1px solid #1E293B;border-radius:7px;'>"
                f"<div style='display:flex;justify-content:space-between;margin-bottom:3px;'>"
                f"<span style='font-size:.78rem;font-weight:700;color:#E2E8F0;'>C{cid:02d}</span>"
                f"<span style='font-size:.78rem;font-weight:800;color:{clr};'>${val:.2f}B</span></div>"
                f"<div style='background:#1E293B;border-radius:3px;height:4px;margin-bottom:4px;'>"
                f"<div style='background:{clr};height:4px;width:{bar_w}%;border-radius:3px;'></div>"
                f"</div>"
                f"<div style='display:flex;justify-content:space-between;font-size:.6rem;color:#334155;'>"
                f"<span>${pc_m:.2f}M per cápita</span></div>"
                f"<div style='font-size:.58rem;color:#1E293B;margin-top:2px;'>{top_s}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

# ── Footer ─────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Fuente: Ministerio de Hacienda y Finanzas · Gobierno de la Ciudad de Buenos Aires · "
    "data.buenosaires.gob.ar · Presupuesto Ejecutado 2024 – Trimestre 2 (Enero–Junio 2024). "
    "Montos en miles de millones de pesos. Ejecución = Devengado / Crédito Vigente."
)
