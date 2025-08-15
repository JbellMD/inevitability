# Geometry kernels for the Will Engine.
# Kernels *shape* the MCMC valley by returning a multiplicative weight K(op, state, action).
# E_effective = E_raw * K. We clamp K to [min,max] from will_engine.yaml defaults.

from __future__ import annotations
from typing import Dict, Any
from pathlib import Path
import yaml
import math

# Load vows (for Grace components) and will defaults
_VOWS = yaml.safe_load(Path("docs/vows.yaml").read_text())
_WILL = yaml.safe_load(Path("core/will/will_engine.yaml").read_text())
_DEFAULTS = _WILL.get("defaults", {})
_K_MIN = float(_DEFAULTS.get("kernel_weight_clamp", {}).get("min", 0.25))
_K_MAX = float(_DEFAULTS.get("kernel_weight_clamp", {}).get("max", 4.0))

def _clamp(x: float) -> float:
    return max(_K_MIN, min(_K_MAX, x))

def _reversibility_bonus(action: Dict[str, Any]) -> float:
    return 0.90 if action.get("reversible", True) else 1.05

def _externality_penalty(action: Dict[str, Any]) -> float:
    # Expect actions in EXP to carry {"externality_priced": bool, "coverage": float}
    if action.get("externality_priced", False):
        cov = float(action.get("coverage", 1.0))
        return 1.0 - 0.25 * min(1.0, cov)   # up to -0.25 weight for full coverage
    return 1.20  # penalize unpriced scaling

def _scale_penalty(action: Dict[str, Any]) -> float:
    s = float(action.get("scale", 1.0))
    if s <= 1.0: return 1.0
    return min(1.0 + 0.10 * (s - 1.0), 1.50)  # mild penalty for aggressive scale

def _repair_bonus(action: Dict[str, Any]) -> float:
    # Repair plans lower effective energy
    return 0.90 if action.get("repair_plan", False) else 1.0

def _aesthetic_bonus(action: Dict[str, Any]) -> float:
    # If aesthetic coherence is evidenced (without truth loss), reward slightly
    aest = float(action.get("aesthetic_coherence", 0.0))
    return 1.0 - 0.10 * max(0.0, min(1.0, aest))

def inverted_tetrahedron(state, action: Dict[str, Any]) -> float:
    """
    NEG: Favor clean cuts that minimize humiliation and carry repair invitations.
    Penalize compromises that leave coercion intact.
    """
    coercion = 1.0 if action.get("coercion_risk", False) else 0.0
    humiliation = float(action.get("humiliation_risk", 0.0))
    base = 1.10 + 0.40*coercion + 0.30*humiliation
    base *= _repair_bonus(action)
    return _clamp(base)

def spiral_sphere(state, action: Dict[str, Any]) -> float:
    """
    POT: Favor reversible micro-moves; discourage large irreversible openings.
    """
    base = 1.0
    base *= _reversibility_bonus(action)
    base *= _scale_penalty({"scale": action.get("scale", 1.0) * 0.5})  # softer scale
    return _clamp(base)

def dual_torus(state, action: Dict[str, Any]) -> float:
    """
    GEN: Reward actions with feedback loops and tending cadence.
    """
    loops = 1.0 if action.get("feedback_loops", False) else 0.0
    cadence = float(action.get("cadence_fit", 0.5))  # 0..1, how well the cadence fits the system
    base = 1.05 - 0.15*loops - 0.10*cadence
    return _clamp(base)

def golden_gnomon(state, action: Dict[str, Any]) -> float:
    """
    EXP: Enforce proportional φ-like scaling; require externality pricing & rollback.
    """
    base = 1.0
    base *= _scale_penalty(action)
    base *= _externality_penalty(action)
    if not action.get("rollback_recipe", False):
        base *= 1.20
    return _clamp(base)

def nested_dodecahedron(state, action: Dict[str, Any]) -> float:
    """
    POS: Reward custody clarity; penalize clutching/ownership theater.
    """
    clutch = float(action.get("clutching_index", 0.0))  # 0..1
    custody = float(action.get("custody_clarity", 0.5)) # 0..1
    base = 1.05 + 0.30*clutch - 0.20*custody
    return _clamp(base)

def mobius_intersect(state, action: Dict[str, Any]) -> float:
    """
    CON: Prefer single-sided continuity across apparent flips; penalize diffusion.
    """
    direction = float(action.get("direction_coherence", 0.5))
    diffusion = float(action.get("diffusion_risk", 0.0))
    base = 1.05 + 0.25*diffusion - 0.20*direction
    return _clamp(base)

def spiral_pyramid(state, action: Dict[str, Any]) -> float:
    """
    ASP: Reward beauty that is priced and testable; block aesthetic bypass.
    """
    aest  = float(action.get("aesthetic_coherence", 0.0))
    priced = bool(action.get("aesthetic_priced", False))
    base = 1.05 - 0.15*aest
    if not priced:
        base *= 1.15
    return _clamp(base)

def vanishing_ellipse(state, action: Dict[str, Any]) -> float:
    """
    TRN: Expand Stand radius near apophatic boundary; favor minimal, gentle moves.
    """
    apophatic_near = bool(action.get("apophatic_nearby", state.paradox_nearby))
    base = 1.10 if apophatic_near else 1.0
    base *= _reversibility_bonus(action)
    base *= _aesthetic_bonus(action)
    return _clamp(base)

def folded_voidstar(state, action: Dict[str, Any]) -> float:
    """
    ANN: Require clean dissolution with repair & kenosis; penalize identity-theater.
    """
    repair = bool(action.get("repair_plan", False))
    theater = float(action.get("identity_theater", 0.0))
    kenosis = float(action.get("kenosis_signal", 0.0))   # negative self-advantage, positive vow
    base = 1.10 + 0.30*theater - 0.20*kenosis
    if repair:
        base *= 0.90
    return _clamp(base)

# Dispatcher

_FUNCS = {
    "inverted_tetrahedron": inverted_tetrahedron,
    "spiral_sphere":        spiral_sphere,
    "dual_torus":           dual_torus,
    "golden_gnomon":        golden_gnomon,
    "nested_dodecahedron":  nested_dodecahedron,
    "mobius_intersect":     mobius_intersect,
    "spiral_pyramid":       spiral_pyramid,
    "vanishing_ellipse":    vanishing_ellipse,
    "folded_voidstar":      folded_voidstar,
}

def weight_for(will_operator: str, state, action_obj) -> float:
    """
    Main entry. Reads operator spec to find kernel, applies it to action params.
    The action object may be a dataclass; extract dict as needed.
    """
    op = _WILL["operators"][will_operator]
    kernel_name = op["kernel"]
    fn = _FUNCS[kernel_name]
    # Extract action params (Action.dataclass-compatible)
    if hasattr(action_obj, "__dict__"):
        params = dict(getattr(action_obj, "params", {}))
        # stitch common fields
        params["reversible"] = getattr(action_obj, "reversible", True)
        params.setdefault("predicted_truth", getattr(action_obj, "predicted_truth", "T"))
    elif isinstance(action_obj, dict):
        params = action_obj
    else:
        params = {}

    k = fn(state, params)
    return _clamp(k)
