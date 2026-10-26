"""Artefacto práctico (Modalidad A): la persona de triaje ve la propuesta del modelo y decide."""
import json
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "models/dss.joblib"
DECISIONS = ROOT / "reports/decision_log.csv"
QUEUES = ["Technical Support", "Product Support", "Customer Service", "IT Support", "Billing and Payments",
          "Returns and Exchanges", "Service Outages and Maintenance", "Sales and Pre-Sales", "Human Resources",
          "General Inquiry"]

st.set_page_config(page_title="Triaje asistido de tickets", layout="wide")
st.title("Triaje asistido de tickets · demostración académica")
st.warning("Datos públicos (Hugging Face, CC BY-NC 4.0), probablemente sintéticos. El sistema sugiere; "
           "la persona coordinadora decide. No ingrese tickets reales ni datos personales.")
if not MODEL.exists():
    st.error("Entrene primero: uv run python scripts/run_all.py")
    st.stop()
dss = joblib.load(MODEL)
results = json.loads((ROOT / "reports/results.json").read_text(encoding="utf-8"))

with st.sidebar:
    st.subheader("Cómo decide el sistema")
    t = dss.calibration
    st.write(f"**Sugerencia** (una cola preseleccionada) si la confianza ≥ {t['t_strong'] or 0:.2f}.")
    st.write(f"**Top-3** si la confianza acumulada de 3 colas ≥ {t['t_top3'] or 0:.2f}.")
    st.write("**Triaje manual** en los demás casos.")
    st.write("Las reglas de prioridad solo pueden **subir** la prioridad sugerida.")
    st.caption(f"Puertas de calidad: {results['gates_status']}")

subject = st.text_input("Asunto", "Payment portal not working")
body = st.text_area("Cuerpo del ticket", "Since this morning our invoices cannot be paid, the billing portal shows an error.", height=150)
if st.button("Obtener propuesta"):
    rec = dss.recommend(f"{subject} \n {body}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Modo", rec["mode"].replace("_", " "))
    c2.metric("Prioridad sugerida", rec["priority_suggested"])
    c3.metric("Confianza top-1", f"{rec['conf_1']:.2f}")
    if rec["options_shown"]:
        st.subheader("Colas propuestas")
        st.table(pd.DataFrame({"cola": [rec["queue_1"], rec["queue_2"], rec["queue_3"]][:len(rec["options_shown"])]}))
    else:
        st.info("Confianza insuficiente: el ticket va a triaje manual sin sugerencia (abstención).")
    if rec["rules_fired"]:
        st.write("Reglas activadas:", rec["rules_fired"])
    if rec["explanation"]:
        st.write("Términos que más pesaron:", ", ".join(term for term, _ in rec["explanation"]))
    st.session_state["rec"] = rec

if "rec" in st.session_state:
    rec = st.session_state["rec"]
    default = QUEUES.index(rec["queue_1"]) if rec["options_shown"] else 0
    final = st.selectbox("Decisión de la persona coordinadora", QUEUES, index=default)
    reason = st.text_input("Motivo (obligatorio si cambia la propuesta)")
    if st.button("Registrar decisión"):
        if final != rec["queue_1"] and not reason.strip():
            st.error("Indique el motivo del cambio.")
        else:
            row = pd.DataFrame([{"modo": rec["mode"], "propuesta": rec["queue_1"], "decision": final,
                                 "cambio": final != rec["queue_1"], "motivo": reason,
                                 "prioridad_sugerida": rec["priority_suggested"]}])
            row.to_csv(DECISIONS, mode="a", header=not DECISIONS.exists(), index=False)
            st.success("Decisión registrada (sin guardar el texto del ticket).")
