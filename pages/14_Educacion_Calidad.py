"""
Página 14 – Educación & Calidad de Vida CABA
Matrícula 2024 · Mercado Laboral · Espacios Verdes · Hospitales
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

st.set_page_config(page_title="Educación & Calidad CABA", page_icon="📚", layout="wide",
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
.stTabs [aria-selected="true"]     { color:#86EFAC!important; border-bottom:2px solid #4ADE80!important; }
</style>""", unsafe_allow_html=True)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

@st.cache_data(show_spinner=False)
def load():
    with open(os.path.join(DATA_DIR, "educacion_calidad_caba.json"), encoding="utf-8") as f:
        return json.load(f)

data = load()
df_mat   = pd.DataFrame(data["matricula_por_zona_sector"])
df_niv   = pd.DataFrame(data["matricula_por_nivel"])
df_ml    = pd.DataFrame(data["mercado_laboral"])
df_ev    = pd.DataFrame(data["espacios_verdes_por_comuna"])
df_evs   = pd.DataFrame(data["espacios_verdes_serie"])
hosp     = data["hospitales_publicos"]
cs       = data["centros_salud_privados"]

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📚 Educación & Calidad")
    st.markdown("<span style='font-size:.73rem;color:#64748B;'>Min. Educación · DGEyC · IVC · Min. Salud</span>", unsafe_allow_html=True)
    st.markdown("---")
    sector_edu = st.radio("Sector educativo", ["Todos", "Estatal", "Privado"], key="edu_sector")
    anio_ml = st.selectbox("Año mercado laboral", list(range(2023, 2006, -1)), key="edu_anio_ml")
    tipo_salud = st.radio("Centros de salud en mapa", ["Públicos", "Privados", "Ambos"], key="edu_salud")
    st.markdown("---")
    # KPI matrícula
    total = data["matricula_total"]
    pct_e = data["matricula_pct_estatal"]
    st.markdown(f"<div style='font-size:.62rem;color:#334155;text-transform:uppercase;'>Matrícula 2024</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:1.8rem;font-weight:800;color:#86EFAC;'>{total//1000}K</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:.65rem;color:#475569;'>alumnos en CABA</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='margin-top:8px;font-size:.7rem;color:#94A3B8;'>Estatal: <b style='color:#4ADE80;'>{pct_e}%</b> · Privado: <b style='color:#FBBF24;'>{100-pct_e}%</b></div>", unsafe_allow_html=True)
    st.markdown("---")
    # Mercado laboral último
    ml_ult = df_ml.dropna(subset=["desocupacion"]).iloc[-1] if len(df_ml) else {}
    if len(ml_ult):
        st.markdown(f"**Mercado Laboral {int(ml_ult['anio'])}**")
        for lbl, key, clr in [("Actividad","actividad","#38BDF8"),("Empleo","empleo","#4ADE80"),
                               ("Desocupación","desocupacion","#EF4444"),("Subocupación","subocupacion","#F59E0B")]:
            v = ml_ult.get(key)
            if v:
                st.markdown(f"<div style='display:flex;justify-content:space-between;font-size:.72rem;'>"
                            f"<span style='color:#94A3B8;'>{lbl}</span>"
                            f"<span style='color:{clr};font-weight:700;'>{v:.1f}%</span></div>",
                            unsafe_allow_html=True)
    st.markdown("---")
    # Espacios verdes
    ev_min = df_ev.nsmallest(1,"m2_por_hab").iloc[0] if len(df_ev) else {}
    ev_max = df_ev.nlargest(1,"m2_por_hab").iloc[0] if len(df_ev) else {}
    if len(ev_min):
        st.markdown("**Espacios verdes/hab.**")
        st.markdown(f"<div style='font-size:.72rem;color:#4ADE80;'>Más verde: C{int(ev_max['comuna']):02d} — {ev_max['m2_por_hab']} m²</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:.72rem;color:#EF4444;'>Menos verde: C{int(ev_min['comuna']):02d} — {ev_min['m2_por_hab']} m²</div>", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#0A1628,#021205);padding:20px 28px;border-radius:12px;
            margin-bottom:20px;border:1px solid #0a2b0a;'>
  <h1 style='color:#fff;margin:0;font-size:1.7rem;'>📚 Educación & Calidad de Vida – Ciudad de Buenos Aires</h1>
  <p style='color:#64748B;margin:5px 0 0;font-size:.88rem;'>Matrícula 2024 · Mercado Laboral · Espacios Verdes · Infraestructura de Salud</p>
</div>""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────
ml_ult = df_ml.dropna(subset=["desocupacion"]).iloc[-1] if len(df_ml) else pd.Series()
ev_prom = df_ev["m2_por_hab"].mean() if len(df_ev) else 0

k1,k2,k3,k4,k5,k6 = st.columns(6)
kpis = [
    (k1, f"{data['matricula_total']//1000}K",  "Alumnos 2024",          "#86EFAC", "en escuelas CABA"),
    (k2, f"{data['matricula_pct_estatal']}%",  "Escuela estatal",        "#4ADE80", f"{100-data['matricula_pct_estatal']}% privada"),
    (k3, f"{ml_ult.get('desocupacion','—')}%" if len(ml_ult) else "—", "Desocupación",  "#EF4444", f"año {int(ml_ult.get('anio',0)) if len(ml_ult) else ''}"),
    (k4, f"{ev_prom:.2f}", "m² verde/hab. prom.", "#22C55E", "promedio 15 comunas"),
    (k5, str(len(hosp)),   "Hospitales públicos",  "#38BDF8", "Ministerio de Salud GCBA"),
    (k6, str(len(cs)),     "Centros salud priv.",  "#A78BFA", "habilitados GCBA"),
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

tab1, tab2, tab3, tab4 = st.tabs(["📖 Educación", "💼 Mercado Laboral", "🌳 Espacios Verdes", "🏥 Salud"])

# ══════════════════════════════════════════════════════════════════════
# TAB 1 – EDUCACIÓN
# ══════════════════════════════════════════════════════════════════════
with tab1:
    df_mat_filt = df_mat if sector_edu == "Todos" else df_mat[df_mat["sector"] == sector_edu]
    df_niv_filt = df_niv if sector_edu == "Todos" else df_niv[df_niv["sector"] == sector_edu]
    c1, c2 = st.columns(2)
    with c1:
        # Matrícula por zona y sector
        fig_mat = px.bar(
            df_mat_filt.sort_values("alumnos", ascending=False),
            x="zona", y="alumnos", color="sector",
            barmode="group",
            color_discrete_map={"Estatal":"#4ADE80","Privado":"#FBBF24"},
            text="alumnos",
        )
        fig_mat.update_traces(texttemplate="%{text:,.0f}", textposition="outside",
                              textfont_size=9)
        fig_mat.update_layout(
            title=dict(text="Matrícula 2024 por zona y sector",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B", title="Alumnos"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            margin=dict(t=35,b=5,l=5,r=5), height=340,
        )
        st.plotly_chart(fig_mat, use_container_width=True)

    with c2:
        # Por nivel educativo
        df_niv_agg = df_niv_filt.groupby("nivel").agg(alumnos=("alumnos","sum"),unidades=("unidades","sum")).reset_index()
        fig_niv = go.Figure(go.Pie(
            labels=df_niv_agg["nivel"], values=df_niv_agg["alumnos"],
            hole=0.5, marker_colors=["#38BDF8","#4ADE80","#FBBF24","#F97316","#C084FC"],
            textinfo="label+percent",
        ))
        fig_niv.update_layout(
            title=dict(text="Alumnos por nivel educativo",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(size=9)),
            margin=dict(t=35,b=5,l=5,r=5), height=340,
        )
        st.plotly_chart(fig_niv, use_container_width=True)

    # Repitencia por zona
    st.markdown("#### Tasa de repitencia por zona y sector (%)")
    df_rep = df_mat_filt[df_mat_filt["repitencia_pct"]>0].copy()
    fig_rep = go.Figure(go.Bar(
        x=df_rep.apply(lambda r: f"{r.zona} {r.sector[:4]}.", axis=1),
        y=df_rep["repitencia_pct"],
        marker_color=["#EF4444" if r>3 else "#F59E0B" if r>1.5 else "#4ADE80"
                      for r in df_rep["repitencia_pct"]],
        text=df_rep["repitencia_pct"].apply(lambda x: f"{x:.2f}%"),
        textposition="outside", textfont=dict(color="#E2E8F0",size=9),
    ))
    fig_rep.update_layout(
        paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
        xaxis=dict(gridcolor="#1E293B"), yaxis=dict(gridcolor="#1E293B",title="%"),
        margin=dict(t=10,b=5,l=5,r=5), height=240, showlegend=False,
    )
    st.plotly_chart(fig_rep, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 2 – MERCADO LABORAL
# ══════════════════════════════════════════════════════════════════════
with tab2:
    c1, c2 = st.columns(2)
    with c1:
        # Tasas históricas
        fig_ml = go.Figure()
        for col, nm, clr in [("actividad","Actividad","#38BDF8"),
                              ("empleo","Empleo","#4ADE80"),
                              ("desocupacion","Desocupación","#EF4444"),
                              ("subocupacion","Subocupación","#F59E0B")]:
            df_v = df_ml.dropna(subset=[col])
            fig_ml.add_trace(go.Scatter(
                x=df_v["anio"].astype(str), y=df_v[col],
                name=nm, mode="lines+markers",
                line=dict(color=clr, width=2.5), marker=dict(size=5),
            ))
        fig_ml.add_vline(x=str(anio_ml), line_dash="dash", line_color="#F59E0B",
                         annotation_text=str(anio_ml), annotation_position="top right",
                         annotation_font_color="#F59E0B", annotation_font_size=10)
        fig_ml.update_layout(
            title=dict(text="Tasas del mercado laboral CABA (2003-2019)",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B", title="Año", tickangle=45),
            yaxis=dict(gridcolor="#1E293B", title="%"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
            margin=dict(t=35,b=5,l=5,r=5), height=380,
        )
        st.plotly_chart(fig_ml, use_container_width=True)

    with c2:
        # Brecha de género en desocupación
        df_des = df_ml.dropna(subset=["des_masc","des_fem"]).copy()
        fig_brc = go.Figure()
        fig_brc.add_trace(go.Scatter(x=df_des["anio"].astype(str), y=df_des["des_masc"],
                                     name="Masculino", mode="lines+markers",
                                     line=dict(color="#3B82F6",width=2.5), marker=dict(size=5)))
        fig_brc.add_trace(go.Scatter(x=df_des["anio"].astype(str), y=df_des["des_fem"],
                                     name="Femenino", mode="lines+markers",
                                     line=dict(color="#EC4899",width=2.5), marker=dict(size=5)))
        fig_brc.add_trace(go.Scatter(
            x=list(df_des["anio"].astype(str))+list(reversed(df_des["anio"].astype(str))),
            y=list(df_des["des_fem"])+list(reversed(df_des["des_masc"])),
            fill="toself", fillcolor="rgba(236,72,153,0.08)", line_color="rgba(0,0,0,0)",
            showlegend=False,
        ))
        fig_brc.update_layout(
            title=dict(text="Brecha de género en desocupación",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B", tickangle=45),
            yaxis=dict(gridcolor="#1E293B", title="Tasa desocupación %"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
            margin=dict(t=35,b=5,l=5,r=5), height=380,
        )
        st.plotly_chart(fig_brc, use_container_width=True)

    # Tabla resumen
    st.markdown("#### Datos completos – Mercado Laboral")
    df_show = df_ml[["anio","actividad","empleo","desocupacion","subocupacion"]].tail(10)
    df_show.columns = ["Año","Tasa actividad","Tasa empleo","Tasa desocupación","Tasa subocupación"]
    st.dataframe(df_show.style.format({c:"{:.1f}%" for c in df_show.columns if c!="Año"},na_rep="—"),
                 use_container_width=True, hide_index=True, height=300)

# ══════════════════════════════════════════════════════════════════════
# TAB 3 – ESPACIOS VERDES
# ══════════════════════════════════════════════════════════════════════
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        df_ev_s = df_ev.sort_values("m2_por_hab", ascending=True)
        media_ev = df_ev["m2_por_hab"].mean()
        colors_ev = ["#4ADE80" if v >= media_ev else "#EF4444" for v in df_ev_s["m2_por_hab"]]
        fig_ev = go.Figure(go.Bar(
            y=df_ev_s["comuna"].apply(lambda c: f"C{int(c):02d}"),
            x=df_ev_s["m2_por_hab"], orientation="h",
            marker_color=colors_ev,
            text=df_ev_s["m2_por_hab"].apply(lambda x: f"{x:.2f}"),
            textposition="outside", textfont=dict(color="#E2E8F0",size=9),
        ))
        fig_ev.add_vline(x=media_ev, line_dash="dot", line_color="#64748B",
                         annotation_text=f"Media: {media_ev:.2f} m²",
                         annotation_font_color="#64748B", annotation_font_size=9)
        fig_ev.update_layout(
            title=dict(text="Espacios verdes por habitante (m²/hab)",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B", range=[0, df_ev_s["m2_por_hab"].max()*1.15]),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=35,b=5,l=5,r=55), height=420, showlegend=False,
        )
        st.plotly_chart(fig_ev, use_container_width=True)

    with c2:
        # Serie histórica CABA total
        fig_evs = go.Figure(go.Scatter(
            x=df_evs["anio"].astype(str), y=df_evs["m2_por_hab"],
            mode="lines+markers",
            line=dict(color="#4ADE80", width=3), marker=dict(size=7),
            fill="tozeroy", fillcolor="rgba(74,222,128,0.08)",
        ))
        fig_evs.update_layout(
            title=dict(text="Evolución m² de espacios verdes/hab · CABA total",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B", title="Año"),
            yaxis=dict(gridcolor="#1E293B", title="m²/hab"),
            margin=dict(t=35,b=5,l=5,r=5), height=420, showlegend=False,
        )
        st.plotly_chart(fig_evs, use_container_width=True)

    # Info
    st.info("💡 La OMS recomienda un mínimo de **9 m² de espacio verde por habitante**. "
            f"Solo {sum(1 for r in df_ev.itertuples() if r.m2_por_hab >= 9)} de las 15 comunas superan ese umbral. "
            f"La commune con mayor déficit es C{int(df_ev.nsmallest(1,'m2_por_hab').iloc[0]['comuna']):02d}.")

# ══════════════════════════════════════════════════════════════════════
# TAB 4 – SALUD / HOSPITALES
# ══════════════════════════════════════════════════════════════════════
with tab4:
    col_map, col_list = st.columns([3, 2])
    with col_map:
        m = folium.Map(location=[-34.615, -58.443], zoom_start=12, tiles=None)
        folium.TileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
                         attr="© CARTO", max_zoom=19).add_to(m)

        # Hospitales públicos (sin coords exactas — usar marker por barrio)
        # Marcar los que tenemos con posición aproximada conocida
        hosp_geo = {
            "Garrahan": (-34.636, -58.373), "Udaondo": (-34.635, -58.393),
            "Fernández": (-34.574, -58.406), "Durand": (-34.610, -58.432),
            "Argerich": (-34.632, -58.358), "Muñiz": (-34.607, -58.407),
            "Piñero": (-34.627, -58.437), "Rivadavia": (-34.621, -58.459),
            "Santojanni": (-34.659, -58.504), "Alvarez": (-34.639, -58.468),
        }
        if tipo_salud in ["Públicos", "Ambos"]:
            for h in hosp:
                nom = h["nombre"]
                # Buscar match parcial
                coords = None
                for k, v in hosp_geo.items():
                    if k.lower() in nom.lower():
                        coords = v; break
                com = h.get("comuna")
                if coords:
                    folium.Marker(
                        location=coords,
                        icon=folium.Icon(color="red", icon="plus-sign", prefix="glyphicon"),
                        tooltip=f"<b>🏥 {nom}</b><br>{h.get('tipo','')}<br>{h.get('direccion','')}<br>C{int(com):02d}" if com else f"<b>🏥 {nom}</b>",
                    ).add_to(m)

        # Centros privados con coords reales
        if tipo_salud in ["Privados", "Ambos"]:
            for c_s in cs:
                if not c_s.get("lat"): continue
                try:
                    folium.CircleMarker(
                        location=[c_s["lat"], c_s["lon"]],
                        radius=5, color="#A78BFA", fill=True, fill_color="#A78BFA", fill_opacity=0.8,
                        tooltip=f"<b>🏨 {c_s.get('nombre','')}</b><br>{c_s.get('barrio','')}<br>C{int(c_s['comuna']):02d}" if c_s.get('comuna') else f"<b>{c_s.get('nombre','')}</b>",
                    ).add_to(m)
                except: pass

        st_folium(m, height=480, use_container_width=True,
                  returned_objects=[], key="salud_map")

        st.markdown(
            "<div style='font-size:.65rem;color:#334155;'>"
            "🔴 Hospitales públicos GCBA &nbsp;&nbsp; 🟣 Centros de salud privados habilitados</div>",
            unsafe_allow_html=True,
        )

    with col_list:
        st.markdown("#### Hospitales públicos GCBA")
        hosp_by_com = {}
        for h in hosp:
            c_ = h.get("comuna") or 0
            hosp_by_com.setdefault(c_, []).append(h)
        for com_n in sorted(hosp_by_com.keys()):
            hs = hosp_by_com[com_n]
            clr = "#38BDF8"
            lbl = f"C{int(com_n):02d}" if com_n else "Sin commune"
            for h in hs:
                esp = h.get("especialidad","")[:25] if h.get("especialidad") else ""
                st.markdown(
                    f"<div style='margin-bottom:5px;padding:6px 10px;background:#0A1628;"
                    f"border:1px solid #1E293B;border-radius:6px;'>"
                    f"<div style='font-size:.73rem;font-weight:600;color:{clr};'>{h['nombre'][:38]}</div>"
                    f"<div style='font-size:.62rem;color:#475569;'>{h.get('tipo','')} · {lbl}</div>"
                    f"<div style='font-size:.6rem;color:#334155;'>{h.get('direccion','')} {('· '+esp) if esp else ''}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

st.markdown("---")
st.caption("Fuente: Ministerio de Educación GCBA · Matrícula 2024. "
           "DGEyC – Encuesta Anual de Hogares (Mercado Laboral 2003-2019). "
           "IVC – Espacios verdes por habitante por commune. "
           "Ministerio de Salud GCBA – Hospitales y centros privados habilitados.")
