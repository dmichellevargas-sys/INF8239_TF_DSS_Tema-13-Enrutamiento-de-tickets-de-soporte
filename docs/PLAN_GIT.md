# Plan de trabajo con Git (6 semanas)

La rúbrica evalúa issues, commits sustantivos, ramas y pull requests **a lo largo de las seis semanas**, además de la defensa. Aunque el código ya está terminado, súbelo **por partes**, en el orden de esta tabla, desde tu cuenta, y **entiende cada parte antes de integrarla**.

## Configuración inicial (semana 1)
```bash
git init && git branch -M main
git add .gitignore pyproject.toml uv.lock .python-version README.md
git commit -m "chore: estructura inicial del proyecto (#1)"
git remote add origin https://github.com/<usuario>/<repositorio>.git && git push -u origin main
```
Crea los issues de `docs/issues.csv` en GitHub (usa la plantilla `.github/ISSUE_TEMPLATE/tarea.md`) y protege `main` para exigir pull requests.

## Ciclo por issue
```bash
git switch -c feat/<nombre>          # una rama por issue
git add <archivos del issue>
git commit -m "feat: <qué hace> (#<n° issue>)"
git push -u origin feat/<nombre>     # abre un pull request que cierre el issue
```
Trabajas sola, así que pide a un compañero o compañera que revise tus pull requests (la política exige revisión de otra persona); a cambio, revisa tú los suyos. Si no es posible, deja en cada PR una autorrevisión con una lista de verificación y declárala.

## Qué archivos van en cada semana
| Semana | Ramas | Archivos |
|---|---|---|
| 1 | feat/alcance, feat/datos-descarga, docs/riesgos | `configs/dss.yml`, `src/tickets_dss/__init__.py`, `config.py`, `data.py` (solo `sha256` y `download`), `scripts/download_data.py`, `docs/RISK_REGISTER.csv`, `docs/DECISIONS.md` |
| 2 | feat/auditoria, feat/particion, feat/lineas-base | resto de `data.py`, `scripts/audit_data.py`, `tests/conftest.py`, `tests/test_data_contract.py`, `models.py` (dummy y nb), `docs/DATASET_CARD.md` |
| 3 | feat/candidato, feat/errores | `models.py` completo, `evaluation.py`, primera versión de `scripts/train_evaluate.py` |
| 4 | feat/dss, feat/app | `dss.py`, `tests/test_models_dss.py`, `app/streamlit_app.py`, `docs/APP_CARD.md` |
| 5 | feat/auditoria-responsable, docs/fichas, ci/actions | versión final de `train_evaluate.py`, `scripts/update_cards.py`, `docs/MODEL_CARD.md`, `.github/` |
| 6 | docs/entrega | `notebooks/`, `reports/`, `docs/AI_USE_DECLARATION.md`, `docs/PLAN_GIT.md`, informe |

Cada semana, actualiza `docs/DECISIONS.md` con lo que decidiste o cambiaste, en tus propias palabras.
