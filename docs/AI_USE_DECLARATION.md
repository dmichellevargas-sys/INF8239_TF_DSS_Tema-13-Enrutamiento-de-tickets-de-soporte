# Declaración de uso de inteligencia artificial

## Herramientas utilizadas
Claude (Anthropic), en claude.ai, dentro de un proyecto de la asignatura. Octubre de 2026.

## Propósito de cada uso
- Ayuda para elegir la modalidad y verificar la licencia del dataset.
- Código: descarga verificada, contrato de datos, auditoría, partición sin casi duplicados, modelos, lógica del artefacto práctico (abstención, reglas de prioridad, explicación), evaluación por subgrupos, Green AI, aplicación Streamlit, pruebas, CI y notebook.
- Borradores: fichas (datos, modelo y artefacto), registro de riesgos y decisiones, backlog de issues, plan de Git, README e informe.

## Prompts o decisiones relevantes
1. Orientaciones del trabajo final y política de evidencia, con la pregunta sobre cómo arrancar.
2. Respuestas de la estudiante: trabajo **individual**; **Tema 13**; *"ayúdame a decidir"* la modalidad. La IA comparó ambas modalidades y la estudiante eligió la **Modalidad A**.
3. Restricción fijada por la estudiante: no usar ningún dato de su empleador. Se aplica como uso prohibido y se verifica con una prueba.
4. La estudiante descargó el CSV de Hugging Face y lo compartió, porque el entorno de la IA no tenía acceso a ese sitio.

## Valores propuestos por la IA que la estudiante debe ratificar o cambiar
- Regla de selección (top-3 en validación).
- Objetivos de los modos (75 % y 85 %).
- Reglas y palabras clave de prioridad.
- Puertas de calidad.
- Decisión final (LIMITAR).
- Elección entre M1 y M2 (pendiente).

## Elementos verificados por la estudiante
> Marque solo lo que haya comprobado personalmente.

- [ ] Ejecuté `uv sync`, `uv run pytest -q` y `uv run python scripts/run_all.py` y obtuve las mismas cifras.
- [ ] Leí los 30 errores de `reports/error_sample_30.csv` y estoy de acuerdo (o no) con el análisis de ruido de etiquetas.
- [ ] Revisé las reglas de prioridad y los umbrales, y los ratifiqué o cambié en `configs/dss.yml`.
- [ ] Verifiqué la licencia, el autor y el año del dataset en Hugging Face, y las referencias del informe.
- [ ] Probé la aplicación y puedo explicar cada módulo de `src/`.

## Cambios realizados sobre resultados generados
| Problema detectado | Corrección |
|---|---|
| El entorno de la IA no tenía acceso a Hugging Face. | La estudiante compartió el CSV; el código siempre descarga del origen y verifica el SHA-256. |
| El sondeo inicial (sin quitar casi duplicados) daba una exactitud de 0.50; el protocolo final da 0.44. | Se reporta la cifra del protocolo final; la diferencia se explica por los casi duplicados. |
| El 26 % de los tickets marcados como alemán están en inglés. | Se añadió el idioma detectado y la auditoría se hace con las dos versiones. |
| Las colas pequeñas casi nunca aparecían en el top-3. | Se añadió la alternativa M2 (pesos balanceados) y se documentó el trade-off sin cambiar la regla de selección. |
| Colores y etiquetas inconsistentes en las figuras. | Se unificaron los colores por idioma y se acortaron las etiquetas. |

## Responsabilidad asumida
La estudiante responde por el código, los resultados, las referencias y las conclusiones, y declara poder explicar, ejecutar y defender todo lo entregado.
