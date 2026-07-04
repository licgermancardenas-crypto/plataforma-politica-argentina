"""
Página 21 – OSINT · Red Política PBA
Mapa de poder interactivo: intendentes, secretarios, concejales y legisladores
Estilo investigation board / tactical intelligence dashboard
"""
import json, os, re, tempfile
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd
from pyvis.network import Network

st.set_page_config(
    page_title="OSINT · Red Política PBA",
    page_icon="🕵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS cinematográfico ────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: #070B14;
    background-image: radial-gradient(ellipse at 20% 50%, rgba(0,60,120,0.15) 0%, transparent 60%),
                      radial-gradient(ellipse at 80% 20%, rgba(0,120,80,0.1) 0%, transparent 60%);
}
[data-testid="stSidebar"] { background: #0A0F1E; border-right: 1px solid #1E3A5F; }
[data-testid="stSidebar"] * { color: #94A3B8 !important; }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #00FF88 !important; }
.stTabs [data-baseweb="tab-list"] { background: #0A0F1E; border-bottom: 1px solid #1E3A5F; }
.stTabs [aria-selected="true"] { color: #00FF88 !important; border-bottom: 2px solid #00FF88 !important; }
.stTabs [aria-selected="false"] { color: #475569 !important; }
.osint-header {
    background: linear-gradient(135deg, #070B14, #0A1628);
    border: 1px solid #1E3A5F;
    border-left: 4px solid #00FF88;
    border-radius: 8px;
    padding: 20px 28px;
    margin-bottom: 16px;
    font-family: 'Courier New', monospace;
}
.osint-card {
    background: #0D1425;
    border: 1px solid #1E3A5F;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 10px;
    font-family: 'Courier New', monospace;
}
.osint-card:hover { border-color: #00FF88; transition: border-color 0.2s; }
.tag-bloque {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 600; margin: 2px;
    font-family: 'Courier New', monospace;
}
.kpi-osint {
    background: #0D1425; border: 1px solid #1E3A5F; border-radius: 8px;
    padding: 14px 20px; text-align: center;
}
.kpi-val { font-size: 2rem; font-weight: 700; font-family: 'Courier New', monospace; }
.kpi-lbl { font-size: 0.72rem; color: #475569; text-transform: uppercase; letter-spacing: 2px; }
</style>
""", unsafe_allow_html=True)

# ── Colores por bloque ─────────────────────────────────────────────────
BLOQUE_HEX = {
    "Unión por la Patria":  "#22C55E",
    "Juntos por el Cambio": "#3B82F6",
    "La Libertad Avanza":   "#F97316",
    "UCR":                  "#A855F7",
    "FIT-U":                "#EF4444",
    "Vecinal":              "#EAB308",
    "PRO":                  "#F59E0B",
    "Fuerza Patria":        "#34D399",
    "Otro":                 "#64748B",
}
BLOQUE_BG = {
    "Unión por la Patria":  "rgba(34,197,94,0.15)",
    "Juntos por el Cambio": "rgba(59,130,246,0.15)",
    "La Libertad Avanza":   "rgba(249,115,22,0.15)",
    "UCR":                  "rgba(168,85,247,0.15)",
    "Vecinal":              "rgba(234,179,8,0.15)",
}

def hex_bloque(bloque):
    for k, v in BLOQUE_HEX.items():
        if k.lower() in (bloque or "").lower():
            return v
    return "#64748B"

SECCION_COLOR = {
    "1ª – Norte Conurbano": "#00FF88",
    "2ª – Norte PBA":       "#00BFFF",
    "3ª – Sur Conurbano":   "#FF6B6B",
    "4ª – Noroeste PBA":    "#FFD93D",
    "5ª – Costa Atlántica": "#C77DFF",
    "6ª – Sudoeste PBA":    "#FF9A3C",
    "7ª – Centro PBA":      "#4ECDC4",
    "8ª – Capital (La Plata)": "#F7FFF7",
}

# ── Carga de datos ─────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d = os.path.join(base, "data")
    with open(f"{d}/intendentes.json", encoding="utf-8") as f:
        ints = json.load(f)
    with open(f"{d}/secretarios.json", encoding="utf-8") as f:
        secs = json.load(f)
    with open(f"{d}/concejales_flat.json", encoding="utf-8") as f:
        conc = json.load(f)
    with open(f"{d}/legisladores.json", encoding="utf-8") as f:
        leg = json.load(f)
    with open(f"{d}/legisladores_caba.json", encoding="utf-8") as f:
        leg_caba = json.load(f)
    return ints, secs, conc, leg, leg_caba

ints, secs_data, conc_data, leg_data, leg_caba = load()

df_int  = pd.DataFrame(ints)
df_conc = pd.DataFrame(conc_data)
df_dp   = pd.DataFrame(leg_data.get("diputados_prov", []))
df_sp   = pd.DataFrame(leg_data.get("senadores_prov", []))
df_dn   = pd.DataFrame(leg_data.get("diputados_nac", []))

# ── Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div class='osint-header'>
  <div style='display:flex;align-items:center;gap:16px;'>
    <div style='font-size:2.5rem;'>🕵</div>
    <div>
      <div style='color:#00FF88;font-size:1.5rem;font-weight:700;letter-spacing:3px;'>
        SISTEMA OSINT · RED POLÍTICA PBA
      </div>
      <div style='color:#475569;font-size:0.8rem;letter-spacing:2px;margin-top:4px;'>
        INTELLIGENCE DASHBOARD · CLASIFICACIÓN: USO POLÍTICO Y ANÁLISIS TERRITORIAL
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)
total_secs = sum(len(v) for v in secs_data.values())
kpi_data = [
    (k1, len(ints),          "INTENDENTES",   "#00FF88"),
    (k2, total_secs,         "SECRETARIOS",   "#3B82F6"),
    (k3, len(conc_data),     "CONCEJALES",    "#A855F7"),
    (k4, len(df_dp)+len(df_sp), "LEG. PBA",   "#F97316"),
    (k5, len(df_dn),         "DIP. NACION.",  "#EF4444"),
    (k6, len(ints) + total_secs + len(conc_data) + len(df_dp) + len(df_sp) + len(df_dn),
         "TOTAL PERSONAS",   "#EAB308"),
]
for col, val, label, color in kpi_data:
    with col:
        st.markdown(f"""
        <div class='kpi-osint' style='border-top:2px solid {color};'>
          <div class='kpi-val' style='color:{color};'>{val:,}</div>
          <div class='kpi-lbl'>{label}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── SIDEBAR ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🕵 OSINT RED POLÍTICA")
    st.markdown("<div style='color:#00FF88;font-size:.7rem;letter-spacing:2px;'>FILTROS DE INTELIGENCIA</div>",
                unsafe_allow_html=True)
    st.markdown("---")

    secciones_disp = ["Todas"] + sorted(df_int["seccion_nombre"].unique().tolist())
    sec_sel = st.selectbox("Sección electoral", secciones_disp, key="osint_sec")

    bloques_disp = ["Todos"] + sorted(df_int["bloque"].unique().tolist())
    blq_sel = st.selectbox("Bloque político", bloques_disp, key="osint_blq")

    mun_sel = st.selectbox(
        "Municipio (detalle)",
        ["— seleccionar —"] + sorted(df_int["municipio"].tolist()),
        key="osint_mun",
    )

    st.markdown("---")
    st.markdown("**Capas del grafo**")
    show_secciones = st.checkbox("Nodos de sección", value=True, key="osint_show_sec")
    show_legislators = st.checkbox("Legisladores PBA", value=False, key="osint_show_leg")
    physics_on = st.checkbox("Física (animado)", value=True, key="osint_physics")

    st.markdown("---")
    busqueda = st.text_input("🔍 Buscar persona", placeholder="Nombre...", key="osint_busq")

    # Stats de filtro activo
    df_filt = df_int.copy()
    if sec_sel != "Todas":
        df_filt = df_filt[df_filt["seccion_nombre"] == sec_sel]
    if blq_sel != "Todos":
        df_filt = df_filt[df_filt["bloque"] == blq_sel]

    st.markdown("---")
    st.markdown(f"<div style='font-size:.8rem;color:#475569;'>"
                f"<b style='color:#00FF88;'>{len(df_filt)}</b> municipios en vista<br>"
                f"<b style='color:#3B82F6;'>{df_filt['n_concejales'].sum():.0f}</b> concejales asociados"
                f"</div>", unsafe_allow_html=True)

# ── TABS ───────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🕸  Red de Poder",
    "🏛  Organigrama Municipal",
    "📊  Distribución Política",
    "🔍  Búsqueda OSINT",
])

# ════════════════════════════════════════════════════════════════════════
# TAB 1 – RED DE PODER (pyvis network)
# ════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("""
    <div style='font-family:monospace;color:#475569;font-size:.8rem;margin-bottom:12px;
         background:#0D1425;border:1px solid #1E3A5F;border-left:3px solid #00FF88;
         border-radius:6px;padding:10px 16px;'>
    <b style='color:#00FF88;'>▶ CLICK en un municipio</b> para expandir su red: secretarías (🟦 rect.) y concejales (🔷 diamante) &nbsp;|&nbsp;
    Doble click = contraer &nbsp;|&nbsp; Tamaño = padrón &nbsp;|&nbsp; Color = bloque político
    </div>""", unsafe_allow_html=True)

    @st.cache_data(show_spinner=False)
    def build_network_html(sec_filter, blq_filter, show_sec, show_leg, phys_on):
        net = Network(
            height="650px",
            width="100%",
            bgcolor="#070B14",
            font_color="#CBD5E1",
            directed=False,
        )

        physics_str = '"enabled": true' if phys_on else '"enabled": false'
        net.set_options(f"""
        {{
          "nodes": {{
            "font": {{"face": "Courier New", "size": 11}},
            "borderWidth": 2,
            "shadow": {{"enabled": true, "color": "rgba(0,255,136,0.3)", "size": 15, "x": 0, "y": 0}}
          }},
          "edges": {{
            "smooth": {{"type": "continuous"}},
            "shadow": false,
            "width": 1.5
          }},
          "physics": {{
            {physics_str},
            "forceAtlas2Based": {{
              "gravitationalConstant": -80,
              "centralGravity": 0.01,
              "springLength": 160,
              "springConstant": 0.08,
              "damping": 0.4,
              "avoidOverlap": 0.8
            }},
            "solver": "forceAtlas2Based",
            "stabilization": {{"iterations": 200}}
          }},
          "interaction": {{
            "hover": true,
            "tooltipDelay": 100,
            "hideEdgesOnDrag": true
          }}
        }}""")

        # ── Nodo central PBA ──
        net.add_node(
            "PBA",
            label="Buenos Aires\nProvincia",
            size=55,
            color={"background": "#1F3864", "border": "#3B82F6", "highlight": {"border": "#60A5FA"}},
            shape="dot",
            title="<b>Provincia de Buenos Aires</b><br>135 municipios",
            font={"size": 14, "color": "#93C5FD", "face": "Courier New"},
        )

        # ── Nodos de sección ──
        secciones_list = sorted(df_int["seccion_nombre"].unique())
        if show_sec:
            for sec_name in secciones_list:
                if sec_filter != "Todas" and sec_name != sec_filter:
                    continue
                color = SECCION_COLOR.get(sec_name, "#64748B")
                n_mun = len(df_int[df_int["seccion_nombre"] == sec_name])
                net.add_node(
                    sec_name,
                    label=sec_name[:20],
                    size=38,
                    color={"background": color + "33", "border": color},
                    shape="dot",
                    title=f"<b>{sec_name}</b><br>{n_mun} municipios",
                    font={"size": 12, "color": color},
                )
                net.add_edge("PBA", sec_name, color={"color": color + "55"}, width=2)

        # ── Nodos de municipio/intendente + hijos ocultos ──
        for row in ints:
            if sec_filter != "Todas" and row["seccion_nombre"] != sec_filter:
                continue
            if blq_filter != "Todos" and row["bloque"] != blq_filter:
                continue

            mun = row["municipio"]
            color = hex_bloque(row["bloque"])
            padron = row.get("padron") or 50000
            size = min(8 + padron / 35000, 40)
            intend = row.get("intendente", "?")
            partido = row.get("partido", "?")
            n_conc = row.get("n_concejales", "?")
            pct = row.get("ganador_pct", "?")
            n_secs = len(secs_data.get(mun, []))

            title = (f"<b style='color:{color}'>{mun}</b><br>"
                     f"<b>Intendente:</b> {intend}<br>"
                     f"<b>Bloque:</b> {row['bloque']}<br>"
                     f"<b>Partido:</b> {partido}<br>"
                     f"<b>Resultado 2023:</b> {pct}%<br>"
                     f"<b>Padrón:</b> {padron:,}<br>"
                     f"<b>Secretarías:</b> {n_secs} &nbsp;·&nbsp; "
                     f"<b>Concejales:</b> {n_conc}<br>"
                     f"<i style='color:#00FF88;'>▶ Click para expandir red</i>")

            net.add_node(
                mun,
                label=f"⊕ {mun}\n{intend.split(',')[0] if ',' in intend else intend[:18]}",
                size=size,
                color={"background": color + "33", "border": color,
                       "highlight": {"background": color + "55", "border": "#FFFFFF"}},
                shape="dot",
                title=title,
                font={"size": 10, "color": "#CBD5E1"},
            )
            parent = row["seccion_nombre"] if show_sec else "PBA"
            edge_color = SECCION_COLOR.get(row["seccion_nombre"], "#334155") + "88"
            net.add_edge(parent, mun, color={"color": edge_color}, width=1)

            # ── Secretarios (ocultos, se revelan al hacer click) ──
            for s in secs_data.get(mun, []):
                sid = f"sec__{mun}__{s['nombre']}"
                net.add_node(
                    sid,
                    label=s["nombre"][:24],
                    size=12,
                    color={"background": "#0F2044", "border": "#3B82F6",
                           "highlight": {"background": "#1E3A5F", "border": "#60A5FA"}},
                    shape="box",
                    hidden=True,
                    title=(f"<b style='color:#60A5FA;'>🏛 SECRETARÍA</b><br>"
                           f"<b>{s['nombre']}</b><br>"
                           f"<i>{s['cargo']}</i><br>"
                           f"<span style='color:#475569;'>{mun}</span>"),
                    font={"size": 9, "color": "#93C5FD", "face": "Courier New"},
                )
                net.add_edge(mun, sid,
                             color={"color": "#3B82F666"}, width=1.5,
                             hidden=True, dashes=True)

            # ── Concejales top-7 por municipio (ocultos) ──
            mun_concs = [c for c in conc_data if c["municipio"] == mun][:7]
            for c in mun_concs:
                cid = f"conc__{mun}__{c['nombre']}"
                blq_col = hex_bloque(c.get("bloque", ""))
                net.add_node(
                    cid,
                    label=c["nombre"][:24],
                    size=10,
                    color={"background": blq_col + "22", "border": blq_col,
                           "highlight": {"background": blq_col + "44", "border": "#FFFFFF"}},
                    shape="diamond",
                    hidden=True,
                    title=(f"<b style='color:{blq_col};'>🗳 CONCEJAL</b><br>"
                           f"<b>{c['nombre']}</b><br>"
                           f"Bloque: {c.get('bloque','')}<br>"
                           f"<span style='color:#475569;'>{mun}</span>"),
                    font={"size": 9, "color": "#CBD5E1", "face": "Courier New"},
                )
                net.add_edge(mun, cid,
                             color={"color": blq_col + "55"}, width=1,
                             hidden=True, dashes=True)

        # ── Nodos de legisladores (opcional) ──
        if show_leg:
            for row in leg_data.get("diputados_prov", []):
                nid = f"dip_{row['nombre']}"
                color = hex_bloque(row.get("bloque", ""))
                sec_leg = None
                for s in df_int["seccion_nombre"].unique():
                    if str(row.get("seccion", "")) in s:
                        sec_leg = s
                        break
                net.add_node(
                    nid,
                    label=row["nombre"][:20],
                    size=8,
                    color={"background": color + "22", "border": color},
                    shape="diamond",
                    title=f"<b>Diputado Prov.</b><br>{row['nombre']}<br>{row.get('bloque','')}",
                    font={"size": 8, "color": "#94A3B8"},
                )
                parent = sec_leg if (sec_leg and show_sec) else "PBA"
                net.add_edge(parent, nid, color={"color": color + "44"}, width=0.8, dashes=True)

        html = net.generate_html()

        # ── Inyectar handler JS: click en municipio → expande/contrae hijos ──
        click_js = """
<script type="text/javascript">
(function() {
  var expanded = {};   // trackea qué municipios están expandidos

  network.on("click", function(params) {
    if (params.nodes.length === 0) return;
    var clickedId = String(params.nodes[0]);

    // Solo actuar sobre nodos de municipio (no PBA, secciones, sec__, conc__, dip_)
    if (clickedId === "PBA") return;
    if (clickedId.startsWith("sec__") || clickedId.startsWith("conc__") || clickedId.startsWith("dip_")) return;
    // Ignorar nodos de sección (contienen "ª")
    if (clickedId.indexOf("ª") !== -1) return;

    var isExpanded = !!expanded[clickedId];
    expanded[clickedId] = !isExpanded;

    var connectedNodeIds = network.getConnectedNodes(clickedId);
    var nodeUpdates = [];
    var edgeUpdates = [];

    connectedNodeIds.forEach(function(cid) {
      var cids = String(cid);
      if (cids.startsWith("sec__") || cids.startsWith("conc__")) {
        var n = nodes.get(cid);
        if (n) nodeUpdates.push({ id: cid, hidden: isExpanded });
      }
    });

    var connectedEdgeIds = network.getConnectedEdges(clickedId);
    connectedEdgeIds.forEach(function(eid) {
      var e = edges.get(eid);
      if (e) {
        var toId = String(e.to);
        if (toId.startsWith("sec__") || toId.startsWith("conc__")) {
          edgeUpdates.push({ id: eid, hidden: isExpanded });
        }
      }
    });

    nodes.update(nodeUpdates);
    edges.update(edgeUpdates);

    // Actualizar label del nodo: ⊕ expandir / ⊖ contraer
    var mainNode = nodes.get(clickedId);
    if (mainNode) {
      var newLabel = mainNode.label;
      if (!isExpanded) {
        newLabel = newLabel.replace(/^⊕ /, "⊖ ");
      } else {
        newLabel = newLabel.replace(/^⊖ /, "⊕ ");
      }
      nodes.update([{ id: clickedId, label: newLabel }]);
    }

    // Foco en el nodo expandido
    if (!isExpanded) {
      network.focus(clickedId, { scale: 1.4, animation: { duration: 600, easingFunction: "easeInOutQuad" } });
    }
  });
})();
</script>
"""
        html = html.replace("</body>", click_js + "\n</body>")
        return html

    net_html = build_network_html(sec_sel, blq_sel, show_secciones, show_legislators, physics_on)
    components.html(net_html, height=670, scrolling=False)

    st.markdown(f"""
    <div style='font-family:monospace;color:#334155;font-size:.72rem;margin-top:8px;'>
    🔵 Hover sobre nodo → info detallada &nbsp;|&nbsp;
    🖱 Scroll → zoom &nbsp;|&nbsp;
    🖱 Drag → mover nodos &nbsp;|&nbsp;
    Activo: <b style='color:#00FF88;'>{len(df_filt)}</b> municipios
    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════
# TAB 2 – ORGANIGRAMA MUNICIPAL
# ════════════════════════════════════════════════════════════════════════
with tab2:
    if mun_sel == "— seleccionar —":
        st.markdown("""
        <div style='text-align:center;padding:60px;color:#334155;font-family:monospace;'>
          <div style='font-size:3rem;'>🏛</div>
          <div style='font-size:1.1rem;margin-top:12px;'>
            Seleccioná un <b style='color:#00FF88;'>municipio</b> en el sidebar para ver su organigrama
          </div>
          <div style='font-size:.8rem;color:#1E3A5F;margin-top:8px;'>
            Intendente → Secretarios → Concejales por bloque
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        # Datos del municipio seleccionado
        int_row = next((r for r in ints if r["municipio"] == mun_sel), {})
        mun_secs = secs_data.get(mun_sel, [])
        mun_conc = [c for c in conc_data if c["municipio"] == mun_sel]
        conc_by_bloque = {}
        for c in mun_conc:
            b = c.get("bloque", "Otro")
            conc_by_bloque.setdefault(b, []).append(c["nombre"])

        color_mun = hex_bloque(int_row.get("bloque", ""))

        # Header del municipio
        st.markdown(f"""
        <div style='background:#0D1425;border:1px solid {color_mun}44;border-left:4px solid {color_mun};
             border-radius:8px;padding:16px 22px;margin-bottom:20px;font-family:monospace;'>
          <div style='font-size:1.4rem;font-weight:700;color:{color_mun};'>{mun_sel}</div>
          <div style='color:#94A3B8;font-size:.85rem;margin-top:4px;'>
            {int_row.get("seccion_nombre","")} &nbsp;·&nbsp; {int_row.get("bloque","")}
          </div>
        </div>""", unsafe_allow_html=True)

        # ── Org chart con Plotly ──
        # Construir treemap como organigrama visual
        labels, parents, values, colors, hovers = [], [], [], [], []

        # Raíz: Intendente
        intend_name = int_row.get("intendente", mun_sel)
        labels.append(f"👤 {intend_name}")
        parents.append("")
        values.append(10)
        colors.append(color_mun)
        hovers.append(f"<b>INTENDENTE</b><br>{mun_sel}<br>Partido: {int_row.get('partido','')}<br>Resultado 2023: {int_row.get('ganador_pct','')}%")

        # Rama secretarios
        if mun_secs:
            labels.append("🏛 Secretarías")
            parents.append(f"👤 {intend_name}")
            values.append(8)
            colors.append("#1E40AF")
            hovers.append(f"<b>{len(mun_secs)} secretarías</b>")
            for s in mun_secs:
                labels.append(f"📋 {s['nombre'][:28]}")
                parents.append("🏛 Secretarías")
                values.append(3)
                colors.append("#1D4ED8")
                hovers.append(f"<b>{s['nombre']}</b><br>{s['cargo']}")

        # Rama concejales por bloque
        if conc_by_bloque:
            labels.append("🗳 Concejo Deliberante")
            parents.append(f"👤 {intend_name}")
            values.append(8)
            colors.append("#6B21A8")
            hovers.append(f"<b>{len(mun_conc)} concejales</b>")

            for blq, concejales in sorted(conc_by_bloque.items(), key=lambda x: -len(x[1])):
                blq_label = f"■ {blq[:20]} ({len(concejales)})"
                labels.append(blq_label)
                parents.append("🗳 Concejo Deliberante")
                values.append(len(concejales) * 2)
                colors.append(hex_bloque(blq))
                hovers.append(f"<b>{blq}</b><br>{len(concejales)} concejales")

                for c_name in concejales:
                    labels.append(f"· {c_name[:24]}")
                    parents.append(blq_label)
                    values.append(1)
                    colors.append(hex_bloque(blq) + "88")
                    hovers.append(f"<b>Concejal</b><br>{c_name}<br>Bloque: {blq}")

        fig_org = go.Figure(go.Treemap(
            labels=labels,
            parents=parents,
            values=values,
            customdata=hovers,
            hovertemplate="%{customdata}<extra></extra>",
            marker=dict(
                colors=colors,
                line=dict(color="#070B14", width=2),
                pad=dict(t=6, l=4, r=4, b=4),
            ),
            textfont=dict(family="Courier New", size=11, color="#E2E8F0"),
            pathbar=dict(visible=True, textfont=dict(family="Courier New", color="#94A3B8")),
        ))
        fig_org.update_layout(
            height=580,
            paper_bgcolor="#070B14",
            plot_bgcolor="#070B14",
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_org, use_container_width=True, key="org_treemap")

        # ── Cards de detalle debajo ──
        col_d1, col_d2 = st.columns(2)

        with col_d1:
            st.markdown("<div style='color:#00FF88;font-family:monospace;font-size:.8rem;letter-spacing:2px;margin-bottom:8px;'>SECRETARÍAS</div>",
                        unsafe_allow_html=True)
            for s in mun_secs:
                st.markdown(f"""
                <div class='osint-card'>
                  <div style='color:#3B82F6;font-size:.82rem;font-weight:700;'>{s['nombre']}</div>
                  <div style='color:#475569;font-size:.75rem;margin-top:3px;'>{s['cargo']}</div>
                </div>""", unsafe_allow_html=True)
            if not mun_secs:
                st.markdown("<div style='color:#334155;font-size:.8rem;font-family:monospace;'>Sin datos disponibles</div>", unsafe_allow_html=True)

        with col_d2:
            st.markdown("<div style='color:#A855F7;font-family:monospace;font-size:.8rem;letter-spacing:2px;margin-bottom:8px;'>CONCEJALES</div>",
                        unsafe_allow_html=True)
            for blq, concejales in sorted(conc_by_bloque.items(), key=lambda x: -len(x[1])):
                color_blq = hex_bloque(blq)
                st.markdown(f"""
                <div style='border-left:3px solid {color_blq};padding-left:10px;margin-bottom:10px;'>
                  <div style='color:{color_blq};font-size:.75rem;font-weight:700;font-family:monospace;'>{blq} ({len(concejales)})</div>
                  {"".join(f"<div style='color:#94A3B8;font-size:.72rem;'>· {c}</div>" for c in concejales)}
                </div>""", unsafe_allow_html=True)
            if not conc_by_bloque:
                st.markdown("<div style='color:#334155;font-size:.8rem;font-family:monospace;'>Sin datos disponibles</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════
# TAB 3 – DISTRIBUCIÓN POLÍTICA
# ════════════════════════════════════════════════════════════════════════
with tab3:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Distribución de intendentes por bloque")
        blq_counts = df_int["bloque"].value_counts().reset_index()
        blq_counts.columns = ["bloque", "n"]
        colors_blq = [hex_bloque(b) for b in blq_counts["bloque"]]

        fig_blq = go.Figure(go.Bar(
            x=blq_counts["n"],
            y=blq_counts["bloque"],
            orientation="h",
            marker_color=colors_blq,
            text=blq_counts["n"],
            textposition="outside",
            textfont=dict(family="Courier New", color="#94A3B8"),
        ))
        fig_blq.update_layout(
            height=280, paper_bgcolor="#070B14", plot_bgcolor="#0D1425",
            xaxis=dict(gridcolor="#1E3A5F", color="#475569"),
            yaxis=dict(color="#94A3B8"),
            font=dict(family="Courier New", color="#94A3B8"),
            margin=dict(t=10, b=10, l=10, r=80),
        )
        st.plotly_chart(fig_blq, use_container_width=True, key="dist_int_blq")

        st.markdown("#### Concejales por bloque (total PBA)")
        blq_conc = df_conc["bloque"].value_counts().reset_index()
        blq_conc.columns = ["bloque", "n"]
        fig_blq_c = go.Figure(go.Bar(
            x=blq_conc["n"],
            y=blq_conc["bloque"],
            orientation="h",
            marker_color=[hex_bloque(b) for b in blq_conc["bloque"]],
            text=blq_conc["n"], textposition="outside",
            textfont=dict(family="Courier New", color="#94A3B8"),
        ))
        fig_blq_c.update_layout(
            height=350, paper_bgcolor="#070B14", plot_bgcolor="#0D1425",
            xaxis=dict(gridcolor="#1E3A5F", color="#475569"),
            yaxis=dict(color="#94A3B8"),
            font=dict(family="Courier New", color="#94A3B8"),
            margin=dict(t=10, b=10, l=10, r=80),
        )
        st.plotly_chart(fig_blq_c, use_container_width=True, key="dist_conc_blq")

    with c2:
        st.markdown("#### Mapa de poder: intendentes por sección y bloque")
        sec_blq = df_int.groupby(["seccion_nombre", "bloque"]).size().reset_index(name="n")
        fig_sb = go.Figure()
        for blq in sec_blq["bloque"].unique():
            d = sec_blq[sec_blq["bloque"] == blq]
            fig_sb.add_trace(go.Bar(
                name=blq,
                x=d["seccion_nombre"].str[:20],
                y=d["n"],
                marker_color=hex_bloque(blq),
                text=d["n"], textposition="inside",
                textfont=dict(family="Courier New", size=10),
            ))
        fig_sb.update_layout(
            barmode="stack", height=320,
            paper_bgcolor="#070B14", plot_bgcolor="#0D1425",
            xaxis=dict(gridcolor="#1E3A5F", color="#475569", tickangle=-20, tickfont=dict(size=9, family="Courier New")),
            yaxis=dict(gridcolor="#1E3A5F", color="#475569"),
            font=dict(family="Courier New", color="#94A3B8"),
            legend=dict(bgcolor="#0D1425", bordercolor="#1E3A5F"),
            margin=dict(t=10, b=80, l=10, r=10),
        )
        st.plotly_chart(fig_sb, use_container_width=True, key="sec_blq_stack")

        st.markdown("#### Legisladores PBA por bloque")
        leg_all = []
        for rol, df_l in [("Diputado Prov.", df_dp), ("Senador Prov.", df_sp), ("Diputado Nac.", df_dn)]:
            if "bloque" in df_l.columns:
                for _, r in df_l.iterrows():
                    leg_all.append({"bloque": r["bloque"], "rol": rol})
        if leg_all:
            df_leg_all = pd.DataFrame(leg_all)
            leg_blq = df_leg_all.groupby(["bloque", "rol"]).size().reset_index(name="n")
            fig_leg = go.Figure()
            for rol in ["Diputado Prov.", "Senador Prov.", "Diputado Nac."]:
                d = leg_blq[leg_blq["rol"] == rol]
                fig_leg.add_trace(go.Bar(
                    name=rol, x=d["bloque"].str[:20], y=d["n"],
                    marker_color=hex_bloque(d["bloque"].iloc[0]) if len(d) else "#64748B",
                    text=d["n"], textposition="inside",
                    textfont=dict(family="Courier New", size=9),
                ))
            fig_leg.update_layout(
                barmode="group", height=280,
                paper_bgcolor="#070B14", plot_bgcolor="#0D1425",
                xaxis=dict(gridcolor="#1E3A5F", color="#475569", tickangle=-20, tickfont=dict(size=8, family="Courier New")),
                yaxis=dict(gridcolor="#1E3A5F", color="#475569"),
                font=dict(family="Courier New", color="#94A3B8"),
                legend=dict(bgcolor="#0D1425", bordercolor="#1E3A5F"),
                margin=dict(t=10, b=80, l=10, r=10),
            )
            st.plotly_chart(fig_leg, use_container_width=True, key="leg_blq")


# ════════════════════════════════════════════════════════════════════════
# TAB 4 – BÚSQUEDA OSINT
# ════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("""
    <div style='font-family:monospace;color:#475569;font-size:.8rem;margin-bottom:12px;'>
    Búsqueda unificada sobre intendentes · secretarios · concejales · legisladores provinciales
    </div>""", unsafe_allow_html=True)

    col_s, col_f = st.columns([3, 1])
    with col_s:
        search_q = st.text_input("Buscar nombre, cargo o municipio", value=busqueda,
                                  placeholder="Ej: García, Secretario Salud, La Matanza...",
                                  key="osint_search_main")
    with col_f:
        tipo_busq = st.selectbox("Tipo", ["Todos", "Intendentes", "Secretarios", "Concejales", "Legisladores"],
                                  key="osint_tipo")

    if search_q and len(search_q) >= 2:
        q = search_q.lower().strip()
        results = []

        if tipo_busq in ("Todos", "Intendentes"):
            for r in ints:
                if (q in r.get("intendente","").lower() or
                    q in r.get("municipio","").lower() or
                    q in r.get("partido","").lower()):
                    results.append({
                        "tipo": "INTENDENTE",
                        "nombre": r["intendente"],
                        "cargo": "Intendente",
                        "municipio": r["municipio"],
                        "partido": r.get("bloque",""),
                        "extra": f"Secc. {r.get('seccion_nombre','')} · {r.get('ganador_pct','')}% en 2023",
                        "color": hex_bloque(r.get("bloque","")),
                    })

        if tipo_busq in ("Todos", "Secretarios"):
            for mun, sec_list in secs_data.items():
                for s in sec_list:
                    if q in s["nombre"].lower() or q in s["cargo"].lower() or q in mun.lower():
                        results.append({
                            "tipo": "SECRETARIO",
                            "nombre": s["nombre"],
                            "cargo": s["cargo"],
                            "municipio": mun,
                            "partido": "",
                            "extra": "",
                            "color": "#3B82F6",
                        })

        if tipo_busq in ("Todos", "Concejales"):
            for c in conc_data:
                if (q in c.get("nombre","").lower() or
                    q in c.get("municipio","").lower() or
                    q in c.get("bloque","").lower()):
                    results.append({
                        "tipo": "CONCEJAL",
                        "nombre": c["nombre"],
                        "cargo": f"Concejal #{c.get('n_orden','')}",
                        "municipio": c["municipio"],
                        "partido": c.get("bloque",""),
                        "extra": c.get("seccion_nombre",""),
                        "color": hex_bloque(c.get("bloque","")),
                    })

        if tipo_busq in ("Todos", "Legisladores"):
            for rol, df_l, tipo_l in [
                ("Diputado Prov.", df_dp, "DIP. PROV."),
                ("Senador Prov.", df_sp, "SEN. PROV."),
                ("Diputado Nac.", df_dn, "DIP. NAC."),
            ]:
                if "nombre" in df_l.columns:
                    for _, r in df_l.iterrows():
                        if q in r["nombre"].lower() or q in r.get("bloque","").lower():
                            results.append({
                                "tipo": tipo_l,
                                "nombre": r["nombre"],
                                "cargo": rol,
                                "municipio": "PBA",
                                "partido": r.get("bloque",""),
                                "extra": f"Secc. {r.get('seccion','')}" if r.get("seccion") else "",
                                "color": hex_bloque(r.get("bloque","")),
                            })

        st.markdown(f"<div style='font-family:monospace;color:#00FF88;font-size:.8rem;margin-bottom:12px;'>"
                    f"▶ {len(results)} resultados para «{search_q}»</div>", unsafe_allow_html=True)

        for r in results[:80]:
            st.markdown(f"""
            <div class='osint-card' style='border-left:3px solid {r["color"]};'>
              <div style='display:flex;justify-content:space-between;align-items:start;'>
                <div>
                  <span style='font-size:.65rem;color:{r["color"]};letter-spacing:2px;
                        font-family:monospace;font-weight:700;'>{r["tipo"]}</span>
                  <div style='color:#E2E8F0;font-size:.9rem;font-weight:700;
                        font-family:monospace;margin-top:4px;'>{r["nombre"]}</div>
                  <div style='color:#64748B;font-size:.75rem;font-family:monospace;margin-top:2px;'>
                    {r["cargo"]} &nbsp;·&nbsp; {r["municipio"]}
                  </div>
                  {"<div style='color:" + r["color"] + ";font-size:.72rem;margin-top:3px;font-family:monospace;'>" + r["partido"] + "</div>" if r["partido"] else ""}
                  {"<div style='color:#334155;font-size:.7rem;margin-top:2px;font-family:monospace;'>" + r["extra"] + "</div>" if r["extra"] else ""}
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

        if len(results) > 80:
            st.markdown(f"<div style='color:#475569;font-size:.75rem;font-family:monospace;'>... y {len(results)-80} más. Refiná la búsqueda.</div>", unsafe_allow_html=True)

    elif not search_q:
        # Panel de personas destacadas
        st.markdown("#### Perfiles destacados – intendentes de GBA")
        gba_secs = ["1ª – Norte Conurbano", "3ª – Sur Conurbano"]
        gba_ints = [r for r in ints if r["seccion_nombre"] in gba_secs]
        gba_ints.sort(key=lambda x: x.get("padron", 0) or 0, reverse=True)

        cols = st.columns(3)
        for i, r in enumerate(gba_ints[:12]):
            col = cols[i % 3]
            color = hex_bloque(r["bloque"])
            padron = r.get("padron", 0) or 0
            with col:
                st.markdown(f"""
                <div class='osint-card' style='border-left:3px solid {color};'>
                  <div style='font-size:.65rem;color:{color};letter-spacing:2px;
                        font-family:monospace;'>INTENDENTE</div>
                  <div style='color:#E2E8F0;font-weight:700;font-family:monospace;
                        font-size:.88rem;margin-top:4px;'>{r['intendente']}</div>
                  <div style='color:#64748B;font-size:.75rem;font-family:monospace;
                        margin-top:2px;'>{r['municipio']}</div>
                  <div style='color:{color};font-size:.7rem;font-family:monospace;
                        margin-top:4px;'>{r['bloque']}</div>
                  <div style='color:#334155;font-size:.68rem;font-family:monospace;
                        margin-top:3px;'>Padrón: {padron:,} · {r.get("ganador_pct","")}%</div>
                </div>""", unsafe_allow_html=True)

# ── Footer ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='font-family:monospace;color:#1E3A5F;font-size:.68rem;text-align:center;'>
SISTEMA OSINT · DATOS: JEPBA 2023 · datos.gba.gob.ar · HCDN ·
USO EXCLUSIVO ANÁLISIS POLÍTICO · NO CLASIFICADO
</div>""", unsafe_allow_html=True)
