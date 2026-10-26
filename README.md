# INF-8239 · Trabajo final · Clasificación de tickets de soporte para apoyar su enrutamiento

**Modalidad A (proyecto aplicado de ciencia de datos) · Tema 13 · trabajo individual.**

**Pregunta:** ¿con qué exactitud se puede predecir la cola de un ticket a partir de su asunto y su cuerpo, y es
suficiente para apoyar el triaje que hoy se hace a mano? Se responde con datos, líneas base, modelos, evaluación
y análisis de errores. El **artefacto práctico** es una aplicación que propone la cola y la prioridad de cada
ticket, se abstiene cuando la confianza es baja y deja la decisión a la persona de triaje.

> Datos: dataset público `Tobi-Bueck/customer-support-tickets` (Hugging Face, CC BY-NC 4.0), probablemente
> sintético. **No se usa ningún dato de organizaciones reales.** Uso académico, no comercial.

## Ejecución
```bash
uv python install 3.12
uv sync
uv run pytest -q                       # 19 pruebas (18 con datos sintéticos mínimos; la de la app se omite si no hay modelo)
uv run python scripts/run_all.py       # descarga verificada -> auditoría -> modelos y artefacto -> Model Card (≈ 5 min en CPU)
uv run streamlit run app/streamlit_app.py
uv run jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 notebooks/TF_DSS_tickets.ipynb
```
Si su red bloquea Hugging Face, descargue el CSV desde la pestaña *Files and versions* y ejecute con
`DATA_PATH=/ruta/al/csv` (en PowerShell: `$env:DATA_PATH="C:\ruta\archivo.csv"`). El SHA-256 se verifica igual.

## Alcance individual (orientaciones del curso)
| Requisito | Cumplimiento |
|---|---|
| Línea base + 1 modelo candidato | B0 clase mayoritaria, B1 Complement NB; M1 regresión logística (y M2 balanceada como alternativa) |
| 6 pruebas | 19 pruebas (`tests/`) y CI en GitHub Actions |
| Documentación | `docs/`: Dataset Card, Model Card, ficha del artefacto (APP_CARD), riesgos, decisiones, issues, plan de Git y declaración de IA |
| Repositorio y demostración | Este repositorio y `app/streamlit_app.py` |
| Green AI | Tiempo de entrenamiento, latencia y tamaño en `reports/test_models.csv` |

## Estructura
```
configs/dss.yml        propósito, usos prohibidos, datos (URL + SHA-256), umbrales, reglas y puertas
src/tickets_dss/       config, data, models, dss (lógica de la app), evaluation
scripts/               download_data, audit_data, train_evaluate, update_cards, run_all
app/                   artefacto práctico: aplicación de triaje asistido
tests/                 contrato de datos, fuga, partición, modelos, reglas, modos y métricas
reports/               métricas, subgrupos, errores, recomendaciones de prueba y figuras
docs/                  fichas, riesgos, decisiones, backlog e integración Git
```

## Resultados (prueba, 2 901 tickets)
| Modelo | Top-1 | Top-3 [IC 95 %] | Entrenamiento | Tamaño |
|---|---|---|---|---|
| B0 Clase mayoritaria | 0.291 | 0.407 | 2.7 s | 0.5 MB |
| B1 Complement NB | 0.426 | 0.714 [0.698, 0.730] | 2.5 s | 5.5 MB |
| **M1 Regresión logística** | 0.437 | **0.787 [0.771, 0.802]** | 23 s | 3.8 MB |
| M2 Logística balanceada | 0.442 | 0.775 [0.759, 0.790] | 24 s | 3.8 MB |

Artefacto en prueba: propone una sola cola en el 15 % de los tickets (acierto 75 %), tres opciones en el 43 % (la
cola correcta está entre las 3 en el 83 %) y no propone nada en el 41 %. La opción correcta queda disponible para la
persona en el 89 % de los casos. Prioridad alta sugerida como baja: 3.0 %. Puertas: **REVISAR** (top-3 0.787 < 0.80).
**Respuesta a la pregunta:** el modelo sirve para apoyar el triaje, no para enrutar solo.
**Recomendación: LIMITAR** a un piloto supervisado (ver `docs/DECISIONS.md`).

> Nota: los nombres internos del código (`tickets_dss`, `configs/dss.yml`, `RoutingDSS`) se conservan para no
> romper el historial del repositorio; corresponden a la lógica del artefacto práctico.

## Cita del dataset
Bueck, T. (2025). *Customer support tickets* [Conjunto de datos]. Hugging Face. https://doi.org/10.57967/hf/6184
