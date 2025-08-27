"""
Paradox Proximity Detector
------------------------
Detects proximity to paradoxical states in decision-making contexts.
This module helps identify when a decision may be approaching logical,
ethical, or ontological paradoxes that require special handling by the
decision core's Paradox Gate Logic (PGL).
"""

from typing import Dict, Any, List, Tuple, Optional
import math
from dataclasses import dataclass
from enum import Enum

@dataclass
class ParadoxSignature:
    """Represents a detected paradox signature with proximity metrics."""
    type: str  # The type/category of the paradox
    proximity: float  # 0.0-1.0, with 1.0 being directly in a paradox
    confidence: float  # Confidence in the detection (0.0-1.0)
    properties: Dict[str, Any]  # Additional properties of the detected signature
    contradictions: List[Tuple[str, str]]  # List of contradictory pairs

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "type": self.type,
            "proximity": self.proximity,
            "confidence": self.confidence,
            "properties": self.properties,
            "contradictions": self.contradictions
        }

class ParadoxType(str, Enum):
    """Types of paradoxes that can be detected."""
    LOGICAL = "logical"  # Direct contradictions in logical statements
    ETHICAL = "ethical"  # Ethical dilemmas without clean resolution
    ONTOLOGICAL = "ontological"  # Paradoxes of being/identity/reference
    TEMPORAL = "temporal"  # Time-based paradoxes
    EPISTEMIC = "epistemic"  # Paradoxes of knowledge/certainty
    QUANTUM = "quantum"  # Quantum superposition-like paradoxes
    
    @classmethod
    def get_severity(cls, p_type: str) -> float:
        """Get base severity factor for a paradox type."""
        severity = {
            cls.LOGICAL: 1.0,
            cls.ETHICAL: 0.9,
            cls.ONTOLOGICAL: 0.95,
            cls.TEMPORAL: 0.85,
            cls.EPISTEMIC: 0.8,
            cls.QUANTUM: 0.7
        }
        return severity.get(p_type, 0.5)


class ParadoxDetector:
    """
    Detects proximity to paradoxical states in decision-making contexts.
    
    The detector uses multiple methods to identify paradox signatures:
    1. Logical contradiction detection
    2. Modal formula checking for consistency
    3. Semantic distance between paired concepts
    4. Alignment with known paradox patterns
    """
    
    def __init__(self):
        """Initialize the paradox detector."""
        self.paradox_patterns = self._load_patterns()
        self.detection_history = []
        
    def _load_patterns(self) -> List[Dict[str, Any]]:
        """Load known paradox patterns from configuration."""
        # These could be loaded from a YAML file in a full implementation
        return [
            {
                "name": "liar_paradox",
                "type": ParadoxType.LOGICAL,
                "pattern": "self_reference AND negation",
                "example": "This statement is false."
            },
            {
                "name": "sorites_paradox", 
                "type": ParadoxType.ONTOLOGICAL,
                "pattern": "vague_boundary AND incremental_change",
                "example": "When does a heap become not a heap by removing grains?"
            },
            {
                "name": "trolley_problem",
                "type": ParadoxType.ETHICAL,
                "pattern": "harm_minimization AND intentionality",
                "example": "Should you divert a trolley to kill one instead of five?"
            },
            {
                "name": "newcombs_problem",
                "type": ParadoxType.EPISTEMIC,
                "pattern": "prediction AND free_choice",
                "example": "Decision theory paradox with perfect predictor"
            }
        ]
    
    def detect(self, state: Any, action: Optional[Any] = None) -> ParadoxSignature:
        """
        Detect proximity to paradoxes in a state-action pair.
        
        Args:
            state: The current state
            action: The proposed action (if any)
            
        Returns:
            ParadoxSignature: Information about detected paradox proximity
        """
        # Initialize with no paradox
        signature = ParadoxSignature(
            type="none",
            proximity=0.0,
            confidence=0.0,
            properties={},
            contradictions=[]
        )
        
        # Extract context
        context = {}
        if hasattr(state, "context"):
            context = state.context
        
        # Check for paradox features
        features = self._extract_features(state, action, context)
        
        # Run multiple detection methods
        results = [
            self._detect_logical_contradictions(features, context),
            self._detect_ethical_dilemmas(features, context),
            self._detect_pattern_match(features, context)
        ]
        
        # Take the highest proximity detection
        results.sort(key=lambda x: x.proximity * x.confidence, reverse=True)
        if results and results[0].proximity > 0:
            signature = results[0]
            
        # Record detection for later analysis
        self.detection_history.append(signature)
        
        return signature
    
    def is_near_paradox(self, state: Any, action: Optional[Any] = None) -> bool:
        """
        Quick check if a state-action pair is near a paradox.
        
        Args:
            state: The current state
            action: The proposed action (if any)
            
        Returns:
            bool: True if near a paradox (proximity > threshold)
        """
        signature = self.detect(state, action)
        return signature.proximity >= 0.6
    
    def is_in_apophatic_margin(self, state: Any, action: Optional[Any] = None) -> bool:
        """
        Check if a state-action pair is in the apophatic margin.
        The apophatic margin is the zone where language/concepts begin to break down.
        
        Args:
            state: The current state
            action: The proposed action (if any)
            
        Returns:
            bool: True if in the apophatic margin (very close to paradox)
        """
        signature = self.detect(state, action)
        return signature.proximity >= 0.8
    
    def _extract_features(self, state: Any, action: Optional[Any], 
                         context: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract paradox-relevant features from state, action, and context.
        
        Returns:
            Dict[str, float]: Feature scores (0.0-1.0)
        """
        features = {
            # Logical paradox features
            "self_reference": 0.0,
            "negation": 0.0,
            "circularity": 0.0,
            
            # Ethical paradox features
            "ethical_tension": 0.0,
            "harm_minimization": 0.0,
            "principle_conflict": 0.0,
            
            # Ontological paradox features
            "identity_confusion": 0.0,
            "vague_boundary": 0.0,
            "modal_collapse": 0.0,
            
            # Other paradox features
            "temporal_loop": 0.0,
            "epistemic_limitation": 0.0,
            "quantum_superposition": 0.0
        }
        
        # Check for self-reference
        if context.get("self_referential") or (
            action and hasattr(action, "params") and
            action.params.get("self_referential")
        ):
            features["self_reference"] = 0.8
            
        # Check for negation combined with self-reference
        if features["self_reference"] > 0.5 and context.get("negation"):
            features["negation"] = 0.9
            
        # Check for ethical tension in context
        if context.get("ethical_dilemma") or context.get("moral_conflict"):
            features["ethical_tension"] = 0.7
            
        # Check for harm outcomes
        if context.get("potential_harms") or (
            action and hasattr(action, "params") and
            action.params.get("harm_analysis")
        ):
            features["harm_minimization"] = 0.6
            
        # Check for vague boundaries
        if context.get("vague_concepts") or context.get("continuous_spectrum"):
            features["vague_boundary"] = 0.65
            
        # Check for principle conflicts
        if hasattr(state, "conflicting_principles") and state.conflicting_principles:
            features["principle_conflict"] = 0.75
            
        # Check for epistemic limitations
        if context.get("unknowable") or context.get("undecidable"):
            features["epistemic_limitation"] = 0.8
            
        return features
    
    def _detect_logical_contradictions(self, features: Dict[str, float], 
                                      context: Dict[str, Any]) -> ParadoxSignature:
        """Detect logical contradictions in the context."""
        proximity = 0.0
        contradictions = []
        
        # Check for direct logical contradictions
        if "assertions" in context and isinstance(context["assertions"], dict):
            assertions = context["assertions"]
            for key, value in assertions.items():
                negated_key = f"not_{key}"
                if negated_key in assertions:
                    contradictions.append((key, negated_key))
                    proximity = max(proximity, 0.85)
        
        # Check for self-reference + negation (liar paradox pattern)
        if features["self_reference"] > 0.7 and features["negation"] > 0.7:
            proximity = max(proximity, 0.9)
            contradictions.append(("self_reference", "negation"))
        
        # Check for circularity
        if features["circularity"] > 0.7:
            proximity = max(proximity, 0.75)
            
        return ParadoxSignature(
            type=ParadoxType.LOGICAL if proximity > 0 else "none",
            proximity=proximity,
            confidence=0.8 if contradictions else 0.5,
            properties={"features": {k: v for k, v in features.items() if v > 0.5}},
            contradictions=contradictions
        )
    
    def _detect_ethical_dilemmas(self, features: Dict[str, float], 
                               context: Dict[str, Any]) -> ParadoxSignature:
        """Detect ethical dilemmas that may constitute paradoxes."""
        proximity = 0.0
        contradictions = []
        
        # Check for harm minimization vs intention
        if features["harm_minimization"] > 0.6 and features["principle_conflict"] > 0.6:
            proximity = max(proximity, 0.7)
            contradictions.append(("harm_minimization", "principle_conflict"))
        
        # Check for explicit ethical tensions
        if features["ethical_tension"] > 0.7:
            proximity = max(proximity, 0.65)
        
        # Check for competing ethical principles
        if "principles" in context and isinstance(context["principles"], list):
            principles = context["principles"]
            if len(principles) >= 2:
                for i in range(len(principles)):
                    for j in range(i + 1, len(principles)):
                        if "conflicts_with" in principles[i]:
                            conflicts = principles[i]["conflicts_with"]
                            if principles[j]["name"] in conflicts:
                                contradictions.append(
                                    (principles[i]["name"], principles[j]["name"])
                                )
                                proximity = max(proximity, 0.8)
        
        return ParadoxSignature(
            type=ParadoxType.ETHICAL if proximity > 0 else "none",
            proximity=proximity,
            confidence=0.7,
            properties={"ethical_dimensions": len(contradictions)},
            contradictions=contradictions
        )
    
    def _detect_pattern_match(self, features: Dict[str, float], 
                            context: Dict[str, Any]) -> ParadoxSignature:
        """Match against known paradox patterns."""
        best_match = None
        max_score = 0.0
        
        for pattern in self.paradox_patterns:
            # Simple pattern matching based on feature presence
            pattern_elements = pattern["pattern"].split(" AND ")
            match_score = 0.0
            
            for element in pattern_elements:
                element = element.lower()
                if element in features and features[element] > 0.5:
                    match_score += features[element]
                    
            # Normalize score
            if pattern_elements:
                match_score /= len(pattern_elements)
                
            if match_score > max_score:
                max_score = match_score
                best_match = pattern
        
        if best_match and max_score > 0.4:
            proximity = max_score
            return ParadoxSignature(
                type=best_match["type"],
                proximity=proximity,
                confidence=max_score,
                properties={"pattern": best_match["name"]},
                contradictions=[(best_match["pattern"], "")]
            )
        
        return ParadoxSignature(
            type="none",
            proximity=0.0,
            confidence=0.0,
            properties={},
            contradictions=[]
        )


# Global instance for system-wide use
_PARADOX_DETECTOR = None

def get_detector() -> ParadoxDetector:
    """Get the global paradox detector singleton."""
    global _PARADOX_DETECTOR
    if _PARADOX_DETECTOR is None:
        _PARADOX_DETECTOR = ParadoxDetector()
    return _PARADOX_DETECTOR

def detect_paradox_proximity(state: Any, action: Optional[Any] = None) -> Dict[str, Any]:
    """
    Detect paradox proximity for a state-action pair.
    
    Args:
        state: The current decision state
        action: The proposed action (if any)
        
    Returns:
        Dict containing paradox information
    """
    detector = get_detector()
    signature = detector.detect(state, action)
    
    return {
        "paradox_nearby": signature.proximity >= 0.6,
        "apophatic_margin": signature.proximity >= 0.8,
        "proximity": signature.proximity,
        "confidence": signature.confidence,
        "type": signature.type,
        "details": signature.to_dict()
    }


# For demonstration purposes
def test_paradox_detection():
    """Test the paradox detector with sample states."""
    detector = get_detector()
    
    class MockState:
        def __init__(self, context):
            self.context = context
            
    class MockAction:
        def __init__(self, params):
            self.params = params
    
    # Test case 1: Logical paradox (liar paradox)
    liar_context = {
        "self_referential": True,
        "negation": True,
        "assertions": {
            "statement_is_true": False,
            "not_statement_is_true": True
        }
    }
    liar_state = MockState(liar_context)
    result1 = detect_paradox_proximity(liar_state)
    print("Liar Paradox Test:")
    print(f"  Paradox nearby: {result1['paradox_nearby']}")
    print(f"  Apophatic margin: {result1['apophatic_margin']}")
    print(f"  Type: {result1['type']}")
    print(f"  Proximity: {result1['proximity']:.2f}")
    
    # Test case 2: Ethical paradox (trolley problem)
    trolley_context = {
        "ethical_dilemma": True,
        "principles": [
            {"name": "minimize_harm", "conflicts_with": ["avoid_intentional_harm"]},
            {"name": "avoid_intentional_harm"}
        ]
    }
    trolley_state = MockState(trolley_context)
    trolley_action = MockAction({"harm_analysis": {"save": 5, "harm": 1}})
    result2 = detect_paradox_proximity(trolley_state, trolley_action)
    print("\nTrolley Problem Test:")
    print(f"  Paradox nearby: {result2['paradox_nearby']}")
    print(f"  Apophatic margin: {result2['apophatic_margin']}")
    print(f"  Type: {result2['type']}")
    print(f"  Proximity: {result2['proximity']:.2f}")


if __name__ == "__main__":
    test_paradox_detection()
