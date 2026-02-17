# /project:start - Protocolo de Apertura

## Ejecucion Automatica

Al ejecutar este comando, Claude DEBE:

### FASE 1: Cargar Contexto (silencioso)
```bash
# Leer en orden:
cat CLAUDE.md
cat .claude/SESSION_LOG.md
cat .claude/PROGRESO.md
cat README.md
```

### FASE 2: Verificar Stack
```bash
ls -la output/
ls -la dashboard/
python3 -c "import json; d=json.load(open('output/huerta_datos.json')); print(f'JSON OK: {len(d)} secciones')"
lsof -i :8501 -i :8502 2>/dev/null || echo "Dashboard no corriendo"
```

### FASE 3: Mostrar Resumen

Presenta este resumen al usuario:

```
================================================================================
            HUERTA INTELIGENTE LPET - SESION INICIADA
================================================================================

PROYECTO: Huerta Inteligente - Finca La Palma y El Tucan
UBICACION: Zipacon, Cundinamarca

ESTADO: [Verde/Amarillo/Rojo segun PROGRESO.md]

ARCHIVOS CORE:
- huerta_datos.json    [OK/ERROR]
- Dashboard            [Corriendo en :XXXX / No corriendo]

ULTIMA SESION:
- Fecha: [de SESSION_LOG.md]
- Se hizo: [resumen 2-3 puntos]
- Quedo pendiente: [lista corta]

PARA EJECUTAR DASHBOARD:
source venv/bin/activate && streamlit run dashboard/huerta_app.py

================================================================================
```

### FASE 4: Preguntar Objetivo

Terminar SIEMPRE con:

"Que quieres lograr en esta sesion?"

NO empezar a trabajar hasta que el usuario confirme.
