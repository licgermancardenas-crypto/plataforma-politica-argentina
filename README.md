# Plataforma Política Argentina

> **Inteligencia política en tiempo real para la Provincia de Buenos Aires y la Ciudad Autónoma de Buenos Aires.**

Una aplicación web interactiva que centraliza datos electorales, legislativos y económicos de Argentina, cruzando información estática de los escrutinios 2023 con APIs oficiales en vivo del Congreso Nacional, el INDEC y ArgentinaDatos.

[![Streamlit](https://img.shields.io/badge/Streamlit-1.58-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Demo en vivo

🔗 **[plataforma-politica-argentina.streamlit.app](https://plataforma-politica-argentina.streamlit.app)**

---

## Funcionalidades

| Módulo | Descripción |
|--------|-------------|
| **Dashboard** | KPIs políticos y económicos en tiempo real, composición de bloques, inflación mensual |
| **Municipios PBA** | Ficha detallada de los 135 municipios bonaerenses con datos electorales, demográficos y legislativos |
| **Mapa Interactivo** | Mapa Folium dark-mode con zoom automático al municipio, panel intel lateral, capas de radios censales |
| **CABA** | Mapa de las 15 comunas con resultados Jefe de Gobierno 2023 por sección |
| **Congreso Nacional** | Composición de bloques de la Cámara de Diputados en tiempo real (HCDN live) |
| **Legisladores PBA** | Diputados y Senadores provinciales 2023-2027, filtros por sección |
| **Economía** | Dólar (7 tipos), Riesgo País, Inflación BCRA vs INDEC, EMAE, tipo de cambio oficial |
| **Búsqueda Global** | Búsqueda full-text sobre intendentes, concejales y legisladores |

---

## Fuentes de datos

### Datos estáticos (escrutinio definitivo 2023)
| Fuente | Descripción |
|--------|-------------|
| **JEPBA** – Junta Electoral PBA | Resultados definitivos por municipio: intendentes, concejales, legisladores provinciales |
| **DINE** – Dirección Nac. Electoral | Diputados nacionales por PBA |
| **Datos Abiertos GCBA** | Resultados Jefe de Gobierno 2023 por mesa, GeoJSON de comunas |
| **INDEC Censo 2022** | Población, superficie y radios censales de los 135 municipios PBA |

### APIs en tiempo real
| API | Datos | TTL cache |
|-----|-------|-----------|
| **HCDN** – datos.hcdn.gob.ar | Bloques, composición, diputados históricos | 30 min |
| **INDEC Series de Tiempo** | IPC, tipo de cambio oficial, EMAE | 60 min |
| **ArgentinaDatos** | Dólar (blue/oficial/MEP/CCL/tarjeta), Riesgo País, Inflación BCRA, Senadores | 15–60 min |

---

## Arquitectura

```
plataforma-politica-argentina/
│
├── app.py                        # Dashboard principal (entry point)
│
├── pages/                        # Páginas Streamlit multi-page
│   ├── 1_Municipios_PBA.py       # Fichas de municipios bonaerenses
│   ├── 2_Congreso_Nacional.py    # Cámara de Diputados Nación (live)
│   ├── 3_Legisladores_PBA.py     # Legislatura bonaerense
│   ├── 4_Economia_Indicadores.py # Indicadores económicos
│   ├── 5_Busqueda_Global.py      # Búsqueda full-text
│   ├── 6_Mapa_Interactivo.py     # Mapa PBA (Folium + fit_bounds)
│   └── 7_CABA_Capital.py         # Mapa CABA por comunas
│
├── core/
│   ├── loader.py                 # Carga y normalización de datos estáticos
│   └── apis.py                   # Conectores API con st.cache_data + TTL
│
├── data/                         # Datos estáticos y GeoJSON
│   ├── municipios_pba.geojson    # 135 municipios PBA (enriquecido)
│   ├── comunas_caba.geojson      # 15 comunas CABA (con resultados 2023)
│   ├── radios_censales_2022.geojson
│   ├── intendentes.json          # 135 intendentes 2023-2027
│   ├── concejales_flat.json      # Concejales electos 2023
│   ├── legisladores.json         # Diputados y senadores PBA
│   ├── secretarios.json          # Secretarios municipales
│   └── elecciones_caba_2023.json # Resultados CABA por comuna
│
├── Dockerfile                    # Container Python 3.11 + libgdal
├── requirements.txt
└── .streamlit/config.toml        # Headless + tema dark
```

### Flujo de datos

```
Fuentes estáticas (JSON/GeoJSON)
        │
        ▼
   core/loader.py  ──────────────────────────────┐
   (normalización + BLOQUE_COLOR map)             │
                                                  ▼
APIs externas (HCDN / INDEC / ArgentinaDatos)   pages/
        │                                         │
        ▼                                         │
   core/apis.py                                   │
   (st.cache_data TTL 15-60 min)                  │
        │                                         │
        └──────────────────────────────────────► app.py
                                               (st.set_page_config
                                                KPI row
                                                sidebar nav)
```

### Stack técnico

| Capa | Tecnología |
|------|------------|
| **Frontend / UI** | Streamlit 1.58, HTML/CSS inyectado, dark mode |
| **Mapas** | Folium 0.20, streamlit-folium, CartoDB Dark tiles |
| **Geoespacial** | GeoPandas, Shapely (`fit_bounds` automático) |
| **Gráficos** | Plotly Express + Graph Objects |
| **HTTP / cache** | requests, `st.cache_data` con TTL por fuente |
| **Datos** | Pandas 3.0, GeoJSON, CSV |
| **Deploy** | Streamlit Community Cloud / Docker |

---

## Correr localmente

```bash
# 1. Clonar el repositorio
git clone https://github.com/licgermancardenas-crypto/plataforma-politica-argentina.git
cd plataforma-politica-argentina

# 2. Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Levantar la app
streamlit run app.py
```

La app queda disponible en `http://localhost:8501`.

### Con Docker

```bash
docker build -t plataforma-politica .
docker run -p 8501:8501 plataforma-politica
```

---

## Deploy

### Streamlit Community Cloud (recomendado)

1. Fork o conectá tu repo en [share.streamlit.io](https://share.streamlit.io)
2. Repository: `licgermancardenas-crypto/plataforma-politica-argentina`
3. Main file: `app.py`
4. Branch: `main`

### Docker (cualquier plataforma compatible)

El `Dockerfile` incluido soporta la variable de entorno `$PORT` para plataformas como Railway, Render o cualquier cloud provider.

---

## Cobertura geográfica

- **135 municipios** de la Provincia de Buenos Aires
- **15 comunas** de la Ciudad Autónoma de Buenos Aires (Capital Federal)
- Datos a nivel de **radio censal** (INDEC 2022) para el mapa interactivo

---

## Licencia

MIT © 2024 — datos electorales de uso público (JEPBA, DINE, GCBA, INDEC)
