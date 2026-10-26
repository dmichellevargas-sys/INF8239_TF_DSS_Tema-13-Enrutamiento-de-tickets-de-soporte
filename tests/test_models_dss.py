import numpy as np
import pandas as pd
import pytest

from tickets_dss.data import ticket_text
from tickets_dss.dss import RoutingDSS, apply_rules, choose_threshold, evaluate_dss
from tickets_dss.evaluation import bootstrap_ci, mcnemar, topk_hits
from tickets_dss.models import build, explain

RULES = [{"name": "caida", "level": "high", "patterns": ["outage", "ausfall"]}]


@pytest.fixture
def fitted(tickets):
    df = tickets.assign(text=ticket_text(tickets))
    queue = build("logreg", C=5).fit(df.text, df.queue)
    prio = build("logreg", C=1).fit(df.text, df.priority)
    return df, queue, prio


@pytest.mark.parametrize("kind", ["dummy", "nb", "logreg"])
def test_each_model_returns_one_label_and_valid_probabilities(tickets, kind):
    df = tickets.assign(text=ticket_text(tickets))
    model = build(kind).fit(df.text, df.queue)
    proba = model.predict_proba(["invoice charged twice"])
    assert len(model.predict(["invoice charged twice"])) == 1
    np.testing.assert_allclose(proba.sum(axis=1), 1.0)


def test_candidate_learns_signal_and_explanation_uses_ticket_words(fitted):
    _, queue, _ = fitted
    text = "My invoice was charged twice, I need a refund"
    assert queue.predict([text])[0] == "Billing and Payments"
    terms = [t for t, _ in explain(queue, text, "Billing and Payments")]
    assert terms and all(any(w in text.lower() for w in t.split()) for t in terms)


def test_choose_threshold_meets_target_or_disables_mode():
    conf = np.linspace(1, 0, 100)
    correct = np.r_[np.ones(50), np.zeros(50)]
    t = choose_threshold(conf, correct, target=0.9, min_support=10)
    assert t is not None and correct[conf >= t].mean() >= 0.9
    assert choose_threshold(conf, np.zeros(100), target=0.5, min_support=10) is None


def test_rules_only_raise_priority():
    assert apply_rules("Total outage of the portal", "low", RULES) == ("high", ["caida"])
    assert apply_rules("Kompletter Ausfall", "medium", RULES)[0] == "high"
    assert apply_rules("Question about invoices", "high", RULES) == ("high", [])


def test_dss_modes_and_options_shown(fitted):
    _df, queue, prio = fitted
    dss = RoutingDSS(queue, prio, RULES, t_strong=0.99, t_top3=0.0)
    rec = dss.recommend("invoice charged twice refund")
    assert rec["mode"] in {"top3", "sugerencia"}
    assert len(rec["options_shown"]) == (3 if rec["mode"] == "top3" else 1)
    manual = RoutingDSS(queue, prio, RULES, t_strong=None, t_top3=None).recommend("hola")
    assert manual["mode"] == "triaje_manual" and manual["options_shown"] == []


def test_dss_evaluation_counts_critical_priority_errors(fitted):
    df, queue, prio = fitted
    dss = RoutingDSS(queue, prio, RULES, t_strong=0.5, t_top3=0.0)
    recs = dss.recommend_batch(df)
    recs.loc[:, "priority_suggested"] = "low"
    result = evaluate_dss(recs, df)
    assert result["high_to_low_rate_dss"] == pytest.approx(1.0)
    assert abs(sum(result[f"share_{m}"] for m in ("sugerencia", "top3", "triaje_manual")) - 1) < 1e-9


def test_metric_helpers():
    proba = np.array([[0.6, 0.3, 0.1], [0.1, 0.2, 0.7]])
    assert topk_hits(proba, ["a", "b", "c"], ["b", "a"], k=2).tolist() == [True, False]
    low, high = bootstrap_ci([1, 0, 1, 1, 0, 1, 1, 1], n_boot=500)
    assert low <= 0.75 <= high
    assert mcnemar(["a", "b"], ["a", "b"], ["a", "b"])["p_value"] == 1.0


def test_dss_never_receives_post_triage_columns(fitted):
    df, queue, prio = fitted
    dss = RoutingDSS(queue, prio, RULES, t_strong=0.5, t_top3=0.0)
    only_text = pd.DataFrame({"text": df.text})
    pd.testing.assert_frame_equal(dss.recommend_batch(only_text), dss.recommend_batch(df).set_index(only_text.index))
