"""
Género & Violencia CABA – Página 18
Fuentes: Sec. Igualdad de Género · DGEyC · Dirección Gral. de la Mujer · OVD CSJN
"""
import json, os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import loader
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Género & Violencia CABA", page_icon="♀", layout="wide")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@st.cache_data
def load():
    with open(os.path.join(BASE, "data", "genero_violencia_caba.json"), encoding="utf-8") as f:
        return json.load(f)



d   = load()
geo = loader.get_comunas_geojson()

PINK   = "#EC4899"
ROSE   = "#BE185D"
LIGHT  = "#FCE7F3"
PURPLE = "#7C3AED"

st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#FFF0F6;}
[data-testid="stSidebar"]{background:#1A0010;}
[data-testid="stSidebar"] *{color:#fff!important;}
</style>""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#831843,#BE185D);
     padding:24px 32px;border-radius:12px;margin-bottom:20px;'>
  <h1 style='color:white;margin:0;font-size:1.8rem;'>♀ Género & Violencia CABA</h1>
  <p style='color:#FBCFE8;margin:4px 0 0;font-size:.9rem;'>
    Violencia doméstica · Femicidios · Línea 144 · Brecha salarial · Estado del GCBA
  </p>
</div>""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────────
res = d["resumen"]
k1, k2, k3, k4, k5 = st.columns(5)

def kpi(col, val, label, color, sublabel=""):
    col.markdown(f"""
    <div style='background:white;border-radius:10px;padding:16px 20px;
         border-left:5px solid {color};box-shadow:0 2px 6px rgba(0,0,0,.08);'>
      <p style='margin:0;font-size:.78rem;color:#666;text-transform:uppercase;letter-spacing:.5px;'>{label}</p>
      <p style='margin:2px 0;font-size:1.8rem;font-weight:700;color:{color};'>{val}</p>
      <p style='margin:0;font-size:.75rem;color:#999;'>{sublabel}</p>
    </div>""", unsafe_allow_html=True)

kpi(k1, str(res["femicidios_ultimo"]),
    f"Femicidios ({res['femicidios_ultimo_anio']})", "#DC2626",
    f"Tasa {res['femicidios_tasa_ultima']} c/100k mujeres")
kpi(k2, f"{res['l144_llamadas']:,}".replace(",","."),
    "Llamadas Línea 144", PINK, f"{res['l144_casos']:,} casos atendidos".replace(",","."))
kpi(k3, f"{res['ovd_ultimo']:,}".replace(",","."),
    f"Casos OVD ({res['ovd_ultimo_anio']})", "#7C3AED", "Oficina Violencia Doméstica CSJN")
kpi(k4, f"{abs(res['brecha_ultima']):.0f}%",
    f"Brecha salarial ({res['brecha_anio']})", "#F59E0B",
    "Las mujeres ganan menos en occ. principal")
kpi(k5, str(d.get("comisarias_total", "–")),
    "Unidades género en comisarías", "#0EA5E9", "División Protección Familiar")

st.markdown("<br>", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ♀ Género & Violencia")
    st.markdown("---")
    st.markdown("**Femicidios en CABA**")
    for r in d["femicidios_victimas"][-5:]:
        color = "#EF4444" if r["victimas"] >= 13 else "#F59E0B" if r["victimas"] >= 9 else "#10B981"
        st.markdown(f"<div style='display:flex;justify-content:space-between;font-size:.85rem;'>"
                    f"<span>{r['anio']}</span>"
                    f"<b style='color:{color};'>{r['victimas']} víctimas</b></div>",
                    unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Tipo de violencia (Línea 144)**")
    for r in d["l144_tipo_violencia"]:
        pct = r["casos"] / d["l144_total_casos"] * 100
        st.markdown(f"<div style='margin-bottom:5px;font-size:.82rem;'>"
                    f"<div style='display:flex;justify-content:space-between;'>"
                    f"<span>{r['tipo']}</span><b>{r['casos']:,}</b></div>"
                    f"<div style='background:#FCE7F3;border-radius:3px;height:5px;'>"
                    f"<div style='width:{pct:.0f}%;background:{PINK};height:5px;border-radius:3px;'></div>"
                    f"</div></div>",
                    unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Modalidad de violencia**")
    for r in d["l144_modalidad"]:
        st.markdown(f"<div style='font-size:.82rem;display:flex;justify-content:space-between;'>"
                    f"<span>{r['modalidad']}</span><b>{r['casos']:,}</b></div>",
                    unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Filtros temporales**")
    anio_desde = st.selectbox("Desde año", list(range(2009, 2024)), index=0, key="gv_desde")
    anio_hasta = st.selectbox("Hasta año", list(range(2009, 2024)), index=13, key="gv_hasta")
    tipos_viol_sel = st.multiselect("Tipos de violencia (L144)", ["Física","Psicológica","Sexual","Económica","Simbólica"], default=["Física","Psicológica","Sexual","Económica"], key="gv_tipos")

tab1, tab2, tab3, tab4 = st.tabs([
    "📞 Línea 144 & Atención",
    "⚠️ Femicidios & Violencia",
    "💰 Brecha Salarial",
    "🏛 Estado & Recursos",
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 – Línea 144 & Atención
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.markdown("#### Llamadas y casos atendidos por mes (último año disponible)")
        meses_order = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                       "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
        ll_mes = d["l144_llamadas_mes"]
        meses_valid = [m for m in meses_order if m in ll_mes or m+" " in ll_mes]
        ll_data = {m: ll_mes.get(m, ll_mes.get(m+" ", {"llamadas":0,"casos":0})) for m in meses_order if m in ll_mes or m+" " in ll_mes}
        mes_names = list(ll_data.keys())
        llamadas = [ll_data[m]["llamadas"] for m in mes_names]
        casos = [ll_data[m]["casos"] for m in mes_names]
        fig_ll = go.Figure()
        fig_ll.add_trace(go.Bar(x=[m[:3] for m in mes_names], y=llamadas, name="Llamadas",
                                marker_color="#FBCFE8", text=llamadas, textposition="outside"))
        fig_ll.add_trace(go.Bar(x=[m[:3] for m in mes_names], y=casos, name="Casos",
                                marker_color=PINK, text=casos, textposition="outside"))
        fig_ll.update_layout(
            barmode="group", height=320,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,240,246,1)",
            yaxis=dict(gridcolor="#FCE7F3"),
            legend=dict(orientation="h"),
        )
        st.plotly_chart(fig_ll, use_container_width=True)

    with col_r:
        st.markdown("#### Vínculos del agresor con la víctima")
        vinc = pd.DataFrame(d["l144_vinculo"]).sort_values("cantidad", ascending=True)
        fig_vinc = go.Figure(go.Bar(
            y=vinc["vinculo"], x=vinc["cantidad"], orientation="h",
            marker_color=[PINK if i == len(vinc)-1 else "#FBCFE8" for i in range(len(vinc))],
            text=vinc["cantidad"], textposition="outside",
        ))
        fig_vinc.update_layout(
            height=320, margin=dict(t=10, b=10, l=10, r=60),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,240,246,1)",
            xaxis=dict(gridcolor="#FCE7F3"),
        )
        st.plotly_chart(fig_vinc, use_container_width=True)

    st.markdown("---")
    col_e, col_m = st.columns(2)

    with col_e:
        st.markdown("#### Casos Línea 144 por grupo etario de la víctima")
        edad_df = pd.DataFrame(d["l144_por_edad"])
        fig_e = px.bar(
            edad_df, x="pct", y="grupo", orientation="h",
            color="pct", color_continuous_scale="RdPu",
            text=[f"{v:.1f}%" for v in edad_df["pct"]],
            labels={"pct": "%", "grupo": "Edad"},
        )
        fig_e.update_traces(textposition="outside")
        fig_e.update_layout(
            height=280, showlegend=False, coloraxis_showscale=False,
            margin=dict(t=10, b=10, l=10, r=60),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_e, use_container_width=True)

    with col_m:
        st.markdown("#### Tipo de violencia (Línea 144)")
        tv_df = pd.DataFrame(d["l144_tipo_violencia"])
        if tipos_viol_sel:
            tv_df = tv_df[tv_df["tipo"].apply(lambda t: any(s in t for s in tipos_viol_sel))]
        fig_tv = px.pie(
            tv_df, values="casos", names="tipo",
            color_discrete_sequence=["#BE185D","#EC4899","#F472B6","#FBCFE8","#FDF2F8"],
            hole=0.4,
        )
        fig_tv.update_traces(textposition="inside", textinfo="percent+label")
        fig_tv.update_layout(
            height=280, margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
        )
        st.plotly_chart(fig_tv, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Casos OVD y CIM por año (2009-2023)")
    casos_df = pd.DataFrame(d["casos_atencion_anual"])
    casos_df = casos_df[(casos_df["anio"] >= anio_desde) & (casos_df["anio"] <= anio_hasta)]
    fig_ca = go.Figure()
    fig_ca.add_trace(go.Bar(x=casos_df["anio"], y=casos_df["ovd"], name="OVD (CSJN)",
                            marker_color="#7C3AED",
                            text=casos_df["ovd"].apply(lambda v: f"{int(v):,}" if v else ""),
                            textposition="outside"))
    fig_ca.add_trace(go.Bar(x=casos_df["anio"], y=casos_df["cim"], name="CIM (GCBA)",
                            marker_color=PINK,
                            text=casos_df["cim"].apply(lambda v: f"{int(v):,}" if v else ""),
                            textposition="outside"))
    fig_ca.add_vrect(x0=2019.5, x1=2020.5, fillcolor="rgba(239,68,68,.1)", layer="below",
                     line_width=0, annotation_text="COVID", annotation_position="top left")
    fig_ca.update_layout(
        barmode="group", height=320,
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,240,246,1)",
        yaxis=dict(gridcolor="#FCE7F3"),
        xaxis=dict(tickmode="linear", dtick=1),
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig_ca, use_container_width=True)
    st.caption("OVD: Oficina de Violencia Doméstica de la CSJN · CIM: Centros Integrales de la Mujer GCBA")

    st.markdown("---")
    col_c, col_cim = st.columns(2)
    with col_c:
        st.markdown("#### Casos Línea 144 por comuna")
        l144_com = pd.DataFrame(d["l144_por_comuna"]).sort_values("casos", ascending=True)
        fig_lc = go.Figure(go.Bar(
            y=[f"C{c}" for c in l144_com["comuna"]], x=l144_com["casos"],
            orientation="h", marker_color=PINK,
            text=l144_com["casos"], textposition="outside",
        ))
        fig_lc.update_layout(
            height=380, margin=dict(t=10, b=10, l=40, r=60),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,240,246,1)",
            xaxis=dict(gridcolor="#FCE7F3"),
        )
        st.plotly_chart(fig_lc, use_container_width=True)

    with col_cim:
        st.markdown(f"#### CIM: víctimas asistidas por edad ({d['cim_ultimo_anio']})")
        cim_e = pd.DataFrame(d["cim_por_edad"])
        fig_cim = px.bar(
            cim_e, x="mujeres", y="grupo", orientation="h",
            color="mujeres", color_continuous_scale="RdPu",
            text="mujeres",
            labels={"mujeres": "Mujeres", "grupo": ""},
        )
        fig_cim.update_traces(textposition="outside")
        fig_cim.update_layout(
            height=380, showlegend=False, coloraxis_showscale=False,
            margin=dict(t=10, b=10, l=10, r=60),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_cim, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 – Femicidios & Violencia
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    col_fv, col_ft = st.columns(2)

    with col_fv:
        st.markdown("#### Víctimas de femicidio por año (CABA)")
        fv_df = pd.DataFrame(d["femicidios_victimas"])
        fv_df = fv_df[(fv_df["anio"] >= anio_desde) & (fv_df["anio"] <= anio_hasta)]
        colors = ["#DC2626" if v >= 13 else "#F59E0B" if v >= 9 else "#FBCFE8"
                  for v in fv_df["victimas"]]
        fig_fv = go.Figure(go.Bar(
            x=fv_df["anio"], y=fv_df["victimas"],
            marker_color=colors,
            text=fv_df["victimas"], textposition="outside",
        ))
        fig_fv.update_layout(
            height=320,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,240,246,1)",
            yaxis=dict(gridcolor="#FCE7F3"),
            xaxis=dict(tickmode="linear", dtick=1),
        )
        st.plotly_chart(fig_fv, use_container_width=True)

    with col_ft:
        st.markdown("#### Tasa de femicidio (c/100.000 mujeres)")
        ft_df = pd.DataFrame(d["femicidios_tasa"])
        ft_df = ft_df[(ft_df["anio"] >= anio_desde) & (ft_df["anio"] <= anio_hasta)]
        fig_ft = go.Figure(go.Scatter(
            x=ft_df["anio"], y=ft_df["tasa"],
            mode="lines+markers+text",
            text=[f"{v}" for v in ft_df["tasa"]],
            textposition="top center",
            marker=dict(size=9, color="#DC2626"),
            line=dict(color="#DC2626", width=2),
            fill="tozeroy",
            fillcolor="rgba(220,38,38,0.08)",
        ))
        fig_ft.update_layout(
            height=320, yaxis_title="Tasa c/100k mujeres",
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,240,246,1)",
            yaxis=dict(gridcolor="#FCE7F3"),
        )
        st.plotly_chart(fig_ft, use_container_width=True)

    st.markdown("---")
    col_vp, col_cp = st.columns(2)

    with col_vp:
        st.markdown("#### Violencia de pareja: tipos por año")
        if d.get("viol_pareja_tipo"):
            vp_df = pd.DataFrame(d["viol_pareja_tipo"])
            vp_df = vp_df[(vp_df["anio"] >= anio_desde) & (vp_df["anio"] <= anio_hasta)]
            TIPO_COLORS = {"Psicológica":"#7C3AED","Física":"#DC2626","Sexual":"#F59E0B","Económica":"#10B981"}
            fig_vp = px.bar(
                vp_df, x="anio", y="casos", color="tipo",
                barmode="group",
                color_discrete_map=TIPO_COLORS,
                labels={"anio":"Año","casos":"Casos","tipo":"Tipo"},
            )
            fig_vp.update_layout(
                height=300, margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,240,246,1)",
                yaxis=dict(gridcolor="#FCE7F3"),
                legend=dict(orientation="h", y=-0.3),
            )
            st.plotly_chart(fig_vp, use_container_width=True)
        else:
            st.info("Datos de violencia de pareja no disponibles")

    with col_cp:
        st.markdown("#### Casos penales con indicadores de violencia de género")
        if d.get("casos_penales_vg"):
            cp_df = pd.DataFrame(d["casos_penales_vg"])
            cp_df = cp_df[(cp_df["anio"] >= anio_desde) & (cp_df["anio"] <= anio_hasta)]
            tipos_pen = cp_df["tipo"].unique()
            fig_cp = go.Figure()
            colors_pen = [PINK, "#7C3AED", "#F59E0B", "#0EA5E9"]
            for i, tipo in enumerate(tipos_pen):
                sub = cp_df[cp_df["tipo"]==tipo]
                fig_cp.add_trace(go.Bar(
                    x=sub["anio"], y=sub["casos"],
                    name=tipo[:35],
                    marker_color=colors_pen[i % len(colors_pen)],
                ))
            fig_cp.update_layout(
                barmode="group", height=300,
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,240,246,1)",
                yaxis=dict(gridcolor="#FCE7F3"),
                legend=dict(orientation="h", y=-0.35, font=dict(size=10)),
            )
            st.plotly_chart(fig_cp, use_container_width=True)

    st.markdown("---")
    st.markdown("#### OVD: casos atendidos por sexo y año")
    ovd_sex = pd.DataFrame(d["ovd_por_sexo"])
    ovd_sex = ovd_sex[(ovd_sex["anio"] >= anio_desde) & (ovd_sex["anio"] <= anio_hasta)]
    fig_os = px.bar(
        ovd_sex, x="anio", y="casos", color="sexo",
        barmode="group",
        color_discrete_map={"Femenino": PINK, "Masculino": "#3B82F6"},
        labels={"anio":"Año","casos":"Casos","sexo":"Sexo"},
    )
    fig_os.update_layout(
        height=280, margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,240,246,1)",
        yaxis=dict(gridcolor="#FCE7F3"),
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig_os, use_container_width=True)
    st.caption("Fuente: OVD CSJN – 90%+ de los casos son mujeres afectadas por violencia doméstica")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 – Brecha Salarial
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    col_bo, col_br = st.columns(2)

    with col_bo:
        st.markdown("#### Brecha de ingresos en ocupación principal (%) – histórico")
        bo_df = pd.DataFrame(d["brecha_ocupacion"])
        bo_df = bo_df[(bo_df["anio"] >= anio_desde) & (bo_df["anio"] <= anio_hasta)]
        colors_bo = ["#DC2626" if v < -20 else "#F59E0B" if v < -15 else "#10B981"
                     for v in bo_df["brecha"]]
        fig_bo = go.Figure(go.Bar(
            x=bo_df["anio"], y=bo_df["brecha"],
            marker_color=colors_bo,
            text=[f"{v:.1f}%" for v in bo_df["brecha"]],
            textposition="outside",
        ))
        fig_bo.add_hline(y=0, line_color="#888", line_width=1)
        fig_bo.update_layout(
            height=320, yaxis_title="Brecha (%)",
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,240,246,1)",
            yaxis=dict(gridcolor="#FCE7F3"),
        )
        st.plotly_chart(fig_bo, use_container_width=True)
        st.caption("Negativo = las mujeres ganan menos que los varones. EJ: -19% = mujeres ganan 19% menos.")

    with col_br:
        st.markdown(f"#### Brecha por rama de actividad ({d['brecha_rama_anio']})")
        br_df = pd.DataFrame(d["brecha_por_rama"]).sort_values("brecha")
        colors_rama = ["#DC2626" if v < -25 else "#F59E0B" if v < -15 else "#10B981"
                       for v in br_df["brecha"]]
        fig_br = go.Figure(go.Bar(
            y=br_df["rama"], x=br_df["brecha"], orientation="h",
            marker_color=colors_rama,
            text=[f"{v:.1f}%" for v in br_df["brecha"]],
            textposition="outside",
        ))
        fig_br.add_vline(x=0, line_color="#888", line_width=1)
        fig_br.update_layout(
            height=320, xaxis_title="Brecha (%)",
            margin=dict(t=10, b=10, l=10, r=60),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,240,246,1)",
            xaxis=dict(gridcolor="#FCE7F3"),
        )
        st.plotly_chart(fig_br, use_container_width=True)

    st.markdown("---")
    col_bc, col_info = st.columns([1, 1])

    with col_bc:
        st.markdown(f"#### Brecha por calificación ocupacional ({d['brecha_calif_anio']})")
        bc_df = pd.DataFrame(d["brecha_calificacion"]).sort_values("brecha")
        fig_bc = go.Figure(go.Bar(
            y=bc_df["calificacion"], x=bc_df["brecha"], orientation="h",
            marker_color=[PINK if v < -20 else "#F59E0B" for v in bc_df["brecha"]],
            text=[f"{v:.1f}%" for v in bc_df["brecha"]],
            textposition="outside",
        ))
        fig_bc.add_vline(x=0, line_color="#888", line_width=1)
        fig_bc.update_layout(
            height=280, xaxis_title="Brecha (%)",
            margin=dict(t=10, b=10, l=10, r=60),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,240,246,1)",
            xaxis=dict(gridcolor="#FCE7F3"),
        )
        st.plotly_chart(fig_bc, use_container_width=True)

    with col_info:
        st.markdown(f"#### Qué dice la brecha")
        bo_last = d["brecha_ocupacion"][-1]
        br_peor = min(d["brecha_por_rama"], key=lambda x: x["brecha"])
        br_mejor = max(d["brecha_por_rama"], key=lambda x: x["brecha"])
        st.markdown(f"""
        <div style='background:white;border-radius:10px;padding:20px;margin-top:10px;'>
        <p style='margin:0 0 12px;font-weight:600;font-size:1rem;'>Brecha de ingresos – CABA ({bo_last['anio']})</p>

        <div style='margin-bottom:10px;padding:10px;background:#FEF2F2;border-radius:8px;border-left:4px solid #DC2626;'>
        <b>Ocupación principal:</b><br>
        Las mujeres ganan un <b>{abs(bo_last['brecha']):.0f}% menos</b> que los varones
        en puestos de la misma categoría.
        </div>

        <div style='margin-bottom:10px;padding:10px;background:#FEF9C3;border-radius:8px;border-left:4px solid #F59E0B;'>
        <b>Peor rama:</b> {br_peor['rama']}<br>
        Brecha de <b>{abs(br_peor['brecha']):.0f}%</b>
        </div>

        <div style='padding:10px;background:#F0FDF4;border-radius:8px;border-left:4px solid #10B981;'>
        <b>Menor brecha:</b> {br_mejor['rama']}<br>
        Brecha de <b>{abs(br_mejor['brecha']):.0f}%</b>
        </div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 – Estado & Recursos
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    col_eg, col_ej = st.columns(2)

    with col_eg:
        st.markdown("#### Empleados GCBA por grupo – % mujeres vs. varones")
        ep_df = pd.DataFrame(d["emp_publicos_grupo"])
        ep_df["muj_pct"] = ep_df["mujeres"] * 100
        ep_df["var_pct"] = ep_df["varones"] * 100
        fig_ep = go.Figure()
        fig_ep.add_trace(go.Bar(
            y=ep_df["grupo"], x=ep_df["muj_pct"], name="Mujeres",
            orientation="h", marker_color=PINK,
            text=[f"{v:.0f}%" for v in ep_df["muj_pct"]], textposition="outside",
        ))
        fig_ep.add_trace(go.Bar(
            y=ep_df["grupo"], x=[-v for v in ep_df["var_pct"]], name="Varones",
            orientation="h", marker_color="#3B82F6",
            text=[f"{v:.0f}%" for v in ep_df["var_pct"]], textposition="outside",
        ))
        fig_ep.add_vline(x=0, line_color="#888", line_width=1)
        fig_ep.update_layout(
            barmode="overlay",
            height=320,
            xaxis=dict(tickvals=[-100,-50,0,50,100],
                       ticktext=["100%","50%","0","50%","100%"]),
            margin=dict(t=10, b=10, l=10, r=80),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,240,246,1)",
            legend=dict(orientation="h"),
        )
        st.plotly_chart(fig_ep, use_container_width=True)
        st.caption("Datos al 1/4/2026. Izquierda = Varones, Derecha = Mujeres")

    with col_ej:
        st.markdown("#### Proporción mujeres en jerarquías del GCBA")
        jer_df = pd.DataFrame(d["emp_publicos_jerarquias"])
        jer_df["muj_pct"] = jer_df["mujeres"] * 100
        jer_sort = jer_df.sort_values("muj_pct", ascending=True).head(15)
        color_j = ["#DC2626" if v < 30 else "#F59E0B" if v < 45 else "#10B981"
                   for v in jer_sort["muj_pct"]]
        fig_j = go.Figure(go.Bar(
            y=jer_sort["jerarquia"].apply(lambda x: x[:35]),
            x=jer_sort["muj_pct"],
            orientation="h",
            marker_color=color_j,
            text=[f"{v:.0f}%" for v in jer_sort["muj_pct"]],
            textposition="outside",
        ))
        fig_j.add_vline(x=50, line_dash="dash", line_color="#888",
                        annotation_text="Paridad 50%")
        fig_j.update_layout(
            height=380, xaxis_title="% mujeres",
            margin=dict(t=10, b=10, l=10, r=60),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,240,246,1)",
            xaxis=dict(gridcolor="#FCE7F3"),
        )
        st.plotly_chart(fig_j, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Unidades de género en comisarías CABA")
    cg_list = d["comisarias_genero"]
    cols_cg = st.columns(2)
    for i, cg in enumerate(cg_list):
        with cols_cg[i % 2]:
            comunas_str = str(cg['comunas']) if cg['comunas'] != "nan" else "–"
            dir_str = str(cg['dir']) if cg['dir'] != "nan" else "–"
            st.markdown(
                f"<div style='background:white;border-radius:8px;padding:12px 16px;"
                f"margin-bottom:8px;border-left:3px solid {PINK};font-size:.83rem;'>"
                f"<b>{cg['area']}</b><br>"
                f"📍 {dir_str}<br>"
                f"🏙 Comunas: {comunas_str}"
                f"</div>",
                unsafe_allow_html=True,
            )
