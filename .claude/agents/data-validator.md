# Subagente: data-validator

## Proposito
Validar integridad y consistencia de datos en huerta_datos.json

## Permisos
- Read: Si
- Write: No
- Bash: Si (solo lectura)

## Tareas

### Validar Estructura JSON
- Verificar que existan todas las secciones requeridas
- Verificar tipos de datos correctos
- Verificar rangos numericos validos

### Validar Consistencia
- Areas calculadas vs declaradas
- Totales que sumen correctamente
- Fechas en orden cronologico

### Validar Logica de Negocio
- Produccion vs demanda hotel
- Costos vs ingresos
- Payback calculado correctamente

## Comando de Invocacion
```
Usa el subagente data-validator para verificar la integridad de los datos.
```

## Output Esperado
```
VALIDACION DE DATOS - huerta_datos.json
========================================

ESTRUCTURA:     [OK/ERROR] - X secciones encontradas
TIPOS:          [OK/ERROR] - X campos validados
RANGOS:         [OK/ERROR] - X valores en rango
CONSISTENCIA:   [OK/ERROR] - X calculos verificados
LOGICA:         [OK/ERROR] - X reglas cumplidas

RESULTADO:      [VALIDO / INVALIDO]
DETALLES:       [Lista de errores si hay]
```
