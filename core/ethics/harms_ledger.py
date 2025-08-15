"""
Harms Ledger
------------
Tracks potential and actual harms, aligned with Crownfire Law and Throne-Fiber constraints.
Integrates with consent_types and apophatic_guard to ensure all harm vectors are contextualized
and justified or rejected.

Metric Coupling:
    - 𝓔 (Energy Integrity)
    - 𝒢 (Grace)
    - Kenosis index
"""

from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel


class HarmEvent(BaseModel):
    id: str
    timestamp: datetime
    agent: str
    category: str  # e.g., 'physical', 'informational', 'psychological'
    severity: float  # 0.0–1.0
    intentionality: float  # 0.0–1.0 (malice vector)
    mitigation_steps: List[str]
    resolved: bool = False
    notes: Optional[str] = None


class HarmsLedger:
    def __init__(self):
        self.events: Dict[str, HarmEvent] = {}

    def record_event(self, event: HarmEvent):
        if event.id in self.events:
            raise ValueError(f"Harm event {event.id} already exists.")
        self.events[event.id] = event
        self._log_event(event)

    def resolve_event(self, event_id: str, resolution_notes: str):
        if event_id not in self.events:
            raise KeyError(f"No such harm event: {event_id}")
        event = self.events[event_id]
        event.resolved = True
        event.notes = (event.notes or "") + f"\n[Resolution] {resolution_notes}"
        self._log_event(event, resolution=True)

    def _log_event(self, event: HarmEvent, resolution=False):
        action = "RESOLVED" if resolution else "RECORDED"
        print(f"[{action} @ {event.timestamp}] {event.category} harm "
              f"(severity={event.severity}, malice={event.intentionality}) by {event.agent}")


if __name__ == "__main__":
    ledger = HarmsLedger()
    # Example usage
    example_event = HarmEvent(
        id="harm001",
        timestamp=datetime.now(),
        agent="external_agent_X",
        category="informational",
        severity=0.65,
        intentionality=0.2,
        mitigation_steps=["Anonymization", "Data purging"]
    )
    ledger.record_event(example_event)
    ledger.resolve_event("harm001", "Issue addressed through targeted mitigation.")
