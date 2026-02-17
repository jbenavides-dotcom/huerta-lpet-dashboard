# /project:catchup - Retomar Trabajo

## Descripcion
Comando para retomar el trabajo en el proyecto Huerta Inteligente LPET.
Carga contexto, muestra estado actual y sugiere proximos pasos.

## Ejecucion

Al ejecutar este comando, Claude debe:

### 1. Cargar Contexto
```bash
# Leer archivos de contexto
cat CLAUDE.md
cat .claude/SESSION_LOG.md
cat .claude/PROGRESO.md
```

### 2. Verificar Estado del Proyecto
```bash
# Estructura actual
ls -la output/
ls -la dashboard/

# Validar JSON
python3 -c "import json; d=json.load(open('output/huerta_datos.json')); print(f'JSON OK: {len(d)} secciones')"

# Estado del entorno
ls venv/ 2>/dev/null && echo "venv existe" || echo "venv NO existe"
```

### 3. Verificar Dashboard
```bash
# Verificar si el dashboard esta corriendo
lsof -i :8501 2>/dev/null || lsof -i :8502 2>/dev/null || echo "Dashboard no esta corriendo"
```

### 4. Mostrar Resumen

Presenta al usuario:

```
================================================================================
                    HUERTA INTELIGENTE LPET - CATCHUP
================================================================================

ESTADO DEL PROYECTO: [Verde/Amarillo/Rojo]

ARCHIVOS GENERADOS:
- [ ] huerta_datos.json (XX KB)
- [ ] PLAN_HUERTA_INTELIGENTE.md (XX KB)
- [ ] CRONOGRAMA_IMPLEMENTACION.md (XX KB)
- [ ] huerta_app.py (XX KB)

ULTIMA SESION:
- Fecha: [fecha]
- Lo que se hizo: [resumen]
- Quedo pendiente: [lista]

DASHBOARD:
- Estado: [Corriendo en puerto XXXX / No corriendo]
- Para iniciar: source venv/bin/activate && streamlit run dashboard/huerta_app.py

PROXIMOS PASOS SUGERIDOS:
1. [Paso 1]
2. [Paso 2]
3. [Paso 3]

================================================================================
```

### 5. Preguntar Objetivo
Terminar preguntando: "Que quieres lograr en esta sesion?"
