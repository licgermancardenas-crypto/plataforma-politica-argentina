"""
Página 8 – Legisladores de la Ciudad de Buenos Aires
Legislatura CABA · 60 Diputados Porteños · composición 2025-2026
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Legisladores CABA",
    page_icon="🏛",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background:#0D1117; }
[data-testid="stSidebar"]          { background:#0A1628; border-right:1px solid #1E293B; }
[data-testid="stSidebar"] *        { color:#E2E8F0 !important; }
[data-testid="stHeader"]           { background:transparent; }
div[data-testid="stMetric"]        { background:#0A1628; border:1px solid #1E293B; border-radius:8px; padding:12px 16px; }
[data-testid="stStatusWidget"]     { display: none !important; }
[data-stale="true"]                { opacity: 1 !important; transition: none !important; }
.stTabs [data-baseweb="tab"]       { color: #94A3B8 !important; }
.stTabs [aria-selected="true"]     { color: #E2E8F0 !important; border-bottom: 2px solid #3B82F6 !important; }
</style>
""", unsafe_allow_html=True)

# ── Datos ──────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

@st.cache_data(show_spinner=False)
def load_data():
    with open(os.path.join(DATA_DIR, "legisladores_caba.json"), encoding="utf-8") as f:
        return json.load(f)

data       = load_data()
autoridades = data["autoridades"]
bloques_raw = data["bloques"]
diputados   = data["diputados"]

df = pd.DataFrame(diputados)
df["presidente_bloque"] = df.get("presidente_bloque", False).fillna(False)

BLOQUE_COLOR = {b["nombre"]: b["color"] for b in bloques_raw}
BLOQUE_BANCAS = {b["nombre"]: b["bancas"] for b in bloques_raw}

# ── Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#0A1628,#1E3A5F);padding:20px 28px;border-radius:12px;
            margin-bottom:20px;border:1px solid #1E293B;'>
  <h1 style='color:#fff;margin:0;font-size:1.7rem;'>🏛 Legislatura de la Ciudad de Buenos Aires</h1>
  <p style='color:#64748B;margin:5px 0 0;font-size:.88rem;'>
    60 Diputados Porteños · Composición actualizada 2025–2026 · 9 bloques parlamentarios
  </p>
</div>
""", unsafe_allow_html=True)

# ── Autoridades ────────────────────────────────────────────────────────
st.markdown("""
<div style='background:#0A1628;border:1px solid #1E293B;border-radius:10px;padding:14px 20px;margin-bottom:18px;'>
  <div style='font-size:.65rem;color:#334155;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;'>
    Autoridades del Cuerpo
  </div>
  <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:12px;'>
""" + "".join([
    f"<div style='text-align:center;'>"
    f"<div style='font-size:.6rem;color:#475569;margin-bottom:4px;'>{rol}</div>"
    f"<div style='font-size:.82rem;font-weight:700;color:#E2E8F0;'>{nombre}</div>"
    f"</div>"
    for rol, nombre in [
        ("Presidenta", autoridades["presidenta"]),
        ("Vicepresidenta 1°", autoridades["vicepresidente_1"]),
        ("Vicepresidente 2°", autoridades["vicepresidente_2"]),
        ("Vicepresidente 3°", autoridades["vicepresidente_3"]),
    ]
]) + """
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────────────
total = len(df)
n_bloques = df["bloque"].nunique()
cohort_23 = len(df[df["mandato"] == "2023-2027"])
cohort_25 = len(df[df["mandato"] == "2025-2029"])
oposicion = BLOQUE_BANCAS.get("Fuerza por Buenos Aires", 0)
gobierno  = BLOQUE_BANCAS.get("Vamos por Más", 0) + BLOQUE_BANCAS.get("La Libertad Avanza", 0)

k1, k2, k3, k4, k5, k6 = st.columns(6)
kpis = [
    (k1, str(total),      "Diputados totales",         "#3B82F6", "🏛"),
    (k2, str(n_bloques),  "Bloques parlamentarios",    "#8B5CF6", "🔷"),
    (k3, str(cohort_23),  "Mandato 2023–2027",         "#6EE7B7", "📅"),
    (k4, str(cohort_25),  "Mandato 2025–2029",         "#FCD34D", "📅"),
    (k5, str(oposicion),  "Oposición (FxBA)",          "#DC2626", "🔴"),
    (k6, str(gobierno),   "Gov. CABA + LLA",           "#7C3AED", "🟣"),
]
for col, val, label, color, icon in kpis:
    with col:
        st.markdown(f"""
<div style='background:#0A1628;border:1px solid #1E293B;border-left:4px solid {color};
            border-radius:8px;padding:12px 16px;'>
  <div style='font-size:.68rem;color:#64748B;text-transform:uppercase;letter-spacing:.04em;'>{icon} {label}</div>
  <div style='font-size:1.5rem;font-weight:800;color:{color};margin-top:2px;'>{val}</div>
</div>""", unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Tabs ────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 Lista de Legisladores", "📊 Composición por Bloques", "🗓 Por Mandato"])

# ══════════════════════════════════════════════════════════════════════
# TAB 1 – LISTA
# ══════════════════════════════════════════════════════════════════════
with tab1:
    col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
    with col_f1:
        bl_opts = ["Todos"] + sorted(df["bloque"].unique().tolist())
        bl_sel  = st.selectbox("Bloque", bl_opts, key="bl_filter")
    with col_f2:
        m_opts  = ["Todos", "2023-2027", "2025-2029"]
        m_sel   = st.selectbox("Mandato", m_opts, key="m_filter")
    with col_f3:
        search  = st.text_input("🔍 Buscar nombre", key="leg_search")

    dff = df.copy()
    if bl_sel  != "Todos": dff = dff[dff["bloque"] == bl_sel]
    if m_sel   != "Todos": dff = dff[dff["mandato"] == m_sel]
    if search:             dff = dff[dff["nombre"].str.contains(search, case=False, na=False)]

    st.markdown(f"<div style='font-size:.75rem;color:#64748B;margin-bottom:8px;'>{len(dff)} legisladores</div>",
                unsafe_allow_html=True)

    # Tabla con color de bloque
    rows_html = ""
    for _, row in dff.sort_values(["bloque", "nombre"]).iterrows():
        color  = BLOQUE_COLOR.get(row["bloque"], "#64748B")
        pres   = " ★" if row.get("presidente_bloque") else ""
        rows_html += (
            f"<tr>"
            f"<td style='padding:8px 12px;color:#E2E8F0;font-size:.82rem;'>{row['nombre']}</td>"
            f"<td style='padding:8px 12px;'>"
            f"  <span style='background:{color}22;color:{color};border:1px solid {color}55;"
            f"  padding:2px 10px;border-radius:12px;font-size:.72rem;font-weight:600;'>"
            f"  {row['bloque']}{pres}</span></td>"
            f"<td style='padding:8px 12px;color:#94A3B8;font-size:.78rem;'>{row['mandato']}</td>"
            f"</tr>"
        )

    st.markdown(f"""
<div style='overflow-x:auto;'>
<table style='width:100%;border-collapse:collapse;background:#0A1628;border-radius:10px;overflow:hidden;'>
  <thead>
    <tr style='background:#1E293B;'>
      <th style='padding:10px 12px;text-align:left;color:#94A3B8;font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;'>Nombre</th>
      <th style='padding:10px 12px;text-align:left;color:#94A3B8;font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;'>Bloque</th>
      <th style='padding:10px 12px;text-align:left;color:#94A3B8;font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;'>Mandato</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 2 – COMPOSICIÓN
# ══════════════════════════════════════════════════════════════════════
with tab2:
    col_a, col_b = st.columns([1, 1])

    with col_a:
        df_bloques = pd.DataFrame(bloques_raw).sort_values("bancas", ascending=False)
        fig_pie = go.Figure(go.Pie(
            labels=df_bloques["nombre"],
            values=df_bloques["bancas"],
            hole=0.55,
            marker_colors=df_bloques["color"].tolist(),
            textinfo="label+value",
            textfont_size=11,
            hovertemplate="<b>%{label}</b><br>%{value} bancas<br>%{percent}<extra></extra>",
        ))
        fig_pie.update_layout(
            title=dict(text="Distribución de bancas", font=dict(color="#E2E8F0", size=14)),
            paper_bgcolor="#0A1628",
            plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            showlegend=False,
            margin=dict(t=40, b=10, l=10, r=10),
            height=380,
            annotations=[dict(
                text=f"<b>60</b><br>bancas",
                x=0.5, y=0.5, font_size=18, showarrow=False,
                font=dict(color="#E2E8F0"),
            )],
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        fig_bar = go.Figure(go.Bar(
            y=df_bloques["nombre"],
            x=df_bloques["bancas"],
            orientation="h",
            marker_color=df_bloques["color"].tolist(),
            text=df_bloques["bancas"],
            textposition="outside",
            textfont=dict(color="#E2E8F0", size=12),
            hovertemplate="<b>%{y}</b><br>%{x} bancas<extra></extra>",
        ))
        fig_bar.update_layout(
            title=dict(text="Bancas por bloque", font=dict(color="#E2E8F0", size=14)),
            paper_bgcolor="#0A1628",
            plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 26]),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=40, b=10, l=10, r=50),
            height=380,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Tarjetas por bloque
    st.markdown("---")
    st.markdown("<div style='font-size:.7rem;color:#475569;font-weight:700;text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px;'>Presidentes de bloque ★</div>", unsafe_allow_html=True)
    pres_df = df[df["presidente_bloque"] == True].sort_values("bloque")
    cards_html = "<div style='display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:8px;'>"
    for _, row in pres_df.iterrows():
        c = BLOQUE_COLOR.get(row["bloque"], "#64748B")
        b = BLOQUE_BANCAS.get(row["bloque"], "?")
        cards_html += (
            f"<div style='background:{c}11;border:1px solid {c}44;border-radius:9px;padding:10px 14px;'>"
            f"<div style='font-size:.72rem;font-weight:800;color:{c};margin-bottom:3px;'>{row['bloque']}</div>"
            f"<div style='font-size:.82rem;color:#E2E8F0;font-weight:600;'>{row['nombre']}</div>"
            f"<div style='font-size:.62rem;color:#475569;margin-top:3px;'>{b} bancas · {row['mandato']}</div>"
            f"</div>"
        )
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 3 – POR MANDATO
# ══════════════════════════════════════════════════════════════════════
with tab3:
    col_c1, col_c2 = st.columns(2)

    for col, mandato_label in [(col_c1, "2023-2027"), (col_c2, "2025-2029")]:
        with col:
            dfc = df[df["mandato"] == mandato_label].copy()
            titulo = "🔵 Electos 2023" if mandato_label == "2023-2027" else "🟢 Electos 2025"
            st.markdown(f"#### {titulo} – {len(dfc)} legisladores")

            bc = dfc.groupby("bloque").size().reset_index(name="n").sort_values("n", ascending=False)
            bc["color"] = bc["bloque"].map(BLOQUE_COLOR).fillna("#64748B")

            fig_c = go.Figure(go.Bar(
                y=bc["bloque"],
                x=bc["n"],
                orientation="h",
                marker_color=bc["color"].tolist(),
                text=bc["n"],
                textposition="outside",
                textfont=dict(color="#E2E8F0", size=11),
            ))
            fig_c.update_layout(
                paper_bgcolor="#0A1628",
                plot_bgcolor="#0A1628",
                font=dict(color="#94A3B8"),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 14]),
                yaxis=dict(gridcolor="#1E293B"),
                margin=dict(t=10, b=5, l=5, r=40),
                height=250,
                showlegend=False,
            )
            st.plotly_chart(fig_c, use_container_width=True)

            for _, row in dfc.sort_values(["bloque", "nombre"]).iterrows():
                c = BLOQUE_COLOR.get(row["bloque"], "#64748B")
                pres = " ★" if row.get("presidente_bloque") else ""
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:8px;padding:4px 0;border-bottom:1px solid #0F172A;'>"
                    f"<span style='width:8px;height:8px;border-radius:50%;background:{c};flex-shrink:0;'></span>"
                    f"<span style='font-size:.78rem;color:#E2E8F0;'>{row['nombre']}{pres}</span>"
                    f"<span style='margin-left:auto;font-size:.65rem;color:#334155;white-space:nowrap;'>{row['bloque'][:20]}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

# ── Footer ─────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Fuente: Legislatura de la Ciudad de Buenos Aires · legislatura.gob.ar · "
    "Elecciones legislativas 2023 y 2025 (escrutinio definitivo). "
    "★ = presidente/a de bloque."
)
