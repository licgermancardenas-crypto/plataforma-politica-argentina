"""
Turismo & Cultura CABA – Página 19
Fuentes: Ente de Turismo GCBA · Min. Cultura · Teatro Colón · Complejo Teatral
"""
import json, os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(page_title="Turismo & Cultura CABA", page_icon="🎭", layout="wide")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@st.cache_data
def load():
    with open(os.path.join(BASE, "data", "turismo_cultura_caba.json"), encoding="utf-8") as f:
        return json.load(f)

d = load()

TEAL   = "#0D9488"
TEAL2  = "#0F766E"
AMBER  = "#F59E0B"
PURPLE = "#7C3AED"
ROSE   = "#EC4899"

# Colores por tipo de espacio cultural
TIPO_COLOR = {
    "MUSEO": "#7C3AED",
    "CENTRO CULTURAL": "#0D9488",
    "SALA DE TEATRO": "#F59E0B",
    "ANFITEATRO": "#10B981",
    "SALA DE CINE": "#3B82F6",
    "GALERIA DE ARTE": "#EC4899",
    "CLUB DE MUSICA EN VIVO": "#F97316",
    "ESPACIO FERIAL": "#6366F1",
    "ESPACIO DE FORMACION": "#84CC16",
}

st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#F0FDFA;}
[data-testid="stSidebar"]{background:#134E4A;}
[data-testid="stSidebar"] *{color:#fff!important;}
</style>""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#134E4A,#0D9488);
     padding:24px 32px;border-radius:12px;margin-bottom:20px;'>
  <h1 style='color:white;margin:0;font-size:1.8rem;'>🎭 Turismo & Cultura CABA</h1>
  <p style='color:#99F6E4;margin:4px 0 0;font-size:.9rem;'>
    Espacios culturales · Teatro Colón · Alojamientos · Murales · Competitividad turística
  </p>
</div>""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────────
res = d["resumen"]
k1, k2, k3, k4, k5 = st.columns(5)

def kpi(col, val, label, color, sub=""):
    col.markdown(f"""
    <div style='background:white;border-radius:10px;padding:16px 20px;
         border-left:5px solid {color};box-shadow:0 2px 6px rgba(0,0,0,.08);'>
      <p style='margin:0;font-size:.78rem;color:#666;text-transform:uppercase;letter-spacing:.5px;'>{label}</p>
      <p style='margin:2px 0;font-size:1.8rem;font-weight:700;color:{color};'>{val}</p>
      <p style='margin:0;font-size:.75rem;color:#999;'>{sub}</p>
    </div>""", unsafe_allow_html=True)

kpi(k1, f"{res['espacios_culturales_total']:,}".replace(",","."),
    "Espacios culturales", TEAL, "Museos, teatros, centros cult., librerías...")
kpi(k2, f"{res['alojamientos_total']}",
    "Alojamientos turísticos", AMBER, "Hoteles 1 a 5★ + hospedajes")
kpi(k3, f"{res['murales_total']}",
    "Murales catalogados", PURPLE, "En edificios públicos y privados")
kpi(k4, f"{res['colon_asistentes_pico']:,}".replace(",","."),
    f"Pico Teatro Colón ({res['colon_asistentes_pico_anio']})", ROSE, "Asistentes en una temporada")
kpi(k5, f"{res['colon_visitas_total']:,}".replace(",","."),
    "Visitas guiadas Colón (2016-18)", "#0EA5E9", "General, escuelas, extranjeros...")

st.markdown("<br>", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎭 Turismo & Cultura")
    st.markdown("---")
    st.markdown("**Espacios por tipo**")
    for tipo, n in list(d["espacios_por_tipo"].items())[:12]:
        color = TIPO_COLOR.get(tipo, "#888")
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;font-size:.82rem;margin-bottom:3px;'>"
            f"<span style='color:{color};'>■</span> {tipo.title()}"
            f"<b>{n:,}</b></div>",
            unsafe_allow_html=True,
        )
    st.markdown("---")
    st.markdown("**Murales – técnicas**")
    for tec, n in list(d["murales_por_tecnica"].items())[:8]:
        st.markdown(f"<div style='font-size:.81rem;display:flex;justify-content:space-between;'>"
                    f"<span>{tec.title()[:30]}</span><b>{n}</b></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "🗺 Mapa Cultural",
    "🎵 Teatro Colón & Complejo",
    "🏨 Turismo",
    "🖼 Arte & Patrimonio",
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 – Mapa Cultural
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    col_f, col_m = st.columns([1, 3])

    with col_f:
        st.markdown("#### Filtrar")
        tipos_disponibles = sorted(set(e["tipo"] for e in d["espacios_culturales_map"]))
        sel_tipos = st.multiselect(
            "Tipo de espacio",
            tipos_disponibles,
            default=["MUSEO","CENTRO CULTURAL","SALA DE TEATRO","SALA DE CINE"],
        )
        mostrar_aloj = st.checkbox("Mostrar alojamientos turísticos", value=False)
        mostrar_murales = st.checkbox("Mostrar murales", value=False)

        st.markdown("---")
        st.markdown("**Alojamientos**")
        for tipo, n in sorted(d["alojamientos_por_tipo"].items(), key=lambda x: -x[1])[:8]:
            st.markdown(f"<div style='font-size:.82rem;display:flex;justify-content:space-between;'>"
                        f"<span>{tipo}</span><b>{n}</b></div>", unsafe_allow_html=True)

    with col_m:
        m = folium.Map(location=[-34.615, -58.437], zoom_start=12, tiles="CartoDB positron")
        cluster_ec = MarkerCluster(name="Espacios culturales").add_to(m)

        # Filter BEFORE building markers — never iterate all 1392 items
        espacios_filtrados = [e for e in d["espacios_culturales_map"] if e["tipo"] in sel_tipos][:600]
        for e in espacios_filtrados:
            color = TIPO_COLOR.get(e["tipo"], "#888")
            folium.CircleMarker(
                location=[e["lat"], e["lon"]],
                radius=5,
                color=color, fill=True, fill_color=color, fill_opacity=0.8,
                tooltip=f"<b>{e['nombre']}</b><br>{e['tipo']}<br>{e['barrio']}",
            ).add_to(cluster_ec)

        if mostrar_aloj:
            cluster_al = MarkerCluster(name="Alojamientos").add_to(m)
            for a in d["alojamientos"]:
                folium.CircleMarker(
                    location=[a["lat"], a["lon"]],
                    radius=6,
                    color="#F59E0B", fill=True, fill_color="#F59E0B", fill_opacity=0.85,
                    tooltip=f"<b>{a['nombre']}</b><br>{a['tipo']}<br>{a['direccion']}",
                ).add_to(cluster_al)

        if mostrar_murales:
            for mu in d["murales_map"]:
                folium.CircleMarker(
                    location=[mu["lat"], mu["lon"]],
                    radius=4,
                    color="#7C3AED", fill=True, fill_color="#7C3AED", fill_opacity=0.7,
                    tooltip=f"<b>{mu['nombre']}</b><br>{mu['tecnica']}<br>{mu['barrio']}",
                ).add_to(m)

        folium.LayerControl().add_to(m)
        st_folium(m, width=None, height=500, returned_objects=[],
                  key=f"turismo_map_{'_'.join(sorted(sel_tipos)[:3])}")

    st.markdown("---")
    col_et, col_eb = st.columns(2)
    with col_et:
        st.markdown("#### Top 15 tipos de espacios culturales")
        tipos_df = pd.DataFrame(
            [{"tipo": k.title(), "cantidad": v} for k, v in d["espacios_por_tipo"].items()]
        ).sort_values("cantidad", ascending=True)
        colors_ec = [TIPO_COLOR.get(k.upper(), "#888") for k in tipos_df["tipo"].str.upper()]
        fig_ec = go.Figure(go.Bar(
            y=tipos_df["tipo"], x=tipos_df["cantidad"], orientation="h",
            marker_color=colors_ec, text=tipos_df["cantidad"], textposition="outside",
        ))
        fig_ec.update_layout(
            height=420, margin=dict(t=10,b=10,l=10,r=60),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(240,253,250,1)",
            xaxis=dict(gridcolor="#CCFBF1"),
        )
        st.plotly_chart(fig_ec, use_container_width=True)

    with col_eb:
        st.markdown("#### Agencias de viajes – top barrios")
        ag_df = pd.DataFrame(
            [{"barrio": k, "agencias": v} for k, v in d["agencias_por_barrio"].items()]
        ).sort_values("agencias", ascending=True)
        fig_ag = go.Figure(go.Bar(
            y=ag_df["barrio"], x=ag_df["agencias"], orientation="h",
            marker_color=AMBER, text=ag_df["agencias"], textposition="outside",
        ))
        fig_ag.update_layout(
            height=420, margin=dict(t=10,b=10,l=10,r=60),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(240,253,250,1)",
            xaxis=dict(gridcolor="#CCFBF1"),
        )
        st.plotly_chart(fig_ag, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 – Teatro Colón & Complejo
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    col_ca, col_cv = st.columns(2)

    with col_ca:
        st.markdown("#### Teatro Colón – asistentes por año (2010-2015)")
        ca_df = pd.DataFrame(d["colon_asistentes"])
        fig_ca = go.Figure(go.Bar(
            x=ca_df["anio"], y=ca_df["asistentes"],
            marker_color=[ROSE if v == ca_df["asistentes"].max() else TEAL for v in ca_df["asistentes"]],
            text=[f"{v:,}" for v in ca_df["asistentes"]], textposition="outside",
        ))
        fig_ca.update_layout(
            height=300, yaxis_title="Asistentes",
            margin=dict(t=10,b=10,l=10,r=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(240,253,250,1)",
            yaxis=dict(gridcolor="#CCFBF1"),
        )
        st.plotly_chart(fig_ca, use_container_width=True)
        st.caption("Pico en 2014: 398,789 asistentes. Datos disponibles: 2010-2015")

    with col_cv:
        st.markdown("#### Teatro Colón – visitas guiadas por tipo")
        cvt_df = pd.DataFrame(d["colon_visitas_por_tipo"])
        cvt_top = cvt_df[cvt_df["visitas"] > 0].sort_values("visitas", ascending=True).tail(10)
        fig_cvt = go.Figure(go.Bar(
            y=cvt_top["tipo"], x=cvt_top["visitas"], orientation="h",
            marker_color=ROSE,
            text=[f"{v:,}" for v in cvt_top["visitas"]], textposition="outside",
        ))
        fig_cvt.update_layout(
            height=300, margin=dict(t=10,b=10,l=10,r=80),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(240,253,250,1)",
            xaxis=dict(gridcolor="#CCFBF1"),
        )
        st.plotly_chart(fig_cvt, use_container_width=True)
        st.caption(f"Total visitas guiadas 2016-2018: {res['colon_visitas_total']:,}")

    st.markdown("---")
    st.markdown("#### Teatro Colón – visitas guiadas anuales (2016-2018)")
    cv_df = pd.DataFrame(d["colon_visitas_guiadas"])
    fig_cv = go.Figure(go.Bar(
        x=cv_df["anio"], y=cv_df["visitas"],
        marker_color=["#EF4444" if v < 100000 else ROSE for v in cv_df["visitas"]],
        text=[f"{v:,}" for v in cv_df["visitas"]], textposition="outside",
    ))
    fig_cv.update_layout(
        height=220, yaxis_title="Visitas guiadas",
        margin=dict(t=10,b=10,l=10,r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(240,253,250,1)",
        yaxis=dict(gridcolor="#CCFBF1"),
    )
    st.plotly_chart(fig_cv, use_container_width=True)
    st.caption("La caída en 2018 refleja datos parciales del año en el dataset")

    st.markdown("---")
    col_ct, col_ent = st.columns(2)

    with col_ct:
        st.markdown("#### Complejo Teatral BA – funciones por teatro y año")
        ct_df = pd.DataFrame(d["complejo_teatral_funciones"])
        TEATRO_COLOR = {
            "SAN MARTIN": TEAL, "SARMIENTO": AMBER, "REGIO": PURPLE,
            "DE LA RIBERA": ROSE, "SM CUNIL": "#10B981",
        }
        fig_ct = go.Figure()
        for teatro in ct_df["teatro"].unique():
            sub = ct_df[ct_df["teatro"]==teatro]
            fig_ct.add_trace(go.Bar(
                x=sub["anio"], y=sub["funciones"],
                name=teatro, marker_color=TEATRO_COLOR.get(teatro, "#888"),
            ))
        fig_ct.update_layout(
            barmode="group", height=300,
            margin=dict(t=10,b=10,l=10,r=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(240,253,250,1)",
            yaxis=dict(gridcolor="#CCFBF1", title="Funciones"),
            legend=dict(orientation="h", y=-0.3),
        )
        st.plotly_chart(fig_ct, use_container_width=True)

    with col_ent:
        st.markdown("#### Complejo Teatral – localidades vendidas por teatro")
        ent_df = pd.DataFrame(d["complejo_entradas"])
        fig_ent = go.Figure()
        for teatro in ent_df["teatro"].unique():
            sub = ent_df[ent_df["teatro"]==teatro]
            fig_ent.add_trace(go.Bar(
                x=sub["anio"], y=sub["entradas"],
                name=teatro, marker_color=TEATRO_COLOR.get(teatro, "#888"),
            ))
        fig_ent.update_layout(
            barmode="group", height=300,
            margin=dict(t=10,b=10,l=10,r=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(240,253,250,1)",
            yaxis=dict(gridcolor="#CCFBF1", title="Localidades"),
            legend=dict(orientation="h", y=-0.3),
        )
        st.plotly_chart(fig_ent, use_container_width=True)

    st.markdown("#### Clasificación de obras – Complejo Teatral")
    cls_df = pd.DataFrame(
        [{"clasificacion": k, "n": v} for k, v in d["complejo_clasificacion"].items()]
    ).sort_values("n", ascending=False)
    fig_cls = px.bar(
        cls_df, x="clasificacion", y="n",
        color="n", color_continuous_scale="Teal",
        text="n", labels={"clasificacion": "", "n": "Funciones"},
    )
    fig_cls.update_traces(textposition="outside")
    fig_cls.update_layout(
        height=240, showlegend=False, coloraxis_showscale=False,
        margin=dict(t=10,b=10,l=10,r=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_cls, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 – Turismo
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    col_al, col_ev = st.columns(2)

    with col_al:
        st.markdown("#### Alojamientos turísticos por categoría")
        al_df = pd.DataFrame(
            [{"tipo": k, "cantidad": v} for k, v in d["alojamientos_por_tipo"].items()]
        ).sort_values("cantidad", ascending=False)
        # Separate stars vs others
        STAR_ORDER = ["5 Estrellas","4 Estrellas","3 Estrellas","2 Estrellas","1 Estrella",
                      "Apart 3 Estrellas","Apart 2 Estrellas","Apart 1 Estrella",
                      "Registro de Prestadores-Boutique","Registro de Prestadores",
                      "Hospedaje A","Hospedaje B"]
        al_df["_o"] = al_df["tipo"].apply(lambda x: STAR_ORDER.index(x) if x in STAR_ORDER else 99)
        al_df = al_df.sort_values("_o")
        color_al = [AMBER if "Estrellas" in t else TEAL for t in al_df["tipo"]]
        fig_al = go.Figure(go.Bar(
            x=al_df["tipo"], y=al_df["cantidad"],
            marker_color=color_al,
            text=al_df["cantidad"], textposition="outside",
        ))
        fig_al.update_layout(
            height=320, xaxis_tickangle=45,
            margin=dict(t=10,b=80,l=10,r=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(240,253,250,1)",
            yaxis=dict(gridcolor="#CCFBF1"),
        )
        st.plotly_chart(fig_al, use_container_width=True)

    with col_ev:
        st.markdown("#### Eventos de turismo – tipos")
        ev_df = pd.DataFrame(
            [{"tipo": k, "eventos": v} for k, v in d["eventos_turismo_por_tipo"].items()]
        )
        fig_ev = px.pie(
            ev_df, values="eventos", names="tipo",
            color_discrete_sequence=[TEAL, AMBER],
            hole=0.4,
        )
        fig_ev.update_traces(textposition="outside", textinfo="label+percent+value")
        fig_ev.update_layout(
            height=320, margin=dict(t=10,b=10,l=10,r=10),
            paper_bgcolor="rgba(0,0,0,0)", showlegend=True,
        )
        st.plotly_chart(fig_ev, use_container_width=True)
        st.caption(f"Total eventos registrados: {res['eventos_turismo_total']} (año 2019)")

    st.markdown("---")
    st.markdown("#### Índice de Competitividad Turística Real Multilateral (base 2001=100)")
    comp_df = pd.DataFrame(d["competitividad_turistica"])
    fig_comp = go.Figure(go.Scatter(
        x=comp_df["anio"], y=comp_df["multilateral"],
        mode="lines+markers",
        marker=dict(size=6, color=TEAL),
        line=dict(color=TEAL, width=2),
        fill="tozeroy", fillcolor="rgba(13,148,136,0.08)",
        name="Índice multilateral",
    ))
    fig_comp.add_hline(y=100, line_dash="dash", line_color="#888",
                       annotation_text="Base 2001=100")
    fig_comp.update_layout(
        height=300, yaxis_title="Índice (base 2001=100)",
        margin=dict(t=10,b=10,l=10,r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(240,253,250,1)",
        yaxis=dict(gridcolor="#CCFBF1"),
    )
    st.plotly_chart(fig_comp, use_container_width=True)
    st.caption("Un índice >100 indica mayor competitividad turística respecto a la base 2001. "
               "La devaluación de 2002 y 2018 genera picos. Fuente: Ente de Turismo GCBA")

    st.markdown("---")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown("#### Mapa – alojamientos por tipo")
        m2 = folium.Map(location=[-34.615, -58.437], zoom_start=12, tiles="CartoDB positron")
        AL_COLOR = {"5 Estrellas":"red","4 Estrellas":"orange","3 Estrellas":"beige",
                    "2 Estrellas":"lightgray","1 Estrella":"gray"}
        for a in d["alojamientos"]:
            col_icon = AL_COLOR.get(a["tipo"], "blue")
            folium.CircleMarker(
                location=[a["lat"], a["lon"]], radius=6,
                color=AMBER, fill=True, fill_color=AMBER, fill_opacity=0.75,
                tooltip=f"<b>{a['nombre']}</b><br>{a['tipo']}",
            ).add_to(m2)
        st_folium(m2, width=None, height=380, returned_objects=[], key="tur_aloj_map")

    with col_m2:
        st.markdown("#### Distribución de alojamientos")
        fig_al2 = px.pie(
            al_df.head(8), values="cantidad", names="tipo",
            color_discrete_sequence=px.colors.sequential.Teal,
            hole=0.35,
        )
        fig_al2.update_traces(textposition="inside", textinfo="percent+label")
        fig_al2.update_layout(
            height=380, margin=dict(t=10,b=10,l=10,r=10),
            paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
        )
        st.plotly_chart(fig_al2, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 – Arte & Patrimonio
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    col_mt, col_mb = st.columns(2)

    with col_mt:
        st.markdown("#### Murales por técnica")
        mt_df = pd.DataFrame(
            [{"tecnica": k.title(), "n": v} for k, v in d["murales_por_tecnica"].items()]
        ).sort_values("n", ascending=True)
        fig_mt = go.Figure(go.Bar(
            y=mt_df["tecnica"], x=mt_df["n"], orientation="h",
            marker_color=PURPLE,
            text=mt_df["n"], textposition="outside",
        ))
        fig_mt.update_layout(
            height=320, margin=dict(t=10,b=10,l=10,r=60),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(240,253,250,1)",
            xaxis=dict(gridcolor="#CCFBF1"),
        )
        st.plotly_chart(fig_mt, use_container_width=True)

    with col_mb:
        st.markdown("#### Murales por barrio (top 15)")
        mb_df = pd.DataFrame(
            [{"barrio": k, "murales": v} for k, v in d["murales_por_barrio"].items()]
        ).sort_values("murales", ascending=True)
        fig_mb = go.Figure(go.Bar(
            y=mb_df["barrio"], x=mb_df["murales"], orientation="h",
            marker_color=[PURPLE if v == mb_df["murales"].max() else "#C4B5FD"
                          for v in mb_df["murales"]],
            text=mb_df["murales"], textposition="outside",
        ))
        fig_mb.update_layout(
            height=320, margin=dict(t=10,b=10,l=10,r=60),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(240,253,250,1)",
            xaxis=dict(gridcolor="#CCFBF1"),
        )
        st.plotly_chart(fig_mb, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Mapa de murales (421 obras en edificios de CABA)")
    m3 = folium.Map(location=[-34.615, -58.437], zoom_start=12, tiles="CartoDB positron")
    cluster_mur = MarkerCluster().add_to(m3)
    TECNICA_COLOR = {
        "MURAL CERAMICO": "#7C3AED", "PINTURA MURAL": "#EC4899",
        "FRESCO": "#0D9488", "OLEO S/ TELA": "#F59E0B",
        "BAJORRELIEVE": "#3B82F6", "VITRAUX": "#10B981",
    }
    for mu in d["murales_map"]:
        color = TECNICA_COLOR.get(mu["tecnica"], "#888")
        folium.CircleMarker(
            location=[mu["lat"], mu["lon"]], radius=6,
            color=color, fill=True, fill_color=color, fill_opacity=0.8,
            tooltip=(f"<b>{mu['nombre']}</b><br>"
                     f"{mu['autores']}<br>{mu['tecnica']}<br>"
                     f"{mu['barrio']} · {str(mu['anio']).split('.')[0]}"),
        ).add_to(cluster_mur)
    st_folium(m3, width=None, height=440, returned_objects=[], key="tur_murales_map")
    st.caption("Colores: Violeta=Cerámico · Rosa=Pintura Mural · Teal=Fresco · Naranja=Óleo · "
               "Azul=Bajorrelieve · Verde=Vitraux")

    st.markdown("---")
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.markdown("""
        <div style='background:white;border-radius:10px;padding:16px;border-left:4px solid #7C3AED;'>
        <b style='color:#7C3AED;'>🏛 Museos en CABA</b><br>
        <span style='font-size:2rem;font-weight:700;color:#7C3AED;'>176</span><br>
        Espacios museísticos registrados
        </div>""", unsafe_allow_html=True)
    with col_info2:
        st.markdown(f"""
        <div style='background:white;border-radius:10px;padding:16px;border-left:4px solid {TEAL};'>
        <b style='color:{TEAL};'>🏛 Centros culturales</b><br>
        <span style='font-size:2rem;font-weight:700;color:{TEAL};'>436</span><br>
        Centros culturales activos
        </div>""", unsafe_allow_html=True)
    with col_info3:
        st.markdown("""
        <div style='background:white;border-radius:10px;padding:16px;border-left:4px solid #F59E0B;'>
        <b style='color:#F59E0B;'>🎭 Salas de teatro</b><br>
        <span style='font-size:2rem;font-weight:700;color:#F59E0B;'>311</span><br>
        Salas de teatro registradas
        </div>""", unsafe_allow_html=True)
