---
name: dashboard-generator
description: |
  Creación de dashboards interactivos con Streamlit desde datos JSON.
  Activa cuando el usuario menciona: crear dashboard, visualización interactiva,
  streamlit, gráficos, KPIs, reportes visuales, métricas, tabla interactiva,
  filtros, selectores, dashboard financiero, dashboard de ventas.
  
  Pipeline: JSON/CSV → Template Streamlit → Dashboard Interactivo
  
  Enfoque en dashboards limpios, profesionales y fáciles de usar.
---

# Generador de Dashboards Streamlit

## Propósito
Crear dashboards interactivos y profesionales usando Streamlit,
partiendo de datos estructurados en JSON o CSV.

## Cuándo Usar Esta Skill
- Visualizar resultados de análisis
- Crear interfaces para explorar datos
- Presentar KPIs y métricas
- Generar reportes interactivos
- Crear herramientas de exploración de datos

## Principios de Diseño

### 1. Jerarquía Visual Clara
```
┌─────────────────────────────────────────────────────────────┐
│  TÍTULO Y CONTEXTO (qué estoy viendo, período, filtros)    │
├─────────────────────────────────────────────────────────────┤
│  KPIs PRINCIPALES (4-6 métricas clave en cards)            │
├─────────────────────────────────────────────────────────────┤
│  GRÁFICOS PRINCIPALES (tendencias, comparativas)           │
├─────────────────────────────────────────────────────────────┤
│  DETALLES Y TABLAS (datos granulares, drill-down)          │
└─────────────────────────────────────────────────────────────┘
```

### 2. Menos es Más
- Máximo 6 KPIs en el header
- Máximo 4 gráficos por vista
- Usar tabs para organizar secciones
- Evitar scroll horizontal

### 3. Interactividad con Propósito
- Filtros que realmente ayuden
- Selectores con valores por defecto útiles
- Tooltips informativos
- Exportación de datos cuando sea útil

## Estructura Base de Dashboard

```python
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path

# ============================================================
# CONFIGURACIÓN
# ============================================================
st.set_page_config(
    page_title="Mi Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados (opcional)
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CARGA DE DATOS
# ============================================================
@st.cache_data
def cargar_datos():
    """Carga datos desde JSON. Usar cache para performance."""
    with open('output/datos.json', 'r', encoding='utf-8') as f:
        return json.load(f)

@st.cache_data
def cargar_csv(path):
    """Carga CSV con cache."""
    return pd.read_csv(path)

# Cargar datos
try:
    datos = cargar_datos()
except FileNotFoundError:
    st.error("❌ No se encontró el archivo de datos. Ejecuta el pipeline primero.")
    st.stop()

# ============================================================
# SIDEBAR - FILTROS
# ============================================================
with st.sidebar:
    st.header("🎛️ Filtros")
    
    # Filtro de fecha
    fecha_inicio = st.date_input("Desde", value=None)
    fecha_fin = st.date_input("Hasta", value=None)
    
    # Filtro categórico
    categorias = ["Todas"] + list(datos.get('categorias', []))
    categoria_sel = st.selectbox("Categoría", categorias)
    
    # Más filtros según necesidad...
    
    st.divider()
    st.caption("Dashboard generado con Claude Code")

# ============================================================
# HEADER
# ============================================================
st.title("📊 Dashboard de [Proyecto]")
st.caption(f"Última actualización: {datos.get('metadata', {}).get('fecha', 'N/A')}")

# ============================================================
# KPIs PRINCIPALES
# ============================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Métrica 1",
        value=f"${datos.get('metrica1', 0):,.0f}",
        delta=f"{datos.get('delta1', 0):+.1f}%"
    )

with col2:
    st.metric(
        label="Métrica 2", 
        value=f"{datos.get('metrica2', 0):,.0f}",
        delta=f"{datos.get('delta2', 0):+.1f}%"
    )

with col3:
    st.metric(
        label="Métrica 3",
        value=f"{datos.get('metrica3', 0):.1%}",
        delta=f"{datos.get('delta3', 0):+.1f}pp"
    )

with col4:
    st.metric(
        label="Métrica 4",
        value=f"{datos.get('metrica4', 0):,.0f}",
        delta=f"{datos.get('delta4', 0):+.1f}%"
    )

st.divider()

# ============================================================
# GRÁFICOS PRINCIPALES
# ============================================================
tab1, tab2, tab3 = st.tabs(["📈 Tendencias", "📊 Comparativas", "📋 Detalle"])

with tab1:
    # Gráfico de líneas - Tendencia temporal
    df_tendencia = pd.DataFrame(datos.get('tendencias', []))
    
    if not df_tendencia.empty:
        fig = px.line(
            df_tendencia, 
            x='fecha', 
            y='valor',
            title='Tendencia en el Tiempo',
            markers=True
        )
        fig.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Valor",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos de tendencia disponibles")

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras
        df_comparativa = pd.DataFrame(datos.get('comparativa', []))
        if not df_comparativa.empty:
            fig = px.bar(
                df_comparativa,
                x='categoria',
                y='valor',
                title='Comparativa por Categoría',
                color='valor',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Gráfico de pie/donut
        df_distribucion = pd.DataFrame(datos.get('distribucion', []))
        if not df_distribucion.empty:
            fig = px.pie(
                df_distribucion,
                values='valor',
                names='categoria',
                title='Distribución',
                hole=0.4  # Donut
            )
            st.plotly_chart(fig, use_container_width=True)

with tab3:
    # Tabla de datos
    df_detalle = pd.DataFrame(datos.get('detalle', []))
    
    if not df_detalle.empty:
        st.subheader("Datos Detallados")
        
        # Búsqueda
        busqueda = st.text_input("🔍 Buscar", "")
        if busqueda:
            df_detalle = df_detalle[
                df_detalle.astype(str).apply(
                    lambda x: x.str.contains(busqueda, case=False)
                ).any(axis=1)
            ]
        
        # Mostrar tabla
        st.dataframe(
            df_detalle,
            use_container_width=True,
            hide_index=True
        )
        
        # Exportar
        csv = df_detalle.to_csv(index=False)
        st.download_button(
            "📥 Descargar CSV",
            csv,
            "datos_detalle.csv",
            "text/csv"
        )

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("Dashboard generado automáticamente | Datos actualizados: " + 
           datos.get('metadata', {}).get('fecha', 'N/A'))
```

## Tipos de Gráficos Recomendados

### Para Tendencias Temporales
```python
# Línea simple
fig = px.line(df, x='fecha', y='valor', title='Tendencia')

# Línea con área
fig = px.area(df, x='fecha', y='valor', title='Tendencia con Área')

# Múltiples series
fig = px.line(df, x='fecha', y='valor', color='serie', title='Comparativa')
```

### Para Comparativas
```python
# Barras verticales
fig = px.bar(df, x='categoria', y='valor')

# Barras horizontales (mejor para muchas categorías)
fig = px.bar(df, x='valor', y='categoria', orientation='h')

# Barras agrupadas
fig = px.bar(df, x='categoria', y='valor', color='grupo', barmode='group')

# Barras apiladas
fig = px.bar(df, x='categoria', y='valor', color='grupo', barmode='stack')
```

### Para Distribución
```python
# Pie chart
fig = px.pie(df, values='valor', names='categoria')

# Donut
fig = px.pie(df, values='valor', names='categoria', hole=0.4)

# Treemap (para jerarquías)
fig = px.treemap(df, path=['nivel1', 'nivel2'], values='valor')
```

### Para Relaciones
```python
# Scatter plot
fig = px.scatter(df, x='variable1', y='variable2', color='categoria')

# Scatter con tamaño
fig = px.scatter(df, x='x', y='y', size='tamaño', color='categoria')

# Heatmap
fig = px.imshow(matriz_correlacion, title='Correlaciones')
```

### Para Funnel
```python
fig = go.Figure(go.Funnel(
    y=['Etapa 1', 'Etapa 2', 'Etapa 3', 'Etapa 4'],
    x=[1000, 500, 200, 50],
    textinfo="value+percent initial"
))
```

### Para KPIs (Gauge)
```python
fig = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=75,
    delta={'reference': 50},
    gauge={'axis': {'range': [0, 100]}},
    title={'text': "Progreso"}
))
```

## Componentes Interactivos

### Filtros Comunes
```python
# Selector único
opcion = st.selectbox("Selecciona", opciones)

# Selector múltiple
seleccionados = st.multiselect("Selecciona varios", opciones)

# Slider numérico
valor = st.slider("Valor", min_value=0, max_value=100, value=50)

# Slider de rango
rango = st.slider("Rango", 0, 100, (25, 75))

# Selector de fecha
fecha = st.date_input("Fecha")

# Rango de fechas
fecha_inicio, fecha_fin = st.date_input("Período", [])

# Checkbox
mostrar = st.checkbox("Mostrar detalle")

# Radio buttons
opcion = st.radio("Modo", ["Opción A", "Opción B"])
```

### Layout Avanzado
```python
# Columns con proporción
col1, col2 = st.columns([2, 1])  # 2:1 ratio

# Expander (acordeón)
with st.expander("Ver más"):
    st.write("Contenido expandible")

# Container
with st.container():
    st.write("Contenido agrupado")

# Tabs
tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])
with tab1:
    st.write("Contenido tab 1")
```

## Flujo de Trabajo

### Fase 1: Validar Datos
```bash
# Verificar que el JSON existe y es válido
python -m json.tool output/datos.json
```

### Fase 2: Identificar Visualizaciones
```markdown
Preguntas a responder:
- ¿Cuáles son los KPIs principales? (4-6 máximo)
- ¿Hay tendencias temporales que mostrar?
- ¿Hay comparativas entre categorías?
- ¿Qué datos necesitan drill-down?
- ¿Qué filtros serían útiles?
```

### Fase 3: Crear Dashboard
```bash
# Crear archivo dashboard
python scripts/generar_dashboard.py \
    --datos output/datos.json \
    --tipo [financiero|marketing|ventas|general] \
    --output dashboard/app.py
```

### Fase 4: Ejecutar y Validar
```bash
streamlit run dashboard/app.py
```

## Scripts Disponibles

| Script | Comando | Función |
|--------|---------|---------|
| Generador | `python scripts/generar_dashboard.py` | Crea dashboard desde template |
| Validador | `python scripts/validar_datos_dashboard.py` | Verifica estructura de datos |
| Exportador | `python scripts/exportar_dashboard.py` | Exporta a HTML estático |

## Outputs Esperados

```
dashboard/
├── app.py                    # Dashboard principal
├── pages/                    # Páginas adicionales (multi-page)
│   ├── 01_detalle.py
│   └── 02_configuracion.py
└── components/               # Componentes reutilizables
    ├── kpis.py
    └── charts.py
```

## Paletas de Colores Recomendadas

### Profesional (por defecto)
```python
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
```

### Corporativo
```python
colors = ['#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087']
```

### Verde (positivo)
```python
colors = ['#006d2c', '#31a354', '#74c476', '#a1d99b', '#c7e9c0']
```

### Rojo-Verde (divergente)
```python
colors = ['#d73027', '#fc8d59', '#fee08b', '#d9ef8b', '#91cf60', '#1a9850']
```

## Restricciones Obligatorias

- [ ] El dashboard SIEMPRE lee de JSON/CSV, nunca de Excel directo
- [ ] Usar @st.cache_data para funciones de carga
- [ ] Validar que los datos existan antes de graficar
- [ ] Incluir manejo de errores para datos faltantes
- [ ] Mostrar última fecha de actualización
- [ ] Usar layout="wide" para dashboards

## Integración con Otras Skills

- **financial-analysis**: Dashboard de métricas financieras
- **marketing-analytics**: Dashboard de campañas
- **data-pipeline**: Visualizar calidad de datos del pipeline
- **document-extraction**: Mostrar resultados de extracción

---

*Skill parte del Kit de Inicio de Proyectos Claude Code*
*Última actualización: Enero 2025*
