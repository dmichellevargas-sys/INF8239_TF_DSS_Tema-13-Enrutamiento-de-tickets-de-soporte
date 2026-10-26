import numpy as np
import pandas as pd
import pytest

VOCAB = {
    "Billing and Payments": ["invoice charged twice", "refund payment card", "billing statement error"],
    "Technical Support": ["software crash error", "application bug freezes", "driver update fails"],
    "Human Resources": ["vacation leave request", "payroll employee contract", "onboarding new employee"],
}


@pytest.fixture
def tickets() -> pd.DataFrame:
    """Tickets sintéticos mínimos (no son datos reales): 3 colas, 2 idiomas, 3 prioridades."""
    rng = np.random.default_rng(0)
    rows = []
    for queue, phrases in VOCAB.items():
        for i in range(40):
            phrase = phrases[i % len(phrases)]
            rows.append({"subject": f"{phrase} {i}", "body": f"Hello, {phrase} number {rng.integers(1000)} please help",
                         "answer": "Thanks", "type": "Request", "queue": queue,
                         "priority": ["low", "medium", "high"][i % 3], "language": ["en", "de"][i % 2],
                         **{f"tag_{k}": "Tag" for k in range(1, 9)}})
    return pd.DataFrame(rows)
