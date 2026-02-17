# /project:verify - Verificacion Completa

## Descripcion
Verificacion completa del proyecto antes de commit o cierre de sesion.

## Ejecucion

### 1. Validar JSON
```bash
python3 << 'EOF'
import json
import sys

try:
    with open('output/huerta_datos.json', 'r') as f:
        data = json.load(f)

    # Verificar secciones requeridas
    required = ['metadata', 'dimensiones', 'finanzas', 'cronograma']
    missing = [s for s in required if s not in data]

    if missing:
        print(f"WARN: Secciones faltantes: {missing}")
    else:
        print(f"OK: JSON valido con {len(data)} secciones")

    # Verificar datos criticos
    camas = data.get('dimensiones', {}).get('camas_huerta', [])
    print(f"OK: {len(camas)} camas de huerta")

    fases = data.get('cronograma', {}).get('fases', [])
    print(f"OK: {len(fases)} fases de cronograma")

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
EOF
```

### 2. Verificar Archivos Criticos
```bash
echo "=== Verificando archivos criticos ==="

files=(
    "output/huerta_datos.json"
    "output/PLAN_HUERTA_INTELIGENTE.md"
    "output/CRONOGRAMA_IMPLEMENTACION.md"
    "dashboard/huerta_app.py"
    "CLAUDE.md"
)

for f in "${files[@]}"; do
    if [ -f "$f" ]; then
        size=$(ls -lh "$f" | awk '{print $5}')
        echo "OK: $f ($size)"
    else
        echo "FALTA: $f"
    fi
done
```

### 3. Verificar Sintaxis Dashboard
```bash
source venv/bin/activate 2>/dev/null
python3 -m py_compile dashboard/huerta_app.py && echo "OK: Sintaxis dashboard correcta" || echo "ERROR: Errores de sintaxis en dashboard"
```

### 4. Verificar Dependencias
```bash
source venv/bin/activate 2>/dev/null
python3 -c "import streamlit, plotly, pandas; print('OK: Dependencias instaladas')" 2>/dev/null || echo "WARN: Faltan dependencias"
```

### 5. Resumen
```
================================================================================
                    VERIFICACION COMPLETA
================================================================================

JSON:           [OK/ERROR]
Archivos:       [X/Y presentes]
Dashboard:      [OK/ERROR]
Dependencias:   [OK/WARN]

RESULTADO:      [LISTO PARA COMMIT / REQUIERE ATENCION]
================================================================================
```
