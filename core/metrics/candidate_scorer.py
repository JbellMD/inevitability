"""
Candidate Scorer
---------------
Provides per-candidate scoring functions for the decision core, bridging the gap between
the class-based metrics (Energy, Grace) and the function-based API expected by decision_core.py.

This module defines the energy(state, action) and grace(state, action, weights) functions
that compute Δ𝓔 (delta energy, negative is good) and 𝒢 (grace score, 0..1).
"""

from typing import Any, Dict, Optional, List
from dataclasses import asdict

from core.ethics.harms_ledger import HarmsLedger, HarmIndex
from core.ethics.externality_pricer import ExternalityPricer, Externality, Assessment
from core.proofs.proof_carrying_advice import AdviceDraft, AdviceWithProof, Proof, blake

# Default weights for grace components
DEFAULT_GRACE_WEIGHTS = {
    "coverage": 0.55,
    "coherence": 0.25,
    "rollback": 0.10,
    "dignity": 0.25,
}

class State:
    """Minimally compatible State object for testing."""
    def __init__(self, context=None, params=None):
        self.context = context or {}
        self.params = params or {}

class Action:
    """Minimally compatible Action object for testing."""
    def __init__(self, id="", description="", params=None):
        self.id = id
        self.description = description
        self.params = params or {}
        self.predicted_truth = "U"  # Unknown default

def energy(state: Any, action: Any) -> float:
    """
    Compute Energy (𝓔) for a candidate action.
    Returns Δ𝓔 (delta energy, negative is better) to align with vows.
    
    Args:
        state: Decision state with context
        action: Candidate action with params
        
    Returns:
        Δ𝓔: Change in energy (negative is better)
    """
    # Create a minimal AdviceDraft from action
    draft = AdviceDraft(
        id=f"candidate:{action.id}",
        query=state.context.get("query", ""),
        plan=action.params.get("plan", {}),
        params=action.params,
        context=state.context
    )
    
    # Quick consent check (minimal)
    consent_ok = _consent_check(state, action)
    
    # Quick apophatic check
    apoph_ok = _apophatic_check(state, action)
    
    # Externality check
    ext_ok = True
    ext_coverage = action.params.get("coverage", 0.0)
    if ext_coverage < 0.5:
        ext_ok = False
    
    # Create proofs (simplified for candidate evaluation)
    proofs = [
        Proof(name="consent", ok=consent_ok, 
              details={"tickets": state.context.get("consent_tickets", [])}, token=blake({"consent": consent_ok})),
        Proof(name="apophatic", ok=apoph_ok, 
              details={"params": action.params}, token=blake({"apophatic": apoph_ok})),
        Proof(name="externalities", ok=ext_ok, 
              details={"coverage": ext_coverage}, token=blake({"externalities": ext_ok}))
    ]
    
    # Base cost (higher for failing consent/apophatic rails)
    base_cost = 0.1
    if not consent_ok:
        base_cost += 0.35
    if not apoph_ok:
        base_cost += 0.25
    if not ext_ok:
        base_cost += 0.20
        
    # Compute risk from externalities
    risk = action.params.get("risk", 0.1)
    if "externality_priced" in action.params and action.params["externality_priced"]:
        risk = min(0.8, action.params.get("risk", 0.1) + 
                (1.0 - action.params.get("coverage", 0.0)) * 0.2)
    
    # Harm pressure (simplified estimate)
    harms_penalty = action.params.get("energy_penalty", 0.0)
    
    # Total delta energy (negative is better)
    delta_e = base_cost + (0.3 * risk) + (0.4 * harms_penalty)
    
    # Make it negative to follow vows semantics (Δ𝓔 < 0 to move)
    return -delta_e

def grace(state: Any, action: Any, weights: Optional[Dict[str, float]] = None) -> float:
    """
    Compute Grace (𝒢) for a candidate action.
    Returns a score between 0 and 1, higher is better.
    
    Args:
        state: Decision state with context
        action: Candidate action with params
        weights: Optional weights for grace components
        
    Returns:
        𝒢: Grace score (0..1)
    """
    w = weights or DEFAULT_GRACE_WEIGHTS
    
    # Coverage component
    coverage = action.params.get("coverage", 0.0)
    coverage_target = state.context.get("coverage_target", 0.95)
    cov_term = min(1.0, max(0.0, (coverage - 0.5) / (coverage_target - 0.5))) if coverage_target > 0.5 else coverage
    
    # Rollback readiness
    has_rollback = bool(action.params.get("rollback_recipe", ""))
    rb_bonus = 0.1 if has_rollback else -0.15
    
    # Coherence proxy (via risk)
    risk = action.params.get("risk", 0.5)
    coherence = max(0.0, 1.0 - risk)
    
    # Dignity preservation
    dignity_penalty = action.params.get("grace_penalty", 0.0)
    
    # Has repair plan
    has_repair = bool(action.params.get("repair_plan", ""))
    repair_bonus = 0.08 if has_repair else 0.0
    
    # Compute weighted grace
    G = max(0.0, min(1.0, 
        (w.get("coverage", 0.55) * cov_term) + 
        (w.get("coherence", 0.25) * coherence) + 
        (w.get("rollback", 0.10) * (1.0 if has_rollback else 0.0)) -
        (w.get("dignity", 0.25) * dignity_penalty) +
        repair_bonus
    ))
    
    return G

def simulate_pca_for_candidate(state: Any, action: Any) -> AdviceWithProof:
    """
    Creates a simplified PCA wrapper for a candidate action to enable scoring.
    This helps bridge class-based metrics to function-based ones.
    
    Used internally by energy() and grace() if needed for full scoring.
    """
    draft = AdviceDraft(
        id=f"candidate:{action.id}",
        query=state.context.get("query", ""),
        plan=action.params.get("plan", {}),
        params=action.params,
        context=state.context
    )
    
    # Simple proofs
    consent_ok = _consent_check(state, action)
    apoph_ok = _apophatic_check(state, action)
    ext_ok = action.params.get("coverage", 0.0) >= 0.75
    
    proofs = [
        Proof(name="consent", ok=consent_ok, 
              details={"scope": state.context.get("consent", {}).get("scope", "self")}, 
              token=blake({"consent": consent_ok})),
        Proof(name="apophatic", ok=apoph_ok, 
              details={"reasons": []}, 
              token=blake({"apophatic": apoph_ok})),
        Proof(name="externalities", ok=ext_ok, 
              details={"coverage": action.params.get("coverage", 0.0)}, 
              token=blake({"externalities": ext_ok}))
    ]
    
    # Simple assessment
    assessment = {
        "externalities": {
            "coverage": action.params.get("coverage", 0.0),
            "rollback_ready": bool(action.params.get("rollback_recipe", "")),
            "externals": []
        },
        "harms": {
            "penalties": {
                "energy_penalty": action.params.get("energy_penalty", 0.0),
                "grace_penalty": action.params.get("grace_penalty", 0.0)
            },
            "H": action.params.get("H", 0.05)
        }
    }
    
    # Create simplified advice with proof
    return AdviceWithProof(
        id=draft.id,
        answer=action.description,
        risk=action.params.get("risk", 0.1),
        proofs=proofs,
        assessment=assessment,
        decided_at=0.0  # Placeholder
    )

# Helper functions

def _consent_check(state: Any, action: Any) -> bool:
    """Simple consent checker compatible with both systems."""
    c = state.context.get("consent", {})
    if c.get("valid") is True and c.get("scope") in {"self", "dyad", "group", "org", "public"}:
        return True
    return False

def _apophatic_check(state: Any, action: Any) -> bool:
    """Simple apophatic guard compatible with both systems."""
    # Minimal local apophatic check (mirror of PCA's logic)
    FORBID_KEYS = {"ground_is", "ultimate_name", "final_owner", "sovereign_claim"}
    CONSTRAINT_ONLY = {"no_image", "no_totalization", "no_equivalence", "no_exchange"}
    
    params = action.params or {}
    # explicit forbiddens
    for k in params.keys():
        if k in FORBID_KEYS:
            return False
    # constraint-only must be boolean/affirmed
    for k in CONSTRAINT_ONLY:
        if k in params and params[k] not in (True, "enforced"):
            return False
    return True

if __name__ == "__main__":
    # Example usage
    s = State(context={"query": "test", "consent": {"valid": True, "scope": "self"}})
    a = Action(id="test", description="Test action", params={
        "coverage": 0.9, 
        "externality_priced": True,
        "risk": 0.2,
        "rollback_recipe": "rollback steps...",
        "energy_penalty": 0.1,
        "grace_penalty": 0.05
    })
    
    print(f"Δ𝓔 = {energy(s, a)}")
    print(f"𝒢 = {grace(s, a, None)}")
