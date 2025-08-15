# apps/dash/app.py
# Inevitability Dash — surfaces 𝓔/𝒢/K/RRI, rails, harms/externalities, Throne-Fiber/Stand.

import os, json, time, math
from typing import Dict, Any, List
import streamlit as st

# Wire core
from core.memory.lattice import MemoryLattice
from core.memory.anamnesis_engine import AnamnesisEngine
from core.ethics.harms_ledger import HarmsLedger
from core.ethics.externality_pricer import ExternalityPricer, Assessment
from core.proofs.proof_carrying_advice import ProofCarryingAdvice, AdviceDraft
from core.metrics.trackers import Trackers

QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
LEDGER_SQLITE_PATH = os.environ.get("LEDGER_SQLITE_PATH", "data/ledger.db")
COVERAGE_TARGET = float(os.environ.get("COVERAGE_TARGET", "0.95"))

# Instantiate
lat = MemoryLattice(qdrant_url=QDRANT_URL, sqlite_path=LEDGER_SQLITE_PATH)
ae  = AnamnesisEngine(lat)
hl  = HarmsLedger()
ep  = ExternalityPricer(coverage_threshold=COVERAGE_TARGET)
pca = ProofCarryingAdvice(lat, ae, hl, ep, coverage_threshold=COVERAGE_TARGET)
trk = Trackers(hl)

st.set_page_config(page_title="INEVITABILITY — Crown Metrics", layout="wide")
st.title("🜏 Inevitability — Crown Metrics")

with st.sidebar:
    st.subheader("Plan Spec")
    default_plan = {
        "id": "plan:demo",
        "data_kind": "personal",
        "deployment_scope": "org",
        "automation_level": "agentic",
        "environmental": "med",
        "budget_lines": {"privacy": 0.9, "safety": 0.8, "technical_debt": 0.6}
    }
    plan_json = st.text_area("Plan JSON", json.dumps(default_plan, indent=2), height=220)
    params_json = st.text_area("Params (rails hints)", json.dumps({"will":"Expansion", "no_image": True}, indent=2), height=150)
    consent_json = st.text_area("Consent Context", json.dumps({"valid": True, "scope":"org"}, indent=2), height=120)
    run_btn = st.button("Evaluate Plan")

    st.markdown("---")
    st.subheader("Lessons")
    if st.button("Record Lesson Atom (L10: no coercion)"):
        ae.record_lesson("L10", {"principle":"no coercion","repair":"invite"}, tags=["ethic"])
        st.success("Lesson recorded.")
    st.caption("RRI improves when decisions cite lesson atoms.")

def safe_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        return {}

def build_and_track(plan: Dict[str, Any], params: Dict[str, Any], consent: Dict[str, Any]):
    draft = AdviceDraft(
        id=str(plan.get("id","plan:unnamed")),
        query="dash:evaluate",
        plan=plan,
        params=params,
        context={"consent": consent}
    )
    answer = "Proceed with reversible micro-moves; uphold consent tickets; monitor externalities."
    awp = pca.build(draft, answer)
    assess = ep.assess(plan)
    bundle = trk.assemble(awp, assess)
    return awp, assess, bundle

# Auto-run once for initial view
if not run_btn and "first_run_done" not in st.session_state:
    st.session_state["first_run_done"] = True
    awp, assess, bundle = build_and_track(default_plan, {"will":"Expansion","no_image": True}, {"valid": True, "scope":"org"})
else:
    awp, assess, bundle = build_and_track(safe_json(plan_json), safe_json(params_json), safe_json(consent_json))

# Layout
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("𝓔 Energy", f"{bundle.E.E:.2f}")
col2.metric("𝒢 Grace", f"{bundle.G.G:.2f}")
col3.metric("K Kenosis", f"{bundle.K.K:.2f}")
col4.metric("RRI", f"{bundle.RRI:.2f}")
col5.metric("Throne-Fiber", "ON" if bundle.throne_fiber else "—")

st.markdown("---")

# Rails + Risk
c1, c2 = st.columns([2,1])
with c1:
    st.subheader("Rails & Proofs")
    rails = {p.name: p.ok for p in awp.proofs}
    st.json(rails)
    st.caption(f"Risk blend: {awp.risk:.2f} (externalities + harms penalties)")
with c2:
    st.subheader("Stand?")
    st.metric("Stand Recommended", "YES" if bundle.stand_recommended else "NO")

# Externalities / Harms
c3, c4 = st.columns(2)
with c3:
    st.subheader("Externality Assessment")
    st.json({
        "coverage": round(assess.coverage,3),
        "rollback_ready": assess.rollback_ready,
        "externals": [e.category for e in assess.externals]
    })
with c4:
    st.subheader("Harms Snapshot (penalties folded into metrics)")
    hidx = hl.compute_index()
    st.json({
        "H": round(hidx.H,3),
        "consent_debt": round(hidx.consent_debt,3),
        "dignity_debt": round(hidx.dignity_debt,3),
        "reversibility": round(hidx.reversibility_score,3)
    })

st.markdown("---")
st.subheader("Decision (Preview)")
st.code(awp.answer)

# Commit decision section
if st.button("Commit Decision (cite L10 lesson if present)"):
    # Try to find any L10 lesson atom
    # (In a full app, we'd query via lattice/hypergraph; here we just allow cite-lessons=[] for simplicity)
    did = ae.register_decision({
        "id": f"advice:{awp.id}", "risk": awp.risk,
        "proofs": [vars(p) for p in awp.proofs],
        "assessment": awp.assessment, "ts": time.time(),
        "note":"Committed from Dash"
    })
    st.success(f"Decision logged with ledger id {did}.")
    st.caption("Subsequent RRI may improve when lessons are cited via PCA pathway.")
