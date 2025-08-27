"""
Apophatic Guard (Python Mirror)
-----------------------------
Python implementation of the apophatic guard that prevents positive predication
of the Ground. This mirrors the TypeScript implementation in apophatic_guard.ts.

The apophatic guard enforces constraints on language that attempts to totalize,
assert equivalence, or claim ownership over that which cannot be contained.
"""

from typing import Any, Dict, List, Tuple, Set, Optional

# Forbidden keys that should never be present
FORBIDDEN_KEYS: Set[str] = {
    "ground_is",           # No positive predication of ground
    "ultimate_name",       # No naming of unnameable
    "final_owner",         # No sovereign ownership claims
    "sovereign_claim",     # No sovereignty assertions
    "ground_truth",        # No privileged access to ground
    "completion",          # No totality/completion claims
}

# Keys that must be constrained (boolean True or "enforced" only)
CONSTRAINT_ONLY: Set[str] = {
    "no_image",            # No images of the unrepresentable
    "no_totalization",     # No system closure
    "no_equivalence",      # No A=B for the incomparable
    "no_exchange",         # No exchange value for the priceless
    "no_possession",       # No ownership of the common
}

# Warning markers (allowed but flagged)
WARN_MARKERS: Set[str] = {
    "meta_closure",        # Meta-level system closure attempt
    "self_grounding",      # Self-reference as ground
    "category_violation",  # Type/category error
}

def admissible(context: Dict[str, Any], params: Dict[str, Any]) -> bool:
    """
    Check if the context and parameters satisfy apophatic constraints.
    
    Args:
        context: The context dictionary
        params: The parameters dictionary to check
        
    Returns:
        bool: True if admissible, False otherwise
    """
    # Check all nested dictionaries
    all_params = _flatten_dict(params)
    all_context = _flatten_dict(context)
    
    # Check combined
    combined = {**all_context, **all_params}
    
    # Check forbidden keys
    for k in FORBIDDEN_KEYS:
        if k in combined:
            return False
    
    # Check constraint-only keys
    for k in CONSTRAINT_ONLY:
        if k in combined and combined[k] not in (True, "enforced"):
            return False
            
    return True

def check_detailed(context: Dict[str, Any], params: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Detailed check with reasons for any violations.
    
    Args:
        context: The context dictionary
        params: The parameters dictionary to check
        
    Returns:
        (bool, List[str]): (admissible?, list of reasons if not)
    """
    reasons: List[str] = []
    
    # Flatten and combine
    all_params = _flatten_dict(params)
    all_context = _flatten_dict(context)
    combined = {**all_context, **all_params}
    
    # Check forbidden keys
    for k in FORBIDDEN_KEYS:
        if k in combined:
            reasons.append(f"forbidden:{k}")
    
    # Check constraint-only keys
    for k in CONSTRAINT_ONLY:
        if k in combined and combined[k] not in (True, "enforced"):
            reasons.append(f"constraint_violation:{k}")
    
    # Check warning markers (these don't cause rejection but are noted)
    warnings = []
    for k in WARN_MARKERS:
        if k in combined:
            warnings.append(f"warning:{k}")
    
    return (len(reasons) == 0), reasons + warnings

def _flatten_dict(d: Dict[str, Any], prefix: str = "", result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Recursively flatten a nested dictionary with dot notation.
    
    Args:
        d: Dictionary to flatten
        prefix: Prefix for keys
        result: Accumulator dictionary
        
    Returns:
        Dict[str, Any]: Flattened dictionary
    """
    if result is None:
        result = {}
    
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        
        if isinstance(v, dict):
            _flatten_dict(v, key, result)
        else:
            result[key] = v
            
    return result

# Test function
def test_guard():
    """Test the guard with various inputs."""
    # Valid case
    valid_params = {
        "no_totalization": True,
        "no_image": "enforced",
        "safe_key": "value"
    }
    
    # Invalid case with forbidden key
    invalid_params1 = {
        "ground_is": "being",
        "no_totalization": True
    }
    
    # Invalid case with constraint violation
    invalid_params2 = {
        "no_totalization": False
    }
    
    # Test with nested dictionaries
    nested_params = {
        "deep": {
            "deeper": {
                "ground_is": "hidden here"
            }
        }
    }
    
    print("Valid params:", admissible({}, valid_params))
    print("Invalid params (forbidden):", admissible({}, invalid_params1))
    print("Invalid params (constraint):", admissible({}, invalid_params2))
    print("Nested params (should be invalid):", admissible({}, nested_params))
    
    # Detailed check
    ok, reasons = check_detailed({}, nested_params)
    print("Detailed check:", ok, reasons)

if __name__ == "__main__":
    test_guard()
