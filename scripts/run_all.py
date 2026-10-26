"""Flujo completo: descarga verificada -> auditoría -> entrenamiento y DSS -> fichas.

Uso:  uv run python scripts/run_all.py
"""
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

for script in ("download_data.py", "audit_data.py", "train_evaluate.py", "update_cards.py"):
    print(f"\n===== {script}", flush=True)
    sys.argv = [script]
    try:
        runpy.run_path(str(HERE / script), run_name="__main__")
    except SystemExit as exit_:
        if exit_.code not in (0, None):
            raise
