"""Auditoría: contrato, nulos, duplicados, balance, idioma, longitud y poder predictivo de los
campos posteriores al triaje (para justificar su exclusión).

Uso:  uv run python scripts/audit_data.py
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

from tickets_dss.config import QUEUES, REPORTS, data_path, load_config
from tickets_dss.data import load


def post_triage_probe(df: pd.DataFrame, seed: int) -> dict:
    """¿Cuánto predicen la cola los campos que el agente llena DESPUÉS del triaje?"""
    tags = df[[f"tag_{i}" for i in range(1, 9)]].fillna("").agg(" ".join, axis=1) + " " + df["type"]
    out = {}
    for name, x in (("tags_y_tipo", tags), ("respuesta_agente", df["answer"].fillna(""))):
        xtr, xte, ytr, yte = train_test_split(x, df["queue"], test_size=0.2, stratify=df["queue"], random_state=seed)
        model = make_pipeline(TfidfVectorizer(min_df=3, sublinear_tf=True), LogisticRegression(max_iter=2000))
        out[name] = float(accuracy_score(yte, model.fit(xtr, ytr).predict(xte)))
    return out


def main() -> None:
    cfg = load_config()
    raw = pd.read_csv(data_path(cfg))
    df = load(data_path(cfg))
    words = df["text"].str.split().str.len()
    summary = {
        "rows_raw": len(raw), "rows_after_cleaning": len(df), "columns": list(raw.columns),
        "nulls": {k: int(v) for k, v in raw.isna().sum().items() if v},
        "removed_empty_or_duplicate_text": len(raw) - len(df),
        "queue": df["queue"].value_counts().to_dict(), "priority": df["priority"].value_counts().to_dict(),
        "language": df["language"].value_counts().to_dict(), "type": df["type"].value_counts().to_dict(),
        "median_words_by_language": words.groupby(df["language"]).median().to_dict(),
        "smallest_queue_share": float(df["queue"].value_counts(normalize=True).min()),
        "post_triage_fields_accuracy": post_triage_probe(df, cfg["split"]["seed"]),
        "majority_class_accuracy": float(df["queue"].value_counts(normalize=True).max()),
        "language_label_vs_detected": {f"{a}->{b}": int(n) for (a, b), n in
                                       df.groupby(["language", "language_detected"]).size().items()},
    }
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "audit_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    cross = pd.crosstab(df["queue"], df["language"]).reindex(QUEUES)
    cross.to_csv(REPORTS / "audit_queue_by_language.csv")
    pd.crosstab(df["queue"], df["priority"], normalize="index").reindex(QUEUES).round(3).to_csv(
        REPORTS / "audit_priority_by_queue.csv")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    cross[["en", "de"]].iloc[::-1].plot.barh(stacked=True, ax=axes[0], color=["#3b6ea5", "#c8a24a"])
    axes[0].set(title="Tickets por cola e idioma", xlabel="Tickets", ylabel="")
    pd.crosstab(df["priority"], df["language"]).reindex(["low", "medium", "high"])[["en", "de"]].plot.bar(
        ax=axes[1], rot=0, color=["#3b6ea5", "#c8a24a"])
    axes[1].set(title="Prioridad por idioma", xlabel="", ylabel="Tickets")
    for lang, color in (("en", "#3b6ea5"), ("de", "#c8a24a")):
        axes[2].hist(words[df["language"] == lang].clip(upper=300), bins=40, alpha=0.6, label=lang, color=color)
    axes[2].set(title="Longitud del ticket (palabras)", xlabel="Palabras", ylabel="Tickets")
    axes[2].legend()
    fig.tight_layout()
    fig.savefig(REPORTS / "fig_audit.png", dpi=160)
    plt.close(fig)
    print(json.dumps({k: summary[k] for k in ("rows_raw", "rows_after_cleaning", "language",
                                              "post_triage_fields_accuracy", "majority_class_accuracy")}, indent=1))


if __name__ == "__main__":
    main()
