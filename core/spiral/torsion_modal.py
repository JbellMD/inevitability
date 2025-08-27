"""
Torsion Modal Activation
-----------------------
Enables torsion modal effects in the Inevitability decision system.
The torsion modal provides topological twisting of decision spaces
to enable graceful navigation around discontinuities and singularities
in the state-action manifold.
"""

from typing import Dict, Any, List, Optional, Tuple, Callable
import math
import numpy as np
from dataclasses import dataclass
from enum import Enum


class TorsionMode(str, Enum):
    """Available torsion modal operation modes."""
    PASSIVE = "passive"  # Observe but don't modify
    ACTIVE = "active"    # Actively reshape decision space
    HYBRID = "hybrid"    # Context-dependent activation


@dataclass
class TorsionParameters:
    """Parameters controlling torsion modal behavior."""
    # Activation parameters
    enabled: bool = False
    mode: TorsionMode = TorsionMode.PASSIVE
    activation_threshold: float = 0.65
    
    # Topological parameters
    twist_factor: float = 1.0
    manifold_dimension: int = 3
    singularity_buffer: float = 0.2
    
    # Interaction parameters
    interlace_coupling: bool = False
    throne_fiber_enabled: bool = False
    paradox_avoidance_strength: float = 0.7


class TorsionModal:
    """
    Torsion Modal system for topological modification of decision spaces.
    Enables graceful navigation around discontinuities by applying a
    torsion field to the state-action manifold.
    """
    
    def __init__(self, params: Optional[TorsionParameters] = None):
        """
        Initialize the torsion modal system.
        
        Args:
            params: Optional configuration parameters
        """
        self.params = params or TorsionParameters()
        self._active = False
        self._field_strength = 0.0
        self._singularity_map = {}
        self._hooks = []
        
    def activate(self) -> bool:
        """
        Activate the torsion modal system.
        
        Returns:
            bool: True if activation succeeded
        """
        if not self.params.enabled:
            print("[TorsionModal] Cannot activate: system is disabled in parameters")
            return False
            
        self._active = True
        self._field_strength = 0.1  # Start at minimal field strength
        print(f"[TorsionModal] Activated in {self.params.mode} mode")
        return True
        
    def deactivate(self):
        """Deactivate the torsion modal system."""
        if self._active:
            self._active = False
            self._field_strength = 0.0
            print("[TorsionModal] Deactivated")
    
    def is_active(self) -> bool:
        """Check if the torsion modal is currently active."""
        return self._active
    
    def get_field_strength(self) -> float:
        """Get the current torsion field strength."""
        return self._field_strength
    
    def register_hook(self, hook: Callable) -> int:
        """
        Register a hook function to be called during torsion operations.
        
        Args:
            hook: Callable that takes (state, action, torsion_data) -> modified_action
            
        Returns:
            int: Hook ID for later removal
        """
        hook_id = len(self._hooks)
        self._hooks.append(hook)
        return hook_id
    
    def remove_hook(self, hook_id: int) -> bool:
        """
        Remove a previously registered hook.
        
        Args:
            hook_id: ID of hook to remove
            
        Returns:
            bool: True if removal succeeded
        """
        if 0 <= hook_id < len(self._hooks):
            self._hooks.pop(hook_id)
            return True
        return False
    
    def apply_torsion(self, state: Any, action: Any) -> Tuple[Any, Dict[str, Any]]:
        """
        Apply torsion modal effects to a state-action pair.
        
        Args:
            state: Current state
            action: Proposed action
            
        Returns:
            Tuple[Any, Dict]: (Modified action, torsion data)
        """
        if not self._active or self.params.mode == TorsionMode.PASSIVE:
            return action, {"applied": False}
            
        # Calculate torsion factors
        torsion_data = self._calculate_torsion(state, action)
        
        # Check if we should apply torsion
        if torsion_data["torsion_required"] < self.params.activation_threshold:
            return action, {"applied": False, "reason": "below_threshold"}
        
        # Apply the torsion transformation
        modified_action = self._apply_transformation(action, torsion_data)
        
        # Run through hooks for further modification
        for hook in self._hooks:
            try:
                modified_action = hook(state, modified_action, torsion_data)
            except Exception as e:
                print(f"[TorsionModal] Hook error: {e}")
        
        return modified_action, torsion_data
    
    def _calculate_torsion(self, state: Any, action: Any) -> Dict[str, Any]:
        """
        Calculate torsion factors for a state-action pair.
        
        Args:
            state: Current state
            action: Proposed action
            
        Returns:
            Dict: Torsion calculation data
        """
        # Default factors
        factors = {
            "applied": True,
            "torsion_required": 0.0,
            "twist_vector": np.zeros(self.params.manifold_dimension),
            "field_strength": self._field_strength,
            "singularities": []
        }
        
        # Check for decision space discontinuities
        if hasattr(state, "discontinuities"):
            disc = state.discontinuities
            if disc and isinstance(disc, list) and len(disc) > 0:
                factors["torsion_required"] = 0.7
                factors["singularities"] = disc
                
        # Check for paradox proximity
        if hasattr(state, "paradox_nearby") and state.paradox_nearby:
            factors["torsion_required"] = max(
                factors["torsion_required"], 
                0.8 * self.params.paradox_avoidance_strength
            )
        
        # Check for direct singularities in the action
        if hasattr(action, "params") and action.params:
            if "singularity_proximity" in action.params:
                proximity = float(action.params["singularity_proximity"])
                factors["torsion_required"] = max(factors["torsion_required"], proximity)
            
        # Calculate twist vector based on torsion requirements
        if factors["torsion_required"] > 0:
            # Simple example: create a twist vector proportional to requirement
            base_vector = np.ones(self.params.manifold_dimension)
            base_vector = base_vector / np.linalg.norm(base_vector)
            factors["twist_vector"] = base_vector * factors["torsion_required"] * self.params.twist_factor
            
        return factors
    
    def _apply_transformation(self, action: Any, torsion_data: Dict[str, Any]) -> Any:
        """
        Apply torsion transformation to an action.
        
        Args:
            action: Action to transform
            torsion_data: Torsion calculation data
            
        Returns:
            Any: Transformed action
        """
        # Clone the action to avoid modifying the original
        if hasattr(action, "clone"):
            new_action = action.clone()
        else:
            # Try to make a shallow copy if no clone method
            try:
                new_action = type(action)()
                for key, value in vars(action).items():
                    setattr(new_action, key, value)
            except Exception:
                # Fallback: return the original action
                return action
        
        # Apply torsion effect to action parameters if they exist
        if hasattr(new_action, "params") and isinstance(new_action.params, dict):
            # Record that torsion was applied
            new_action.params["torsion_applied"] = True
            new_action.params["torsion_strength"] = float(torsion_data["torsion_required"])
            
            # Apply paradox avoidance if relevant
            if "paradox_proximity" in new_action.params:
                avoidance = self.params.paradox_avoidance_strength
                proximity = float(new_action.params["paradox_proximity"])
                if proximity > 0.5:
                    # Increase caution parameters
                    if "caution" in new_action.params:
                        new_action.params["caution"] *= (1 + avoidance * proximity)
                    else:
                        new_action.params["caution"] = avoidance * proximity
                        
                    # Add reversibility markers
                    new_action.params["reversible_micro_move"] = True
        
        return new_action


# Global singleton instance
_TORSION_MODAL = None

def get_torsion_modal() -> TorsionModal:
    """Get the global torsion modal singleton."""
    global _TORSION_MODAL
    if _TORSION_MODAL is None:
        _TORSION_MODAL = TorsionModal()
    return _TORSION_MODAL

def activate_torsion_modal(params: Optional[TorsionParameters] = None) -> bool:
    """
    Activate the global torsion modal with given parameters.
    
    Args:
        params: Optional parameters override
        
    Returns:
        bool: True if activation succeeded
    """
    modal = get_torsion_modal()
    if params:
        modal.params = params
    return modal.activate()


if __name__ == "__main__":
    # Test the torsion modal
    params = TorsionParameters(
        enabled=True,
        mode=TorsionMode.ACTIVE,
        activation_threshold=0.5
    )
    
    modal = TorsionModal(params)
    modal.activate()
    
    # Mock state and action
    class MockState:
        def __init__(self, paradox_nearby=False):
            self.paradox_nearby = paradox_nearby
            self.discontinuities = ["test_disc"] if paradox_nearby else []
            
    class MockAction:
        def __init__(self):
            self.params = {"caution": 0.5}
            
        def clone(self):
            new_action = MockAction()
            new_action.params = self.params.copy()
            return new_action
    
    state = MockState(paradox_nearby=True)
    action = MockAction()
    
    # Apply torsion
    new_action, data = modal.apply_torsion(state, action)
    
    print("Torsion Test:")
    print(f"  Torsion applied: {data['applied']}")
    print(f"  Torsion required: {data.get('torsion_required', 0):.2f}")
    print(f"  Original caution: {action.params['caution']}")
    print(f"  New caution: {new_action.params['caution']}")
    print(f"  Other params: {', '.join(f'{k}={v}' for k, v in new_action.params.items() if k not in ['caution'])}")
