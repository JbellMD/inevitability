"""
Externality Pricer
------------------
Assigns and maintains valuations for externalities—positive and negative—
to ensure all actions are evaluated against total systemic cost/benefit.

Couples with HarmsLedger for negative externalities and
with Grace/Energy metrics for positive externalities.
"""

from typing import Dict, Optional
from pydantic import BaseModel


class Externality(BaseModel):
    id: str
    description: str
    type: str  # 'positive' or 'negative'
    magnitude: float  # Impact score (-1.0 to 1.0)
    beneficiaries: Optional[int] = None
    harmed_parties: Optional[int] = None
    notes: Optional[str] = None


class ExternalityPricer:
    def __init__(self):
        self.registry: Dict[str, Externality] = {}

    def register(self, ext: Externality):
        if ext.id in self.registry:
            raise ValueError(f"Externality {ext.id} already exists.")
        self.registry[ext.id] = ext
        self._log(ext)

    def value_score(self, ext_id: str) -> float:
        ext = self.registry.get(ext_id)
        if not ext:
            raise KeyError(f"No such externality: {ext_id}")
        return ext.magnitude * (1 + (ext.beneficiaries or 0) - (ext.harmed_parties or 0))

    def _log(self, ext: Externality):
        print(f"[REGISTERED] {ext.type.upper()} externality '{ext.description}' "
              f"with magnitude {ext.magnitude}")


if __name__ == "__main__":
    pricer = ExternalityPricer()
    example_pos = Externality(
        id="pos001",
        description="Improved access to public knowledge",
        type="positive",
        magnitude=0.85,
        beneficiaries=120
    )
    pricer.register(example_pos)
    print("Value score:", pricer.value_score("pos001"))
