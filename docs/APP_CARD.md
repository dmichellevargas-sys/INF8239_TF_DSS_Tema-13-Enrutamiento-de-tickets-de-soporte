# Ficha del artefacto práctico · Aplicación de triaje asistido

> Modalidad A: esta aplicación es el artefacto práctico del proyecto. Muestra cómo se usaría el modelo de forma
> responsable; el centro del trabajo es la pregunta, la evaluación y el análisis de errores.

## Tarea apoyada y usuaria
- **Decisión:** a qué cola enviar un ticket nuevo y con qué prioridad atenderlo.
- **Usuaria:** la persona coordinadora de triaje. El sistema propone; la persona confirma, elige otra cola o hace el triaje sin ayuda.
- **Alternativa sin modelo (línea base operativa):** triaje manual de todos los tickets por orden de llegada.

## Componentes
| Componente | Qué hace | Dónde |
|---|---|---|
| Modelo de cola | Probabilidad de cada una de las 10 colas a partir del asunto y el cuerpo | `src/tickets_dss/models.py` |
| Abstención (tres modos) | **Sugerencia:** una cola preseleccionada si la confianza ≥ t₁. **Top-3:** tres opciones si la confianza acumulada ≥ t₃. **Triaje manual:** sin propuesta | `src/tickets_dss/dss.py` |
| Prioridad | Modelo de prioridad + reglas explícitas (caída de servicio, seguridad o pérdida de datos, urgencia) que **solo suben** la prioridad | `configs/dss.yml` |
| Explicación | Términos del ticket que más pesaron hacia la cola propuesta | `explain()` |
| Registro | Decisión final, cambio respecto a la propuesta y motivo, **sin guardar el texto** | `app/streamlit_app.py` |

Los umbrales t₁ y t₃ se fijan en validación con dos objetivos: acierto ≥ 75 % en el modo sugerencia y cola correcta entre las 3 opciones ≥ 85 % en el modo top-3. Esos objetivos son una **propuesta a ratificar** por la estudiante.

## Criterios explícitos de priorización
1. Si una regla de `priority_rules` se activa, la prioridad sugerida sube al nivel de la regla.
2. En los demás casos, se usa la prioridad del modelo.
3. Una regla nunca baja la prioridad. El error más grave es sugerir **baja** para un ticket de prioridad **alta**, y se mide como `high_to_low_rate`.

## Puertas de calidad (propuesta)
Top-3 ≥ 0.80; brecha de top-3 entre idiomas ≤ 0.10; alta→baja ≤ 5 %; latencia ≤ 50 ms; modelo ≤ 50 MB. Resultado en `reports/results.json` (`gates_status`).

## Ética y uso responsable
- Datos públicos y probablemente sintéticos; ningún dato de una organización real.
- Separación entre predicción y decisión: no existe un modo automático.
- La abstención es obligatoria cuando la confianza es baja.
- Se audita por idioma, cola y prioridad.
- El registro de decisiones no guarda el texto del ticket (minimización).

## Monitoreo propuesto (si se usara en un piloto)
Tasa de cambios de la persona sobre la propuesta, por cola e idioma; proporción de cada modo; tasa alta→baja; y distribución de colas confirmadas. Si la tasa de cambio en el modo sugerencia supera el 30 % en un mes, o la tasa alta→baja supera el 5 %, se vuelve al triaje manual completo y se reentrena.
