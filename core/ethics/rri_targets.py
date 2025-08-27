"""
RRI Targets Manager
-----------------
Aligns Responsible Research and Innovation (RRI) targets across all components
by providing a centralized configuration source. This ensures consistent
application of ethical guidelines across decision making, metrics, and evaluations.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class RRIConfiguration:
    """Responsible Research & Innovation configuration parameters."""
    # Coverage and quality thresholds
    min_coverage: float = 0.75
    min_positive_ratio: float = 0.25
    grace_threshold: float = 0.65
    
    # Component weights
    tech_ethics_weight: float = 0.60
    social_impact_weight: float = 0.50
    ecological_weight: float = 0.70
    governance_weight: float = 0.45
    
    # Penalties and boosts
    harm_penalty_factor: float = 1.2
    coverage_boost_factor: float = 1.1
    
    # Additional RRI dimension settings
    anticipation_required: bool = True
    inclusion_threshold: float = 0.4
    reflexivity_depth: int = 2
    responsiveness_window_days: int = 14
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "min_coverage": self.min_coverage,
            "min_positive_ratio": self.min_positive_ratio,
            "grace_threshold": self.grace_threshold,
            "tech_ethics_weight": self.tech_ethics_weight,
            "social_impact_weight": self.social_impact_weight,
            "ecological_weight": self.ecological_weight,
            "governance_weight": self.governance_weight,
            "harm_penalty_factor": self.harm_penalty_factor,
            "coverage_boost_factor": self.coverage_boost_factor,
            "anticipation_required": self.anticipation_required,
            "inclusion_threshold": self.inclusion_threshold,
            "reflexivity_depth": self.reflexivity_depth,
            "responsiveness_window_days": self.responsiveness_window_days
        }


class RRITargetsManager:
    """
    Manages and provides access to RRI targets for all system components.
    Ensures consistent application of RRI guidelines across the system.
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance of the RRI targets manager."""
        if cls._instance is None:
            cls._instance = RRITargetsManager()
        return cls._instance
    
    def __init__(self):
        """Initialize by loading RRI configuration from vows.yaml."""
        self.config = self._load_rri_config()
        self._component_overrides = {}
    
    def _load_rri_config(self) -> RRIConfiguration:
        """Load RRI configuration from vows.yaml."""
        try:
            # Find project root (parent of core directory)
            root_dir = Path(__file__).parent.parent.parent
            vows_path = root_dir / "docs" / "vows.yaml"
            
            with open(vows_path, "r") as f:
                vows = yaml.safe_load(f) or {}
                
            # Extract RRI targets section
            rri_data = vows.get("rri_targets", {})
            
            # Convert to configuration object
            config_dict = {
                "min_coverage": rri_data.get("total_coverage_threshold", 0.75),
                "min_positive_ratio": rri_data.get("minimum_positive_ratio", 0.25),
                "grace_threshold": rri_data.get("grace_threshold", 0.65),
                "tech_ethics_weight": rri_data.get("tech_ethics_weight", 0.60),
                "social_impact_weight": rri_data.get("social_impact_weight", 0.50),
                "ecological_weight": rri_data.get("ecological_weight", 0.70),
                "governance_weight": rri_data.get("governance_weight", 0.45),
                "harm_penalty_factor": rri_data.get("harm_penalty_factor", 1.2),
                "coverage_boost_factor": rri_data.get("coverage_boost_factor", 1.1),
                "anticipation_required": rri_data.get("anticipation_required", True),
                "inclusion_threshold": rri_data.get("inclusion_threshold", 0.4),
                "reflexivity_depth": rri_data.get("reflexivity_depth", 2),
                "responsiveness_window_days": rri_data.get("responsiveness_window_days", 14)
            }
            
            return RRIConfiguration(**config_dict)
            
        except Exception as e:
            print(f"Warning: Failed to load RRI targets from vows.yaml: {e}")
            # Return default configuration
            return RRIConfiguration()
    
    def get_config(self, component: Optional[str] = None) -> RRIConfiguration:
        """
        Get RRI configuration, optionally for a specific component.
        
        Args:
            component: Optional component name for specialized configuration
            
        Returns:
            RRIConfiguration: The RRI configuration for the component
        """
        if component and component in self._component_overrides:
            return self._component_overrides[component]
        return self.config
    
    def register_component_override(self, component: str, config: RRIConfiguration):
        """
        Register component-specific RRI configuration overrides.
        
        Args:
            component: Component name
            config: Custom RRI configuration for this component
        """
        self._component_overrides[component] = config
    
    def get_rri_dimensions(self) -> List[str]:
        """Get the list of RRI dimensions used by the system."""
        return [
            "anticipation",
            "inclusion",
            "reflexivity",
            "responsiveness",
            "techethics",
            "social",
            "ecological",
            "governance"
        ]
    
    def validate_rri_compliance(self, 
                               component_scores: Dict[str, float]) -> Dict[str, Any]:
        """
        Validate if a component meets RRI compliance requirements.
        
        Args:
            component_scores: Dictionary of RRI dimension scores
            
        Returns:
            Dict: Compliance results with overall status and dimension details
        """
        dimensions = self.get_rri_dimensions()
        
        # Check that all required dimensions are present
        missing = [d for d in dimensions if d not in component_scores]
        if missing:
            return {
                "compliant": False,
                "missing_dimensions": missing,
                "overall_score": 0.0,
                "reason": f"Missing required RRI dimensions: {', '.join(missing)}"
            }
        
        # Calculate weighted score
        weights = {
            "anticipation": 0.15,
            "inclusion": 0.15,
            "reflexivity": 0.15,
            "responsiveness": 0.15,
            "techethics": self.config.tech_ethics_weight / 2,
            "social": self.config.social_impact_weight / 2,
            "ecological": self.config.ecological_weight / 2,
            "governance": self.config.governance_weight / 2
        }
        
        weighted_score = sum(component_scores[d] * weights[d] for d in dimensions)
        
        # Check compliance
        min_threshold = 0.65  # Minimum overall weighted score for compliance
        compliant = weighted_score >= min_threshold
        
        return {
            "compliant": compliant,
            "overall_score": weighted_score,
            "dimension_scores": {d: component_scores[d] for d in dimensions},
            "reason": "Sufficient RRI compliance" if compliant else "Below RRI threshold"
        }


def test_rri_manager():
    """Test the RRI targets manager."""
    manager = RRITargetsManager.get_instance()
    
    # Print general configuration
    config = manager.get_config()
    print("RRI Configuration:")
    for key, value in config.to_dict().items():
        print(f"  {key}: {value}")
    
    # Test validation
    test_scores = {
        "anticipation": 0.8,
        "inclusion": 0.7,
        "reflexivity": 0.65,
        "responsiveness": 0.75,
        "techethics": 0.82,
        "social": 0.73,
        "ecological": 0.68,
        "governance": 0.60
    }
    
    result = manager.validate_rri_compliance(test_scores)
    print("\nRRI Compliance Test:")
    print(f"  Compliant: {result['compliant']}")
    print(f"  Overall score: {result['overall_score']:.2f}")
    print(f"  Reason: {result['reason']}")


if __name__ == "__main__":
    test_rri_manager()
