"""Rellena la sección automática de docs/MODEL_CARD.md con los resultados de reports/ (trazabilidad)."""
import json
import re

import pandas as pd

from tickets_dss.config import REPORTS, ROOT

CARD = ROOT / "docs/MODEL_CARD.md"
START, END = "<!-- AUTO:START -->", "<!-- AUTO:END -->"


def md(df: pd.DataFrame) -> str:
    rows = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    return "\n".join(rows + ["| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False)])


def main() -> None:
    r = json.loads((REPORTS / "results.json").read_text(encoding="utf-8"))
    t = pd.read_csv(REPORTS / "test_models.csv")
    lang = pd.read_csv(REPORTS / "by_language_detected.csv")
    models = pd.DataFrame({
        "Modelo": t["model"], "Top-1": t["accuracy"].map("{:.3f}".format), "F1 macro": t["f1_macro"].map("{:.3f}".format),
        "Top-3 [IC 95 %]": [f"{a:.3f} [{b:.3f}, {c:.3f}]" for a, b, c in zip(t.top3_accuracy, t.top3_ci_low, t.top3_ci_high)],
        "Entrenamiento (s)": t["train_seconds"].map("{:.1f}".format), "Latencia (ms)": t["latency_ms"].map("{:.2f}".format),
        "Tamaño (MB)": t["size_mb"].map("{:.1f}".format), "SHA-256": t["sha256"].str[:12]})
    d = r["dss_test"]
    dss = pd.DataFrame([
        ["Tickets en modo sugerencia", f"{d['share_sugerencia']:.1%}", f"acierto {d['accuracy_sugerencia']:.1%}"],
        ["Tickets en modo top-3", f"{d['share_top3']:.1%}", f"cola correcta entre 3: {d['hit_top3_mode']:.1%}"],
        ["Tickets a triaje manual", f"{d['share_triaje_manual']:.1%}", "decide la persona"],
        ["Prioridad alta sugerida como baja", f"{d['high_to_low_rate_dss']:.1%}", f"modelo solo: {d['high_to_low_rate_model']:.1%}"],
        ["Recall de prioridad alta", f"{d['high_recall_dss']:.1%}", f"modelo solo: {d['high_recall_model']:.1%}"]],
        columns=["Indicador del artefacto (prueba)", "Valor", "Detalle"])
    lang = lang.assign(**{c: lang[c].map("{:.3f}".format) for c in ["accuracy", "top3", "triaje_manual", "sugerencia"]})
    auto = "\n\n".join([START, "_Generado por `scripts/update_cards.py` desde `reports/`._",
                        (f"Candidato seleccionado: `{r['candidate']}` · regla: {r['selection_rule']} · "
                        f"puertas de calidad: **{r['gates_status']}** ({', '.join(k for k, v in r['gates'].items() if not v) or 'todas cumplen'})."),
                        md(models), md(dss), "Por idioma (etiqueta del dataset → idioma detectado en el texto):",
                        md(lang.rename(columns={"lang_group": "Idioma"})),
                        (f"Entorno: {r['environment']['platform']} · Python {r['environment']['python']} · "
                        f"scikit-learn {r['environment']['scikit_learn']}."), END])
    text = CARD.read_text(encoding="utf-8")
    CARD.write_text(re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: auto, text, flags=re.DOTALL),
                    encoding="utf-8")
    print("MODEL_CARD.md actualizado")


if __name__ == "__main__":
    main()
