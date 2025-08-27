"""
Unified Externality Pricer
-------------------------
Unifies externality pricing approaches across the system. This module provides
a consistent interface for valuing externalities that integrates with:
1. HarmsLedger for negative externalities
2. Grace/Energy metrics for positive externalities
3. Shadow Twin for risk-assessment of mixed externalities
4. RRI targets from vows configuration

This ensures consistent externality pricing and valuation across all components.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass
from pydantic import BaseModel

from core.ethics.externality_pricer import Externality, ExternalityPricer


@dataclass
class ExternalityAssessment:
    """Assessment of externalities for a given action/context pair."""
    # Overall scores
    total_score: float = 0.0
    coverage: float = 0.0
    
    # Component breakdowns
    positive_externalities: List[Externality] = None
    negative_externalities: List[Externality] = None
    
    # Valuation details
    positive_value: float = 0.0
    negative_value: float = 0.0
    net_value: float = 0.0
    
    # RRI (Responsible Research & Innovation) alignment
    rri_alignment: float = 0.0
    
    def __post_init__(self):
        if self.positive_externalities is None:
            self.positive_externalities = []
        if self.negative_externalities is None:
            self.negative_externalities = []
        self.net_value = self.positive_value - self.negative_value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert assessment to dictionary for storage/transmission."""
        return {
            "total_score": self.total_score,
            "coverage": self.coverage,
            "positive_count": len(self.positive_externalities),
            "negative_count": len(self.negative_externalities),
            "positive_value": self.positive_value,
            "negative_value": self.negative_value,
            "net_value": self.net_value,
            "rri_alignment": self.rri_alignment
        }


class UnifiedExternalityPricer:
    """
    Unified pricer for externalities across all system components.
    Ensures consistent valuation and coverage assessment.
    """
    
    def __init__(self):
        """Initialize with standard pricer and RRI targets."""
        self.pricer = ExternalityPricer()
        self.rri_targets = self._load_rri_targets()
        
    def _load_rri_targets(self) -> Dict[str, float]:
        """Load RRI targets from vows configuration."""
        try:
            # Find project root (parent of core directory)
            root_dir = Path(__file__).parent.parent.parent
            vows_path = root_dir / "docs" / "vows.yaml"
            
            with open(vows_path, "r") as f:
                vows = yaml.safe_load(f) or {}
                
            # Extract RRI targets section
            return vows.get("rri_targets", {})
        except Exception as e:
            print(f"Warning: Failed to load RRI targets from vows.yaml: {e}")
            # Default RRI targets if loading fails
            return {
                "total_coverage_threshold": 0.8,
                "minimum_positive_ratio": 0.25,
                "harm_penalty_factor": 1.2,
                "tech_ethics_weight": 0.6,
                "social_impact_weight": 0.5,
                "ecological_weight": 0.7
            }
    
    def register(self, ext: Externality):
        """Register an externality in the unified registry."""
        self.pricer.register(ext)
    
    def assess(self, context: Dict[str, Any], action_params: Dict[str, Any]) -> ExternalityAssessment:
        """
        Perform a comprehensive externality assessment for a context/action pair.
        
        Args:
            context: The context in which the action is being considered
            action_params: Parameters of the action being assessed
            
        Returns:
            ExternalityAssessment: Complete assessment results
        """
        assessment = ExternalityAssessment()
        
        # Extract externalities from context and action
        positive_exts = self._extract_externalities(context, action_params, "positive")
        negative_exts = self._extract_externalities(context, action_params, "negative")
        
        assessment.positive_externalities = positive_exts
        assessment.negative_externalities = negative_exts
        
        # Calculate values
        assessment.positive_value = sum(self.pricer.value_score(ext.id) for ext in positive_exts)
        assessment.negative_value = sum(abs(self.pricer.value_score(ext.id)) for ext in negative_exts)
        assessment.net_value = assessment.positive_value - assessment.negative_value
        
        # Calculate coverage
        total_possible = self._estimate_externality_coverage(context, action_params)
        total_covered = len(positive_exts) + len(negative_exts)
        assessment.coverage = min(1.0, total_covered / max(1, total_possible))
        
        # Calculate RRI alignment
        assessment.rri_alignment = self._calculate_rri_alignment(assessment)
        
        # Calculate final score with penalties for low coverage
        coverage_penalty = 1.0
        if assessment.coverage < self.rri_targets.get("total_coverage_threshold", 0.8):
            coverage_penalty = assessment.coverage
        
        assessment.total_score = (
            assessment.net_value * coverage_penalty * 
            (0.5 + 0.5 * assessment.rri_alignment)  # RRI boosts score but doesn't zero it
        )
        
        return assessment
    
    def _extract_externalities(self, context: Dict[str, Any], 
                              action_params: Dict[str, Any],
                              ext_type: str) -> List[Externality]:
        """
        Extract externalities of a given type from context and action parameters.
        
        Args:
            context: The context dictionary
            action_params: Action parameters
            ext_type: Type of externality to extract ('positive' or 'negative')
            
        Returns:
            List[Externality]: Extracted externalities
        """
        externalities = []
        
        # Extract from explicit externalities list in action params
        if "externalities" in action_params and isinstance(action_params["externalities"], list):
            for ext_data in action_params["externalities"]:
                if isinstance(ext_data, dict) and ext_data.get("type") == ext_type:
                    try:
                        ext = Externality(**ext_data)
                        externalities.append(ext)
                        # Register if not already in system
                        if ext.id not in self.pricer.registry:
                            self.register(ext)
                    except Exception:
                        # Skip invalid externality
                        continue
        
        # Also look in context for externalities
        if "identified_externalities" in context and isinstance(context["identified_externalities"], list):
            for ext_data in context["identified_externalities"]:
                if isinstance(ext_data, dict) and ext_data.get("type") == ext_type:
                    # Avoid duplicates
                    if any(e.id == ext_data.get("id") for e in externalities):
                        continue
                        
                    try:
                        ext = Externality(**ext_data)
                        externalities.append(ext)
                        # Register if not already in system
                        if ext.id not in self.pricer.registry:
                            self.register(ext)
                    except Exception:
                        # Skip invalid externality
                        continue
                        
        return externalities
    
    def _estimate_externality_coverage(self, context: Dict[str, Any], 
                                      action_params: Dict[str, Any]) -> int:
        """
        Estimate how many externalities should be covered for complete assessment.
        
        Args:
            context: The context dictionary
            action_params: Action parameters
            
        Returns:
            int: Estimated total externalities for full coverage
        """
        # Base minimum externalities based on action complexity
        base = 2  # Even simple actions have at least 2 externalities
        
        # Adjust based on explicit complexity declaration
        if "complexity" in action_params:
            complexity = action_params.get("complexity", 1)
            if isinstance(complexity, (int, float)):
                base = max(2, int(complexity) + 1)
        
        # Adjust based on context markers
        context_markers = {
            "multi_agent": 1,
            "public_facing": 2,
            "safety_critical": 2,
            "potentially_harmful": 1
        }
        
        for marker, value in context_markers.items():
            if marker in context and context[marker]:
                base += value
                
        return base
    
    def _calculate_rri_alignment(self, assessment: ExternalityAssessment) -> float:
        """
        Calculate alignment with Responsible Research & Innovation targets.
        
        Args:
            assessment: The externality assessment
            
        Returns:
            float: RRI alignment score [0..1]
        """
        # Extract RRI weights
        tech_weight = self.rri_targets.get("tech_ethics_weight", 0.6)
        social_weight = self.rri_targets.get("social_impact_weight", 0.5)
        eco_weight = self.rri_targets.get("ecological_weight", 0.7)
        
        # Check positive ratio requirement
        pos_ratio = 0.0
        total_exts = len(assessment.positive_externalities) + len(assessment.negative_externalities)
        if total_exts > 0:
            pos_ratio = len(assessment.positive_externalities) / total_exts
            
        min_pos_ratio = self.rri_targets.get("minimum_positive_ratio", 0.25)
        pos_ratio_score = min(1.0, pos_ratio / min_pos_ratio)
        
        # Simplified RRI calculation
        base_score = 0.5  # Default middle score
        
        # Technical ethics adjustment
        if "tech_ethics_assessed" in assessment.to_dict():
            base_score += 0.2 * tech_weight
            
        # Social impact adjustment
        if assessment.net_value > 0:
            base_score += 0.1 * social_weight
        
        # Coverage adjustment
        if assessment.coverage >= 0.8:
            base_score += 0.2 * eco_weight
            
        # Final RRI score is product of base and positive ratio requirement
        return base_score * pos_ratio_score


def test_unified_pricer():
    """Test the unified externality pricer with sample data."""
    pricer = UnifiedExternalityPricer()
    
    # Sample context and action
    context = {
        "identified_externalities": [
            {
                "id": "privacy_leak",
                "description": "Potential privacy exposure",
                "type": "negative",
                "magnitude": -0.7,
                "harmed_parties": 50
            }
        ],
        "safety_critical": True
    }
    
    action_params = {
        "complexity": 3,
        "externalities": [
            {
                "id": "knowledge_access",
                "description": "Improved access to knowledge",
                "type": "positive",
                "magnitude": 0.8,
                "beneficiaries": 100
            },
            {
                "id": "resource_usage",
                "description": "Computational resource consumption",
                "type": "negative",
                "magnitude": -0.3,
                "harmed_parties": 0
            }
        ]
    }
    
    assessment = pricer.assess(context, action_params)
    
    print("Externality Assessment:")
    print(f"  Total Score: {assessment.total_score:.2f}")
    print(f"  Coverage: {assessment.coverage:.2f}")
    print(f"  Positive Value: {assessment.positive_value:.2f}")
    print(f"  Negative Value: {assessment.negative_value:.2f}")
    print(f"  Net Value: {assessment.net_value:.2f}")
    print(f"  RRI Alignment: {assessment.rri_alignment:.2f}")
    print(f"  Positive Externalities: {len(assessment.positive_externalities)}")
    print(f"  Negative Externalities: {len(assessment.negative_externalities)}")


if __name__ == "__main__":
    test_unified_pricer()
