"""
Live API connectors – HCDN (Congreso Nacional) + INDEC (datos económicos).
Todos usan st.cache_data con TTL para no saturar los servidores.
"""
import requests
import pandas as pd
from io import StringIO
import streamlit as st

TIMEOUT = 12

# ── HCDN – Cámara de Diputados de la Nación ──────────────────────────
_HCDN = {
    'bloques':         'https://datos.hcdn.gob.ar/dataset/b238e6ab-691a-4e64-91d9-1445c4506ef4/resource/02a14a9d-b868-4565-9a76-6f458e9227dd/download/listado_bloques_actualizado3.6.csv',
    'comp_bloques':    'https://datos.hcdn.gob.ar/dataset/b238e6ab-691a-4e64-91d9-1445c4506ef4/resource/237f85b1-0b99-42e4-9b64-31a3935870a2/download/composicion_actual_por_bloques3.6.csv',
    'interbloques':    'https://datos.hcdn.gob.ar/dataset/b238e6ab-691a-4e64-91d9-1445c4506ef4/resource/9bb8f5e9-c316-46b4-9ae5-d5681f349511/download/listado_interbloques_actualizado0.6.csv',
    'comp_interbl':    'https://datos.hcdn.gob.ar/dataset/b238e6ab-691a-4e64-91d9-1445c4506ef4/resource/d32d7640-22f6-460d-9a0c-2fe068f747d0/download/composicion_actual_por_interbloque0.6.csv',
    'diputados_hist':  'https://datos.hcdn.gob.ar/dataset/a80e0fa7-d73a-4ed1-9dec-80465e368951/resource/169de2eb-465f-4007-a4c2-39a5ba4c0df3/download/diputados_hist1.8.csv',
    'votaciones_cab':  'https://datos.hcdn.gob.ar/dataset/59fff38a-0a79-405b-a11b-29bc8722891b/resource/4a1f2093-c77a-4205-b53d-c5a0a8458e2c/download/actas-datos-generales-135.csv',
    'sesiones':        'https://datos.hcdn.gob.ar/dataset/f744ea10-83b4-4493-8bef-6fc9fb9e41e9/resource/',
}

def _fetch_csv(url, encoding='utf-8', **kwargs):
    try:
        r = requests.get(url, timeout=TIMEOUT, allow_redirects=True)
        r.raise_for_status()
        if 'text/html' in r.headers.get('Content-Type', ''):
            return None
        try:
            return pd.read_csv(StringIO(r.content.decode(encoding)), **kwargs)
        except UnicodeDecodeError:
            return pd.read_csv(StringIO(r.content.decode('latin-1')), **kwargs)
    except Exception:
        return None


@st.cache_data(ttl=1800, show_spinner=False)
def get_bloques_camara():
    """Composición actual de Cámara de Diputados por bloque (live)."""
    df = _fetch_csv(_HCDN['bloques'])
    if df is None:
        return None
    df.columns = [c.strip().upper() for c in df.columns]
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def get_composicion_bloques():
    """Lista de diputados por bloque (nombre, apellido, periodo, bloque)."""
    df = _fetch_csv(_HCDN['comp_bloques'])
    if df is None:
        return None
    df.columns = [c.strip().upper() for c in df.columns]
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def get_diputados_pba_actual():
    """Diputados nacionales de Buenos Aires en mandato vigente (live)."""
    df = _fetch_csv(_HCDN['diputados_hist'])
    if df is None:
        return None
    df.columns = [c.strip().upper() for c in df.columns]
    # Keep only Buenos Aires
    df = df[df['DISTRITO'].str.upper().str.contains('BUENOS AIRES', na=False)].copy()
    # Filter current mandates: MANDATO column is "YYYY-YYYY"; keep end year >= current year
    if 'MANDATO' in df.columns:
        df['_fin_año'] = df['MANDATO'].str.extract(r'(\d{4})$').astype(float)
        df = df[df['_fin_año'] >= 2026].drop(columns=['_fin_año'])
    elif 'FIN' in df.columns:
        df['FIN'] = pd.to_datetime(df['FIN'], errors='coerce')
        df = df[df['FIN'] >= pd.Timestamp('2025-01-01')]
    return df.sort_values('APELLIDO')


@st.cache_data(ttl=1800, show_spinner=False)
def get_votaciones_recientes(n: int = 30):
    """Últimas N sesiones de votación nominal período 135 (live)."""
    df = _fetch_csv(_HCDN['votaciones_cab'])
    if df is None:
        return None
    df.columns = [c.strip().upper() for c in df.columns]
    date_col = next((c for c in df.columns if 'FECHA' in c), None)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.sort_values(date_col, ascending=False)
    return df.head(n)


# ── INDEC – Series de Tiempo ──────────────────────────────────────────
_INDEC_BASE = 'https://apis.datos.gob.ar/series/api/series/'

_SERIES = {
    'ipc':         '148.3_INIVELNAL_DICI_M_26',   # IPC Nivel General (mensual, base dic 2016)
    'ipc_alim':    '148.3_IALIMYDEB_DICI_M_27',    # IPC Alimentos
    'ipc_ropa':    '148.3_IINDUMENT_DICI_M_33',    # IPC Indumentaria
    'dolar_oficial': '168.1_T_CAMBIOR_0_0_32',      # Tipo de cambio oficial
    'emae':        '143.3_NO_PR_2004_A_21',         # EMAE (actividad económica)
}


def _fetch_series(series_id: str, last: int = 24):
    try:
        url = f"{_INDEC_BASE}?ids={series_id}&last={last}&format=json"
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        rows = data.get('data', [])
        if not rows:
            return None
        df = pd.DataFrame(rows, columns=['fecha', 'valor'])
        df['fecha'] = pd.to_datetime(df['fecha'])
        return df
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_ipc(months: int = 24):
    """IPC Nivel General mensual, últimos N meses."""
    df = _fetch_series(_SERIES['ipc'], months)
    if df is None:
        return None
    df['var_mensual_pct']     = df['valor'].pct_change() * 100
    df['var_interanual_pct']  = df['valor'].pct_change(12) * 100
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def get_ipc_alimentos(months: int = 24):
    """IPC Alimentos y Bebidas mensual."""
    return _fetch_series(_SERIES['ipc_alim'], months)


@st.cache_data(ttl=3600, show_spinner=False)
def get_dolar_oficial(months: int = 24):
    """Tipo de cambio oficial (pesos por dólar), mensual."""
    return _fetch_series(_SERIES['dolar_oficial'], months)


@st.cache_data(ttl=3600, show_spinner=False)
def get_emae(months: int = 36):
    """Estimador Mensual de Actividad Económica (EMAE)."""
    return _fetch_series(_SERIES['emae'], months)
