---
name: document-extraction
description: |
  Extracción inteligente de datos estructurados desde PDFs, Word, facturas y contratos.
  Activa cuando el usuario menciona: extraer datos de PDF, parsear facturas, OCR,
  tablas en PDF, documentos escaneados, extracción de contratos, facturas proveedores,
  reconocimiento de texto, formularios PDF, datos de documentos.
  
  Pipeline: PDF/Word → VisionParser → Schema Dinámico → JSON estructurado
  
  Usa Vision API para documentos complejos, PyMuPDF para simples.
---

# Extracción Inteligente de Documentos

## Propósito
Extraer datos estructurados de documentos PDF, Word, facturas y contratos
utilizando combinación de OCR tradicional y Vision API para máxima precisión.

## Cuándo Usar Esta Skill
- Extraer datos de facturas de proveedores
- Parsear contratos y extraer cláusulas clave
- Digitalizar reportes escaneados
- Extraer tablas de PDFs complejos
- Procesar formularios rellenados
- Consolidar datos de múltiples documentos

## Arquitectura del Pipeline

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Documento   │     │   Parser     │     │   Schema     │     │    JSON      │
│  (PDF/Word)  │ ──► │  (Vision/    │ ──► │  (Pydantic)  │ ──► │ Estructurado │
│              │     │   PyMuPDF)   │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

## Tipos de Parser

### SimpleParser (Gratuito)
- Usa PyMuPDF para extracción de texto
- Ideal para PDFs con texto seleccionable
- Sin costo de API
- Limitado para documentos escaneados

```python
from scripts.parse_document import SimpleParser
parser = SimpleParser()
texto = parser.parse("documento.pdf")
```

### VisionParser (Recomendado)
- Usa OpenAI Vision API
- Maneja documentos escaneados
- Preserva contexto entre páginas
- Excelente para tablas complejas
- Costo: ~$0.01-0.03 por página

```python
from scripts.parse_document import VisionParser
parser = VisionParser(dpi=300, use_context=True)
texto = parser.parse("documento_escaneado.pdf")
```

## Flujo de Trabajo

### Fase 1: Análisis del Documento
```bash
# Ver estructura del documento
python scripts/analizar_documento.py documento.pdf
```

**Determinar:**
- ¿Texto seleccionable o escaneado?
- ¿Tablas simples o complejas?
- ¿Una página o múltiples?
- ¿Formato consistente o variable?

### Fase 2: Definir Requisitos de Extracción

El usuario describe en lenguaje natural qué datos necesita:

```
"Necesito extraer de las facturas:
- Número de factura
- Fecha de emisión
- Nombre del proveedor
- Lista de productos con: código, descripción, cantidad, precio unitario, subtotal
- Total con impuestos"
```

### Fase 3: Generar Schema Dinámico
```bash
python scripts/generate_schema.py "requisitos del usuario" --output schema.py
```

**El generador:**
1. Analiza los requisitos en lenguaje natural
2. Detecta estructura (plana vs anidada)
3. Genera modelo Pydantic tipado
4. Incluye validaciones automáticas

### Fase 4: Extraer Datos
```bash
python scripts/extract_data.py documento.md requisitos.json --output datos.json
```

### Fase 5: Validar y Exportar
```bash
# Validar JSON generado
python -m json.tool output/datos.json

# Convertir a Excel si necesario
python scripts/json_to_excel.py output/datos.json
```

## Estructura de Requisitos

### Formato Plano (un registro por documento)
```json
{
  "use_case_name": "factura_simple",
  "fields": [
    {"field_name": "numero_factura", "field_type": "string", "required": true},
    {"field_name": "fecha", "field_type": "date", "format": "YYYY-MM-DD"},
    {"field_name": "proveedor", "field_type": "string"},
    {"field_name": "total", "field_type": "decimal", "required": true}
  ]
}
```

### Formato Anidado (lista de items)
```json
{
  "use_case_name": "factura_con_lineas",
  "fields": [
    {"field_name": "numero_factura", "field_type": "string"},
    {"field_name": "productos", "field_type": "list", "items": [
      {"field_name": "codigo", "field_type": "string"},
      {"field_name": "descripcion", "field_type": "string"},
      {"field_name": "cantidad", "field_type": "integer"},
      {"field_name": "precio_unitario", "field_type": "decimal"},
      {"field_name": "subtotal", "field_type": "decimal"}
    ]},
    {"field_name": "total", "field_type": "decimal"}
  ]
}
```

## Tipos de Campo Soportados

| Tipo | Descripción | Normalización |
|------|-------------|---------------|
| `string` | Texto libre | Trim, normalización Unicode |
| `integer` | Número entero | Elimina separadores |
| `decimal` | Número con decimales | Normaliza separadores (. vs ,) |
| `date` | Fecha | Convierte a ISO 8601 |
| `boolean` | Verdadero/Falso | Interpreta Sí/No, True/False |
| `enum` | Valor de lista | Valida contra opciones |
| `list` | Lista de objetos | Extrae múltiples registros |

## Scripts Disponibles

| Script | Comando | Función |
|--------|---------|---------|
| Analizador | `python scripts/analizar_documento.py doc.pdf` | Inspecciona estructura |
| Parser | `python scripts/parse_document.py doc.pdf` | Convierte a Markdown |
| Schema | `python scripts/generate_schema.py "requisitos"` | Genera modelo Pydantic |
| Extractor | `python scripts/extract_data.py doc.md req.json` | Extrae datos estructurados |
| Pipeline | `python scripts/extract_pipeline.py doc.pdf "requisitos"` | Todo en uno |

## Ejemplo Completo: Factura de Proveedor

### 1. Requisitos del Usuario
```
"Extraer de facturas de café:
- Número de factura (ej: FAC-2024-001)
- Fecha de emisión
- Proveedor (nombre y NIT)
- Lista de productos: código, descripción, cantidad en kg, precio/kg, subtotal
- Subtotal antes de impuestos
- IVA
- Total a pagar"
```

### 2. Ejecutar Pipeline
```bash
python scripts/extract_pipeline.py \
    documentos/factura_cafe.pdf \
    "Extraer: número factura, fecha, proveedor con NIT, productos (código, descripción, kg, precio/kg, subtotal), subtotal, IVA, total" \
    --vision \
    --output factura_cafe
```

### 3. Resultado (output/factura_cafe_extraido.json)
```json
{
  "numero_factura": "FAC-2024-001",
  "fecha": "2024-12-15",
  "proveedor": {
    "nombre": "Café Altura S.A.",
    "nit": "900123456-7"
  },
  "productos": [
    {
      "codigo": "CAF-001",
      "descripcion": "Café Arábica Huila",
      "cantidad_kg": 50.0,
      "precio_kg": 45000.00,
      "subtotal": 2250000.00
    },
    {
      "codigo": "CAF-002", 
      "descripcion": "Café Especial Nariño",
      "cantidad_kg": 30.0,
      "precio_kg": 55000.00,
      "subtotal": 1650000.00
    }
  ],
  "subtotal": 3900000.00,
  "iva": 741000.00,
  "total": 4641000.00
}
```

## Procesamiento por Lotes

Para múltiples documentos del mismo tipo:

```bash
# Procesar todas las facturas en una carpeta
python scripts/extract_batch.py \
    --input-dir documentos/facturas/ \
    --requirements requisitos_factura.json \
    --output-dir output/facturas_procesadas/
```

## Manejo de Documentos Problemáticos

### PDFs Escaneados con Baja Calidad
```python
parser = VisionParser(
    dpi=400,           # Mayor resolución
    use_context=True,  # Contexto entre páginas
    clean_output=True  # Limpiar con LLM
)
```

### Tablas que Cruzan Páginas
```python
parser = VisionParser(
    use_context=True,     # CRÍTICO: preserva contexto
    merge_tables=True,    # Une tablas divididas
    page_overlap=100      # Píxeles de overlap
)
```

### Documentos con Múltiples Idiomas
```python
# Especificar idioma en el prompt de extracción
extractor = DataExtractor(language_hint="español")
```

## Costos Estimados

| Operación | Costo Aproximado |
|-----------|------------------|
| SimpleParser (PyMuPDF) | Gratis |
| VisionParser (por página) | $0.01 - $0.03 |
| Generación de Schema | $0.02 - $0.05 |
| Extracción de datos | $0.05 - $0.15 |
| **Pipeline completo (10 págs)** | **$0.20 - $0.50** |

**Optimización de costos:**
- Reusar schemas para documentos del mismo tipo
- Usar SimpleParser cuando sea posible
- Procesar en lotes para amortizar schema

## Restricciones Obligatorias

- [ ] Siempre analizar documento antes de extraer
- [ ] Validar JSON de salida con schema
- [ ] Preservar documento original sin modificar
- [ ] Documentar cualquier dato que no se pudo extraer
- [ ] Usar Vision solo cuando SimpleParser no funcione
- [ ] Notificar al usuario sobre costos antes de procesar lotes grandes

## Integración con Otras Skills

- **financial-analysis**: Extraer datos de reportes financieros PDF
- **data-pipeline**: Consolidar datos extraídos de múltiples documentos
- **dashboard-generator**: Visualizar datos extraídos

## Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| "Tabla incompleta" | Tabla cruza páginas | Usar `use_context=True` |
| "Datos no encontrados" | Schema no coincide | Ajustar requisitos |
| "OCR ilegible" | Documento muy dañado | Aumentar DPI, limpiar imagen |
| "JSON inválido" | Extracción parcial | Revisar documento manualmente |

---

*Skill parte del Kit de Inicio de Proyectos Claude Code*
*Última actualización: Enero 2025*
