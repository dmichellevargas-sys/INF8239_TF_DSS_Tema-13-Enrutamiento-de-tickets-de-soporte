"""Descarga el CSV público desde Hugging Face y verifica su SHA-256.

Uso:  uv run python scripts/download_data.py
Si la red bloquea Hugging Face, descargue el archivo a mano (pestaña "Files and versions")
y defina DATA_PATH=/ruta/al/csv; el hash se verifica igual.
"""
import json
import sys

from tickets_dss.config import REPORTS, ROOT, data_path, load_config
from tickets_dss.data import download, sha256


def main() -> int:
    cfg = load_config()
    target = data_path(cfg)
    try:
        download(cfg["data"]["url"], target, cfg["data"]["sha256"])
    except Exception as error:  # noqa: BLE001 - se informa y se sale con código de error
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    REPORTS.mkdir(exist_ok=True)
    manifest = {"source": cfg["data"]["source"], "url": cfg["data"]["url"], "license": cfg["data"]["license"],
                "file": str(target.relative_to(ROOT)) if target.is_relative_to(ROOT) else target.name,
                "sha256": sha256(target)}
    (REPORTS / "data_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("OK", manifest["file"], manifest["sha256"][:16])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
