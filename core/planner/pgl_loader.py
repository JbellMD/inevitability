"""
PGL & Paradox Gate Configuration Loader
-------------------------------------
Loads and provides access to the PGL (Paradox Gate Logic) configurations
from the YAML files. This enables the decision core to apply the appropriate
paradox handling and grace floor adjustments based on the configured rules.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

class PGLConfig:
    """Loads and provides access to PGL and Paradox Gate configurations."""
    
    def __init__(self):
        self.pgl_config = self._load_yaml("core/logic/pgl_coalgebra.yaml")
        self.paradox_gate_config = self._load_yaml("core/planner/paradox_gate.yaml")
        
    def _load_yaml(self, relative_path: str) -> Dict[str, Any]:
        """Load a YAML file relative to the project root."""
        try:
            # Find project root (parent of core directory)
            root_dir = Path(__file__).parent.parent.parent
            file_path = root_dir / relative_path
            
            with open(file_path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load {relative_path}: {e}")
            return {}
    
    def get_grace_floor(self, paradox_nearby: bool = False, apophatic_margin: bool = False) -> float:
        """
        Get the appropriate grace floor threshold based on the proximity to paradox.
        
        Args:
            paradox_nearby: Whether the state is near a paradox
            apophatic_margin: Whether the state is in the apophatic margin
            
        Returns:
            float: The grace threshold to enforce
        """
        floors = self.paradox_gate_config.get("grace_floor_by_zone", {})
        
        if apophatic_margin:
            return floors.get("apophatic_margin", 0.62)
        elif paradox_nearby:
            return floors.get("paradox_near", 0.60)
        else:
            return floors.get("normal", 0.55)
    
    def get_repair_horizon_days(self) -> Tuple[float, float]:
        """
        Get the min and max repair horizon days.
        
        Returns:
            Tuple[float, float]: (min_days, max_days)
        """
        rh = self.paradox_gate_config.get("repair_horizon", {})
        return (
            float(rh.get("min_days", 1)),
            float(rh.get("max_days", 14))
        )
    
    def requires_counter_context(self, paradox_nearby: bool) -> bool:
        """
        Check if a counter context is required in the current state.
        
        Args:
            paradox_nearby: Whether the state is near a paradox
            
        Returns:
            bool: True if counter context is required
        """
        if not paradox_nearby:
            return False
            
        return bool(self.paradox_gate_config.get("repair_horizon", {}).get("require_counter_context", True))
    
    def requires_micro_move(self, paradox_nearby: bool) -> bool:
        """
        Check if a reversible micro move is required in the current state.
        
        Args:
            paradox_nearby: Whether the state is near a paradox
            
        Returns:
            bool: True if a reversible micro move is required
        """
        if not paradox_nearby:
            return False
            
        overrides = self.pgl_config.get("paradox_overrides", {}).get("paradox_near", {})
        return bool(overrides.get("require_reversible_micro_move", True))
    
    def get_answer_conditions(self) -> List[str]:
        """Get the conditions required for an Answer decision."""
        return self.paradox_gate_config.get("answer_conditions", [])
    
    def get_stand_conditions(self) -> List[str]:
        """Get the conditions required for a Stand decision."""
        return self.paradox_gate_config.get("stand_conditions", [])
    
    def get_refuse_conditions(self) -> List[str]:
        """Get the conditions required for a Refuse decision."""
        return self.paradox_gate_config.get("refuse_conditions", [])
    
    def get_transitions(self) -> List[Dict[str, Any]]:
        """Get the PGL transitions for decision making."""
        return self.pgl_config.get("transitions", [])

# Global singleton instance
_PGL_CONFIG = None

def get_pgl_config() -> PGLConfig:
    """Get the global PGL configuration singleton."""
    global _PGL_CONFIG
    if _PGL_CONFIG is None:
        _PGL_CONFIG = PGLConfig()
    return _PGL_CONFIG

def pgl_decide(state: Any, action: Any, proofs: Any, truth: str) -> str:
    """
    Make a decision using the PGL coalgebra rules.
    
    Args:
        state: Decision state
        action: Selected action (if any)
        proofs: Proof bundle
        truth: Truth value ("T", "F", "B", "N")
        
    Returns:
        str: Decision ("Answer", "Refuse", "Stand")
    """
    config = get_pgl_config()
    
    # Extract state flags
    consent_clean = getattr(proofs, "consent", {}).get("ok", False)
    apophatic_ok = getattr(proofs, "logic", {}).get("apophatic_ok", False)
    delta_E_ok = action is not None and getattr(state, "delta_E", 0) < 0
    
    # Get appropriate grace floor
    paradox_near = getattr(state, "paradox_nearby", False)
    grace_floor = config.get_grace_floor(paradox_near)
    grace_ok = action is not None and getattr(state, "grace", 0) >= grace_floor
    
    # Check for micro move requirement
    requires_micro = config.requires_micro_move(paradox_near)
    micro_move_ok = not requires_micro or (
        action is not None and 
        getattr(action, "params", {}).get("reversible_micro_move", False)
    )
    
    # Process transitions in order
    transitions = config.get_transitions()
    
    for t in transitions:
        when = t.get("when", {})
        matches = True
        
        # Check all conditions
        for key, value in when.items():
            if key == "truth_val" and truth != value:
                matches = False
                break
            elif key == "consent_clean" and consent_clean != value:
                matches = False
                break
            elif key == "apophatic_ok" and apophatic_ok != value:
                matches = False
                break
            elif key == "delta_E_ok" and delta_E_ok != value:
                matches = False
                break
            elif key == "grace_ok" and grace_ok != value:
                matches = False
                break
            elif key == "paradox_near" and paradox_near != value:
                matches = False
                break
        
        # If all conditions match, apply this transition
        if matches:
            decision = t.get("then", {}).get("decision")
            
            # Check additional requirements for this transition
            requirements = t.get("then", {}).get("requirements", [])
            if "reversible_micro_move" in requirements and not micro_move_ok:
                continue
            if "repair_horizon" in requirements and not hasattr(proofs, "repair_horizon"):
                continue
                
            # Return the decision if all requirements are satisfied
            if decision:
                return decision
    
    # Default to Stand if no transition matched
    return "Stand"

if __name__ == "__main__":
    # Test loading configurations
    config = get_pgl_config()
    
    print("Grace floors:")
    print(f"  Normal: {config.get_grace_floor()}")
    print(f"  Paradox nearby: {config.get_grace_floor(True)}")
    print(f"  Apophatic margin: {config.get_grace_floor(False, True)}")
    
    print("\nRepair horizon days (min, max):", config.get_repair_horizon_days())
    print("Requires counter context when paradox nearby:", config.requires_counter_context(True))
    print("Requires micro move when paradox nearby:", config.requires_micro_move(True))
    
    print("\nPGL Transitions:")
    for i, t in enumerate(config.get_transitions()):
        print(f"  {i+1}. When {t.get('when')}, Then {t.get('then')}")
