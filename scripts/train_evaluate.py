"""Entrenamiento, comparación, lógica del artefacto (abstención y reglas), auditoría por subgrupos y Green AI.

Protocolo (declarado antes de mirar la prueba):
  * Partición estratificada por cola × idioma: 70 % entrenamiento, 15 % validación, 15 % prueba.
    El dataset no tiene fechas, así que no es posible una partición temporal (limitación declarada).
  * Se eliminan de validación y prueba los tickets casi duplicados de entrenamiento.
  * Entrada: solo asunto + cuerpo. Se excluyen respuesta, tipo y etiquetas (se llenan después del triaje).
  * Modelos: B0 clase mayoritaria, B1 Complement Naive Bayes (líneas base) y M1 regresión logística
    (candidato). El parámetro C del candidato se elige en validación. M2 (logística con pesos
    balanceados) se reporta como alternativa para las colas pequeñas, no entra en la selección.
  * Selección: mayor exactitud top-3 en validación (lo que ve la persona decisora); empate (< 1 punto)
    → menor tiempo de entrenamiento.
  * Umbrales de los modos del DSS: en validación, con los objetivos de configs/dss.yml.
  * La prueba se usa una sola vez al final.

Uso:  uv run python scripts/train_evaluate.py
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from time import perf_counter

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn

from tickets_dss.config import MODELS, QUEUES, REPORTS, data_path, load_config
from tickets_dss.data import load, split
from tickets_dss.dss import RoutingDSS, evaluate_dss
from tickets_dss.evaluation import (
    bootstrap_ci,
    bootstrap_gap,
    mcnemar,
    metrics,
    top_confusions,
    topk_hits,
)
from tickets_dss.models import build, explain

C_GRID = [2.0, 5.0, 10.0]


def fit_timed(model, x, y):
    start = perf_counter()
    model.fit(x, y)
    return model, perf_counter() - start


def size_mb(model, name: str) -> tuple[float, str]:
    path = MODELS / f"{name}.joblib"
    joblib.dump(model, path, compress=3)
    return path.stat().st_size / 1e6, hashlib.sha256(path.read_bytes()).hexdigest()


def latency_ms(model, texts: pd.Series) -> float:
    sample = texts.iloc[:1]
    model.predict_proba(sample)
    times = []
    for _ in range(30):
        start = perf_counter()
        model.predict_proba(sample)
        times.append((perf_counter() - start) * 1000)
    return float(np.median(times))


def main() -> None:
    cfg = load_config()
    REPORTS.mkdir(exist_ok=True)
    MODELS.mkdir(exist_ok=True)
    df = load(data_path(cfg))
    s = cfg["split"]
    train, valid, test, split_log = split(df, s["valid_fraction"], s["test_fraction"], s["seed"],
                                          s["near_duplicate_cosine"])
    (REPORTS / "split.json").write_text(json.dumps(split_log, indent=2), encoding="utf-8")
    print("Partición:", split_log, flush=True)

    # ---------- selección del candidato en validación
    rows, fitted, seconds = [], {}, {}
    grid = [("dummy", {}), ("nb", {}), *[("logreg", {"C": c}) for c in C_GRID],
            ("logreg", {"C": 5.0, "balanced": True})]
    for kind, params in grid:
        name = kind if not params else f"logreg_C{params['C']:g}" + ("_bal" if params.get("balanced") else "")
        model, sec = fit_timed(build(kind, **params, seed=s["seed"]), train["text"], train["queue"])
        proba = model.predict_proba(valid["text"])
        pred = model.classes_[proba.argmax(1)]
        rows.append({"model": name, **metrics(valid["queue"], pred, proba, model.classes_), "train_seconds": sec})
        fitted[name], seconds[name] = model, sec
        print("valid", rows[-1], flush=True)
    val = pd.DataFrame(rows)
    val.to_csv(REPORTS / "validation_models.csv", index=False)
    cands = val[val.model.str.startswith("logreg") & ~val.model.str.endswith("_bal")]
    best = cands.loc[cands["top3_accuracy"].idxmax()]
    eligible = cands[cands["top3_accuracy"] >= best["top3_accuracy"] - 0.01]
    candidate = str(eligible.sort_values("train_seconds").iloc[0]["model"])
    finalists = {"B0 Clase mayoritaria": "dummy", "B1 Complement NB": "nb",
                 f"M1 Regresión logística ({candidate})": candidate,
                 "M2 Logística con pesos balanceados (alternativa)": "logreg_C5_bal"}

    # ---------- prioridad: mismo tipo de modelo, entrenado solo con texto
    prio_model, prio_sec = fit_timed(build("logreg", C=2.0, seed=s["seed"]), train["text"], train["priority"])

    # ---------- artefacto: umbrales en validación
    dss = RoutingDSS(fitted[candidate], prio_model, cfg["priority_rules"]).calibrate(
        valid, cfg["modes"]["strong_min_accuracy"], cfg["modes"]["top3_min_hit"], cfg["modes"]["min_support"])
    dss_valid = evaluate_dss(dss.recommend_batch(valid), valid)

    # ---------- evaluación única en prueba
    test_rows, preds, probas = [], {}, {}
    for label, name in finalists.items():
        model = fitted[name]
        proba = model.predict_proba(test["text"])
        pred = model.classes_[proba.argmax(1)]
        preds[name], probas[name] = pred, proba
        hit3 = topk_hits(proba, model.classes_, test["queue"], 3)
        mb, digest = size_mb(model, name)
        test_rows.append({"model": label, "key": name, **metrics(test["queue"], pred, proba, model.classes_),
                          "acc_ci_low": bootstrap_ci(pred == test["queue"].to_numpy())[0],
                          "acc_ci_high": bootstrap_ci(pred == test["queue"].to_numpy())[1],
                          "top3_ci_low": bootstrap_ci(hit3)[0], "top3_ci_high": bootstrap_ci(hit3)[1],
                          "train_seconds": seconds[name], "latency_ms": latency_ms(model, test["text"]),
                          "size_mb": mb, "sha256": digest})
    table = pd.DataFrame(test_rows)
    table["selected"] = table["key"] == candidate
    table.to_csv(REPORTS / "test_models.csv", index=False)
    joblib.dump(prio_model, MODELS / "priority.joblib", compress=3)
    joblib.dump(dss, MODELS / "dss.joblib", compress=3)

    recs = dss.recommend_batch(test)
    dss_test = evaluate_dss(recs, test)
    out = test[["ticket_id", "language", "language_detected", "queue", "priority"]].join(recs)
    out.to_csv(REPORTS / "test_recommendations.csv", index=False)

    # ---------- subgrupos: idioma, cola, prioridad
    m = fitted[candidate]
    proba = probas[candidate]
    test = test.assign(hit1=preds[candidate] == test["queue"].to_numpy(),
                       hit3=topk_hits(proba, m.classes_, test["queue"], 3), mode=recs["mode"].to_numpy())
    lang = test.groupby("language").agg(n=("hit1", "size"), accuracy=("hit1", "mean"), top3=("hit3", "mean"),
                                        triaje_manual=("mode", lambda x: (x == "triaje_manual").mean()),
                                        sugerencia=("mode", lambda x: (x == "sugerencia").mean()))
    lang.to_csv(REPORTS / "by_language.csv")
    # la etiqueta de idioma del dataset es ruidosa: también se audita por idioma detectado en el texto
    test["lang_group"] = test["language"] + "→" + test["language_detected"]
    lang_detected = test.groupby("lang_group").agg(
        n=("hit1", "size"), accuracy=("hit1", "mean"), top3=("hit3", "mean"),
        triaje_manual=("mode", lambda x: (x == "triaje_manual").mean()),
        sugerencia=("mode", lambda x: (x == "sugerencia").mean()))
    lang_detected.to_csv(REPORTS / "by_language_detected.csv")
    gap_ci = {"top3_en_minus_de": bootstrap_gap(test["hit3"], test["language"], "en", "de"),
              "acc_en_minus_de": bootstrap_gap(test["hit1"], test["language"], "en", "de"),
              "top3_detected_en_minus_de": bootstrap_gap(test["hit3"], test["language_detected"], "en", "de")}
    queue = test.groupby("queue").agg(n=("hit1", "size"), recall=("hit1", "mean"), top3=("hit3", "mean")).reindex(QUEUES)
    queue.to_csv(REPORTS / "by_queue.csv")
    prio = test.groupby("priority").agg(n=("hit1", "size"), accuracy=("hit1", "mean"), top3=("hit3", "mean"))
    prio.to_csv(REPORTS / "by_priority.csv")
    dss_lang = {g: evaluate_dss(recs[test.language.to_numpy() == g], test[test.language == g]) for g in ("en", "de")}
    confusions = top_confusions(test["queue"], preds[candidate])
    confusions.to_csv(REPORTS / "top_confusions.csv", index=False)

    # ---------- muestra de errores más confiados para análisis manual
    conf = proba.max(1)
    errors = test.assign(pred=preds[candidate], conf=conf)[~test["hit1"]].sort_values("conf", ascending=False)
    sample = errors.groupby("language").head(15).head(30)
    sample = sample.assign(excerpt=sample["text"].str.replace(r"\s+", " ", regex=True).str[:220],
                           top_terms=[", ".join(t for t, _ in explain(m, x, p, 5)) for x, p in zip(sample.text, sample.pred)])
    sample[["ticket_id", "language", "queue", "pred", "conf", "priority", "top_terms", "excerpt"]].to_csv(
        REPORTS / "error_sample_30.csv", index=False)

    # ---------- puertas de calidad (gobernanza)
    g = cfg["gates"]
    sel = table[table.selected].iloc[0]
    checks = {
        "top3_accuracy": bool(sel["top3_accuracy"] >= g["min_top3_accuracy"]),
        "language_gap_top3": bool(abs(lang.loc["en", "top3"] - lang.loc["de", "top3"]) <= g["max_language_gap_top3"]),
        "language_gap_top3_detected": bool(abs(test.loc[test.language_detected == "en", "hit3"].mean()
                                               - test.loc[test.language_detected == "de", "hit3"].mean())
                                           <= g["max_language_gap_top3"]),
        "high_to_low_rate": bool(dss_test["high_to_low_rate_dss"] <= g["max_high_to_low_rate"]),
        "latency": bool(sel["latency_ms"] <= g["max_latency_ms"]),
        "model_size": bool(sel["size_mb"] <= g["max_model_mb"]),
    }
    results = {
        "candidate": candidate, "selection_rule": "mayor top-3 en validación; empate < 1 punto → menor tiempo",
        "split": split_log, "thresholds": dss.calibration, "dss_valid": dss_valid, "dss_test": dss_test,
        "dss_test_by_language": dss_lang, "language_gap_ci95": gap_ci,
        "mcnemar_nb_vs_candidate": mcnemar(test["queue"], preds["nb"], preds[candidate]),
        "macro_recall_top3_by_queue": {k: float(v) for k, v in topk_queue_recall(test, probas, fitted).items()},
        "priority_model_train_seconds": prio_sec, "gates": checks,
        "gates_status": "PASA" if all(checks.values()) else "REVISAR",
        "environment": {"python": sys.version.split()[0], "platform": platform.platform(),
                        "processor": platform.processor() or platform.machine(),
                        "scikit_learn": sklearn.__version__, "pandas": pd.__version__, "numpy": np.__version__},
    }
    (REPORTS / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    figures(table, lang, queue, confusions, test, conf)
    print(table.drop(columns=["sha256", "key"]).round(3).to_string(index=False))
    print(json.dumps({k: results[k] for k in ("thresholds", "dss_test", "language_gap_ci95", "gates", "gates_status")},
                     indent=1, ensure_ascii=False))


def topk_queue_recall(test, probas, fitted) -> dict:
    """Recall top-3 medio por cola (macro) de cada modelo: mide si las colas pequeñas quedan desatendidas."""
    out = {}
    for name, proba in probas.items():
        hit = topk_hits(proba, fitted[name].classes_, test["queue"], 3)
        out[name] = pd.Series(hit).groupby(test["queue"].to_numpy()).mean().mean()
    return out


def figures(table, lang, queue, confusions, test, conf) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(table))
    for i, (col, low, high, label, color) in enumerate((("accuracy", "acc_ci_low", "acc_ci_high", "Top-1", "#3b6ea5"),
                                                        ("top3_accuracy", "top3_ci_low", "top3_ci_high", "Top-3", "#c8a24a"))):
        ax.bar(x + (i - 0.5) * 0.38, table[col], 0.38, label=label, color=color,
               yerr=[table[col] - table[low], table[high] - table[col]], capsize=3)
    ax.set_xticks(x, ["B0 Mayoritaria", "B1 Naive Bayes", "M1 Logística\n(seleccionado)", "M2 Logística\nbalanceada"], fontsize=9)
    ax.set(ylim=(0, 1), ylabel="Exactitud en prueba (IC 95 %)", title="Líneas base frente al candidato")
    ax.legend()
    fig.tight_layout()
    fig.savefig(REPORTS / "fig_models.png", dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    queue[["recall", "top3"]].iloc[::-1].plot.barh(ax=axes[0], color=["#3b6ea5", "#c8a24a"])
    axes[0].set(title="Acierto por cola real (prueba)", xlabel="Proporción", xlim=(0, 1), ylabel="")
    axes[0].legend(["Top-1", "Top-3"], loc="lower right")
    lang.loc[["en", "de"], ["accuracy", "top3", "sugerencia", "triaje_manual"]].T.plot.bar(ax=axes[1], rot=0, color=["#3b6ea5", "#c8a24a"])
    axes[1].set(title="Desempeño y modos de la app por idioma", ylim=(0, 1))
    axes[1].set_xticks(range(4), ["Top-1", "Top-3", "Modo sugerencia", "Triaje manual"])
    fig.tight_layout()
    fig.savefig(REPORTS / "fig_subgroups.png", dpi=160)
    plt.close(fig)

    order = np.argsort(-conf)
    hits = test["hit1"].to_numpy()[order]
    coverage = np.arange(1, len(order) + 1) / len(order)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(coverage, np.cumsum(hits) / np.arange(1, len(order) + 1), color="#3b6ea5")
    ax.set(xlabel="Proporción de tickets con sugerencia (ordenados por confianza)", ylabel="Exactitud top-1 acumulada",
           title="Curva de abstención: menos cobertura, más acierto", ylim=(0.3, 1))
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(REPORTS / "fig_abstention.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
