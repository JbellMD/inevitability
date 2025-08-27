"""
Energy Delta (Δ𝓔) Semantics
--------------------------
Defines the semantics for Δ𝓔 (delta energy) calculations in the decision-making process.
This module ensures that Δ𝓔 < 0 is consistently applied across all components to align
with the vows specification.

The delta energy is computed as a cost function where:
- Negative values indicate beneficial moves (less energy required)
- Positive values indicate costly moves (more energy required)
- The Will kernel K shapes the energy cost based on will operator
"""

from typing import Any, Dict, Optional
import yaml
from pathlib import Path

from core.will.kernels import weight_for
from core.ethics.harms_ledger import HarmsLedger, HarmIndex

# Load vows configuration for energy thresholds
def _load_vows():
    """Load vows.yaml to get energy thresholds."""
    try:
        vows_path = Path(__file__).parent.parent.parent / "docs" / "vows.yaml"
        with open(vows_path, "r") as f:
            return yaml.safe_load(f)
    except Exception:
        # Default thresholds if loading fails
        return {
            "infinite_elegance": {
                "energy_threshold": -0.05,
                "energy_components": {
                    "base_cost": 1.0,
                    "harm_pressure": 0.4,
                    "rail_violations": 0.35,
                    "risk": 0.3
                }
            },
            "decision_policy": {
                "energy_delta_threshold": -0.05
            }
        }

# Load vows
_VOWS = _load_vows()
_VOW_IE = _VOWS.get("infinite_elegance", {})
_DECISION_POLICY = _VOWS.get("decision_policy", {})

# Energy threshold from vows
ENERGY_DELTA_THRESHOLD = _DECISION_POLICY.get("energy_delta_threshold", -0.05)
ENERGY_COMPONENTS = _VOW_IE.get("energy_components", {
    "base_cost": 1.0,
    "harm_pressure": 0.4, 
    "rail_violations": 0.35,
    "risk": 0.3
})

def delta_energy(state: Any, action: Any) -> float:
    """
    Calculate the energy delta (Δ𝓔) for an action.
    Implements "Δ𝓔 < 0 to move" as specified in vows.
    
    A negative return value indicates a beneficial move (lower energy).
    
    Args:
        state: The current state
        action: The candidate action
        
    Returns:
        delta_e: The energy delta (negative is better)
    """
    # Base cost depends on action complexity
    base_cost = _base_cost(action)
    
    # Rail violations increase cost
    rail_cost = _rail_violations_cost(state, action)
    
    # Harm pressure from ledger
    harm_cost = _harm_pressure_cost(state)
    
    # Risk component
    risk_cost = _risk_cost(action)
    
    # Total raw cost
    total_cost = (
        ENERGY_COMPONENTS.get("base_cost", 1.0) * base_cost +
        ENERGY_COMPONENTS.get("rail_violations", 0.35) * rail_cost +
        ENERGY_COMPONENTS.get("harm_pressure", 0.4) * harm_cost +
        ENERGY_COMPONENTS.get("risk", 0.3) * risk_cost
    )
    
    # Apply kernel weight
    K = weight_for(state.will_operator, state, action)
    
    # Final delta energy (negative = good, positive = bad)
    delta_e = -1.0 * (K * total_cost)
    
    return delta_e

def check_threshold(delta_e: float) -> bool:
    """
    Check if delta energy meets the threshold from vows.yaml.
    
    Args:
        delta_e: The energy delta value
        
    Returns:
        bool: True if it meets threshold, False otherwise
    """
    return delta_e <= ENERGY_DELTA_THRESHOLD

# Helper functions

def _base_cost(action: Any) -> float:
    """Calculate base cost based on action complexity."""
    # Default minimal cost
    cost = 0.1
    
    # If action has specific energy cost metadata, use that
    if hasattr(action, "params") and action.params:
        params = action.params
        if "energy_cost" in params:
            return float(params["energy_cost"])
    
    # Proportional to description complexity
    if hasattr(action, "description") and action.description:
        desc_len = len(action.description)
        cost += 0.02 * (desc_len / 100)  # 0.02 per 100 chars
    
    return min(1.0, cost)

def _rail_violations_cost(state: Any, action: Any) -> float:
    """Calculate cost from rail violations."""
    # Check consent
    consent_ok = True
    if hasattr(state, "consent_tickets") and state.consent_tickets:
        consent_ok = all(t.is_valid() for t in state.consent_tickets)
    
    # Check apophatic guard
    apoph_ok = True
    try:
        from core.logic.apophatic_guard import admissible
        context = state.context if hasattr(state, "context") else {}
        params = action.params if hasattr(action, "params") else {}
        apoph_ok = admissible(context, params)
    except (ImportError, AttributeError):
        pass
    
    # Check externality coverage
    ext_ok = True
    if hasattr(action, "params") and action.params:
        coverage = action.params.get("coverage", 0.0)
        ext_ok = coverage >= 0.75
    
    # Cost from violations
    cost = 0.0
    if not consent_ok:
        cost += 0.35
    if not apoph_ok:
        cost += 0.25
    if not ext_ok:
        cost += 0.20
    
    return cost

def _harm_pressure_cost(state: Any) -> float:
    """Calculate cost from harm pressure in ledger."""
    try:
        harms = HarmsLedger()
        hidx = harms.compute_index()
        penalties = harms.penalties(hidx)
        return penalties["energy_penalty"]
    except Exception:
        # Default moderate cost if ledger not available
        return 0.15

def _risk_cost(action: Any) -> float:
    """Calculate cost from risk assessment."""
    # Default moderate risk
    risk = 0.2
    
    if hasattr(action, "params") and action.params:
        # Use risk if explicitly provided
        if "risk" in action.params:
            return float(action.params["risk"])
        
        # Otherwise estimate from action attributes
        if "externality_priced" in action.params and action.params["externality_priced"]:
            coverage = action.params.get("coverage", 0.0)
            risk = 0.5 - (0.5 * coverage)  # Lower coverage = higher risk
    
    return risk

if __name__ == "__main__":
    # Test with minimal state/action structures
    class TestState:
        def __init__(self):
            self.will_operator = "EXP"
            self.context = {}
            self.consent_tickets = []
    
    class TestAction:
        def __init__(self, desc="Test", coverage=0.8, risk=0.2):
            self.id = "test"
            self.description = desc
            self.params = {
                "coverage": coverage,
                "risk": risk,
                "externality_priced": True
            }
    
    state = TestState()
    action = TestAction()
    
    delta_e = delta_energy(state, action)
    print(f"Delta Energy (Δ𝓔): {delta_e}")
    print(f"Meets threshold: {check_threshold(delta_e)}")
    print(f"Threshold: {ENERGY_DELTA_THRESHOLD}")
