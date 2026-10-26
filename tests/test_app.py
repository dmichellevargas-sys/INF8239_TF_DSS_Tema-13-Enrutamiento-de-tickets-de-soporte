from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


@pytest.mark.skipif(not (ROOT / "models/dss.joblib").exists(), reason="requiere ejecutar scripts/run_all.py")
def test_app_starts_warns_and_returns_a_proposal():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(ROOT / "app/streamlit_app.py"), default_timeout=60).run()
    assert not at.exception
    assert any("no ingrese tickets reales" in w.value.lower() for w in at.warning)
    at.button[0].click().run()
    assert not at.exception
    assert any(m.label == "Modo" for m in at.metric)
