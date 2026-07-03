#!/usr/bin/env python3
"""
build_data_cache.py  –  ejecutar una vez para construir data/*.json
Convierte los datasets fuente en JSON limpios para la plataforma web.
"""
import os, json, csv, unicodedata, sys
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def _norm(s):
    s = s.lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn').replace('.', '').replace('  ', ' ')

# ══════════════════════════════════════════════════════════════════════
# 1. INTENDENTES + SECRETARIOS (del script base)
# ══════════════════════════════════════════════════════════════════════
print("Cargando INTENDENTES y SECRETARIOS...")
with open(os.path.join(BASE, 'crear_excel_intendentes.py'), encoding='utf-8') as f:
    _src = f.read()
_cut = _src.index('\n# ─────────────────────────────────────────────────────────────\n# ESTILOS')
_vars = {}
exec(_src[:_cut], _vars)
INTENDENTES = _vars['INTENDENTES']
SECRETARIOS = _vars['SECRETARIOS']

# ══════════════════════════════════════════════════════════════════════
# 2. DATOS LEGISLATIVOS (del script completo)
# ══════════════════════════════════════════════════════════════════════
print("Cargando datos legislativos...")
with open(os.path.join(BASE, 'crear_excel_completo.py'), encoding='utf-8') as f:
    _src2 = f.read()
# Extraer desde SECCION_ELECTORAL hasta wb = openpyxl.Workbook()
_start = _src2.index('SECCION_ELECTORAL = {')
_end   = _src2.index('\nwb = openpyxl.Workbook()')
_vars2 = {}
exec(_src2[_start:_end], _vars2)
SECCION_ELECTORAL = _vars2['SECCION_ELECTORAL']
SECCION_NOMBRE    = _vars2['SECCION_NOMBRE']
DIPUTADOS_PROV    = _vars2.get('DIPUTADOS_PROV', [])
SENADORES_PROV    = _vars2.get('SENADORES_PROV', [])
DIPUTADOS_NAC     = _vars2.get('DIPUTADOS_NAC', [])
SENADORES_NAC     = _vars2.get('SENADORES_NAC', [])

# ══════════════════════════════════════════════════════════════════════
# 3. RESULTADOS ELECTORALES 2023
# ══════════════════════════════════════════════════════════════════════
print("Cargando resultados electorales 2023...")
_CSV_MAP = {
    '25 de mayo':                   'Veinticinco de Mayo',
    'coronel de marina l rosales':  'Coronel Rosales',
    'general lamadrid':             'General La Madrid',
    'partido de la costa':          'La Costa',
}
_norm_to_muni = {_norm(m): m for m, _, _ in INTENDENTES}
_norm_to_muni.update({_norm(k): v for k, v in _CSV_MAP.items()})

RESULTADOS_2023 = {}
_csv_path = os.path.join(BASE, 'elecciones_pba_2005_2023.csv')
if os.path.exists(_csv_path):
    with open(_csv_path, encoding='latin-1') as f:
        rows = list(csv.DictReader(f))
    int_rows = [r for r in rows if r['eleccion'] == '2023' and r['cargo'] == 'Intendente'
                and r['lista'] not in ('VOTO EN BLANCO', 'VOTOS NULOS') and int(r['votos']) > 0]
    by_dist = defaultdict(list)
    for r in int_rows:
        by_dist[_norm(r['distrito'])].append(r)
    for norm_key, listas in by_dist.items():
        muni = _norm_to_muni.get(norm_key)
        if not muni:
            continue
        listas_s = sorted(listas, key=lambda x: int(x['votos']), reverse=True)
        total = sum(int(r['votos']) for r in listas_s)
        w  = listas_s[0]
        s2 = listas_s[1] if len(listas_s) > 1 else None
        RESULTADOS_2023[muni] = {
            'ganador':      w['lista'],
            'ganador_pct':  round(int(w['votos']) / total * 100, 1),
            'segundo':      s2['lista'] if s2 else '',
            'segundo_pct':  round(int(s2['votos']) / total * 100, 1) if s2 else 0,
            'margen':       round((int(w['votos']) - (int(s2['votos']) if s2 else 0)) / total * 100, 1),
            'padron':       int(w['votantes_habilitados']),
        }

# ══════════════════════════════════════════════════════════════════════
# 4. CONCEJALES 2023
# ══════════════════════════════════════════════════════════════════════
print("Cargando concejales 2023...")
CONCEJALES = {}
_conc_path = os.path.join(BASE, 'concejales_2023.json')
if os.path.exists(_conc_path):
    with open(_conc_path, encoding='utf-8') as f:
        raw_conc = json.load(f)
    _upper_to_muni = {_norm(m): m for m, _, _ in INTENDENTES}
    for dist_id, data in raw_conc.items():
        norm = _norm(data['distrito'])
        muni = _upper_to_muni.get(norm) or _upper_to_muni.get(_norm(_CSV_MAP.get(norm, '')))
        if muni:
            CONCEJALES[muni] = {
                'n_elige': data.get('n_elige'),
                'concejales': data.get('concejales', []),
            }

# ══════════════════════════════════════════════════════════════════════
# 5. CLASIFICACIÓN POLÍTICA
# ══════════════════════════════════════════════════════════════════════
def get_bloque(partido):
    p = partido.lower()
    if any(k in p for k in ('patria', 'frente de todos', 'peronismo', 'kirchner', 'pj')):
        return 'Unión por la Patria'
    if any(k in p for k in ('libertad avanza', 'avanza libertad')):
        return 'La Libertad Avanza'
    if any(k in p for k in ('juntos por el cambio', 'juntos somos', 'pro', 'cambiemos')):
        return 'Juntos por el Cambio'
    if any(k in p for k in ('ucr', 'radical')):
        return 'UCR'
    if any(k in p for k in ('fit', 'izquierda')):
        return 'FIT-U'
    if any(k in p for k in ('vecin', 'local', 'comun')):
        return 'Vecinal'
    return 'Otro'

# ══════════════════════════════════════════════════════════════════════
# 6. CONSTRUIR JSON DE SALIDA
# ══════════════════════════════════════════════════════════════════════

# --- intendentes.json ---
print("Generando intendentes.json...")
intendentes_data = []
for municipio, intendente, partido in INTENDENTES:
    seccion_n = SECCION_ELECTORAL.get(municipio, 0)
    res = RESULTADOS_2023.get(municipio, {})
    conc = CONCEJALES.get(municipio, {})
    intendentes_data.append({
        'municipio':    municipio,
        'intendente':   intendente,
        'partido':      partido,
        'bloque':       get_bloque(partido),
        'seccion':      seccion_n,
        'seccion_nombre': SECCION_NOMBRE.get(seccion_n, ''),
        'ganador_2023': res.get('ganador', ''),
        'ganador_pct':  res.get('ganador_pct', 0),
        'segundo':      res.get('segundo', ''),
        'segundo_pct':  res.get('segundo_pct', 0),
        'margen':       res.get('margen', 0),
        'padron':       res.get('padron', 0),
        'n_concejales': len(conc.get('concejales', [])),
        'n_secretarios': len(SECRETARIOS.get(municipio, [])),
    })
with open(os.path.join(DATA_DIR, 'intendentes.json'), 'w', encoding='utf-8') as f:
    json.dump(intendentes_data, f, ensure_ascii=False, indent=2)
print(f"  → {len(intendentes_data)} intendentes")

# --- secretarios.json ---
print("Generando secretarios.json...")
sec_data = {}
for muni, items in SECRETARIOS.items():
    sec_data[muni] = [{'nombre': s[0], 'cargo': s[1]} for s in items]
with open(os.path.join(DATA_DIR, 'secretarios.json'), 'w', encoding='utf-8') as f:
    json.dump(sec_data, f, ensure_ascii=False, indent=2)
print(f"  → {sum(len(v) for v in sec_data.values())} secretarios en {len(sec_data)} municipios")

# --- concejales_flat.json  (lista plana para filtros rápidos) ---
print("Generando concejales_flat.json...")
concejales_flat = []
for municipio, _, _ in INTENDENTES:
    data = CONCEJALES.get(municipio, {})
    seccion_n = SECCION_ELECTORAL.get(municipio, 0)
    for i, c in enumerate(data.get('concejales', []), 1):
        bloque = get_bloque(c.get('partido', ''))
        concejales_flat.append({
            'municipio':  municipio,
            'seccion':    seccion_n,
            'seccion_nombre': SECCION_NOMBRE.get(seccion_n, ''),
            'n_orden':    i,
            'nombre':     c.get('nombre', ''),
            'partido':    c.get('partido', ''),
            'bloque':     bloque,
        })
with open(os.path.join(DATA_DIR, 'concejales_flat.json'), 'w', encoding='utf-8') as f:
    json.dump(concejales_flat, f, ensure_ascii=False, indent=2)
print(f"  → {len(concejales_flat)} concejales")

# --- legisladores.json ---
print("Generando legisladores.json...")
leg_data = {
    'diputados_prov': [
        {'nombre': n, 'seccion': s, 'bloque': b}
        for n, s, b in DIPUTADOS_PROV
    ],
    'senadores_prov': [
        {'nombre': n, 'seccion': s, 'bloque': b}
        for n, s, b in SENADORES_PROV
    ],
    'diputados_nac': [
        {'nombre': n, 'bloque': b}
        for n, b in DIPUTADOS_NAC
    ],
    'senadores_nac': [
        {'nombre': n, 'bloque': b}
        for n, b in SENADORES_NAC
    ],
}
with open(os.path.join(DATA_DIR, 'legisladores.json'), 'w', encoding='utf-8') as f:
    json.dump(leg_data, f, ensure_ascii=False, indent=2)
print(f"  → {len(leg_data['diputados_prov'])} dip.prov / {len(leg_data['senadores_prov'])} sen.prov / "
      f"{len(leg_data['diputados_nac'])} dip.nac / {len(leg_data['senadores_nac'])} sen.nac")

print("\nCache generado correctamente en data/")
