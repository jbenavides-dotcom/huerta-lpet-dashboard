# Subagente: dashboard-tester

## Proposito
Probar y validar el dashboard de Streamlit

## Permisos
- Read: Si
- Write: No
- Bash: Si

## Tareas

### Verificar Sintaxis
- Compilar huerta_app.py sin errores
- Verificar imports

### Verificar Dependencias
- streamlit instalado
- plotly instalado
- pandas instalado

### Verificar Datos
- JSON accesible desde dashboard
- Rutas correctas

### Prueba de Ejecucion
- Iniciar dashboard
- Verificar que carga sin errores
- Verificar paginas principales

## Comando de Invocacion
```
Usa el subagente dashboard-tester para verificar el dashboard.
```

## Output Esperado
```
TEST DE DASHBOARD - huerta_app.py
==================================

SINTAXIS:       [OK/ERROR]
IMPORTS:        [OK/ERROR]
DEPENDENCIAS:   [OK/ERROR]
DATOS:          [OK/ERROR]
EJECUCION:      [OK/ERROR]

PAGINAS PROBADAS:
- Vista General:    [OK/ERROR]
- Mapa Interactivo: [OK/ERROR]
- Zonas:            [OK/ERROR]
- Finanzas:         [OK/ERROR]
- Cronograma:       [OK/ERROR]

RESULTADO:      [FUNCIONAL / CON ERRORES]
URL:            http://localhost:XXXX
```
