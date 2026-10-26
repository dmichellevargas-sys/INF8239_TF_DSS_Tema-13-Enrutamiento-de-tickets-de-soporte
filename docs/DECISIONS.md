# Registro de decisiones técnicas y de alcance

| Fecha | Decisión | Motivo | Alternativas descartadas | Estado |
|---|---|---|---|---|
| 2026-10-09 | Trabajo individual, Modalidad A (proyecto aplicado), Tema 13 | Decisión de la estudiante; la aplicación con abstención y reglas es el artefacto práctico | Modalidad B (DSS); ambas modalidades a la vez | Firme |
| 2026-10-09 | Usar solo el dataset público de Hugging Face; ningún dato del empleador de la estudiante ni de otra organización | Decisión de la estudiante; política del curso sobre datos institucionales | — | Firme |
| 2026-10-09 | Entrada = asunto + cuerpo; excluir respuesta, tipo y etiquetas | Se asignan después del triaje (no disponibles al decidir) | Usarlas para subir métricas | Firme |
| 2026-10-09 | Partición aleatoria estratificada 70/15/15 sin casi duplicados | No hay fechas en el dataset | Partición temporal (imposible) | Firme, limitación declarada |
| 2026-10-09 | Líneas base: clase mayoritaria y Complement NB; candidato: regresión logística | Probabilidades para top-3 y abstención; costo bajo | SVM lineal (sin probabilidades); palabra + carácter (sondeo exploratorio: mismo acierto global, 3 veces más lento) | Firme |
| 2026-10-09 | Selección por top-3 en validación (empate < 1 punto → más rápido) | Es lo que ve la persona de triaje en la aplicación | Exactitud top-1; F1 macro | PROPUESTA a ratificar |
| 2026-10-09 | Objetivos de modos: sugerencia ≥ 75 % y top-3 ≥ 85 % | Equilibrio entre ayuda y error | Otros niveles | PROPUESTA a ratificar |
| 2026-10-09 | Auditar idioma también por idioma detectado | El 26 % de los tickets marcados como alemán están en inglés | Confiar en la etiqueta | Firme |
| 2026-10-09 | Decisión final: LIMITAR (piloto supervisado) | La puerta de top-3 no se cumple (0.787 < 0.80) y hay brechas por cola e idioma | Desplegar; no utilizar | PROPUESTA a ratificar |
| pendiente | M1 (acierto global) o M2 (pesos balanceados, mejor para colas pequeñas) | Decisión de valor | — | DECIDE LA ESTUDIANTE |
