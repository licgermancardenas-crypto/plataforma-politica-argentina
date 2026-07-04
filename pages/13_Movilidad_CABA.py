"""
Página 13 – Movilidad & Transporte CABA
Subte · Siniestros Viales · EcoBici
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

st.set_page_config(page_title="Movilidad CABA", page_icon="🚇", layout="wide",
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
.stTabs [aria-selected="true"]     { color:#38BDF8!important; border-bottom:2px solid #0EA5E9!important; }
</style>""", unsafe_allow_html=True)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

@st.cache_data(show_spinner=False)
def load():
    with open(os.path.join(DATA_DIR, "movilidad_caba.json"), encoding="utf-8") as f:
        return json.load(f)

data = load()

df_sv  = pd.DataFrame(data["subte_viajes_por_linea_anio"])
df_tot = pd.DataFrame(data["subte_total_anual"])
df_sin = pd.DataFrame(data["siniestros_anual"])
df_com = pd.DataFrame(data["siniestros_por_comuna"])
df_mod = pd.DataFrame(data["siniestros_por_modo"])
df_hr  = pd.DataFrame(data["siniestros_por_hora"])
eco    = data["ecobici"]

LINEA_COLOR = {"A":"#F59E0B","B":"#EF4444","C":"#3B82F6","D":"#10B981",
               "E":"#8B5CF6","H":"#EC4899"}

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚇 Movilidad CABA")
    st.markdown("<span style='font-size:.73rem;color:#64748B;'>SBASE · DGIT · Min. Transporte</span>", unsafe_allow_html=True)
    st.markdown("---")
    lineas_sel = st.multiselect("Líneas de subte", ["A","B","C","D","E","H"], default=["A","B","C","D","E","H"], key="mov_lineas")
    anio_sub = st.selectbox("Año subte", [2020,2019,2018,2017,2016,2015,2014,2013], key="mov_anio")
    st.markdown("---")
    ultimo = data["subte_ultimo_anio"]
    ranking_filt = [r for r in data["subte_ranking_lineas"] if r["linea"] in lineas_sel]
    total_u = sum(r["total"] for r in ranking_filt) if ranking_filt else 0
    st.markdown(f"<div style='font-size:.65rem;color:#334155;text-transform:uppercase;'>Subte {ultimo}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:1.8rem;font-weight:800;color:#38BDF8;'>{total_u/1e6:.0f}M</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:.6rem;color:#475569;'>viajes totales</div>", unsafe_allow_html=True)
    st.markdown("")
    for r in ranking_filt:
        clr = LINEA_COLOR.get(r["linea"],"#64748B")
        bw  = int(r["pct"])
        st.markdown(
            f"<div style='margin-bottom:5px;'><div style='display:flex;justify-content:space-between;font-size:.73rem;'>"
            f"<span style='color:{clr};font-weight:700;'>Línea {r['linea']}</span>"
            f"<span style='color:{clr};'>{r['total']/1e6:.1f}M · {r['pct']}%</span></div>"
            f"<div style='background:#1E293B;border-radius:3px;height:4px;'>"
            f"<div style='background:{clr};height:4px;width:{bw}%;border-radius:3px;'></div></div></div>",
            unsafe_allow_html=True,
        )
    st.markdown("---")
    sin_tot = df_sin["total"].sum()
    sin_fall = df_sin["fallecidos"].sum()
    st.markdown(f"**Siniestros viales** 2019-2025")
    st.markdown(f"<div style='font-size:1.4rem;font-weight:800;color:#EF4444;'>{sin_tot:,}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:.65rem;color:#475569;'>{sin_fall} fallecidos totales</div>", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#0A1628,#020817);padding:20px 28px;border-radius:12px;
            margin-bottom:20px;border:1px solid #0c2b4a;'>
  <h1 style='color:#fff;margin:0;font-size:1.7rem;'>🚇 Movilidad & Transporte – Ciudad de Buenos Aires</h1>
  <p style='color:#64748B;margin:5px 0 0;font-size:.88rem;'>Subte SBASE · Siniestros Viales · EcoBici · 2013-2025</p>
</div>""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────
eco24 = next(e for e in eco if e["anio"]==2024)
eco22 = next(e for e in eco if e["anio"]==2022)
sin25 = df_sin[df_sin["anio"]==df_sin["anio"].max()].iloc[0] if len(df_sin) else {}
fall25 = int(sin25.get("fallecidos",0)) if len(sin25) else 0

k1,k2,k3,k4,k5 = st.columns(5)
kpis = [
    (k1, f"{total_u/1e6:.0f}M", f"Viajes subte {ultimo}", "#38BDF8", "6 líneas"),
    (k2, "90", "Estaciones de subte", "#3B82F6", "A · B · C · D · E · H"),
    (k3, f"{eco24['total']/1e3:.0f}K", "Usuarios EcoBici 2024", "#4ADE80", f"+{round((eco24['total']-eco22['total'])/eco22['total']*100)}% vs 2022"),
    (k4, f"{int(df_sin['total'].iloc[-1] if len(df_sin) else 0):,}", f"Siniestros {df_sin['anio'].max() if len(df_sin) else ''}", "#F97316", "hechos registrados"),
    (k5, str(fall25), f"Fallecidos {df_sin['anio'].max() if len(df_sin) else ''}", "#EF4444", "víctimas mortales"),
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

tab1, tab2, tab3 = st.tabs(["🚇 Subte", "🚦 Siniestros Viales", "🚲 EcoBici"])

# ══════════════════════════════════════════════════════════════════════
# TAB 1 – SUBTE
# ══════════════════════════════════════════════════════════════════════
with tab1:
    c1, c2 = st.columns([3,2])
    with c1:
        df_sv_filt = df_sv[df_sv["linea"].isin(lineas_sel)] if lineas_sel else df_sv.iloc[0:0]
        fig_sub = px.line(
            df_sv_filt.sort_values(["anio","linea"]),
            x="anio", y="total", color="linea",
            color_discrete_map=LINEA_COLOR,
            markers=True,
            title="Viajes anuales por línea de subte (2013-2024)",
        )
        fig_sub.update_traces(line_width=2.5, marker_size=5)
        fig_sub.add_vrect(x0=2019.5, x1=2021, fillcolor="#EF4444", opacity=0.08,
                          annotation_text="COVID-19", annotation_position="top left",
                          annotation_font_color="#EF4444", annotation_font_size=9)
        fig_sub.add_vline(x=anio_sub, line_dash="dot", line_color="#F59E0B",
                          annotation_text=str(anio_sub), annotation_position="top right",
                          annotation_font_color="#F59E0B", annotation_font_size=9)
        fig_sub.update_layout(
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
            font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B", title="Año", dtick=1),
            yaxis=dict(gridcolor="#1E293B", title="Viajes"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
            title=dict(font=dict(color="#E2E8F0", size=12)),
            margin=dict(t=35,b=5,l=5,r=5), height=380,
        )
        st.plotly_chart(fig_sub, use_container_width=True)

    with c2:
        # Mapa estaciones
        m = folium.Map(location=[-34.615, -58.443], zoom_start=12, tiles=None)
        folium.TileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
                         attr="© CARTO", max_zoom=19).add_to(m)
        for est in data["subte_estaciones"]:
            if not est.get("lat"): continue
            if est["linea"] not in lineas_sel: continue
            clr = LINEA_COLOR.get(est["linea"],"#64748B")
            folium.CircleMarker(
                location=[est["lat"], est["lon"]],
                radius=5, color=clr, fill=True, fill_color=clr, fill_opacity=0.9,
                tooltip=f"<b>{est['nombre']}</b> (Línea {est['linea']})",
            ).add_to(m)
        st_folium(m, height=380, use_container_width=True,
                  returned_objects=[], key="subte_map")

    # Total anual
    fig_tot = go.Figure()
    fig_tot.add_trace(go.Bar(
        x=df_tot["anio"].astype(str), y=df_tot["total"],
        marker_color=["#EF4444" if a in [2020,2021] else "#F59E0B" if a == anio_sub else "#38BDF8" for a in df_tot["anio"]],
        text=(df_tot["total"]/1e6).round(1).astype(str)+"M",
        textposition="outside", textfont=dict(color="#E2E8F0", size=9),
    ))
    fig_tot.update_layout(
        title=dict(text=f"Total viajes subte por año (todas las líneas) — seleccionado: {anio_sub}",font=dict(color="#E2E8F0",size=12)),
        paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
        xaxis=dict(gridcolor="#1E293B"), yaxis=dict(gridcolor="#1E293B",title="Viajes"),
        margin=dict(t=35,b=5,l=5,r=5), height=240, showlegend=False,
    )
    st.plotly_chart(fig_tot, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 2 – SINIESTROS VIALES
# ══════════════════════════════════════════════════════════════════════
with tab2:
    c1, c2 = st.columns(2)
    with c1:
        fig_sin = go.Figure()
        fig_sin.add_trace(go.Bar(x=df_sin["anio"].astype(str), y=df_sin["total"],
                                  name="Total siniestros", marker_color="#F97316",
                                  opacity=0.7))
        fig_sin.add_trace(go.Scatter(x=df_sin["anio"].astype(str), y=df_sin["fallecidos"],
                                      name="Fallecidos", mode="lines+markers",
                                      line=dict(color="#EF4444", width=3),
                                      marker=dict(size=8),
                                      yaxis="y2"))
        fig_sin.update_layout(
            title=dict(text="Siniestros viales anuales y fallecidos",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B", title="Siniestros", side="left"),
            yaxis2=dict(title="Fallecidos", side="right", overlaying="y",
                        gridcolor="#1E293B", showgrid=False),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
            margin=dict(t=35,b=5,l=5,r=5), height=320,
        )
        st.plotly_chart(fig_sin, use_container_width=True)

    with c2:
        # Por modo de desplazamiento
        fig_mod = go.Figure(go.Bar(
            y=df_mod["modo"], x=df_mod["total"], orientation="h",
            marker_color="#F59E0B",
            text=df_mod["total"], textposition="outside", textfont=dict(color="#E2E8F0",size=9),
        ))
        fig_mod.update_layout(
            title=dict(text="Por modo de desplazamiento (total histórico)",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"), yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=35,b=5,l=5,r=50), height=320, showlegend=False,
        )
        st.plotly_chart(fig_mod, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        # Por hora
        fig_hr = go.Figure(go.Bar(
            x=df_hr["hora"], y=df_hr["total"],
            marker_color=["#EF4444" if 7<=h<=10 or 17<=h<=20 else "#334155" for h in df_hr["hora"]],
        ))
        fig_hr.update_layout(
            title=dict(text="Siniestros por hora del día",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B",title="Hora",dtick=2),
            yaxis=dict(gridcolor="#1E293B",title="Total siniestros"),
            margin=dict(t=35,b=5,l=5,r=5), height=280, showlegend=False,
        )
        st.plotly_chart(fig_hr, use_container_width=True)

    with c4:
        # Por commune
        df_com_s = df_com.sort_values("total", ascending=False)
        fig_com = go.Figure(go.Bar(
            x=df_com_s["comuna"].astype(str).apply(lambda x: f"C{int(x):02d}"),
            y=df_com_s["total"],
            marker_color="#F97316",
            text=df_com_s["total"], textposition="outside", textfont=dict(color="#E2E8F0",size=8),
        ))
        fig_com.update_layout(
            title=dict(text="Siniestros por commune (histórico)",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"), yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=35,b=5,l=5,r=5), height=280, showlegend=False,
        )
        st.plotly_chart(fig_com, use_container_width=True)

    # Por sexo y modo (víctimas)
    c5, c6 = st.columns(2)
    with c5:
        vic_sexo = data["victimas_por_sexo"]
        fig_sx = go.Figure(go.Pie(
            labels=list(vic_sexo.keys()), values=list(vic_sexo.values()),
            hole=0.55, marker_colors=["#3B82F6","#EC4899","#64748B"],
        ))
        fig_sx.update_layout(
            title=dict(text="Víctimas por sexo (último año)",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            margin=dict(t=35,b=5,l=5,r=5), height=280, showlegend=True,
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9)),
        )
        st.plotly_chart(fig_sx, use_container_width=True)

    with c6:
        vic_modo = data["victimas_por_modo"]
        fig_vm = go.Figure(go.Bar(
            y=list(vic_modo.keys()), x=list(vic_modo.values()),
            orientation="h", marker_color="#EF4444",
            text=list(vic_modo.values()), textposition="outside",
            textfont=dict(color="#E2E8F0",size=9),
        ))
        fig_vm.update_layout(
            title=dict(text="Víctimas por modo (último año)",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"), yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=35,b=5,l=5,r=50), height=280, showlegend=False,
        )
        st.plotly_chart(fig_vm, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 3 – ECOBICI
# ══════════════════════════════════════════════════════════════════════
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        fig_eco = go.Figure(go.Bar(
            x=[str(e["anio"]) for e in eco],
            y=[e["total"] for e in eco],
            marker_color=["#4ADE80","#22C55E","#16A34A"],
            text=[f"{e['total']/1e3:.0f}K" for e in eco],
            textposition="outside", textfont=dict(color="#E2E8F0",size=13),
        ))
        fig_eco.update_layout(
            title=dict(text="Usuarios nuevos EcoBici por año",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B", range=[0, max(e["total"] for e in eco)*1.2]),
            margin=dict(t=35,b=5,l=5,r=5), height=320, showlegend=False,
        )
        st.plotly_chart(fig_eco, use_container_width=True)

    with c2:
        # Distribución por género (último año)
        eco_l = eco[-1]
        gen   = eco_l.get("por_genero",{})
        gen_lbl_map = {"MALE":"Masculino","FEMALE":"Femenino","OTHER":"Otro","M":"Masculino","F":"Femenino"}
        gen_clean = {gen_lbl_map.get(k,k): v for k,v in gen.items()}
        fig_gen = go.Figure(go.Pie(
            labels=list(gen_clean.keys()), values=list(gen_clean.values()),
            hole=0.55, marker_colors=["#3B82F6","#EC4899","#64748B","#F59E0B"],
        ))
        fig_gen.update_layout(
            title=dict(text=f"Por género · {eco_l['anio']}",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
            margin=dict(t=35,b=5,l=5,r=5), height=320,
            annotations=[dict(text=f"Edad prom.<br>{eco_l.get('edad_prom',0)}",x=0.5,y=0.5,
                              font=dict(size=12,color="#E2E8F0"),showarrow=False)],
        )
        st.plotly_chart(fig_gen, use_container_width=True)

    # Distribución de edades
    edad_dist = eco_l.get("edad_dist", {})
    if edad_dist:
        fig_edad = go.Figure(go.Bar(
            x=list(edad_dist.keys()), y=list(edad_dist.values()),
            marker_color="#4ADE80",
            text=list(edad_dist.values()), textposition="outside",
            textfont=dict(color="#E2E8F0",size=10),
        ))
        fig_edad.update_layout(
            title=dict(text=f"Distribución por edad · EcoBici {eco_l['anio']}",font=dict(color="#E2E8F0",size=12)),
            paper_bgcolor="#0A1628", plot_bgcolor="#0A1628", font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="#1E293B",title="Rango etario"),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(t=35,b=5,l=5,r=5), height=260, showlegend=False,
        )
        st.plotly_chart(fig_edad, use_container_width=True)

st.markdown("---")
st.caption("Fuente: SBASE (viajes subte 2013-2024) · DGIT/Min. Transporte (siniestros viales 2019-2025) · "
           "Min. Transporte (EcoBici 2022-2024) · Gobierno de la Ciudad de Buenos Aires.")
