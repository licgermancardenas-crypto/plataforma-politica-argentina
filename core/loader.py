"""
Carga los datasets estáticos desde data/*.json con cache de Streamlit.
Proporciona DataFrames listos para usar en las páginas.
"""
import os, json
import pandas as pd
import streamlit as st

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data')

# ── Colores por bloque político ────────────────────────────────────────
BLOQUE_COLOR = {
    'Unión por la Patria':    '#1B5E20',
    'La Libertad Avanza':     '#E65100',
    'Juntos por el Cambio':   '#1565C0',
    'UCR':                    '#6A1B9A',
    'FIT-U':                  '#B71C1C',
    'Vecinal':                '#F57F17',
    'Otro':                   '#546E7A',
}

BLOQUE_BG = {
    'Unión por la Patria':    '#E8F5E9',
    'La Libertad Avanza':     '#FFF3E0',
    'Juntos por el Cambio':   '#E3F2FD',
    'UCR':                    '#F3E5F5',
    'FIT-U':                  '#FFEBEE',
    'Vecinal':                '#FFFDE7',
    'Otro':                   '#ECEFF1',
}


def _load_json(filename):
    path = os.path.join(DATA, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def get_intendentes_df() -> pd.DataFrame:
    data = _load_json('intendentes.json')
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df['bloque_color'] = df['bloque'].map(BLOQUE_COLOR).fillna('#546E7A')
    return df


@st.cache_data(show_spinner=False)
def get_secretarios() -> dict:
    return _load_json('secretarios.json') or {}


@st.cache_data(show_spinner=False)
def get_concejales_df() -> pd.DataFrame:
    data = _load_json('concejales_flat.json')
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df['bloque_color'] = df['bloque'].map(BLOQUE_COLOR).fillna('#546E7A')
    return df


@st.cache_data(show_spinner=False)
def get_legisladores() -> dict:
    return _load_json('legisladores.json') or {}


@st.cache_data(show_spinner=False)
def get_diputados_prov_df() -> pd.DataFrame:
    leg = get_legisladores()
    return pd.DataFrame(leg.get('diputados_prov', []))


@st.cache_data(show_spinner=False)
def get_senadores_prov_df() -> pd.DataFrame:
    leg = get_legisladores()
    return pd.DataFrame(leg.get('senadores_prov', []))


@st.cache_data(show_spinner=False)
def get_diputados_nac_df() -> pd.DataFrame:
    leg = get_legisladores()
    return pd.DataFrame(leg.get('diputados_nac', []))


@st.cache_data(show_spinner=False)
def get_senadores_nac_df() -> pd.DataFrame:
    leg = get_legisladores()
    return pd.DataFrame(leg.get('senadores_nac', []))


def bloque_counts(df: pd.DataFrame, col: str = 'bloque') -> pd.DataFrame:
    """Conteo de registros por bloque para gráficos."""
    counts = df[col].value_counts().reset_index()
    counts.columns = ['bloque', 'cantidad']
    counts['color'] = counts['bloque'].map(BLOQUE_COLOR).fillna('#546E7A')
    return counts
