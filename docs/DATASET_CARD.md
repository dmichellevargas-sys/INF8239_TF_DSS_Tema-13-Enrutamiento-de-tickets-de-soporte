# Dataset Card · Customer Support Tickets (Tobi-Bueck)

## Fuente, versión y licencia
- **Fuente:** Hugging Face, `Tobi-Bueck/customer-support-tickets`, archivo `dataset-tickets-multi-lang-4-20k.csv`.
- **Licencia:** CC BY-NC 4.0 (uso no comercial con atribución). Este proyecto es académico y cita la fuente; no se usa con fines comerciales.
- **Integridad:** SHA-256 `9be3bf810584fe01e8e83383e83dfd33f4c3910938ecad03ef151da79d8f0635` (en `configs/dss.yml`). `scripts/download_data.py` falla si el archivo descargado no coincide, porque el repositorio de origen se actualiza sin versiones numeradas.
- **Procedencia:** la ficha del autor no declara si los tickets son reales; la página promociona un generador de tickets sintéticos y el texto tiene rasgos de generación automática (estructura repetida, nombres anonimizados con `<name>`). Se trata como **probablemente sintético**. No contiene datos personales identificables según la ficha.
- **Restricción del proyecto:** no se usan datos de ninguna organización real, incluido el empleador de la estudiante.

## Diccionario
| Columna | Tipo | Uso en el proyecto |
|---|---|---|
| subject | texto | **Entrada** (asunto; 1 461 nulos, se reemplazan por vacío) |
| body | texto | **Entrada** (cuerpo) |
| queue | categoría, 10 valores | **Objetivo** del enrutamiento |
| priority | low / medium / high | **Objetivo** del modelo de prioridad |
| language | en / de | Auditoría por subgrupo (etiqueta ruidosa, ver abajo) |
| answer | texto | **Excluida:** la escribe el agente después del triaje |
| type | Incident / Request / Problem / Change | **Excluida:** la asigna el agente |
| tag_1 … tag_8 | categorías | **Excluidas:** las asigna el agente |

## Hallazgos de la auditoría (`reports/audit_summary.json`)
- 20 000 filas; se elimina 1 texto duplicado: quedan 19 999.
- Colas desbalanceadas: Technical Support concentra el 29 %; General Inquiry, el 1.3 %.
- **Etiqueta de idioma ruidosa:** de los 8 077 tickets marcados como alemán, 2 111 (26 %) están escritos en inglés según una heurística transparente de palabras funcionales. Por eso la auditoría por idioma se reporta también por idioma detectado.
- **Campos posteriores al triaje:** etiquetas + tipo predicen la cola con una exactitud de 0.39, y la respuesta del agente con 0.41. Se excluyen por disponibilidad (no existen al llegar el ticket), no por su poder predictivo.
- **Casi duplicados:** 104 tickets de validación y 99 de prueba tienen un gemelo en entrenamiento con similitud coseno > 0.90 y se eliminan. Solo 1 tiene una cola distinta a su gemelo.
- **Ruido de etiquetas:** la lectura de errores muestra tickets técnicos asignados a colas como Returns and Exchanges o Human Resources. Esto pone un techo al desempeño de cualquier modelo.
- No hay fechas: no es posible una partición temporal ni medir deriva en el tiempo.

## Usos prohibidos
Perfilar clientes o agentes, enrutar sin confirmación humana, entrenar con tickets reales sin autorización y presentar los resultados como representativos de una mesa de ayuda real.

## Cita
Bueck, T. (2025). *Customer support tickets* [Conjunto de datos]. Hugging Face. https://doi.org/10.57967/hf/6184
