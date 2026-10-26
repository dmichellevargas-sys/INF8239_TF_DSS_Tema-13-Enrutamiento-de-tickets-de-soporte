# Model Card · Enrutamiento de tickets (regresión logística TF-IDF)

## Modelo y versión
- **M1 (seleccionado):** TF-IDF de palabras (unigramas y bigramas, `min_df=3`, hasta 150 000 términos, tf sublineal) + regresión logística multinomial (C elegido en validación). Archivo `models/logreg_C2.joblib`, con su hash en `reports/test_models.csv`.
- **Modelo de prioridad:** misma arquitectura (C = 2), entrenado solo con texto.
- **Líneas base:** B0 clase mayoritaria y B1 Complement Naive Bayes. **Alternativa reportada:** M2, la logística con pesos balanceados por cola.
- Responsable: [nombre de la estudiante], INF-8239, UASD.

## Uso previsto
Proponer a una persona coordinadora de mesa de ayuda la cola (una o tres opciones) y la prioridad de cada ticket nuevo, dentro del artefacto práctico descrito en `docs/APP_CARD.md`. La persona confirma o cambia la propuesta.

## Fuera de alcance
Enrutamiento automático sin revisión, evaluación de personas (clientes o agentes), tickets reales con datos personales, idiomas distintos de inglés y alemán, y cualquier dato de una organización real.

## Datos y partición
Dataset público de tickets (`docs/DATASET_CARD.md`). Partición estratificada por cola × idioma: 70 / 15 / 15, semilla 42, sin casi duplicados entre particiones. Entrada: asunto + cuerpo. Se excluyen respuesta, tipo y etiquetas. No hay partición temporal porque el dataset no tiene fechas.

## Resultados
<!-- AUTO:START -->

_Generado por `scripts/update_cards.py` desde `reports/`._

Candidato seleccionado: `logreg_C2` · regla: mayor top-3 en validación; empate < 1 punto → menor tiempo · puertas de calidad: **REVISAR** (top3_accuracy).

| Modelo | Top-1 | F1 macro | Top-3 [IC 95 %] | Entrenamiento (s) | Latencia (ms) | Tamaño (MB) | SHA-256 |
|---|---|---|---|---|---|---|---|
| B0 Clase mayoritaria | 0.291 | 0.045 | 0.407 [0.390, 0.426] | 1.5 | 0.41 | 0.5 | be3614203262 |
| B1 Complement NB | 0.426 | 0.331 | 0.714 [0.698, 0.730] | 1.6 | 1.12 | 5.5 | 192bf610c618 |
| M1 Regresión logística (logreg_C2) | 0.437 | 0.291 | 0.787 [0.771, 0.802] | 20.6 | 0.54 | 3.8 | 8be97da213b3 |
| M2 Logística con pesos balanceados (alternativa) | 0.442 | 0.426 | 0.775 [0.759, 0.790] | 19.1 | 0.58 | 3.8 | 78cf4194c3e0 |

| Indicador del artefacto (prueba) | Valor | Detalle |
|---|---|---|
| Tickets en modo sugerencia | 15.3% | acierto 74.8% |
| Tickets en modo top-3 | 43.3% | cola correcta entre 3: 83.3% |
| Tickets a triaje manual | 41.4% | decide la persona |
| Prioridad alta sugerida como baja | 3.0% | modelo solo: 3.4% |
| Recall de prioridad alta | 64.7% | modelo solo: 59.6% |

Por idioma (etiqueta del dataset → idioma detectado en el texto):

| Idioma | n | accuracy | top3 | triaje_manual | sugerencia |
|---|---|---|---|---|---|
| de→de | 914 | 0.392 | 0.739 | 0.539 | 0.085 |
| de→en | 294 | 0.425 | 0.810 | 0.391 | 0.180 |
| en→de | 1 | 0.000 | 1.000 | 0.000 | 0.000 |
| en→en | 1692 | 0.465 | 0.809 | 0.351 | 0.185 |

Entorno: Linux-6.18.44-fc-v153-x86_64-with-glibc2.39 · Python 3.12.13 · scikit-learn 1.9.1.

<!-- AUTO:END -->

## Errores y subgrupos
- Las colas grandes se reconocen bien con el top-3 (Technical Support 0.97), pero las pequeñas casi nunca aparecen (General Inquiry 0.00, Human Resources 0.12, Sales and Pre-Sales 0.18). Gran parte de los errores se van a Technical Support, la cola mayoritaria.
- M2 (pesos balanceados) sube el recall top-3 medio por cola de 0.53 a 0.67 a cambio de bajar el top-3 global de 0.787 a 0.775. Es una decisión de valor pendiente: priorizar el acierto global o la atención a las colas pequeñas.
- Los tickets realmente escritos en alemán reciben menos apoyo: más triaje manual (54 % frente a 35 %) y menos sugerencias directas (9 % frente a 18 %). El top-3 es 0.74 frente a 0.81 en inglés.
- Hay ruido de etiquetas en el dataset: tickets técnicos asignados a colas comerciales. Parte del error no es atribuible al modelo.

## Green AI
Modelo lineal en CPU: unos 23 s de entrenamiento, alrededor de 1 ms de latencia por ticket y 3.8 MB comprimido. Naive Bayes entrena 10 veces más rápido, pero su top-3 es 7 puntos peor. No se probaron modelos de lenguaje grandes: su costo no se justifica sin evidencia de que el techo impuesto por el ruido de etiquetas lo permita.

## Limitaciones y supervisión
Probabilidades sin calibración formal (los umbrales se fijaron empíricamente en validación), datos probablemente sintéticos, un solo corte aleatorio sin validación temporal y etiqueta de idioma ruidosa. Supervisión: cada propuesta requiere confirmación, los cambios se registran con su motivo y la tasa de cambios se revisa por cola e idioma.
