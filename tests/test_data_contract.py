import pandas as pd
import pytest

from tickets_dss.config import POST_TRIAGE_COLUMNS, load_config
from tickets_dss.data import download, load, split, ticket_text, validate


def test_contract_accepts_valid_and_rejects_missing_columns(tickets):
    validate(tickets)
    with pytest.raises(ValueError, match="Faltan columnas"):
        validate(tickets.drop(columns="body"))


def test_contract_rejects_undocumented_queue(tickets):
    bad = tickets.copy()
    bad.loc[0, "queue"] = "Cola inventada"
    with pytest.raises(ValueError, match="no documentados"):
        validate(bad)


def test_text_uses_only_fields_available_at_intake(tickets):
    leaky = tickets.assign(answer="SECRET_ANSWER", type="SECRET_TYPE", tag_1="SECRET_TAG")
    text = ticket_text(leaky)
    assert not text.str.contains("SECRET").any()
    assert {"answer", "type", "tag_1"} <= set(POST_TRIAGE_COLUMNS)


def test_load_removes_duplicate_and_empty_texts(tickets, tmp_path):
    dup = pd.concat([tickets, tickets.iloc[[0]], tickets.iloc[[1]].assign(subject="", body="")])
    path = tmp_path / "t.csv"
    dup.to_csv(path, index=False)
    df = load(path)
    assert len(df) == len(tickets)  # salen la copia duplicada y la fila vacía
    assert df["text"].str.lower().is_unique


def test_split_is_disjoint_and_removes_near_duplicates(tickets):
    df = tickets.assign(text=ticket_text(tickets))
    train, valid, test, log = split(df, 0.15, 0.15, seed=42, near_dup=0.90)
    assert set(train.text).isdisjoint(test.text) and set(train.text).isdisjoint(valid.text)
    assert log["train"] + log["valid"] + log["test"] + log["removed_near_dup_valid"] + log["removed_near_dup_test"] == len(df)


def test_download_rejects_file_with_unexpected_hash(tmp_path):
    target = tmp_path / "data.csv"
    target.write_text("otra versión")
    with pytest.raises(ValueError, match="SHA-256"):
        download("https://example.invalid/no-se-usa", target, "0" * 64)


def test_only_public_dataset_is_configured():
    cfg = load_config()
    assert cfg["data"]["url"].startswith("https://huggingface.co/datasets/Tobi-Bueck/customer-support-tickets/")
    assert any("organización real" in use for use in cfg["prohibited_uses"])


def test_language_detector_flags_english_text_labelled_german():
    from tickets_dss.data import detect_language
    text = pd.Series(["Ich bitte um Hilfe, die Rechnung ist nicht korrekt und wir warten",
                      "I am writing because the invoice is wrong and we need help with this"])
    assert detect_language(text).tolist() == ["de", "en"]
