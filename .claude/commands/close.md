# /project:close - Protocolo de Cierre

## Ejecucion Automatica

Al ejecutar este comando, Claude DEBE hacer todo esto SIN pedir confirmacion:

### FASE 1: Actualizar SESSION_LOG.md

Agregar nueva entrada al final de `.claude/SESSION_LOG.md`:

```markdown
## Sesion: [FECHA ACTUAL]
**Duracion:** [estimar]

### Objetivo
[Lo que el usuario pidio]

### Completado
- [x] Tarea 1
- [x] Tarea 2
- [ ] Tarea incompleta (si hay)

### Archivos Modificados
| Archivo | Accion | Descripcion |
|---------|--------|-------------|
| path/file | Creado/Modificado | Que se hizo |

### Pendiente para Proxima Sesion
1. [Prioridad ALTA]
2. [Prioridad MEDIA]

### Notas
- [Observaciones importantes]
```

### FASE 2: Actualizar PROGRESO.md

Actualizar `.claude/PROGRESO.md` con:
- Fecha de ultima actualizacion
- Mover tareas completadas a "Completados"
- Actualizar % de avance en "En Progreso"
- Agregar nuevos pendientes

### FASE 3: Verificacion Rapida
```bash
python3 -c "import json; json.load(open('output/huerta_datos.json')); print('JSON OK')"
ls output/*.md | wc -l
```

### FASE 4: Mostrar Resumen de Cierre

```
================================================================================
            SESION CERRADA - HUERTA INTELIGENTE LPET
================================================================================

FECHA: [hoy]

LO QUE SE LOGRO:
1. [Logro 1]
2. [Logro 2]
3. [Logro 3]

ARCHIVOS MODIFICADOS:
- [lista]

QUEDO PENDIENTE:
1. [ALTA] ...
2. [MEDIA] ...

CONTEXTO GUARDADO EN:
- .claude/SESSION_LOG.md
- .claude/PROGRESO.md

PARA RETOMAR:
cd "/Users/felipesardi/Desktop/EL GREEN HUB/LP&ET/HUERTA/AI STRATEGY"
claude
/project:start

================================================================================
```

### FASE 5: Recordatorio Final

Mostrar:
- Usa `/compact` si la sesion fue larga
- Usa `/cost` para ver costo de la sesion
