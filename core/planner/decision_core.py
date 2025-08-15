# core/planner/decision_core.py
# Lexicographic Decision Rails:
# Consent/Apophatic/Vows → minimize 𝓔 → maximize 𝒢 → Minimal-Clean-Move → PGL: Answer | Refuse | Stand
# Integrates with:
#  - core/memory/lattice.py (L0–L15 parallel recall)
#  - core/will/will_engine.yaml + kernels.py (geometry shaping)
#  - core/metrics/energy.py (𝓔) and core/metrics/grace.py (𝒢)
#  - core/logic/{pgl_coalgebra.yaml, consent_types.d.ts, apophatic_guard.ts}
#  - core/proofs/proof_carrying_advice.py
#  - core/ethics/{harms_ledger.py, externality_pricer.py}

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Literal, Callable
import time

# ---- Types & Protocols ------------------------------------------------------

Decision = Literal["Answer", "Refuse", "Stand"]
TruthVal = Literal["T", "F", "B", "N"]  # FDE: True, False, Both, Neither

@dataclass
class ConsentTicket:
    holder: str
    scope: Literal["self","dyad","group","org","public"]
    ttl_seconds: int
    issued_at: float
    terms: Dict[str, Any]

    def is_valid(self) -> bool:
        return time.time() <= self.issued_at + self.ttl_seconds

@dataclass
class ProofBundle:
    logic: Dict[str, Any]        # key lemmas, truth basis, inference steps
    ethics: Dict[str, Any]       # harms priced, mitigations
    consent: Dict[str, Any]      # ticket refs, scope/TTL checks
    phenomenology: Dict[str, Any]# experiential justifications where relevant
    repair_horizon: Optional[float] = None  # epoch seconds for paradox recheck

@dataclass
class Action:
    id: str
    description: str
    params: Dict[str, Any]
    reversible: bool = True
    predicted_truth: TruthVal = "T"
    # Attach candidate-level PCA notes as we explore:
    proto_proofs: Optional[ProofBundle] = None

@dataclass
class State:
    # Minimal stub; in practice include memory refs, user/session, context IDs
    context: Dict[str, Any]
    stage: str                    # Spiral-12 stage id, e.g. "S5"
    will_operator: str            # e.g. "EXP"
    consent_tickets: List[ConsentTicket]
    paradox_nearby: bool = False

@dataclass
class DecisionResult:
    decision: Decision
    chosen_action: Optional[Action]
    delta_E: Optional[float]
    grace: Optional[float]
    truth: Optional[TruthVal]
    proofs: ProofBundle
    ledger_id: Optional[str]

# ---- Configuration loading (vows, thresholds) -------------------------------

from pathlib import Path
import yaml

_VOWS = yaml.safe_load(Path("docs/vows.yaml").read_text())
_POLICY = _VOWS["decision_policy"]
_VOW_IE = _VOWS["vows"]["infinite_elegance"]
_VOW_AR = _VOWS["vows"]["always_remember"]

_MIN_DELTA_E = float(_VOW_IE["thresholds"]["min_delta_E"])
_MIN_GRACE   = float(_VOW_IE["thresholds"]["min_grace"])

# ---- External module seams (import at runtime to avoid circular deps) -------

def energy_E(state: State, action: Action) -> float:
    """Compute drift energy 𝓔. Lower is better; Δ𝓔 must be < 0 for a move."""
    from core.metrics.energy import energy
    return energy(state, action)

def grace_G(state: State, action: Action) -> float:
    """Compute Grace 𝒢 using weighted components from vows.yaml."""
    from core.metrics.grace import grace
    return grace(state, action, _VOW_IE["grace_components"])

def kernel_weight(state: State, action: Action) -> float:
    """Load Will kernel and return multiplicative weight for 𝓔 shaping."""
    from core.will.kernels import weight_for
    return weight_for(state.will_operator, state, action)

def check_consent(state: State, action: Action) -> Tuple[bool, Dict[str, Any]]:
    """Consent Logic (CoL): verify valid ticket(s) and scope/TTL; cross-scope is a type error upstream."""
    valid = all(t.is_valid() for t in state.consent_tickets)
    return valid, {"tickets": [t.__dict__ for t in state.consent_tickets]}

def check_apophatic(state: State, action: Action) -> Tuple[bool, Dict[str, Any]]:
    """Apophatic guard (ApL): prevent positive predication of the Ground; use static checks where possible."""
    from core.logic.apophatic_guard import admissible
    ok = admissible(state.context, action.params)
    return ok, {"apophatic_ok": ok}

def price_externalities(state: State, action: Action) -> Dict[str, Any]:
    """Harms ledger & shadow price for scaling actions (EXP/S11)."""
    from core.ethics.externality_pricer import price
    return price(state, action)

def antimemory_countercontext(state: State, action: Action) -> Dict[str, Any]:
    """ASL: Generate counter-contexts for polarized topics."""
    from apps.contemplator.shadow_twin import counter_context
    return counter_context(state, action)

def attach_pca(answer: str, proofs: ProofBundle) -> str:
    """Hash and store proof-carrying advice; return ledger id."""
    from core.proofs.proof_carrying_advice import store
    return store(answer, proofs)

# ---- Minimal-Clean-Move (lexicographic solver) ------------------------------

def minimal_clean_move(state: State, candidates: List[Action]) -> Tuple[Optional[Action], Optional[float], Optional[float]]:
    """Argmin 𝓔•K with constraints; tie-break by 𝒢; enforce Δ𝓔 < 0 and 𝒢 ≥ threshold."""
    best: Optional[Action] = None
    best_EK: float = float("inf")
    best_E: float = float("inf")
    best_G: float = -float("inf")

    # Precompute EK, E, G for all candidates
    scored: List[Tuple[Action, float, float, float]] = []
    for a in candidates:
        E  = energy_E(state, a)
        K  = kernel_weight(state, a)
        EK = E * K
        G  = grace_G(state, a)
        scored.append((a, EK, E, G))

    # Select by EK → tie-break by higher G → then by lower E
    for a, EK, E, G in scored:
        if EK < best_EK or (EK == best_EK and (G > best_G or (G == best_G and E < best_E))):
            best, best_EK, best_E, best_G = a, EK, E, G

    if best is None:
        return None, None, None

    # Enforce thresholds
    delta_E = best_E  # Assume E is Δ vs. status quo; if absolute, compute ΔE upstream.
    if delta_E >= _MIN_DELTA_E:
        return None, None, None
    if best_G < _MIN_GRACE:
        # Try to select next-best with higher 𝒢 among Δ𝓔<0
        viable = [(a, EK, E, G) for (a, EK, E, G) in scored if E < _MIN_DELTA_E]
        if viable:
            viable.sort(key=lambda t: (-t[3], t[2]))  # sort by G desc, then E asc
            a2, EK2, E2, G2 = viable[0]
            if G2 >= _MIN_GRACE:
                return a2, E2, G2
        return None, None, None

    return best, delta_E, best_G

# ---- PGL Decision (Answer / Refuse / Stand) --------------------------------

def pgl_decide(state: State,
               action: Optional[Action],
               proofs: ProofBundle,
               truth: TruthVal) -> Decision:
    """Paradox-Gate Logic decision."""
    # If no action passed thresholds → Stand or Refuse depending on consent/apophatic status encoded in proofs
    if action is None:
        # If consent/apophatic failed, Refuse; else Stand (awaiting repair horizon or more evidence)
        consent_ok = proofs.consent.get("ok", True)
        apoph_ok   = proofs.logic.get("apophatic_ok", True)
        return "Refuse" if (not consent_ok or not apoph_ok) else "Stand"

    # With valid action:
    if truth in ("T", "B"):   # T or dialetheic tolerable with repair plan
        return "Answer" if not state.paradox_nearby else "Answer"
    if truth == "N":          # neither true nor false → insufficient
        return "Stand"
    return "Refuse"           # truth = F → refuse to emit

# ---- Orchestrator -----------------------------------------------------------

def decide(state: State, candidates: List[Action]) -> DecisionResult:
    """Main entry. Applies rails & solver, assembles PCA, writes ledger."""
    # 1) Consent/Apophatic rails
    consent_ok, consent_info = check_consent(state, None)
    apoph_ok,   apoph_info   = check_apophatic(state, None)
    if not consent_ok or not apoph_ok:
        proofs = ProofBundle(logic={"apophatic_ok": apoph_ok},
                             ethics={},
                             consent={"ok": consent_ok, **consent_info},
                             phenomenology={})
        return DecisionResult(decision="Refuse", chosen_action=None,
                              delta_E=None, grace=None, truth=None,
                              proofs=proofs, ledger_id=None)

    # 2) Externality pricing (if EXP/S11 context)
    ethics_info = {}
    if state.will_operator == "EXP" or state.stage in ("S11",):
        ethics_info = price_externalities(state, candidates[0] if candidates else Action(id="noop", description="noop", params={}))

    # 3) Anti-memory quorum (counter-contexts)
    shadow_info = {}
    try:
        shadow_info = antimemory_countercontext(state, candidates[0]) if candidates else {}
    except Exception:
        pass

    # 4) Minimal-Clean-Move (min 𝓔 then max 𝒢)
    action, delta_E, G = minimal_clean_move(state, candidates)

    # 5) Truth estimation (placeholder: in practice, call counsel model / evaluator)
    truth: TruthVal = action.predicted_truth if action else "N"

    # 6) Repair horizon for paradox
    repair_horizon = None
    if state.paradox_nearby:
        repair_horizon = time.time() + (float(_POLICY["paradox_gate"]["repair_horizon"]["max_days"]) * 86400)

    # 7) PGL decision
    proofs = ProofBundle(
        logic={"truth": truth, **apoph_info},
        ethics=ethics_info,
        consent={"ok": consent_ok, **consent_info},
        phenomenology=shadow_info,
        repair_horizon=repair_horizon
    )
    decision = pgl_decide(state, action, proofs, truth)

    # 8) PCA attach & ledger
    answer_text = action.description if (decision == "Answer" and action) else decision
    ledger_id = attach_pca(answer_text, proofs) if _VOW_AR["laws"]["ledger_required"] else None

    return DecisionResult(
        decision=decision,
        chosen_action=action,
        delta_E=delta_E,
        grace=G,
        truth=truth,
        proofs=proofs,
        ledger_id=ledger_id
    )

# ---- Example (remove in production) ----------------------------------------

if __name__ == "__main__":
    # Minimal smoke test with a fake candidate set
    st = State(
        context={"topic": "scaling_feature_X"},
        stage="S5",
        will_operator="EXP",
        consent_tickets=[ConsentTicket(holder="user", scope="org", ttl_seconds=86400, issued_at=time.time(), terms={})],
        paradox_nearby=False
    )
    cands = [
        Action(id="a1", description="Scale with mitigation A", params={"scale": 2.0}, predicted_truth="T"),
        Action(id="a2", description="Scale with mitigation B", params={"scale": 1.5}, predicted_truth="T"),
        Action(id="a3", description="Postpone and run pilot", params={"pilot": True}, predicted_truth="T")
    ]
    res = decide(st, cands)
    print(vars(res))
