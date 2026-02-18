"""
Dashboard de Gestion de Tareas - Proyecto Circular de Produccion Agricola
Huerta Inteligente LPET - Finca La Palma y El Tucan
VERSION CON SUPABASE - v3.0 (Mejorado)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from pathlib import Path
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar variables de entorno (soporta .env local y Streamlit Cloud secrets)
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

# Intentar cargar desde Streamlit secrets (Cloud) o .env (local)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Configuracion de la pagina
st.set_page_config(
    page_title="Tareas - Huerta LPET",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Crear cliente Supabase
@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# ============================================
# FUNCIONES DE CARGA DESDE SUPABASE
# ============================================

def cargar_equipo():
    response = supabase.table('equipo').select('*').execute()
    return response.data

def cargar_estados():
    response = supabase.table('estados').select('*').order('orden').execute()
    return response.data

def cargar_categorias():
    response = supabase.table('categorias').select('*').execute()
    return response.data

def cargar_metadata():
    response = supabase.table('metadata').select('*').limit(1).execute()
    return response.data[0] if response.data else {}

def cargar_tareas():
    response = supabase.table('tareas').select('*').order('fecha_objetivo').execute()
    return response.data

def actualizar_tarea(tarea_id, datos):
    datos['updated_at'] = datetime.now().isoformat()
    response = supabase.table('tareas').update(datos).eq('id', tarea_id).execute()
    return response.data

def crear_tarea(datos):
    datos['created_at'] = datetime.now().isoformat()
    datos['updated_at'] = datetime.now().isoformat()
    response = supabase.table('tareas').insert(datos).execute()
    return response.data

# ============================================
# AUTENTICACION
# ============================================

def cargar_passwords():
    """Carga passwords desde secrets o defaults para desarrollo local"""
    try:
        # Normalizar keys a minuscula para match con IDs de equipo
        return {k.lower(): v for k, v in dict(st.secrets["passwords"]).items()}
    except Exception:
        # Defaults para desarrollo local - cambiar en produccion
        return {
            "felipe": "lpet2026",
            "katherine": "lpet2026",
            "william": "lpet2026",
            "john": "lpet2026",
            "andres": "lpet2026",
        }

PASSWORDS = cargar_passwords()

ADMINS = {'felipe', 'katherine'}

def verificar_login(usuario, password):
    """Verifica credenciales del usuario"""
    return PASSWORDS.get(usuario) == password

def usuario_logueado():
    """Retorna True si hay un usuario logueado"""
    return st.session_state.get('logged_in', False)

def get_usuario_actual():
    """Retorna el id del usuario logueado"""
    return st.session_state.get('usuario_id', None)

def es_admin():
    """Retorna True si el usuario logueado es admin"""
    return get_usuario_actual() in ADMINS

# ============================================
# CARGAR DATOS DESDE SUPABASE
# ============================================

if 'datos_cargados' not in st.session_state or st.session_state.get('recargar', False):
    with st.spinner('Cargando datos desde Supabase...'):
        st.session_state['equipo'] = cargar_equipo()
        st.session_state['estados'] = cargar_estados()
        st.session_state['categorias'] = cargar_categorias()
        st.session_state['metadata'] = cargar_metadata()
        st.session_state['tareas'] = cargar_tareas()
        st.session_state['datos_cargados'] = True
        st.session_state['recargar'] = False

equipo = st.session_state['equipo']
estados = st.session_state['estados']
categorias = st.session_state['categorias']
metadata = st.session_state['metadata']
tareas = st.session_state['tareas']

# ============================================
# LOOKUPS O(1) - Diccionarios precalculados
# ============================================

equipo_dict = {e['id']: e for e in equipo}
estados_dict = {e['id']: e for e in estados}
categorias_dict = {c['id']: c for c in categorias}
tareas_dict = {t['id']: t for t in tareas}

def get_estado_color(estado_id):
    return estados_dict.get(estado_id, {}).get('color', '#6c757d')

def get_estado_nombre(estado_id):
    return estados_dict.get(estado_id, {}).get('nombre', estado_id)

def get_responsable_nombre(resp_id):
    return equipo_dict.get(resp_id, {}).get('nombre', resp_id)

def get_categoria_info(cat_id):
    return categorias_dict.get(cat_id, {'nombre': cat_id, 'icono': '📌'})

# ============================================
# VARIABLES GLOBALES PRECALCULADAS
# ============================================

hoy = date.today()

# Fechas criticas
fecha_inicio_obra_str = metadata.get('fecha_inicio_obra', '2026-02-23')
fecha_limite_compras_str = metadata.get('fecha_limite_compras', '2026-02-20')
try:
    fecha_inicio_obra = datetime.strptime(fecha_inicio_obra_str, "%Y-%m-%d").date()
except Exception:
    fecha_inicio_obra = date(2026, 2, 23)
try:
    fecha_limite_compras = datetime.strptime(fecha_limite_compras_str, "%Y-%m-%d").date()
except Exception:
    fecha_limite_compras = date(2026, 2, 20)

dias_para_obra = (fecha_inicio_obra - hoy).days
dias_para_compras = (fecha_limite_compras - hoy).days

# Grafo de dependencias
def calcular_grafo_dependencias():
    bloqueado_por = {}  # tarea_id -> [ids de tareas que la bloquean y NO estan finalizadas]
    bloquea_a = {}      # tarea_id -> [ids de tareas que dependen de esta]
    for t in tareas:
        tid = t['id']
        deps = t.get('dependencias') or []
        # Filtrar dependencias no cumplidas
        deps_no_cumplidas = []
        for d in deps:
            dep_tarea = tareas_dict.get(d)
            if dep_tarea and dep_tarea['estado'] != 'finalizado':
                deps_no_cumplidas.append(d)
        bloqueado_por[tid] = deps_no_cumplidas
        # Construir inverso
        for d in deps:
            if d not in bloquea_a:
                bloquea_a[d] = []
            bloquea_a[d].append(tid)
    return bloqueado_por, bloquea_a

bloqueado_por, bloquea_a = calcular_grafo_dependencias()

# Tareas vencidas (no finalizadas, fecha pasada)
def calcular_tareas_vencidas():
    vencidas = set()
    for t in tareas:
        if t['estado'] == 'finalizado':
            continue
        try:
            fecha_obj = datetime.strptime(t['fecha_objetivo'], "%Y-%m-%d").date()
            if fecha_obj < hoy:
                vencidas.add(t['id'])
        except Exception:
            pass
    return vencidas

tareas_vencidas_set = calcular_tareas_vencidas()

# Tareas de hoy y manana
tareas_hoy_set = set()
tareas_manana_set = set()
for t in tareas:
    if t['estado'] == 'finalizado':
        continue
    try:
        fecha_obj = datetime.strptime(t['fecha_objetivo'], "%Y-%m-%d").date()
        if fecha_obj == hoy:
            tareas_hoy_set.add(t['id'])
        elif fecha_obj == hoy + timedelta(days=1):
            tareas_manana_set.add(t['id'])
    except Exception:
        pass

# Impacto en cascada: cuantas tareas se afectan si una tarea se retrasa
def calcular_impacto_cascada(tarea_id, visitados=None):
    if visitados is None:
        visitados = set()
    if tarea_id in visitados:
        return set()
    visitados.add(tarea_id)
    dependientes = bloquea_a.get(tarea_id, [])
    afectadas = set(dependientes)
    for d in dependientes:
        afectadas |= calcular_impacto_cascada(d, visitados)
    return afectadas

# ============================================
# CSS PROFESIONAL
# ============================================

st.markdown("""
<style>
    /* Header del proyecto */
    .project-header {
        background: linear-gradient(135deg, #1B5E20, #388E3C, #4CAF50);
        color: white;
        padding: 20px 30px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(27, 94, 32, 0.3);
    }
    .project-header h1 {
        margin: 0;
        font-size: 1.8em;
    }
    .project-header p {
        margin: 5px 0 0 0;
        opacity: 0.9;
        font-size: 0.95em;
    }

    /* KPI cards */
    .kpi-card {
        padding: 18px 15px;
        border-radius: 12px;
        text-align: center;
        color: white;
        transition: transform 0.2s, box-shadow 0.2s;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    .kpi-card h2 {
        margin: 0;
        font-size: 2em;
    }
    .kpi-card p {
        margin: 5px 0 0 0;
        font-size: 0.85em;
        opacity: 0.9;
    }

    /* Task cards con fondos solidos por prioridad */
    .task-card {
        padding: 14px 16px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 5px solid;
        transition: box-shadow 0.2s;
        color: #ffffff !important;
    }
    .task-card strong, .task-card small, .task-card span {
        color: #ffffff !important;
    }
    .task-card:hover {
        box-shadow: 0 3px 12px rgba(0,0,0,0.25);
        transform: translateY(-2px);
    }
    .urgente {
        background: linear-gradient(135deg, #b71c1c, #d32f2f);
        border-left-color: #ff5252;
    }
    .alta {
        background: linear-gradient(135deg, #e65100, #ef6c00);
        border-left-color: #ffab40;
    }
    .media {
        background: linear-gradient(135deg, #1565c0, #1976d2);
        border-left-color: #448aff;
    }
    .baja {
        background: linear-gradient(135deg, #455a64, #546e7a);
        border-left-color: #90a4ae;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        color: white;
    }
    .badge-estado {
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 11px;
        font-weight: 600;
        color: white;
    }
    .badge-prioridad-urgente { background-color: #dc3545; }
    .badge-prioridad-alta { background-color: #ff9800; }
    .badge-prioridad-media { background-color: #2196f3; }
    .badge-prioridad-baja { background-color: #9e9e9e; }

    /* Alertas criticas */
    .alerta-critica {
        background: linear-gradient(135deg, #b71c1c, #c62828);
        border: 1px solid #d32f2f;
        border-left: 5px solid #ff5252;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        color: #ffffff !important;
    }
    .alerta-critica strong { color: #ffffff !important; }
    .alerta-warning {
        background: linear-gradient(135deg, #e65100, #ef6c00);
        border: 1px solid #f57c00;
        border-left: 5px solid #ffab40;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        color: #ffffff !important;
    }
    .alerta-warning strong { color: #ffffff !important; }
    .alerta-info {
        background: linear-gradient(135deg, #1565c0, #1976d2);
        border: 1px solid #1e88e5;
        border-left: 5px solid #448aff;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        color: #ffffff !important;
    }
    .alerta-info strong { color: #ffffff !important; }

    /* Semaforo de categorias */
    .semaforo-verde { color: #28a745; font-weight: bold; }
    .semaforo-amarillo { color: #ffc107; font-weight: bold; }
    .semaforo-rojo { color: #dc3545; font-weight: bold; }

    /* Panel del dia cards */
    .dia-card {
        padding: 14px 18px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 5px solid;
        color: #ffffff !important;
    }
    .dia-card strong, .dia-card small, .dia-card span {
        color: #ffffff !important;
    }
    .dia-card-vencida {
        background: linear-gradient(135deg, #c62828, #e53935);
        border-left-color: #b71c1c;
    }
    .dia-card-hoy {
        background: linear-gradient(135deg, #e65100, #f57c00);
        border-left-color: #bf360c;
    }
    .dia-card-manana {
        background: linear-gradient(135deg, #1565c0, #1e88e5);
        border-left-color: #0d47a1;
    }

    /* Dependencias */
    .dep-bloqueada {
        background: linear-gradient(135deg, #b71c1c, #c62828);
        border: 1px solid #d32f2f;
        padding: 8px 12px;
        border-radius: 6px;
        margin: 4px 0;
        font-size: 0.85em;
        color: #ffffff !important;
    }
    .dep-libre {
        background: linear-gradient(135deg, #1b5e20, #2e7d32);
        border: 1px solid #388e3c;
        padding: 8px 12px;
        border-radius: 6px;
        margin: 4px 0;
        font-size: 0.85em;
        color: #ffffff !important;
    }

    /* Hitos timeline */
    .hito-card {
        padding: 10px 15px;
        border-radius: 8px;
        text-align: center;
        font-weight: 600;
        color: white;
        font-size: 0.9em;
    }

    /* Progress bar override */
    .stProgress > div > div > div > div {
        background-color: #28a745;
    }

    .fecha-vencida { color: #dc3545; font-weight: bold; }
    .fecha-hoy { color: #ff9800; font-weight: bold; }

    .supabase-badge {
        background-color: #3ECF8E;
        color: white;
        padding: 3px 8px;
        border-radius: 5px;
        font-size: 12px;
    }

    /* Sidebar mini KPIs */
    .sidebar-kpi {
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        font-size: 0.9em;
    }
    .sidebar-kpi-val {
        font-weight: 700;
    }

    /* Countdown */
    .countdown-card {
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 6px;
        text-align: center;
        font-weight: 600;
        font-size: 0.85em;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR
# ============================================

st.sidebar.title("📋 Gestion de Tareas")
st.sidebar.markdown(f"**Proyecto:** {metadata.get('proyecto', 'N/A')}")
st.sidebar.markdown(f"**Finca:** {metadata.get('finca', 'N/A')}")
st.sidebar.markdown(f'<span class="supabase-badge">Supabase</span>', unsafe_allow_html=True)

# Mini KPIs rapidos
st.sidebar.markdown("---")
st.sidebar.markdown("**Estado Rapido**")

n_vencidas = len(tareas_vencidas_set)
n_hoy = len(tareas_hoy_set)
n_manana = len(tareas_manana_set)

color_vencidas = "#dc3545" if n_vencidas > 0 else "#28a745"
color_hoy = "#ff9800" if n_hoy > 0 else "#28a745"
color_manana = "#2196f3" if n_manana > 0 else "#28a745"

st.sidebar.markdown(f"""
<div class="sidebar-kpi">
    <span>🔴 Vencidas</span>
    <span class="sidebar-kpi-val" style="color:{color_vencidas}">{n_vencidas}</span>
</div>
<div class="sidebar-kpi">
    <span>🟡 Hoy</span>
    <span class="sidebar-kpi-val" style="color:{color_hoy}">{n_hoy}</span>
</div>
<div class="sidebar-kpi">
    <span>🔵 Manana</span>
    <span class="sidebar-kpi-val" style="color:{color_manana}">{n_manana}</span>
</div>
""", unsafe_allow_html=True)

# Countdown a hitos criticos
st.sidebar.markdown("---")
st.sidebar.markdown("**Countdown**")

color_compras = "#dc3545" if dias_para_compras <= 1 else ("#ff9800" if dias_para_compras <= 3 else "#28a745")
color_obra = "#dc3545" if dias_para_obra <= 3 else ("#ff9800" if dias_para_obra <= 7 else "#2196f3")

st.sidebar.markdown(f"""
<div class="countdown-card" style="background-color: {color_compras}; color: white;">
    🛒 Limite Compras: {dias_para_compras} dias
</div>
<div class="countdown-card" style="background-color: {color_obra}; color: white;">
    🏗️ Inicio Obra: {dias_para_obra} dias
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

# Login / Sesion
if usuario_logueado():
    usuario_actual = get_usuario_actual()
    nombre_actual = equipo_dict.get(usuario_actual, {}).get('nombre', usuario_actual)
    st.sidebar.markdown(f"**👤 {nombre_actual}**")
    if st.sidebar.button("🚪 Cerrar Sesion"):
        st.session_state['logged_in'] = False
        st.session_state['usuario_id'] = None
        st.rerun()
else:
    st.sidebar.markdown("**🔒 Iniciar Sesion**")
    st.sidebar.caption("Inicia sesion para editar y crear tareas")
    usuarios_login = [e['id'] for e in equipo if e['id'] != 'sin_asignar' and e['id'] != 'contratistas']
    usuarios_nombres = {e['id']: e['nombre'] for e in equipo if e['id'] in usuarios_login}
    login_usuario = st.sidebar.selectbox("Usuario", usuarios_login, format_func=lambda x: usuarios_nombres.get(x, x), key="login_user")
    login_password = st.sidebar.text_input("Contraseña", type="password", key="login_pass")
    if st.sidebar.button("🔑 Entrar", use_container_width=True):
        if verificar_login(login_usuario, login_password):
            st.session_state['logged_in'] = True
            st.session_state['usuario_id'] = login_usuario
            st.rerun()
        else:
            st.sidebar.error("Contraseña incorrecta")

st.sidebar.markdown("---")

# Filtros en sidebar
st.sidebar.subheader("Filtros")

# Responsable: solo visible para admins y usuarios no logueados
filtro_responsable = "Todos"
if not usuario_logueado() or es_admin():
    responsables_opciones = ["Todos"] + [e['nombre'] for e in equipo]
    filtro_responsable = st.sidebar.selectbox("Responsable", responsables_opciones, index=0)

categorias_opciones = ["Todas"] + [f"{c['icono']} {c['nombre']}" for c in categorias]
filtro_categoria = st.sidebar.selectbox("Categoria", categorias_opciones, index=0)

estados_opciones_filtro = ["Todos"] + [e['nombre'] for e in estados]
filtro_estado = st.sidebar.selectbox("Estado", estados_opciones_filtro, index=0)

prioridades_opciones = ["Todas", "urgente", "alta", "media", "baja"]
filtro_prioridad = st.sidebar.selectbox("Prioridad", prioridades_opciones, index=0)

# Aplicar filtros
tareas_filtradas = tareas.copy()

# Usuarios normales: filtrar automaticamente por sus tareas
if usuario_logueado() and not es_admin():
    tareas_filtradas = [t for t in tareas_filtradas if t['responsable'] == get_usuario_actual()]
elif filtro_responsable != "Todos":
    resp_id = next((e['id'] for e in equipo if e['nombre'] == filtro_responsable), None)
    if resp_id:
        tareas_filtradas = [t for t in tareas_filtradas if t['responsable'] == resp_id]

if filtro_categoria != "Todas":
    cat_nombre = filtro_categoria.split(' ', 1)[1] if ' ' in filtro_categoria else filtro_categoria
    cat_id = next((c['id'] for c in categorias if c['nombre'] == cat_nombre), None)
    if cat_id:
        tareas_filtradas = [t for t in tareas_filtradas if t['categoria'] == cat_id]

if filtro_estado != "Todos":
    estado_id = next((e['id'] for e in estados if e['nombre'] == filtro_estado), None)
    if estado_id:
        tareas_filtradas = [t for t in tareas_filtradas if t['estado'] == estado_id]

if filtro_prioridad != "Todas":
    tareas_filtradas = [t for t in tareas_filtradas if t['prioridad'] == filtro_prioridad]

# Navegacion
st.sidebar.markdown("---")

if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = "📊 Resumen"

paginas = [
    "📊 Resumen",
    "📝 Lista de Tareas",
    "🗓️ Linea de Tiempo",
    "🔗 Dependencias",
    "🎯 Tablero Kanban",
    "📅 Panel del Dia",
    "➕ Nuevo Proyecto",
    "✏️ Editar Tarea"
]
pagina_idx = paginas.index(st.session_state['pagina_actual']) if st.session_state['pagina_actual'] in paginas else 0

pagina = st.sidebar.radio("Vista", paginas, index=pagina_idx)
st.session_state['pagina_actual'] = pagina

# ============================================
# PAGINA: RESUMEN
# ============================================
if pagina == "📊 Resumen":
    # Determinar si es vista personal o general
    vista_personal = usuario_logueado() and not es_admin()
    if vista_personal:
        nombre_usuario = equipo_dict.get(get_usuario_actual(), {}).get('nombre', get_usuario_actual())
        mis_tareas = [t for t in tareas if t['responsable'] == get_usuario_actual()]
        mis_vencidas = [t for t in mis_tareas if t['id'] in tareas_vencidas_set]
        resumen_tareas = mis_tareas
    else:
        resumen_tareas = tareas

    # Header visual
    if vista_personal:
        st.markdown(f"""
        <div class="project-header">
            <h1>👤 Mi Resumen - {nombre_usuario}</h1>
            <p>Huerta Inteligente LPET - Mis tareas asignadas</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="project-header">
            <h1>🌱 Huerta Inteligente LPET</h1>
            <p>Finca La Palma y El Tucan - Proyecto Circular de Produccion Agricola</p>
        </div>
        """, unsafe_allow_html=True)

    # Mini timeline de hitos
    col_h1, col_h2, col_h3 = st.columns(3)
    with col_h1:
        st.markdown(f"""
        <div class="hito-card" style="background-color: {color_compras};">
            🛒 Limite Compras<br>{fecha_limite_compras_str}<br>{dias_para_compras} dias
        </div>
        """, unsafe_allow_html=True)
    with col_h2:
        st.markdown(f"""
        <div class="hito-card" style="background-color: {color_obra};">
            🏗️ Inicio Obra<br>{fecha_inicio_obra_str}<br>{dias_para_obra} dias
        </div>
        """, unsafe_allow_html=True)
    with col_h3:
        st.markdown(f"""
        <div class="hito-card" style="background-color: #6c757d;">
            📅 Hoy<br>{hoy.strftime('%Y-%m-%d')}<br>&nbsp;
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # KPIs basados en resumen_tareas
    total_tareas = len(resumen_tareas)
    por_iniciar = len([t for t in resumen_tareas if t['estado'] == 'por_iniciar'])
    en_proceso = len([t for t in resumen_tareas if t['estado'] == 'en_proceso'])
    finalizadas = len([t for t in resumen_tareas if t['estado'] == 'finalizado'])
    bloqueadas = len([t for t in resumen_tareas if t['estado'] == 'bloqueado'])
    n_vencidas_kpi = len([t for t in resumen_tareas if t['id'] in tareas_vencidas_set])

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.markdown(f"""
        <div class="kpi-card" style="background-color: #6c757d;">
            <h2>{total_tareas}</h2>
            <p>Total</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card" style="background-color: #17a2b8;">
            <h2>{por_iniciar}</h2>
            <p>Por Iniciar</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card" style="background-color: #ffc107; color: #333;">
            <h2>{en_proceso}</h2>
            <p>En Proceso</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="kpi-card" style="background-color: #28a745;">
            <h2>{finalizadas}</h2>
            <p>Finalizadas</p>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="kpi-card" style="background-color: #6f42c1;">
            <h2>{bloqueadas}</h2>
            <p>Bloqueadas</p>
        </div>
        """, unsafe_allow_html=True)
    with col6:
        bg_vencidas = "#dc3545" if n_vencidas_kpi > 0 else "#28a745"
        st.markdown(f"""
        <div class="kpi-card" style="background-color: {bg_vencidas};">
            <h2>{n_vencidas_kpi}</h2>
            <p>Vencidas</p>
        </div>
        """, unsafe_allow_html=True)

    # Progreso
    progreso = finalizadas / total_tareas if total_tareas > 0 else 0
    st.markdown("### Mi Progreso" if vista_personal else "### Progreso General")
    st.progress(progreso)
    st.markdown(f"**{finalizadas}/{total_tareas}** tareas completadas ({progreso*100:.1f}%)")

    st.markdown("---")

    # Graficos Plotly
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("### Distribucion por Estado")
        estado_counts = {}
        estado_colors_map = {}
        for t in resumen_tareas:
            ename = get_estado_nombre(t['estado'])
            estado_counts[ename] = estado_counts.get(ename, 0) + 1
            estado_colors_map[ename] = get_estado_color(t['estado'])

        if estado_counts:
            fig_donut = go.Figure(data=[go.Pie(
                labels=list(estado_counts.keys()),
                values=list(estado_counts.values()),
                hole=0.45,
                marker=dict(colors=[estado_colors_map[k] for k in estado_counts.keys()]),
                textinfo='label+value',
                textposition='outside',
                hovertemplate='<b>%{label}</b><br>Tareas: %{value}<br>%{percent}<extra></extra>'
            )])
            fig_donut.update_layout(
                showlegend=False,
                margin=dict(t=20, b=20, l=20, r=20),
                height=320
            )
            st.plotly_chart(fig_donut, use_container_width=True)

    with col_g2:
        if vista_personal:
            # Usuario normal: grafico por categoria
            st.markdown("### Mis Tareas por Categoria")
            cat_estado_data = []
            for t in resumen_tareas:
                cat_info = get_categoria_info(t['categoria'])
                cat_estado_data.append({
                    'Categoria': f"{cat_info['icono']} {cat_info['nombre']}",
                    'Estado': get_estado_nombre(t['estado']),
                    'Tareas': 1
                })
            df_cat = pd.DataFrame(cat_estado_data)
            if not df_cat.empty:
                df_cat_grouped = df_cat.groupby(['Categoria', 'Estado']).sum().reset_index()
                estado_order = [get_estado_nombre(e['id']) for e in estados]
                color_map = {get_estado_nombre(e['id']): e['color'] for e in estados}
                fig_cat = px.bar(
                    df_cat_grouped,
                    y='Categoria',
                    x='Tareas',
                    color='Estado',
                    orientation='h',
                    color_discrete_map=color_map,
                    category_orders={'Estado': estado_order}
                )
                fig_cat.update_traces(hovertemplate='<b>%{y}</b><br>Tareas: %{x}<extra>%{fullData.name}</extra>')
                fig_cat.update_layout(
                    xaxis_title="Tareas",
                    yaxis_title="",
                    margin=dict(t=20, b=20, l=20, r=20),
                    height=320,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3)
                )
                st.plotly_chart(fig_cat, use_container_width=True)
        else:
            # Admin: grafico por responsable
            st.markdown("### Tareas por Responsable")
            resp_estado_data = []
            for t in resumen_tareas:
                resp_estado_data.append({
                    'Responsable': get_responsable_nombre(t['responsable']),
                    'Estado': get_estado_nombre(t['estado']),
                    'Tareas': 1
                })
            df_resp = pd.DataFrame(resp_estado_data)
            if not df_resp.empty:
                df_grouped = df_resp.groupby(['Responsable', 'Estado']).sum().reset_index()
                estado_order = [get_estado_nombre(e['id']) for e in estados]
                color_map = {get_estado_nombre(e['id']): e['color'] for e in estados}
                fig_resp = px.bar(
                    df_grouped,
                    y='Responsable',
                    x='Tareas',
                    color='Estado',
                    orientation='h',
                    color_discrete_map=color_map,
                    category_orders={'Estado': estado_order}
                )
                fig_resp.update_traces(hovertemplate='<b>%{y}</b><br>Tareas: %{x}<extra>%{fullData.name}</extra>')
                fig_resp.update_layout(
                    xaxis_title="Tareas",
                    yaxis_title="",
                    margin=dict(t=20, b=20, l=20, r=20),
                    height=320,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3)
                )
                st.plotly_chart(fig_resp, use_container_width=True)

    st.markdown("---")

    # Semaforo por categoria (solo las que tienen tareas del usuario)
    st.markdown("### Semaforo por Categoria")
    cats_con_tareas = [cat for cat in categorias if any(t['categoria'] == cat['id'] for t in resumen_tareas)]

    if cats_con_tareas:
        cat_cols = st.columns(min(len(cats_con_tareas), 6))
        for idx, cat in enumerate(cats_con_tareas):
            col_idx = idx % len(cat_cols)
            with cat_cols[col_idx]:
                cat_tareas = [t for t in resumen_tareas if t['categoria'] == cat['id']]
                cat_total = len(cat_tareas)
                cat_completadas = len([t for t in cat_tareas if t['estado'] == 'finalizado'])
                cat_vencidas = len([t for t in cat_tareas if t['id'] in tareas_vencidas_set])

                pct = cat_completadas / cat_total if cat_total > 0 else 0

                if cat_vencidas > 0:
                    semaforo = "🔴"
                elif pct >= 0.7:
                    semaforo = "🟢"
                elif pct >= 0.3:
                    semaforo = "🟡"
                else:
                    semaforo = "🟡"

                st.markdown(f"""
                <div style="text-align:center; padding: 10px; border-radius: 8px; background: #fafafa; margin-bottom: 8px;">
                    <div style="font-size: 1.5em;">{cat['icono']}</div>
                    <div style="font-weight: 600; font-size: 0.85em;">{cat['nombre']}</div>
                    <div style="font-size: 1.3em;">{semaforo}</div>
                    <div style="font-size: 0.8em; color: #666;">{cat_completadas}/{cat_total}</div>
                </div>
                """, unsafe_allow_html=True)
                if cat_total > 0:
                    st.progress(pct)

    st.markdown("---")

    # Tareas urgentes
    st.markdown("### 🚨 Tareas Urgentes (Vencidas o Hoy)")

    tareas_urgentes = []
    for t in resumen_tareas:
        if t['estado'] == 'finalizado':
            continue
        try:
            fecha_obj = datetime.strptime(t['fecha_objetivo'], "%Y-%m-%d").date()
            dias_retraso = (hoy - fecha_obj).days
            if fecha_obj <= hoy or t['prioridad'] == 'urgente':
                fila = {
                    'Tarea': t['tarea'],
                    'Fecha': t['fecha_objetivo'],
                    'Dias Retraso': max(dias_retraso, 0),
                    'Estado': get_estado_nombre(t['estado']),
                    'Prioridad': t['prioridad']
                }
                if not vista_personal:
                    fila['Responsable'] = get_responsable_nombre(t['responsable'])
                tareas_urgentes.append(fila)
        except Exception:
            pass

    if tareas_urgentes:
        tareas_urgentes.sort(key=lambda x: -x['Dias Retraso'])
        df_urgentes = pd.DataFrame(tareas_urgentes)
        st.dataframe(df_urgentes, use_container_width=True, hide_index=True)
    else:
        st.success("No hay tareas urgentes pendientes")

# ============================================
# PAGINA: LISTA DE TAREAS
# ============================================
elif pagina == "📝 Lista de Tareas":
    st.title("📝 Lista de Tareas")
    st.markdown(f"**Mostrando {len(tareas_filtradas)} tareas**")

    tareas_filtradas_sorted = sorted(tareas_filtradas, key=lambda x: x['fecha_objetivo'] or '9999-99-99')

    for tarea in tareas_filtradas_sorted:
        cat_info = get_categoria_info(tarea['categoria'])
        estado_color = get_estado_color(tarea['estado'])
        estado_nombre = get_estado_nombre(tarea['estado'])
        resp_nombre = get_responsable_nombre(tarea['responsable'])

        # Indicador de fecha
        fecha_tag = ""
        try:
            fecha_obj = datetime.strptime(tarea['fecha_objetivo'], "%Y-%m-%d").date()
            if tarea['estado'] != 'finalizado':
                if fecha_obj < hoy:
                    dias_r = (hoy - fecha_obj).days
                    fecha_tag = f'<span style="color:#ffcdd2;font-weight:bold;"> ⚠️ {dias_r}d atraso</span>'
                elif fecha_obj == hoy:
                    fecha_tag = '<span style="color:#ffe082;font-weight:bold;"> 📌 HOY</span>'
        except Exception:
            pass

        notas_html = f'<br><small style="color:#e0e0e0;">📝 {tarea["notas"]}</small>' if tarea.get('notas') else ''

        st.markdown(f"""
        <div class="task-card {tarea['prioridad']}">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div style="flex:1;">
                    <strong>{cat_info['icono']} {tarea['tarea']}</strong>{notas_html}
                </div>
                <div style="text-align:right; min-width:180px;">
                    <span class="badge-estado" style="background-color: {estado_color};">{estado_nombre}</span>
                    <br><small>👤 {resp_nombre}</small>
                    <br><small>📅 {tarea['fecha_objetivo']}{fecha_tag}</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("✏️ Editar", key=f"edit_{tarea['id']}", help="Editar tarea"):
            st.session_state['tarea_editar'] = tarea['id']
            st.session_state['pagina_actual'] = "✏️ Editar Tarea"
            st.rerun()

# ============================================
# PAGINA: LINEA DE TIEMPO (GANTT)
# ============================================
elif pagina == "🗓️ Linea de Tiempo":
    st.title("🗓️ Linea de Tiempo")

    # Controles
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
    with col_ctrl1:
        gantt_color = st.selectbox("Colorear por", ["Categoria", "Estado", "Responsable", "Prioridad"])
    with col_ctrl2:
        gantt_grupo = st.selectbox("Agrupar por", ["Categoria", "Responsable", "Individual"])
    with col_ctrl3:
        mostrar_finalizadas = st.checkbox("Mostrar finalizadas", value=False)

    # Preparar datos para Gantt
    gantt_data = []
    for t in tareas_filtradas:
        if not mostrar_finalizadas and t['estado'] == 'finalizado':
            continue

        try:
            fecha_fin = datetime.strptime(t['fecha_objetivo'], "%Y-%m-%d")
        except Exception:
            continue

        # Estimar fecha inicio (3 dias antes si no hay info)
        fecha_inicio = fecha_fin - timedelta(days=3)

        cat_info = get_categoria_info(t['categoria'])
        resp_nombre = get_responsable_nombre(t['responsable'])

        if gantt_grupo == "Categoria":
            grupo = f"{cat_info['icono']} {cat_info['nombre']}"
        elif gantt_grupo == "Responsable":
            grupo = resp_nombre
        else:
            grupo = t['tarea'][:50]

        row = {
            'Tarea': t['tarea'][:45] + ('...' if len(t['tarea']) > 45 else ''),
            'Inicio': fecha_inicio,
            'Fin': fecha_fin,
            'Grupo': grupo,
            'Categoria': f"{cat_info['icono']} {cat_info['nombre']}",
            'Estado': get_estado_nombre(t['estado']),
            'Responsable': resp_nombre,
            'Prioridad': t['prioridad']
        }
        gantt_data.append(row)

    if gantt_data:
        df_gantt = pd.DataFrame(gantt_data)

        color_col_map = {
            "Categoria": "Categoria",
            "Estado": "Estado",
            "Responsable": "Responsable",
            "Prioridad": "Prioridad"
        }

        # Color maps
        if gantt_color == "Estado":
            cmap = {get_estado_nombre(e['id']): e['color'] for e in estados}
        elif gantt_color == "Prioridad":
            cmap = {"urgente": "#dc3545", "alta": "#ff9800", "media": "#2196f3", "baja": "#9e9e9e"}
        else:
            cmap = None

        fig_gantt = px.timeline(
            df_gantt,
            x_start="Inicio",
            x_end="Fin",
            y="Grupo",
            color=color_col_map[gantt_color],
            hover_name="Tarea",
            hover_data=["Estado", "Responsable", "Prioridad"],
            color_discrete_map=cmap
        )

        # Lineas verticales: HOY, limite compras, inicio obra
        lineas_ref = [
            (hoy, "red", "solid", 3, "🔴 HOY"),
            (fecha_limite_compras, "orange", "dash", 2, "🛒 Limite Compras"),
            (fecha_inicio_obra, "blue", "dash", 2, "🏗️ Inicio Obra"),
        ]
        for fecha_ref, color_ref, dash_ref, width_ref, label_ref in lineas_ref:
            x_val = datetime.combine(fecha_ref, datetime.min.time()).isoformat()
            fig_gantt.add_shape(
                type="line", x0=x_val, x1=x_val, y0=0, y1=1,
                yref="paper", line=dict(color=color_ref, width=width_ref, dash=dash_ref)
            )
            fig_gantt.add_annotation(
                x=x_val, y=1.05, yref="paper",
                text=label_ref, showarrow=False,
                font=dict(color=color_ref, size=11, family="Arial Black")
            )

        fig_gantt.update_layout(
            height=max(400, len(set(df_gantt['Grupo'])) * 40),
            margin=dict(t=60, b=20),
            xaxis_title="Fecha",
            yaxis_title="",
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig_gantt, use_container_width=True)

        # Carga por fecha de vencimiento
        st.markdown("### Carga por Fecha de Vencimiento")
        df_carga = df_gantt.groupby(df_gantt['Fin'].dt.date).size().reset_index(name='Tareas')
        df_carga.columns = ['Fecha', 'Tareas']
        df_carga['Fecha'] = pd.to_datetime(df_carga['Fecha'])

        fig_carga = px.bar(
            df_carga,
            x='Fecha',
            y='Tareas',
            color_discrete_sequence=['#4CAF50'],
            labels={'Tareas': 'Tareas', 'Fecha': 'Fecha'}
        )
        fig_carga.update_traces(hovertemplate='<b>%{x|%d %b %Y}</b><br>Tareas: %{y}<extra></extra>')
        x_hoy_iso = datetime.combine(hoy, datetime.min.time()).isoformat()
        fig_carga.add_shape(
            type="line", x0=x_hoy_iso, x1=x_hoy_iso, y0=0, y1=1,
            yref="paper", line=dict(color="red", width=2, dash="solid")
        )
        fig_carga.add_annotation(
            x=x_hoy_iso, y=1.05, yref="paper",
            text="🔴 HOY", showarrow=False,
            font=dict(color="red", size=10)
        )
        fig_carga.update_layout(height=250, margin=dict(t=40, b=20))
        st.plotly_chart(fig_carga, use_container_width=True)
    else:
        st.info("No hay tareas para mostrar en la linea de tiempo.")

# ============================================
# PAGINA: DEPENDENCIAS
# ============================================
elif pagina == "🔗 Dependencias":
    st.title("🔗 Analisis de Dependencias")

    tab1, tab2, tab3 = st.tabs(["🚨 Alertas", "⛓️ Cadenas Criticas", "💥 Impacto Cascada"])

    with tab1:
        st.markdown("### Tareas Bloqueadas por Dependencias No Cumplidas")
        alertas_data = []
        for t in tareas:
            if t['estado'] == 'finalizado':
                continue
            deps_pendientes = bloqueado_por.get(t['id'], [])
            if deps_pendientes:
                deps_nombres = []
                for d_id in deps_pendientes:
                    d_tarea = tareas_dict.get(d_id)
                    if d_tarea:
                        deps_nombres.append(f"{d_tarea['tarea'][:30]} ({get_estado_nombre(d_tarea['estado'])})")
                    else:
                        deps_nombres.append(str(d_id))
                alertas_data.append({
                    'Tarea': t['tarea'],
                    'Estado': get_estado_nombre(t['estado']),
                    'Fecha': t['fecha_objetivo'],
                    'Bloqueada por': ' | '.join(deps_nombres),
                    'Deps pendientes': len(deps_pendientes)
                })

        if alertas_data:
            alertas_data.sort(key=lambda x: x['Fecha'] or '9999')
            st.markdown(f"""
            <div class="alerta-critica">
                <strong>⚠️ {len(alertas_data)} tareas</strong> tienen dependencias sin cumplir
            </div>
            """, unsafe_allow_html=True)
            df_alertas = pd.DataFrame(alertas_data)
            st.dataframe(df_alertas, use_container_width=True, hide_index=True)
        else:
            st.success("Todas las dependencias estan cumplidas")

    with tab2:
        st.markdown("### Tareas que Bloquean a 2+ Tareas")
        cadenas_data = []
        for t in tareas:
            n_bloquea = len(bloquea_a.get(t['id'], []))
            if n_bloquea >= 2 and t['estado'] != 'finalizado':
                bloqueadas_nombres = [tareas_dict.get(b, {}).get('tarea', str(b))[:35] for b in bloquea_a[t['id']]]
                cadenas_data.append({
                    'Tarea Critica': t['tarea'],
                    'Estado': get_estado_nombre(t['estado']),
                    'Fecha': t['fecha_objetivo'],
                    'Bloquea a': n_bloquea,
                    'Tareas bloqueadas': ' | '.join(bloqueadas_nombres)
                })

        if cadenas_data:
            cadenas_data.sort(key=lambda x: -x['Bloquea a'])
            df_cadenas = pd.DataFrame(cadenas_data)
            st.dataframe(df_cadenas, use_container_width=True, hide_index=True)

            # Grafico de barras de impacto
            fig_cadenas = px.bar(
                df_cadenas,
                x='Bloquea a',
                y='Tarea Critica',
                orientation='h',
                color='Bloquea a',
                color_continuous_scale='Reds',
                title="Tareas con mayor impacto de bloqueo"
            )
            fig_cadenas.update_traces(hovertemplate='<b>%{y}</b><br>Bloquea a: %{x} tareas<extra></extra>')
            fig_cadenas.update_layout(
                height=max(300, len(cadenas_data) * 35),
                margin=dict(t=40, b=20),
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_cadenas, use_container_width=True)
        else:
            st.info("No hay tareas que bloqueen a 2 o mas tareas.")

    with tab3:
        st.markdown("### Impacto en Cascada - Si una tarea se retrasa, cuantas se afectan")
        st.caption("Calculo recursivo: incluye dependencias directas e indirectas")

        impacto_data = []
        for t in tareas:
            if t['estado'] == 'finalizado':
                continue
            afectadas = calcular_impacto_cascada(t['id'])
            if len(afectadas) > 0:
                impacto_data.append({
                    'Tarea': t['tarea'],
                    'Estado': get_estado_nombre(t['estado']),
                    'Fecha': t['fecha_objetivo'],
                    'Impacto cascada': len(afectadas),
                    'Tareas afectadas': ' | '.join([tareas_dict.get(a, {}).get('tarea', str(a))[:30] for a in list(afectadas)[:5]]) + ('...' if len(afectadas) > 5 else '')
                })

        if impacto_data:
            impacto_data.sort(key=lambda x: -x['Impacto cascada'])
            top_20 = impacto_data[:20]
            df_impacto = pd.DataFrame(top_20)
            st.dataframe(df_impacto, use_container_width=True, hide_index=True)

            fig_impacto = px.bar(
                df_impacto,
                x='Impacto cascada',
                y='Tarea',
                orientation='h',
                color='Impacto cascada',
                color_continuous_scale='OrRd',
                title="Top 20 - Mayor impacto en cascada"
            )
            fig_impacto.update_traces(hovertemplate='<b>%{y}</b><br>Tareas afectadas: %{x}<extra></extra>')
            fig_impacto.update_layout(
                height=max(350, len(top_20) * 30),
                margin=dict(t=40, b=20),
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_impacto, use_container_width=True)
        else:
            st.info("Ninguna tarea tiene dependencias en cascada.")

# ============================================
# PAGINA: TABLERO KANBAN
# ============================================
elif pagina == "🎯 Tablero Kanban":
    st.title("🎯 Tablero Kanban")

    # 5 columnas incluyendo bloqueado
    estados_kanban = ['por_iniciar', 'en_proceso', 'revision', 'bloqueado', 'finalizado']
    cols = st.columns(len(estados_kanban))

    for idx, estado_id in enumerate(estados_kanban):
        estado_info = estados_dict.get(estado_id)
        if not estado_info:
            # Si no existe en BD, crear info minima
            estado_info = {'id': estado_id, 'nombre': estado_id.replace('_', ' ').title(), 'color': '#6c757d'}

        tareas_estado = [t for t in tareas_filtradas if t['estado'] == estado_id]
        vencidas_en_col = len([t for t in tareas_estado if t['id'] in tareas_vencidas_set])

        with cols[idx]:
            # Header con contador de vencidas
            vencida_badge = f' <span style="background:#dc3545;color:white;padding:2px 6px;border-radius:10px;font-size:11px;">{vencidas_en_col}🔥</span>' if vencidas_en_col > 0 else ''
            st.markdown(f"""
            <div style="background-color: {estado_info['color']}; color: white; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
                <h4 style="margin:0;">{estado_info['nombre']}</h4>
                <p style="margin:3px 0 0 0;">{len(tareas_estado)} tareas{vencida_badge}</p>
            </div>
            """, unsafe_allow_html=True)

            for tarea in tareas_estado:
                cat_info = get_categoria_info(tarea['categoria'])
                resp_nombre = get_responsable_nombre(tarea['responsable'])

                # Indicador de fecha
                fecha_ind = ""
                try:
                    fecha_obj = datetime.strptime(tarea['fecha_objetivo'], "%Y-%m-%d").date()
                    if tarea['estado'] != 'finalizado':
                        if fecha_obj < hoy:
                            dias_r = (hoy - fecha_obj).days
                            fecha_ind = f'<span style="color:#ffcdd2;font-weight:bold;">⚠️ {dias_r}d atraso</span>'
                        elif fecha_obj == hoy:
                            fecha_ind = '<span style="color:#ffe082;font-weight:bold;">📌 HOY</span>'
                except Exception:
                    pass

                # Indicador de dependencias bloqueantes
                dep_ind = ""
                deps_pendientes = bloqueado_por.get(tarea['id'], [])
                if deps_pendientes:
                    dep_ind = f'<span style="color:#ffcdd2;font-size:11px;">🔒 {len(deps_pendientes)} dep(s)</span>'

                st.markdown(f"""
                <div class="task-card {tarea['prioridad']}">
                    <strong>{cat_info['icono']} {tarea['tarea'][:35]}{'...' if len(tarea['tarea']) > 35 else ''}</strong><br>
                    <small>👤 {resp_nombre}</small><br>
                    <small>📅 {tarea['fecha_objetivo']}</small> {fecha_ind}<br>
                    {dep_ind}
                </div>
                """, unsafe_allow_html=True)

                # Boton de edicion rapida
                if st.button("✏️", key=f"kanban_edit_{tarea['id']}", help="Editar"):
                    st.session_state['tarea_editar'] = tarea['id']
                    st.session_state['pagina_actual'] = "✏️ Editar Tarea"
                    st.rerun()

# ============================================
# PAGINA: PANEL DEL DIA
# ============================================
elif pagina == "📅 Panel del Dia":
    st.title("📅 Panel del Dia - Que hacer hoy")

    tab_vencidas, tab_hoy, tab_manana = st.tabs([
        f"🔴 Vencidas ({len(tareas_vencidas_set)})",
        f"🟡 Hoy ({len(tareas_hoy_set)})",
        f"🔵 Manana ({len(tareas_manana_set)})"
    ])

    def render_panel_tareas(tarea_ids, card_class, label):
        """Renderiza las tareas del panel agrupadas por responsable"""
        panel_tareas = [tareas_dict[tid] for tid in tarea_ids if tid in tareas_dict]
        if not panel_tareas:
            st.info(f"No hay tareas {label}")
            return

        # Agrupar por responsable
        por_responsable = {}
        for t in panel_tareas:
            resp = get_responsable_nombre(t['responsable'])
            if resp not in por_responsable:
                por_responsable[resp] = []
            por_responsable[resp].append(t)

        for resp_nombre, resp_tareas in por_responsable.items():
            st.markdown(f"#### 👤 {resp_nombre}")
            for t in resp_tareas:
                cat_info = get_categoria_info(t['categoria'])
                estado_nombre = get_estado_nombre(t['estado'])
                prioridad_color = {"urgente": "#dc3545", "alta": "#ff9800", "media": "#2196f3", "baja": "#9e9e9e"}.get(t['prioridad'], "#9e9e9e")

                # Dependencias
                deps_pendientes = bloqueado_por.get(t['id'], [])
                dep_text = ""
                if deps_pendientes:
                    dep_names = [tareas_dict.get(d, {}).get('tarea', str(d))[:25] for d in deps_pendientes]
                    dep_text = f"🔒 Bloqueada por: {', '.join(dep_names)}"

                col_check, col_info = st.columns([0.3, 5])
                with col_check:
                    # Checkbox para marcar como finalizada (solo si logueado)
                    if usuario_logueado():
                        if st.checkbox("✅", key=f"panel_check_{t['id']}", value=False):
                            actualizar_tarea(t['id'], {'estado': 'finalizado'})
                            st.session_state['recargar'] = True
                            st.rerun()
                    else:
                        st.markdown("🔒")

                with col_info:
                    st.markdown(f"""
                    <div class="dia-card {card_class}">
                        <strong>{cat_info['icono']} {t['tarea']}</strong><br>
                        <small>
                            <span class="badge-estado" style="background-color: {prioridad_color};">{t['prioridad']}</span>
                            &nbsp;
                            <span class="badge-estado" style="background-color: {get_estado_color(t['estado'])};">{estado_nombre}</span>
                            &nbsp; 📅 {t['fecha_objetivo']}
                        </small>
                        {'<br><small style="color:#ffcdd2;">⚠️ ' + dep_text + '</small>' if dep_text else ''}
                        {'<br><small style="color:#e0e0e0;">📝 ' + t['notas'] + '</small>' if t.get('notas') else ''}
                    </div>
                    """, unsafe_allow_html=True)

    with tab_vencidas:
        render_panel_tareas(tareas_vencidas_set, "dia-card-vencida", "vencidas")

    with tab_hoy:
        render_panel_tareas(tareas_hoy_set, "dia-card-hoy", "para hoy")

    with tab_manana:
        render_panel_tareas(tareas_manana_set, "dia-card-manana", "para manana")

# ============================================
# PAGINA: EDITAR TAREA
# ============================================
elif pagina == "✏️ Editar Tarea":
    st.title("✏️ Editar Tarea")

    if not usuario_logueado():
        st.warning("🔒 Debes iniciar sesion para editar tareas. Usa el panel de login en el sidebar.")
        st.stop()

    # Admins ven todas, usuarios normales solo las suyas
    if es_admin():
        tareas_editables = tareas
    else:
        tareas_editables = [t for t in tareas if t['responsable'] == get_usuario_actual()]

    if not tareas_editables:
        st.info("No tienes tareas asignadas.")
        st.stop()

    tareas_ordenadas = sorted(tareas_editables, key=lambda t: (get_categoria_info(t['categoria'])['nombre'], t['tarea']))
    tareas_opciones = {f"{get_categoria_info(t['categoria'])['icono']} {t['tarea'][:60]}": t['id'] for t in tareas_ordenadas}
    opciones_lista = list(tareas_opciones.keys())

    default_idx = 0
    if 'tarea_editar' in st.session_state:
        tarea_id = st.session_state['tarea_editar']
        for idx_t, (key, val) in enumerate(tareas_opciones.items()):
            if val == tarea_id:
                default_idx = idx_t
                break

    tarea_seleccionada = st.selectbox(
        "Seleccionar tarea",
        opciones_lista,
        index=default_idx
    )

    if tarea_seleccionada:
        tarea_id = tareas_opciones[tarea_seleccionada]
        tarea = tareas_dict.get(tarea_id)

        if tarea:
            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Informacion de la Tarea")

                cat_info = get_categoria_info(tarea['categoria'])
                st.markdown(f"**Categoria:** {cat_info['icono']} {cat_info['nombre']}")
                st.markdown(f"**Tarea:** {tarea['tarea']}")

                if tarea.get('dependencias'):
                    deps = [tareas_dict.get(d, {}).get('tarea', str(d)) for d in tarea['dependencias']]
                    st.markdown(f"**Dependencias:** {', '.join(deps[:3])}{'...' if len(deps) > 3 else ''}")

                # Info de dependencias
                deps_pendientes = bloqueado_por.get(tarea['id'], [])
                if deps_pendientes:
                    st.markdown("**🔒 Dependencias NO cumplidas:**")
                    for d_id in deps_pendientes:
                        d_tarea = tareas_dict.get(d_id)
                        if d_tarea:
                            st.markdown(f'<div class="dep-bloqueada">❌ {d_tarea["tarea"][:40]} - {get_estado_nombre(d_tarea["estado"])}</div>', unsafe_allow_html=True)
                else:
                    if tarea.get('dependencias'):
                        st.markdown('<div class="dep-libre">✅ Todas las dependencias cumplidas</div>', unsafe_allow_html=True)

                # Tareas que bloquea
                bloquea = bloquea_a.get(tarea['id'], [])
                if bloquea:
                    st.markdown(f"**⛓️ Esta tarea bloquea a {len(bloquea)} tarea(s):**")
                    for b_id in bloquea:
                        b_tarea = tareas_dict.get(b_id)
                        if b_tarea:
                            st.caption(f"→ {b_tarea['tarea'][:40]}")

            with col2:
                if es_admin():
                    # Admin: puede editar todo
                    st.markdown("### Editar (Admin)")

                    resp_opciones = [e['nombre'] for e in equipo]
                    resp_actual = get_responsable_nombre(tarea['responsable'])
                    resp_idx = resp_opciones.index(resp_actual) if resp_actual in resp_opciones else 0
                    nuevo_responsable = st.selectbox("Responsable", resp_opciones, index=resp_idx)

                    try:
                        fecha_actual = datetime.strptime(tarea['fecha_objetivo'], "%Y-%m-%d").date()
                    except Exception:
                        fecha_actual = date.today()
                    nueva_fecha = st.date_input("Fecha objetivo", value=fecha_actual)

                    estados_opciones_edit = [e['nombre'] for e in estados]
                    estado_actual = get_estado_nombre(tarea['estado'])
                    estado_idx = estados_opciones_edit.index(estado_actual) if estado_actual in estados_opciones_edit else 0
                    nuevo_estado = st.selectbox("Estado", estados_opciones_edit, index=estado_idx)

                    prioridad_opciones_edit = ['urgente', 'alta', 'media', 'baja']
                    prioridad_idx = prioridad_opciones_edit.index(tarea['prioridad']) if tarea['prioridad'] in prioridad_opciones_edit else 2
                    nueva_prioridad = st.selectbox("Prioridad", prioridad_opciones_edit, index=prioridad_idx)

                    nuevas_notas = st.text_area("Notas", value=tarea.get('notas', '') or '')

                else:
                    # No admin: solo puede cambiar estado
                    st.markdown("### Cambiar Estado")
                    st.caption("Solo puedes cambiar el estado de la tarea")

                    estados_opciones_edit = [e['nombre'] for e in estados]
                    estado_actual = get_estado_nombre(tarea['estado'])
                    estado_idx = estados_opciones_edit.index(estado_actual) if estado_actual in estados_opciones_edit else 0
                    nuevo_estado = st.selectbox("Estado", estados_opciones_edit, index=estado_idx)

            st.markdown("---")

            if es_admin():
                col1, col2, col3 = st.columns([1, 1, 2])

                with col1:
                    if st.button("💾 Guardar Cambios", type="primary", use_container_width=True):
                        nuevo_resp_id = next((e['id'] for e in equipo if e['nombre'] == nuevo_responsable), tarea['responsable'])
                        nuevo_estado_id = next((e['id'] for e in estados if e['nombre'] == nuevo_estado), tarea['estado'])

                        datos_actualizados = {
                            'responsable': nuevo_resp_id,
                            'fecha_objetivo': nueva_fecha.strftime("%Y-%m-%d"),
                            'estado': nuevo_estado_id,
                            'prioridad': nueva_prioridad,
                            'notas': nuevas_notas
                        }

                        actualizar_tarea(tarea_id, datos_actualizados)
                        st.success("✅ Tarea actualizada en Supabase")
                        st.session_state['recargar'] = True
                        st.rerun()

                with col2:
                    if tarea['estado'] != 'finalizado':
                        if st.button("✅ Marcar Finalizada", use_container_width=True):
                            actualizar_tarea(tarea_id, {'estado': 'finalizado'})
                            st.success("✅ Tarea marcada como finalizada")
                            st.session_state['recargar'] = True
                            st.rerun()
            else:
                if st.button("💾 Guardar Estado", type="primary"):
                    nuevo_estado_id = next((e['id'] for e in estados if e['nombre'] == nuevo_estado), tarea['estado'])
                    actualizar_tarea(tarea_id, {'estado': nuevo_estado_id})
                    st.success("✅ Estado actualizado")
                    st.session_state['recargar'] = True
                    st.rerun()

# ============================================
# PAGINA: NUEVO PROYECTO
# ============================================
elif pagina == "➕ Nuevo Proyecto":
    st.title("➕ Nuevo Proyecto")

    if not usuario_logueado():
        st.warning("🔒 Debes iniciar sesion para crear proyectos. Usa el panel de login en el sidebar.")
        st.stop()

    if not es_admin():
        st.warning("🔒 Solo los administradores (Felipe, Katherine) pueden crear nuevos proyectos.")
        st.stop()

    with st.form("form_nueva_tarea", clear_on_submit=True):
        # Nombre de la tarea
        nueva_tarea_nombre = st.text_input("Nombre de la tarea *", placeholder="Ej: Comprar manguera para riego")

        col1, col2 = st.columns(2)

        with col1:
            # Categoria
            cat_opciones = [f"{c['icono']} {c['nombre']}" for c in categorias]
            nueva_categoria = st.selectbox("Categoria *", cat_opciones)

            # Responsable
            resp_opciones = [e['nombre'] for e in equipo]
            nuevo_responsable = st.selectbox("Responsable *", resp_opciones)

            # Fecha objetivo
            nueva_fecha = st.date_input("Fecha objetivo *", value=hoy + timedelta(days=3))

        with col2:
            # Prioridad
            nueva_prioridad = st.selectbox("Prioridad", ["media", "urgente", "alta", "baja"], index=0)

            # Estado
            estados_opciones_new = [e['nombre'] for e in estados]
            nuevo_estado = st.selectbox("Estado inicial", estados_opciones_new, index=0)

            # Dependencias
            tareas_dep_opciones = [f"{get_categoria_info(t['categoria'])['icono']} {t['tarea'][:50]}" for t in tareas]
            nuevas_dependencias = st.multiselect("Dependencias (opcional)", tareas_dep_opciones)

        # Notas
        nuevas_notas = st.text_area("Notas (opcional)", placeholder="Detalles adicionales...")

        submitted = st.form_submit_button("✅ Crear Tarea", type="primary", use_container_width=True)

        if submitted:
            if not nueva_tarea_nombre.strip():
                st.error("El nombre de la tarea es obligatorio")
            else:
                # Resolver IDs
                cat_nombre_sel = nueva_categoria.split(' ', 1)[1] if ' ' in nueva_categoria else nueva_categoria
                cat_id = next((c['id'] for c in categorias if c['nombre'] == cat_nombre_sel), categorias[0]['id'])
                resp_id = next((e['id'] for e in equipo if e['nombre'] == nuevo_responsable), equipo[0]['id'])
                estado_id = next((e['id'] for e in estados if e['nombre'] == nuevo_estado), estados[0]['id'])

                # Resolver dependencias
                deps_ids = []
                for dep_label in nuevas_dependencias:
                    for t in tareas:
                        dep_check = f"{get_categoria_info(t['categoria'])['icono']} {t['tarea'][:50]}"
                        if dep_check == dep_label:
                            deps_ids.append(t['id'])
                            break

                datos_nueva = {
                    'tarea': nueva_tarea_nombre.strip(),
                    'categoria': cat_id,
                    'responsable': resp_id,
                    'fecha_objetivo': nueva_fecha.strftime("%Y-%m-%d"),
                    'prioridad': nueva_prioridad,
                    'estado': estado_id,
                    'dependencias': deps_ids if deps_ids else None,
                    'notas': nuevas_notas.strip() if nuevas_notas.strip() else None
                }

                crear_tarea(datos_nueva)
                st.success(f"✅ Tarea '{nueva_tarea_nombre}' creada exitosamente en Supabase")
                st.session_state['recargar'] = True
                st.rerun()

# ============================================
# FOOTER
# ============================================
st.sidebar.markdown("---")
st.sidebar.markdown("**Huerta Inteligente LPET**")
st.sidebar.markdown("Finca La Palma y El Tucan")
st.sidebar.markdown("Dashboard v3.0 - Supabase")

if st.sidebar.button("🔄 Recargar Datos"):
    st.session_state['recargar'] = True
    st.rerun()
