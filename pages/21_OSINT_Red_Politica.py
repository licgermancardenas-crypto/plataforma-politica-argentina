"""
Página 21 – OSINT · Red Política PBA
Investigation board: intendentes, secretarios, concejales y legisladores
Pirámide jerárquica con fotos + red interactiva de poder
"""
import json, os, urllib.parse
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
    background-image: radial-gradient(ellipse at 20% 50%, rgba(0,60,120,0.12) 0%, transparent 60%),
                      radial-gradient(ellipse at 80% 20%, rgba(0,120,80,0.08) 0%, transparent 60%);
}
[data-testid="stSidebar"] { background: #0A0F1E; border-right: 1px solid #1E3A5F; }
[data-testid="stSidebar"] * { color: #94A3B8 !important; }
[data-testid="stSidebar"] h2 { color: #00FF88 !important; }
.stTabs [data-baseweb="tab-list"] { background: #0A0F1E; border-bottom: 1px solid #1E3A5F; }
.stTabs [aria-selected="true"]  { color: #00FF88 !important; border-bottom: 2px solid #00FF88 !important; }
.stTabs [aria-selected="false"] { color: #475569 !important; }
.osint-header {
    background: linear-gradient(135deg, #070B14, #0A1628);
    border: 1px solid #1E3A5F; border-left: 4px solid #00FF88;
    border-radius: 8px; padding: 20px 28px; margin-bottom: 16px;
    font-family: 'Courier New', monospace;
}
.osint-card {
    background: #0D1425; border: 1px solid #1E3A5F; border-radius: 8px;
    padding: 14px 18px; margin-bottom: 10px; font-family: 'Courier New', monospace;
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
SECCION_COLOR = {
    "1ª – Norte Conurbano":    "#00FF88",
    "2ª – Norte PBA":          "#00BFFF",
    "3ª – Sur Conurbano":      "#FF6B6B",
    "4ª – Noroeste PBA":       "#FFD93D",
    "5ª – Costa Atlántica":    "#C77DFF",
    "6ª – Sudoeste PBA":       "#FF9A3C",
    "7ª – Centro PBA":         "#4ECDC4",
    "8ª – Capital (La Plata)": "#F7FFF7",
}

def hex_bloque(bloque):
    for k, v in BLOQUE_HEX.items():
        if k.lower() in (bloque or "").lower():
            return v
    return "#64748B"

def dicebear_url(name, style="personas"):
    seed = urllib.parse.quote(name.strip())
    return f"https://api.dicebear.com/9.x/{style}/png?seed={seed}&size=200&backgroundColor=070b14"

def avatar_url(name, bloque):
    color = hex_bloque(bloque).lstrip("#")
    encoded = urllib.parse.quote(name)
    return f"https://ui-avatars.com/api/?name={encoded}&background={color}&color=ffffff&size=200&bold=true&font-size=0.38&rounded=true"

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

@st.cache_data(show_spinner=False)
def load_fotos():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "data", "fotos_intendentes.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)

ints, secs_data, conc_data, leg_data, leg_caba = load()
fotos_ints = load_fotos()

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
        INTELLIGENCE DASHBOARD · 135 MUNICIPIOS · ANÁLISIS TERRITORIAL 2023-2027
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)
total_secs = sum(len(v) for v in secs_data.values())
for col, val, label, color in [
    (k1, len(ints),                        "INTENDENTES",  "#00FF88"),
    (k2, total_secs,                       "SECRETARIOS",  "#3B82F6"),
    (k3, len(conc_data),                   "CONCEJALES",   "#A855F7"),
    (k4, len(df_dp) + len(df_sp),          "LEG. PBA",     "#F97316"),
    (k5, len(df_dn),                       "DIP. NAC.",    "#EF4444"),
    (k6, len(ints)+total_secs+len(conc_data)+len(df_dp)+len(df_sp)+len(df_dn),
         "TOTAL PERSONAS", "#EAB308"),
]:
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
        "Municipio (pirámide)",
        ["— seleccionar —"] + sorted(df_int["municipio"].tolist()),
        key="osint_mun",
    )

    st.markdown("---")
    st.markdown("**Capas del grafo**")
    show_secciones  = st.checkbox("Nodos de sección",  value=True,  key="osint_show_sec")
    show_legislators = st.checkbox("Legisladores PBA",  value=False, key="osint_show_leg")
    physics_on      = st.checkbox("Física (animado)",   value=True,  key="osint_physics")

    st.markdown("---")
    busqueda = st.text_input("🔍 Buscar persona", placeholder="Nombre...", key="osint_busq")

    df_filt = df_int.copy()
    if sec_sel != "Todas":
        df_filt = df_filt[df_filt["seccion_nombre"] == sec_sel]
    if blq_sel != "Todos":
        df_filt = df_filt[df_filt["bloque"] == blq_sel]

    st.markdown("---")
    st.markdown(f"<div style='font-size:.8rem;color:#475569;'>"
                f"<b style='color:#00FF88;'>{len(df_filt)}</b> municipios en vista<br>"
                f"<b style='color:#3B82F6;'>{df_filt['n_concejales'].sum():.0f}</b> concejales"
                f"</div>", unsafe_allow_html=True)

# ── TABS ───────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🕸  Red de Poder",
    "🏛  Pirámide de Mando",
    "📊  Distribución Política",
    "🔍  Búsqueda OSINT",
])

# ════════════════════════════════════════════════════════════════════════
# TAB 1 – RED DE PODER
# ════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("""
    <div style='font-family:monospace;color:#475569;font-size:.8rem;margin-bottom:12px;
         background:#0D1425;border:1px solid #1E3A5F;border-left:3px solid #00FF88;
         border-radius:6px;padding:10px 16px;'>
    <b style='color:#00FF88;'>▶ CLICK</b> en municipio → expande secretarías (🟦) y concejales (🔷)
    &nbsp;|&nbsp; Doble-click en fondo → colapsa todo
    &nbsp;|&nbsp; Foto = Wikipedia / avatar por bloque
    </div>""", unsafe_allow_html=True)

    @st.cache_data(show_spinner=False)
    def build_network_html(sec_filter, blq_filter, show_sec, show_leg, phys_on):
        net = Network(height="700px", width="100%", bgcolor="#070B14",
                      font_color="#CBD5E1", directed=False)

        physics_str = '"enabled": true' if phys_on else '"enabled": false'
        net.set_options(f"""{{
          "nodes": {{
            "font": {{"face": "Courier New", "size": 11, "color": "#E2E8F0",
                     "strokeWidth": 3, "strokeColor": "#070B14"}},
            "borderWidth": 3, "borderWidthSelected": 5,
            "shadow": {{"enabled": true, "color": "rgba(0,255,136,0.35)",
                       "size": 18, "x": 0, "y": 0}}
          }},
          "edges": {{
            "smooth": {{"type": "curvedCW", "roundness": 0.12}},
            "shadow": false, "selectionWidth": 3
          }},
          "physics": {{
            {physics_str},
            "forceAtlas2Based": {{
              "gravitationalConstant": -100, "centralGravity": 0.008,
              "springLength": 210, "springConstant": 0.06,
              "damping": 0.45, "avoidOverlap": 1.0
            }},
            "solver": "forceAtlas2Based",
            "stabilization": {{"iterations": 250, "updateInterval": 25}}
          }},
          "interaction": {{"hover": true, "tooltipDelay": 80,
                           "hideEdgesOnDrag": true}}
        }}""")

        # Nodo PBA central
        net.add_node("PBA", label="BUENOS AIRES\nPROVINCIA", size=72,
                     color={"background":"#0F2044","border":"#3B82F6",
                            "highlight":{"background":"#1E3A5F","border":"#60A5FA"}},
                     shape="dot", borderWidth=4,
                     title="<b style='color:#60A5FA;'>🗺 PROVINCIA DE BUENOS AIRES</b><br>135 municipios · 8 secciones",
                     font={"size":15,"color":"#93C5FD","face":"Courier New","bold":True})

        # Secciones
        secciones_list = sorted(df_int["seccion_nombre"].unique())
        if show_sec:
            for sn in secciones_list:
                if sec_filter != "Todas" and sn != sec_filter:
                    continue
                sc = SECCION_COLOR.get(sn, "#64748B")
                nm = len(df_int[df_int["seccion_nombre"] == sn])
                net.add_node(sn, label=sn[:22], size=50, borderWidth=3,
                             color={"background":"#0A0F1E","border":sc,
                                    "highlight":{"background":sc+"22","border":sc}},
                             shape="dot",
                             title=f"<b style='color:{sc};'>{sn}</b><br>{nm} municipios",
                             font={"size":12,"color":sc,"face":"Courier New"})
                net.add_edge("PBA", sn, color={"color":sc+"66"}, width=2.5)

        # Municipios/intendentes con foto
        for row in ints:
            if sec_filter != "Todas" and row["seccion_nombre"] != sec_filter:
                continue
            if blq_filter != "Todos" and row["bloque"] != blq_filter:
                continue
            mun = row["municipio"]
            color = hex_bloque(row["bloque"])
            padron = row.get("padron") or 50000
            size = min(35 + padron / 30000, 72)
            intend = row.get("intendente", "?")
            n_secs = len(secs_data.get(mun, []))
            foto = fotos_ints.get(mun) or dicebear_url(intend)

            title = (f"<div style='font-family:Courier New;min-width:220px;'>"
                     f"<b style='color:{color};font-size:.95rem;'>{mun}</b><br>"
                     f"<b style='color:#E2E8F0;'>Intendente:</b> {intend}<br>"
                     f"<span style='color:{color};'>{row['bloque']}</span><br>"
                     f"<span style='color:#475569;font-size:.75rem;'>"
                     f"Partido: {row.get('partido','')}<br>"
                     f"Resultado 2023: {row.get('ganador_pct','')}% · Padrón: {padron:,}<br>"
                     f"Secretarías: {n_secs} · Concejales: {row.get('n_concejales','')}</span><br>"
                     f"<span style='color:#00FF88;font-size:.72rem;'>▶ Click para expandir</span></div>")

            net.add_node(mun, label=f"{mun}\n{intend[:20]}",
                         size=size, shape="circularImage", image=foto,
                         color={"border":color,"highlight":{"border":"#FFFFFF","background":color+"33"}},
                         borderWidth=4, title=title,
                         font={"size":11,"color":"#E2E8F0","face":"Courier New",
                               "strokeWidth":3,"strokeColor":"#070B14"})
            parent = row["seccion_nombre"] if show_sec else "PBA"
            ec = SECCION_COLOR.get(row["seccion_nombre"],"#334155") + "77"
            net.add_edge(parent, mun, color={"color":ec}, width=1.5)

            # Secretarios ocultos con foto DiceBear
            for s in secs_data.get(mun, []):
                sid = f"sec__{mun}__{s['nombre']}"
                sfoto = dicebear_url(s["nombre"])
                net.add_node(sid, label=s["nombre"][:22],
                             size=22, shape="circularImage", image=sfoto,
                             color={"border":"#3B82F6",
                                    "highlight":{"border":"#60A5FA","background":"#1E3A5F"}},
                             borderWidth=3, hidden=True,
                             title=(f"<div style='font-family:Courier New;'>"
                                    f"<b style='color:#60A5FA;'>🏛 SECRETARÍA</b><br>"
                                    f"<b style='color:#E2E8F0;'>{s['nombre']}</b><br>"
                                    f"<span style='color:#94A3B8;'>{s['cargo']}</span><br>"
                                    f"<span style='color:#475569;font-size:.75rem;'>{mun}</span>"
                                    f"</div>"),
                             font={"size":9,"color":"#93C5FD","face":"Courier New"})
                net.add_edge(mun, sid, color={"color":"#3B82F666"},
                             width=2, hidden=True, dashes=True)

            # Concejales ocultos con foto DiceBear
            for c in [x for x in conc_data if x["municipio"] == mun][:7]:
                cid = f"conc__{mun}__{c['nombre']}"
                bc = hex_bloque(c.get("bloque",""))
                cfoto = dicebear_url(c["nombre"])
                net.add_node(cid, label=c["nombre"][:22],
                             size=18, shape="circularImage", image=cfoto,
                             color={"border":bc,
                                    "highlight":{"border":"#FFFFFF","background":bc+"33"}},
                             borderWidth=3, hidden=True,
                             title=(f"<div style='font-family:Courier New;'>"
                                    f"<b style='color:{bc};'>🗳 CONCEJAL #{c.get('n_orden','')}</b><br>"
                                    f"<b style='color:#E2E8F0;'>{c['nombre']}</b><br>"
                                    f"<span style='color:{bc};'>{c.get('bloque','')}</span><br>"
                                    f"<span style='color:#94A3B8;font-size:.75rem;'>Partido: {c.get('partido','')}</span><br>"
                                    f"<span style='color:#475569;font-size:.75rem;'>{mun}</span>"
                                    f"</div>"),
                             font={"size":9,"color":"#CBD5E1","face":"Courier New"})
                net.add_edge(mun, cid, color={"color":bc+"55"},
                             width=1.5, hidden=True, dashes=True)

        # Legisladores opcionales
        if show_leg:
            for row in leg_data.get("diputados_prov", []):
                nid = f"dip_{row['nombre']}"
                color = hex_bloque(row.get("bloque",""))
                lfoto = dicebear_url(row["nombre"], style="notionists-neutral")
                sec_leg = next((s for s in df_int["seccion_nombre"].unique()
                                if str(row.get("seccion","")) in s), None)
                net.add_node(nid, label=row["nombre"][:20], size=14,
                             shape="circularImage", image=lfoto,
                             color={"border":color,"highlight":{"border":"#FFFFFF","background":color+"33"}},
                             borderWidth=2,
                             title=f"<b>Diputado Prov.</b><br>{row['nombre']}<br>{row.get('bloque','')}",
                             font={"size":8,"color":"#94A3B8","face":"Courier New"})
                parent = sec_leg if (sec_leg and show_sec) else "PBA"
                net.add_edge(parent, nid, color={"color":color+"44"}, width=0.8, dashes=True)

        html = net.generate_html()

        inject = """
<style>
body { margin:0; padding:0; background:#070B14; overflow:hidden; }
#mynetwork {
  background: #070B14 !important;
  background-image:
    linear-gradient(rgba(0,255,136,0.022) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,255,136,0.022) 1px, transparent 1px);
  background-size: 50px 50px;
  border: 1px solid #1E3A5F;
}
#osint-hud {
  position:fixed; bottom:0; left:0; right:0;
  background:rgba(7,11,20,0.93);
  border-top:1px solid #1E3A5F;
  padding:6px 16px;
  font-family:'Courier New',monospace;
  font-size:11px; color:#475569;
  display:flex; gap:20px; align-items:center; z-index:999;
}
#hud-sel { color:#3B82F6; }
#hud-exp { color:#00FF88; font-weight:700; }
</style>
<div id="osint-hud">
  <span>🕵 OSINT PBA</span>
  <span id="hud-sel">— sin selección —</span>
  <span id="hud-exp"></span>
  <span style="margin-left:auto;color:#1E3A5F;">CLICK=expandir · DBL-CLICK fondo=colapsar todo</span>
</div>
<script type="text/javascript">
(function(){
  var expanded={};
  function isDetail(id){var s=String(id);return s.startsWith("sec__")||s.startsWith("conc__");}
  function isMun(id){var s=String(id);return s!=="PBA"&&!s.startsWith("sec__")&&!s.startsWith("conc__")&&!s.startsWith("dip_")&&s.indexOf("ª")===-1;}

  network.on("click",function(p){
    if(!p.nodes.length){document.getElementById("hud-sel").textContent="— sin selección —";return;}
    var id=String(p.nodes[0]);
    document.getElementById("hud-sel").innerHTML="<b>"+id+"</b>";
    if(!isMun(id))return;
    var isExp=!!expanded[id]; expanded[id]=!isExp;
    var nu=[],eu=[];
    network.getConnectedNodes(id).forEach(function(cid){
      if(isDetail(cid)){var n=nodes.get(cid);if(n)nu.push({id:cid,hidden:isExp});}
    });
    network.getConnectedEdges(id).forEach(function(eid){
      var e=edges.get(eid);if(e&&isDetail(e.to))eu.push({id:eid,hidden:isExp});
    });
    nodes.update(nu); edges.update(eu);
    var cnt=Object.keys(expanded).filter(function(k){return expanded[k];}).length;
    document.getElementById("hud-exp").textContent=cnt?"▶ "+cnt+" expandido(s)":"";
    if(!isExp){network.focus(id,{scale:1.6,animation:{duration:700,easingFunction:"easeInOutCubic"}});}
    else{network.fit({animation:{duration:500,easingFunction:"easeInOutQuad"}});}
  });
  network.on("doubleClick",function(p){
    if(p.nodes.length)return;
    var nu=[],eu=[];
    nodes.get().forEach(function(n){if(isDetail(n.id))nu.push({id:n.id,hidden:true});});
    edges.get().forEach(function(e){if(isDetail(e.to))eu.push({id:e.id,hidden:true});});
    nodes.update(nu);edges.update(eu);
    expanded={};document.getElementById("hud-exp").textContent="";
    network.fit({animation:{duration:500}});
  });
})();
</script>"""
        html = html.replace("</body>", inject + "\n</body>")
        return html

    net_html = build_network_html(sec_sel, blq_sel, show_secciones, show_legislators, physics_on)
    components.html(net_html, height=730, scrolling=False)


# ════════════════════════════════════════════════════════════════════════
# TAB 2 – PIRÁMIDE DE MANDO
# ════════════════════════════════════════════════════════════════════════
with tab2:

    def make_person_card(name, role, foto_url, color, extra_lines=None, size="md"):
        """Genera HTML de una tarjeta persona con foto circular."""
        w = {"sm": 120, "md": 150, "lg": 200}[size]
        ph = {"sm": 64, "md": 80, "lg": 110}[size]
        fn = {"sm": 9, "md": 10, "lg": 13}[size]
        rn = {"sm": 8, "md": 9, "lg": 11}[size]
        fallback = avatar_url(name, "Otro")
        extra_html = ""
        for line in (extra_lines or []):
            extra_html += f"<div style='color:#94A3B8;font-size:{rn}px;margin-top:2px;text-align:center;font-family:Courier New;'>{line}</div>"

        return f"""
<div class="pcard" style="width:{w}px;--c:{color};">
  <div class="pphoto-wrap" style="width:{ph}px;height:{ph}px;">
    <img src="{foto_url}"
         onerror="this.onerror=null;this.src='{fallback}'"
         style="width:{ph}px;height:{ph}px;border-radius:50%;object-fit:cover;
                border:3px solid {color};display:block;" />
    <div class="pring" style="border-color:{color};width:{ph+10}px;height:{ph+10}px;
         top:-5px;left:-5px;"></div>
  </div>
  <div style="color:#E2E8F0;font-size:{fn}px;font-weight:700;font-family:'Courier New';
       text-align:center;margin-top:8px;line-height:1.3;word-break:break-word;
       max-width:{w-10}px;">{name}</div>
  <div style="color:{color};font-size:{rn}px;text-align:center;font-family:'Courier New';
       margin-top:3px;font-weight:600;">{role}</div>
  {extra_html}
</div>"""

    def make_organigrama_html(mun):
        int_row   = next((r for r in ints if r["municipio"] == mun), {})
        mun_secs  = secs_data.get(mun, [])
        mun_conc  = [c for c in conc_data if c["municipio"] == mun]
        color     = hex_bloque(int_row.get("bloque", ""))
        intend    = int_row.get("intendente", mun)
        partido   = int_row.get("partido", "")
        pct       = int_row.get("ganador_pct", "")
        padron    = int_row.get("padron", 0) or 0
        seccion   = int_row.get("seccion_nombre", "")
        n_secs    = len(mun_secs)
        n_conc    = len(mun_conc)
        foto_int  = fotos_ints.get(mun) or dicebear_url(intend)

        # ── Intendente card ──
        int_card = make_person_card(
            intend, "INTENDENTE", foto_int, color,
            extra_lines=[
                int_row.get("bloque", ""),
                f"Partido: {partido}",
                f"Resultado 2023: <b style='color:{color}'>{pct}%</b>",
                f"Padrón: {padron:,}",
                f"{seccion}",
                f"Secretarías: {n_secs}  ·  Concejales: {n_conc}",
            ], size="lg"
        )

        # ── Secretarios cards ──
        sec_cards = ""
        for s in mun_secs:
            sfoto = dicebear_url(s["nombre"])
            sec_cards += make_person_card(
                s["nombre"], s["cargo"][:30], sfoto, "#3B82F6",
                size="md"
            )

        # ── Concejales por bloque ──
        conc_by_bloque = {}
        for c in mun_conc:
            b = c.get("bloque", "Otro")
            conc_by_bloque.setdefault(b, []).append(c)
        conc_bloques_html = ""
        for blq, concejales in sorted(conc_by_bloque.items(), key=lambda x: -len(x[1])):
            bc = hex_bloque(blq)
            cards_blq = ""
            for c in concejales:
                cfoto = dicebear_url(c["nombre"])
                cards_blq += make_person_card(
                    c["nombre"], f"#{c.get('n_orden','')} · {c.get('partido','')[:20]}",
                    cfoto, bc, size="sm"
                )
            conc_bloques_html += f"""
<div style="margin-bottom:24px;">
  <div style="font-family:'Courier New';font-size:11px;color:{bc};
       font-weight:700;letter-spacing:2px;text-transform:uppercase;
       margin-bottom:12px;padding:4px 12px;
       background:{bc}22;border-left:3px solid {bc};border-radius:4px;
       display:inline-block;">
    {blq} ({len(concejales)})
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:12px;">{cards_blq}</div>
</div>"""

        section_connector = """
<div style="display:flex;flex-direction:column;align-items:center;margin:4px 0;">
  <div style="width:2px;height:24px;background:linear-gradient(#1E3A5F,#3B82F6);"></div>
  <div style="width:40px;height:2px;background:#1E3A5F;"></div>
  <div style="width:2px;height:16px;background:#1E3A5F;"></div>
</div>"""

        return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: #070B14;
  background-image:
    linear-gradient(rgba(0,255,136,0.018) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,255,136,0.018) 1px, transparent 1px);
  background-size: 48px 48px;
  font-family: 'Courier New', monospace;
  padding: 24px;
  min-height: 100vh;
}}
.pcard {{
  background: #0D1425;
  border: 1px solid var(--c);
  border-radius: 10px;
  padding: 14px 10px;
  display: flex; flex-direction: column; align-items: center;
  transition: all 0.25s;
  cursor: default;
  box-shadow: 0 0 0 transparent;
}}
.pcard:hover {{
  box-shadow: 0 0 18px var(--c);
  transform: translateY(-3px) scale(1.03);
  border-color: #FFFFFF;
  z-index: 2;
}}
.pphoto-wrap {{ position:relative; flex-shrink:0; }}
.pring {{
  position: absolute;
  border-radius: 50%;
  border: 1.5px solid currentColor;
  opacity: 0.3;
  animation: ringpulse 2.5s ease-in-out infinite;
  pointer-events: none;
}}
@keyframes ringpulse {{
  0%,100% {{ opacity:0.3; transform:scale(1); }}
  50%      {{ opacity:0.08; transform:scale(1.08); }}
}}
.section-block {{
  background: #0A0F1E;
  border: 1px solid #1E3A5F;
  border-radius: 10px;
  padding: 20px 24px;
  margin-bottom: 8px;
}}
.section-title {{
  font-size: 11px; letter-spacing: 3px; font-weight: 700;
  text-transform: uppercase; margin-bottom: 16px;
  padding-bottom: 8px;
}}
.v-connector {{
  width: 2px; height: 32px; margin: 0 auto;
}}
.h-bar {{
  height: 2px; border-radius: 1px;
}}
</style>
</head><body>

<!-- HEADER MUNICIPIO -->
<div style="border:1px solid {color};border-left:4px solid {color};
     border-radius:8px;padding:14px 20px;margin-bottom:24px;
     background:linear-gradient(135deg,#0A0F1E,#070B14);">
  <div style="color:{color};font-size:1.3rem;font-weight:700;letter-spacing:3px;">{mun.upper()}</div>
  <div style="color:#475569;font-size:.75rem;margin-top:4px;">
    {seccion} &nbsp;·&nbsp; {int_row.get("bloque","")} &nbsp;·&nbsp;
    Padrón: {padron:,} &nbsp;·&nbsp; {n_secs} secretarías &nbsp;·&nbsp; {n_conc} concejales
  </div>
</div>

<!-- NIVEL 0: INTENDENTE -->
<div style="display:flex;justify-content:center;margin-bottom:4px;">
  {int_card}
</div>

<!-- CONECTOR -->
<div class="v-connector" style="background:linear-gradient({color},{color}55);"></div>
<div style="text-align:center;margin-bottom:4px;">
  <span style="font-size:10px;color:#1E3A5F;letter-spacing:2px;">ORGANIGRAMA · ESTRUCTURA DE GOBIERNO</span>
</div>
<div class="v-connector" style="background:linear-gradient({color}55,#3B82F6);"></div>

<!-- NIVEL 1: SECRETARÍAS -->
<div class="section-block" style="border-color:#3B82F622;">
  <div class="section-title" style="color:#3B82F6;border-bottom:1px solid #3B82F622;">
    🏛 SECRETARÍAS Y ÁREAS DE GOBIERNO ({n_secs})
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:14px;justify-content:center;">
    {sec_cards if sec_cards else "<div style='color:#334155;font-size:11px;'>Sin datos de secretarías</div>"}
  </div>
</div>

<!-- CONECTOR -->
<div class="v-connector" style="background:linear-gradient(#3B82F6,#A855F7);"></div>

<!-- NIVEL 2: CONCEJO DELIBERANTE -->
<div class="section-block" style="border-color:#A855F722;">
  <div class="section-title" style="color:#A855F7;border-bottom:1px solid #A855F722;">
    🗳 CONCEJO DELIBERANTE ({n_conc} concejales)
  </div>
  {conc_bloques_html if conc_bloques_html else "<div style='color:#334155;font-size:11px;'>Sin datos de concejales</div>"}
</div>

<div style="height:40px;"></div>
</body></html>"""

    if mun_sel == "— seleccionar —":
        # Mostrar grilla de municipios grandes como preview
        st.markdown("""
        <div style='text-align:center;padding:40px 20px;color:#334155;font-family:monospace;'>
          <div style='font-size:2.5rem;'>🏛</div>
          <div style='font-size:1rem;margin-top:10px;color:#475569;'>
            Seleccioná un <b style='color:#00FF88;'>municipio</b> en el sidebar
          </div>
          <div style='font-size:.8rem;color:#1E3A5F;margin-top:6px;'>
            Ver: intendente → secretarías → concejales con foto
          </div>
        </div>""", unsafe_allow_html=True)

        # Preview: los 12 municipios más grandes
        st.markdown("#### Municipios más grandes del GBA")
        gba = df_int[df_int["seccion_nombre"].isin(
            ["1ª – Norte Conurbano","3ª – Sur Conurbano"])
        ].sort_values("padron", ascending=False).head(12)

        cols = st.columns(4)
        for i, (_, r) in enumerate(gba.iterrows()):
            c = cols[i % 4]
            color = hex_bloque(r["bloque"])
            foto = fotos_ints.get(r["municipio"]) or dicebear_url(r["intendente"])
            with c:
                st.markdown(f"""
                <div style='background:#0D1425;border:1px solid {color}44;border-top:3px solid {color};
                     border-radius:8px;padding:12px;text-align:center;margin-bottom:12px;'>
                  <img src="{foto}" style='width:60px;height:60px;border-radius:50%;
                       border:2px solid {color};object-fit:cover;display:block;margin:0 auto 8px;'/>
                  <div style='color:#E2E8F0;font-weight:700;font-family:monospace;font-size:.82rem;'>
                    {r['municipio']}</div>
                  <div style='color:#94A3B8;font-family:monospace;font-size:.72rem;margin-top:2px;'>
                    {r['intendente']}</div>
                  <div style='color:{color};font-family:monospace;font-size:.68rem;margin-top:3px;'>
                    {r['bloque']}</div>
                  <div style='color:#334155;font-family:monospace;font-size:.65rem;margin-top:3px;'>
                    Padrón: {r["padron"]:,}</div>
                </div>""", unsafe_allow_html=True)
    else:
        org_html = make_organigrama_html(mun_sel)
        components.html(org_html, height=900, scrolling=True)


# ════════════════════════════════════════════════════════════════════════
# TAB 3 – DISTRIBUCIÓN POLÍTICA
# ════════════════════════════════════════════════════════════════════════
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Intendentes por bloque")
        blq_counts = df_int["bloque"].value_counts().reset_index()
        blq_counts.columns = ["bloque","n"]
        fig = go.Figure(go.Bar(
            x=blq_counts["n"], y=blq_counts["bloque"], orientation="h",
            marker_color=[hex_bloque(b) for b in blq_counts["bloque"]],
            text=blq_counts["n"], textposition="outside",
            textfont=dict(family="Courier New", color="#94A3B8"),
        ))
        fig.update_layout(height=280, paper_bgcolor="#070B14", plot_bgcolor="#0D1425",
                          xaxis=dict(gridcolor="#1E3A5F",color="#475569"),
                          yaxis=dict(color="#94A3B8"),
                          font=dict(family="Courier New",color="#94A3B8"),
                          margin=dict(t=10,b=10,l=10,r=80))
        st.plotly_chart(fig, use_container_width=True, key="dist_int_blq")

        st.markdown("#### Concejales totales PBA por bloque (top 15)")
        bq = df_conc["bloque"].value_counts().head(15).reset_index()
        bq.columns = ["bloque","n"]
        fig2 = go.Figure(go.Bar(
            x=bq["n"], y=bq["bloque"], orientation="h",
            marker_color=[hex_bloque(b) for b in bq["bloque"]],
            text=bq["n"], textposition="outside",
            textfont=dict(family="Courier New", color="#94A3B8"),
        ))
        fig2.update_layout(height=350, paper_bgcolor="#070B14", plot_bgcolor="#0D1425",
                           xaxis=dict(gridcolor="#1E3A5F",color="#475569"),
                           yaxis=dict(color="#94A3B8"),
                           font=dict(family="Courier New",color="#94A3B8"),
                           margin=dict(t=10,b=10,l=10,r=80))
        st.plotly_chart(fig2, use_container_width=True, key="dist_conc_blq")

    with c2:
        st.markdown("#### Mapa de poder: intendentes por sección y bloque")
        sb = df_int.groupby(["seccion_nombre","bloque"]).size().reset_index(name="n")
        fig3 = go.Figure()
        for blq in sb["bloque"].unique():
            d = sb[sb["bloque"]==blq]
            fig3.add_trace(go.Bar(name=blq, x=d["seccion_nombre"].str[:20], y=d["n"],
                                  marker_color=hex_bloque(blq),
                                  text=d["n"], textposition="inside",
                                  textfont=dict(family="Courier New",size=10)))
        fig3.update_layout(barmode="stack", height=320,
                           paper_bgcolor="#070B14", plot_bgcolor="#0D1425",
                           xaxis=dict(gridcolor="#1E3A5F",color="#475569",
                                      tickangle=-20,tickfont=dict(size=9,family="Courier New")),
                           yaxis=dict(gridcolor="#1E3A5F",color="#475569"),
                           font=dict(family="Courier New",color="#94A3B8"),
                           legend=dict(bgcolor="#0D1425",bordercolor="#1E3A5F"),
                           margin=dict(t=10,b=80,l=10,r=10))
        st.plotly_chart(fig3, use_container_width=True, key="sec_blq_stack")

        st.markdown("#### Legisladores PBA por bloque")
        leg_all = []
        for rol, df_l in [("Dip. Prov.",df_dp),("Sen. Prov.",df_sp),("Dip. Nac.",df_dn)]:
            if "bloque" in df_l.columns:
                for _, r in df_l.iterrows():
                    leg_all.append({"bloque":r["bloque"],"rol":rol})
        if leg_all:
            df_la = pd.DataFrame(leg_all)
            lb = df_la.groupby(["bloque","rol"]).size().reset_index(name="n")
            fig4 = go.Figure()
            for rol in ["Dip. Prov.","Sen. Prov.","Dip. Nac."]:
                d = lb[lb["rol"]==rol]
                if len(d):
                    fig4.add_trace(go.Bar(name=rol, x=d["bloque"].str[:20], y=d["n"],
                                          marker_color=[hex_bloque(b) for b in d["bloque"]],
                                          text=d["n"], textposition="inside",
                                          textfont=dict(family="Courier New",size=9)))
            fig4.update_layout(barmode="group", height=280,
                               paper_bgcolor="#070B14", plot_bgcolor="#0D1425",
                               xaxis=dict(gridcolor="#1E3A5F",color="#475569",
                                          tickangle=-20,tickfont=dict(size=8,family="Courier New")),
                               yaxis=dict(gridcolor="#1E3A5F",color="#475569"),
                               font=dict(family="Courier New",color="#94A3B8"),
                               legend=dict(bgcolor="#0D1425",bordercolor="#1E3A5F"),
                               margin=dict(t=10,b=80,l=10,r=10))
            st.plotly_chart(fig4, use_container_width=True, key="leg_blq")


# ════════════════════════════════════════════════════════════════════════
# TAB 4 – BÚSQUEDA OSINT
# ════════════════════════════════════════════════════════════════════════
with tab4:
    col_s, col_f = st.columns([3,1])
    with col_s:
        search_q = st.text_input("Buscar nombre, cargo o municipio", value=busqueda,
                                  placeholder="Ej: García, Secretario Salud, La Matanza...",
                                  key="osint_search_main")
    with col_f:
        tipo_busq = st.selectbox("Tipo",
                                  ["Todos","Intendentes","Secretarios","Concejales","Legisladores"],
                                  key="osint_tipo")

    if search_q and len(search_q) >= 2:
        q = search_q.lower().strip()
        results = []

        if tipo_busq in ("Todos","Intendentes"):
            for r in ints:
                if any(q in (r.get(f,"") or "").lower()
                       for f in ["intendente","municipio","partido","bloque"]):
                    results.append({"tipo":"INTENDENTE","nombre":r["intendente"],
                                    "cargo":"Intendente","municipio":r["municipio"],
                                    "partido":r.get("bloque",""),
                                    "extra":f"Secc. {r.get('seccion_nombre','')} · {r.get('ganador_pct','')}% · Padrón {r.get('padron',0):,}",
                                    "color":hex_bloque(r.get("bloque","")),
                                    "foto": fotos_ints.get(r["municipio"]) or dicebear_url(r["intendente"])})

        if tipo_busq in ("Todos","Secretarios"):
            for mun, sl in secs_data.items():
                for s in sl:
                    if q in s["nombre"].lower() or q in s["cargo"].lower() or q in mun.lower():
                        results.append({"tipo":"SECRETARIO","nombre":s["nombre"],
                                        "cargo":s["cargo"],"municipio":mun,
                                        "partido":"","extra":"",
                                        "color":"#3B82F6","foto":dicebear_url(s["nombre"])})

        if tipo_busq in ("Todos","Concejales"):
            for c in conc_data:
                if any(q in (c.get(f,"") or "").lower()
                       for f in ["nombre","municipio","bloque","partido"]):
                    results.append({"tipo":"CONCEJAL",
                                    "nombre":c["nombre"],
                                    "cargo":f"Concejal #{c.get('n_orden','')}",
                                    "municipio":c["municipio"],
                                    "partido":c.get("bloque",""),
                                    "extra":f"{c.get('seccion_nombre','')} · Partido: {c.get('partido','')}",
                                    "color":hex_bloque(c.get("bloque","")),
                                    "foto":dicebear_url(c["nombre"])})

        if tipo_busq in ("Todos","Legisladores"):
            for df_l, tipo_l, rol in [(df_dp,"DIP. PROV.","Diputado Prov."),
                                       (df_sp,"SEN. PROV.","Senador Prov."),
                                       (df_dn,"DIP. NAC.","Diputado Nac.")]:
                if "nombre" in df_l.columns:
                    for _, r in df_l.iterrows():
                        if q in r["nombre"].lower() or q in r.get("bloque","").lower():
                            results.append({"tipo":tipo_l,"nombre":r["nombre"],
                                            "cargo":rol,"municipio":"PBA",
                                            "partido":r.get("bloque",""),
                                            "extra":f"Secc. {r.get('seccion','')}",
                                            "color":hex_bloque(r.get("bloque","")),
                                            "foto":dicebear_url(r["nombre"],"notionists-neutral")})

        st.markdown(f"<div style='font-family:monospace;color:#00FF88;font-size:.8rem;margin-bottom:12px;'>"
                    f"▶ {len(results)} resultados</div>", unsafe_allow_html=True)

        cols_r = st.columns(3)
        for i, r in enumerate(results[:60]):
            with cols_r[i % 3]:
                st.markdown(f"""
                <div style='background:#0D1425;border:1px solid {r["color"]}44;
                     border-left:3px solid {r["color"]};border-radius:8px;
                     padding:12px;margin-bottom:10px;display:flex;gap:10px;align-items:center;'>
                  <img src="{r['foto']}" style='width:48px;height:48px;border-radius:50%;
                       border:2px solid {r["color"]};object-fit:cover;flex-shrink:0;'
                       onerror="this.src='https://ui-avatars.com/api/?name={urllib.parse.quote(r["nombre"])}&background=64748B&color=fff&size=100'"
                  />
                  <div>
                    <div style='font-size:.6rem;color:{r["color"]};letter-spacing:2px;
                          font-family:monospace;font-weight:700;'>{r["tipo"]}</div>
                    <div style='color:#E2E8F0;font-weight:700;font-family:monospace;
                          font-size:.82rem;margin-top:2px;line-height:1.3;'>{r["nombre"]}</div>
                    <div style='color:#64748B;font-size:.7rem;font-family:monospace;'>
                      {r["cargo"]} · {r["municipio"]}</div>
                    {"<div style='color:"+r["color"]+";font-size:.68rem;font-family:monospace;'>"+r["partido"]+"</div>" if r["partido"] else ""}
                    {"<div style='color:#334155;font-size:.65rem;font-family:monospace;'>"+r["extra"]+"</div>" if r["extra"] else ""}
                  </div>
                </div>""", unsafe_allow_html=True)

        if len(results) > 60:
            st.markdown(f"<div style='color:#475569;font-size:.75rem;font-family:monospace;'>"
                        f"... y {len(results)-60} más. Refiná la búsqueda.</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='text-align:center;padding:60px;color:#334155;font-family:monospace;'>
          <div style='font-size:2.5rem;'>🔍</div>
          <div style='font-size:.95rem;margin-top:10px;color:#475569;'>
            Buscá por nombre, cargo, partido o municipio
          </div>
          <div style='font-size:.75rem;color:#1E3A5F;margin-top:6px;'>
            ~2,000 personas · intendentes · secretarios · concejales · legisladores
          </div>
        </div>""", unsafe_allow_html=True)

# ── Footer ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='font-family:monospace;color:#1E3A5F;font-size:.68rem;text-align:center;'>
OSINT · DATOS: JEPBA 2023 · datos.gba.gob.ar · HCDN · Fotos: Wikipedia / DiceBear AI Personas
</div>""", unsafe_allow_html=True)
