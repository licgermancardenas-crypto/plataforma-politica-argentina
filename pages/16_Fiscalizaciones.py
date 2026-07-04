"""
Página 16 – Fiscalizaciones CABA (AGC)
Agencia Gubernamental de Control · 2022-2024
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Fiscalizaciones CABA", page_icon="🔍", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background:#0D1117; }
[data-testid="stSidebar"]          { background:#0A1628; border-right:1px solid #1E293B; }
[data-testid="stSidebar"] *        { color:#E2E8F0 !important; }
[data-testid="stHeader"]           { background:transparent; }
[data-testid="stStatusWidget"]     { display:none !important; }
[data-stale],[data-stale="true"],[aria-busy="true"],.stApp>*,iframe { opacity:1!important; transition:none!important; }
.stTabs [data-baseweb="tab"]       { color:#94A3B8!important; }
.stTabs [aria-selected="true"]     { color:#67E8F9!important; border-bottom:2px solid #06B6D4!important; }
</style>""", unsafe_allow_html=True)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

@st.cache_data(show_spinner=False)
def load():
    with open(os.path.join(DATA_DIR, "fiscalizaciones_caba.json"), encoding="utf-8") as f:
        return json.load(f)

data = load()

df_cat  = pd.DataFrame(data["por_categoria_anio"])
df_mes  = pd.DataFrame(data["por_mes"])
df_area = pd.DataFrame(data["area_por_anio"])

CAT_COLORS = {
    "Alimenticios":            "#F59E0B",
    "Inspecciones Simples":    "#38BDF8",
    "Obras / AVO":             "#F97316",
    "Mercadería / Vía Pública":"#A78BFA",
    "Fiscalización Crítica":   "#EF4444",
    "Auditorías Integrales":   "#4ADE80",
    "Verificaciones":          "#FBBF24",
    "Fiscalización Nocturna":  "#C084FC",
    "Educativos":              "#86EFAC",
    "Salud / Geriátricos":     "#67E8F9",
    "Deportivos":              "#34D399",
    "Hoteles / Pensiones":     "#FCA5A5",
    "Eventos":                 "#FB923C",
    "Grandes Superficies":     "#94A3B8",
    "Elevadores":              "#475569",
    "Seguridad (Incendio/Térmicas)": "#DC2626",
    "Otros":                   "#1E293B",
}

MES_NOMBRES = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
               7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}

# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 Fiscalizaciones CABA")
    st.markdown("<span style='font-size:.73rem;color:#64748B;'>AGC · 2022-2024</span>", unsafe_allow_html=True)
    st.markdown("---")

    for t in data["totales_por_anio"]:
        yr, n = t["anio"], t["total"]
        st.markdown(
            f"<div style='margin-bottom:8px;'>"
            f"<div style='font-size:.62rem;color:#334155;'>{yr}</div>"
            f"<div style='font-size:1.3rem;font-weight:800;color:#67E8F9;'>{n:,}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    st.markdown(f"<div style='font-size:.65rem;color:#475569;'>Total histórico: <b>{data['total_historico']:,}</b></div>", unsafe_allow_html=True)
    st.markdown("---")

    # Top categorías globales
    st.markdown("**Por categoría (total)**")
    top_cat = {k:v for k,v in data["top_categorias"].items() if k != "Otros"}
    max_cat = max(top_cat.values()) if top_cat else 1
    for cat, n in sorted(top_cat.items(), key=lambda x:-x[1])[:10]:
        clr = CAT_COLORS.get(cat, "#64748B")
        bw  = int(n / max_cat * 100)
        st.markdown(
            f"<div style='margin-bottom:4px;'>"
            f"<div style='display:flex;justify-content:space-between;font-size:.68rem;'>"
            f"<span style='color:{clr};'>{cat[:22]}</span>"
            f"<span style='color:{clr};font-weight:700;'>{n:,}</span></div>"
            f"<div style='background:#1E293B;border-radius:2px;height:3px;'>"
            f"<div style='background:{clr};height:3px;width:{bw}%;border-radius:2px;'></div></div></div>",
            unsafe_allow_html=True,
        )
    st.markdown("---")
    año_fisc = st.selectbox("Año", [2024, 2023, 2022], key="fisc_anio")
    all_cats = sorted(df_cat[df_cat["categoria"] != "Otros"]["categoria"].unique().tolist())
    cats_sel = st.multiselect("Categorías", all_cats, default=all_cats[:5], key="fisc_cats")

# ── Header ──────────────────────────────────────────────────────────────
total = data["total_historico"]
t22, t23, t24 = [t["total"] for t in data["totales_por_anio"]]
d_2324 = round((t24-t23)/t23*100, 1) if t23 else 0

st.markdown(f"""
<div style='background:linear-gradient(135deg,#0A1628,#001a1a);padding:20px 28px;border-radius:12px;
            margin-bottom:20px;border:1px solid #06452244;'>
  <h1 style='color:#fff;margin:0;font-size:1.7rem;'>🔍 Fiscalizaciones – Agencia Gubernamental de Control CABA</h1>
  <p style='color:#64748B;margin:5px 0 0;font-size:.88rem;'>
    {total:,} inspecciones · 2022-2024 · Alimentos · Obras · Eventos · Salud · Espacio Público
  </p>
</div>""", unsafe_allow_html=True)

# ── KPIs ────────────────────────────────────────────────────────────────
cat_mas = max(top_cat.items(), key=lambda x:x[1]) if top_cat else ("—",0)
pct_alim = round(data["top_categorias"].get("Alimenticios",0)/total*100,1)

k1,k2,k3,k4,k5 = st.columns(5)
kpis = [
    (k1, f"{t22:,}",          "Inspecciones 2022",    "#67E8F9", "incluye rezago post-pandemia"),
    (k2, f"{t23:,}",          "Inspecciones 2023",    "#38BDF8", f"{round((t23-t22)/t22*100,1):+}% vs 2022"),
    (k3, f"{t24:,}",          "Inspecciones 2024",    "#0EA5E9", f"{d_2324:+}% vs 2023"),
    (k4, f"{pct_alim:.0f}%",  "Inspecciones aliment.", "#F59E0B", f"la categoría dominante"),
    (k5, f"{len(data['top_areas'])}", "Tipos de operativos", "#A78BFA", "áreas de la AGC"),
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

# ── Datos filtrados ──────────────────────────────────────────────────────
df_mes_f  = df_mes[df_mes["anio"] == año_fisc].copy()
df_cat_f  = df_cat[(df_cat["anio"] == año_fisc) & (df_cat["categoria"].isin(cats_sel))].copy()
df_area_f = df_area[df_area["anio"] == año_fisc].copy()

total_anio = next((t["total"] for t in data["totales_por_anio"] if t["anio"] == año_fisc), 0)
st.markdown(f"""
<div style='background:#0A1628;border:1px solid #1E293B;border-left:4px solid #67E8F9;
            border-radius:8px;padding:12px 16px;margin-bottom:14px;display:inline-block;'>
  <div style='font-size:.62rem;color:#64748B;text-transform:uppercase;letter-spacing:.04em;'>Inspecciones {año_fisc}</div>
  <div style='font-size:1.35rem;font-weight:800;color:#67E8F9;margin:3px 0;'>{total_anio:,}</div>
  <div style='font-size:.6rem;color:#334155;'>año seleccionado</div>
</div>""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Por Categoría", "📅 Evolución Temporal", "🔬 Detalle por Área"])

# ══════════════════════════════════════════════════════════════════════
# TAB 1 – POR CATEGORÍA
# ══════════════════════════════════════════════════════════════════════
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        # Stacked bar por categoría×año
        df_cat_clean = df_cat[df_cat["categoria"] != "Otros"].copy()
        fig_cat = px.bar(
            df_cat_f, x="anio", y="n", color="categoria",
            barmode="stack",
            color_discrete_map=CAT_COLORS,
        )
        fig_cat.update_layout(
            title=dict(text="Fiscalizaciones por categoría y año",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B", tickvals=[2022,2023,2024]),
            yaxis=dict(gridcolor="#1E293B", title="Inspecciones"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=8)),
            margin=dict(t=35,b=5,l=5,r=5), height=400,
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    with c2:
        # Donut total
        cat_total = df_cat_f.groupby("categoria")["n"].sum().reset_index()
        cat_total = cat_total.sort_values("n",ascending=False)
        fig_don = go.Figure(go.Pie(
            labels=cat_total["categoria"],
            values=cat_total["n"],
            hole=0.5,
            marker_colors=[CAT_COLORS.get(c,"#64748B") for c in cat_total["categoria"]],
            textinfo="label+percent",
            textfont_size=9,
        ))
        fig_don.update_layout(
            title=dict(text="Distribución total 2022-2024",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=8)),
            margin=dict(t=35,b=5,l=5,r=5), height=400,
        )
        st.plotly_chart(fig_don, use_container_width=True)

    # Bar horizontal ranking
    fig_rank = go.Figure(go.Bar(
        y=cat_total.sort_values("n")["categoria"],
        x=cat_total.sort_values("n")["n"],
        orientation="h",
        marker_color=[CAT_COLORS.get(c,"#64748B") for c in cat_total.sort_values("n")["categoria"]],
        text=cat_total.sort_values("n")["n"].apply(lambda x: f"{x:,}"),
        textposition="outside", textfont=dict(color="#E2E8F0",size=9),
    ))
    fig_rank.update_layout(
        title=dict(text="Total de inspecciones por categoría (2022-2024)",font=dict(color="#E2E8F0",size=12)),
        paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
        xaxis=dict(gridcolor="#1E293B"),
        yaxis=dict(gridcolor="#1E293B"),
        margin=dict(t=35,b=5,l=5,r=70), height=340, showlegend=False,
    )
    st.plotly_chart(fig_rank, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 2 – EVOLUCIÓN TEMPORAL
# ══════════════════════════════════════════════════════════════════════
with tab2:
    # Por mes × año
    df_mes["mes_nom"] = df_mes["mes"].map(MES_NOMBRES)
    df_mes["periodo"] = df_mes["anio"].astype(str) + "-" + df_mes["mes"].astype(str).str.zfill(2)

    c1, c2 = st.columns(2)
    with c1:
        # Totales por año (bar)
        fig_tot = go.Figure(go.Bar(
            x=[str(t["anio"]) for t in data["totales_por_anio"]],
            y=[t["total"] for t in data["totales_por_anio"]],
            marker_color=["#38BDF8","#0EA5E9","#0284C7"],
            text=[f"{t['total']:,}" for t in data["totales_por_anio"]],
            textposition="outside", textfont=dict(color="#E2E8F0",size=13),
        ))
        fig_tot.update_layout(
            title=dict(text="Total de inspecciones por año",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B", range=[0, max(t["total"] for t in data["totales_por_anio"])*1.2]),
            margin=dict(t=35,b=5,l=5,r=5), height=280, showlegend=False,
        )
        st.plotly_chart(fig_tot, use_container_width=True)

    with c2:
        # Mensual por año (line)
        colors_anio = {2022:"#F59E0B", 2023:"#38BDF8", 2024:"#4ADE80"}
        fig_men = go.Figure()
        for yr in [año_fisc]:
            df_yr = df_mes_f.sort_values("mes")
            if len(df_yr) == 0: continue
            fig_men.add_trace(go.Scatter(
                x=df_yr["mes"].map(MES_NOMBRES),
                y=df_yr["n"],
                name=str(yr), mode="lines+markers",
                line=dict(color=colors_anio[yr], width=2.5),
                marker=dict(size=6),
            ))
        fig_men.update_layout(
            title=dict(text="Evolución mensual por año",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B", title="Inspecciones"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            margin=dict(t=35,b=5,l=5,r=5), height=280,
        )
        st.plotly_chart(fig_men, use_container_width=True)

    # Variación interanual por categoría
    cat_pivot = df_cat_clean.pivot_table(index="categoria", columns="anio", values="n", fill_value=0).reset_index()
    if 2023 in cat_pivot.columns and 2024 in cat_pivot.columns:
        cat_pivot["var_pct"] = ((cat_pivot[2024] - cat_pivot[2023]) / cat_pivot[2023].replace(0,1) * 100).round(1)
        cat_pivot = cat_pivot.sort_values("var_pct")
        colors_var = ["#EF4444" if v < 0 else "#4ADE80" for v in cat_pivot["var_pct"]]
        fig_var = go.Figure(go.Bar(
            y=cat_pivot["categoria"],
            x=cat_pivot["var_pct"],
            orientation="h",
            marker_color=colors_var,
            text=cat_pivot["var_pct"].apply(lambda x: f"{x:+.1f}%"),
            textposition="outside", textfont=dict(color="#E2E8F0",size=9),
        ))
        fig_var.add_vline(x=0, line_color="#475569", line_width=1)
        fig_var.update_layout(
            title=dict(text="Variación interanual 2023→2024 por categoría (%)",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=35,b=5,l=5,r=70), height=340, showlegend=False,
        )
        st.plotly_chart(fig_var, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 3 – DETALLE POR ÁREA
# ══════════════════════════════════════════════════════════════════════
with tab3:
    # Top áreas nominales (limpias)
    top_areas_clean = {k:v for k,v in data["top_areas"].items()
                       if not any(c in k for c in ["Ã","â","Â"])}
    top_areas_sorted = sorted(top_areas_clean.items(), key=lambda x:-x[1])[:20]

    fig_top = go.Figure(go.Bar(
        y=[a[:40] for a,_ in top_areas_sorted],
        x=[n for _,n in top_areas_sorted],
        orientation="h",
        marker_color="#67E8F9",
        text=[f"{n:,}" for _,n in top_areas_sorted],
        textposition="outside", textfont=dict(color="#E2E8F0",size=9),
    ))
    fig_top.update_layout(
        title=dict(text="Top 20 tipos de operativo (total histórico 2022-2024)",font=dict(color="#E2E8F0",size=12)),
        paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
        xaxis=dict(gridcolor="#1E293B"),
        yaxis=dict(gridcolor="#1E293B", categoryorder="total ascending"),
        margin=dict(t=35,b=5,l=5,r=70), height=560, showlegend=False,
    )
    st.plotly_chart(fig_top, use_container_width=True)

    st.markdown("#### Tabla completa por área y año")
    df_pivot = df_area_f.pivot_table(index="area", columns="anio", values="n", fill_value=0).reset_index()
    df_pivot.columns = [str(c) for c in df_pivot.columns]
    df_pivot["Total"] = df_pivot[[c for c in df_pivot.columns if c.isdigit()]].sum(axis=1)
    df_pivot = df_pivot.sort_values("Total", ascending=False)
    st.dataframe(df_pivot.rename(columns={"area":"Área"}),
                 use_container_width=True, hide_index=True, height=400)

st.markdown("---")
st.caption("Fuente: AGC (Agencia Gubernamental de Control) – Inspecciones realizadas 2022-2024 · "
           "Gobierno de la Ciudad de Buenos Aires · data.buenosaires.gob.ar. "
           "El volumen de 2022 incluye recupero post-pandemia de operativos alimenticios diferidos.")
