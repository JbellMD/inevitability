# core/metrics/trackers.py
# Unified metric assembly + Stand/Throne-Fiber heuristics for the dash & core.

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional

from core.metrics.energy import Energy, EnergySnapshot
from core.metrics.grace import Grace, GraceSnapshot
from core.metrics.kenosis import Kenosis, KenosisSnapshot
from core.proofs.proof_carrying_advice import AdviceWithProof
from core.ethics.harms_ledger import HarmsLedger
from core.ethics.externality_pricer import Assessment
from core.memory.anamnesis_engine import AnamnesisEngine, MemoryLattice

@dataclass
class MetricBundle:
    E: EnergySnapshot
    G: GraceSnapshot
    K: KenosisSnapshot
    RRI: float
    throne_fiber: bool
    stand_recommended: bool
    notes: str

class Trackers:
    def __init__(self,
                 harms: Optional[HarmsLedger] = None,
                 energy: Optional[Energy] = None,
                 grace: Optional[Grace] = None,
                 kenosis: Optional[Kenosis] = None,
                 anam: Optional[AnamnesisEngine] = None):
        self.harms = harms or HarmsLedger()
        self.energy = energy or Energy(self.harms)
        self.grace  = grace or Grace(self.harms)
        self.kenosis = kenosis or Kenosis()
        self.anam = anam or AnamnesisEngine(MemoryLattice())

    def assemble(self, awp: AdviceWithProof, assess: Assessment) -> MetricBundle:
        # Harms index informs both E and G
        hidx = self.harms.compute_index()

        E = self.energy.from_proofs(awp, hidx)
        G = self.grace.from_assessment(awp, assess, hidx)
        K = self.kenosis.compute()
        RRI = self.anam.compute_rri()  # remembrance retention index

        throne_fiber = self._throne_fiber(E, G, K, RRI, awp)
        stand_flag   = self._stand(E, G, RRI, awp)

        return MetricBundle(E=E, G=G, K=K, RRI=RRI,
                            throne_fiber=throne_fiber,
                            stand_recommended=stand_flag,
                            notes="Metrics fused; thresholds configurable in vows/config.")

    # --- Heuristics ---
    def _stand(self, E: EnergySnapshot, G: GraceSnapshot, RRI: float, awp: AdviceWithProof) -> bool:
        # Stand if any hard rails fail OR Energy/Grace too low OR RRI below vow target
        by = {p.name: p.ok for p in awp.proofs}
        hard_fail = not (by.get("consent", False) and by.get("apophatic", False) and by.get("externalities", False))
        low_E = E.E < 0.55
        low_G = G.G < 0.55
        low_RRI = RRI < 0.70
        return bool(hard_fail or (low_E and low_G) or low_RRI)

    def _throne_fiber(self, E: EnergySnapshot, G: GraceSnapshot, K: KenosisSnapshot, RRI: float, awp: AdviceWithProof) -> bool:
        # Throne-Fiber estimate: clean rails + E,G,K ≥ 0.7 and RRI ≥ 0.7
        rails_ok = all(p.ok for p in awp.proofs if p.name in ("consent","apophatic","externalities"))
        return bool(rails_ok and E.E >= 0.70 and G.G >= 0.70 and K.K >= 0.70 and RRI >= 0.70)
