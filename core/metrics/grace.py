# core/metrics/grace.py
# 𝒢 — Grace: measures aesthetic coherence, sufficiency of externality coverage,
# dignity preservation, and smoothness of plan reversibility.

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional

from core.ethics.harms_ledger import HarmsLedger, HarmIndex
from core.proofs.proof_carrying_advice import AdviceWithProof
from core.ethics.externality_pricer import Assessment

@dataclass
class GraceSnapshot:
    G: float
    components: Dict[str, float]
    notes: str

class Grace:
    def __init__(self, harms: Optional[HarmsLedger] = None, coverage_target: float = 0.95):
        self.harms = harms or HarmsLedger()
        self.coverage_target = coverage_target

    def from_assessment(self, awp: AdviceWithProof, assess: Assessment, hidx: Optional[HarmIndex]=None) -> GraceSnapshot:
        if hidx is None:
            hidx = self.harms.compute_index()
        penalties = self.harms.penalties(hidx)
        dignity_pen = penalties["grace_penalty"]  # 0..1

        # Externality coverage smoothness
        cov = float(assess.coverage or 0.0)
        cov_term = min(1.0, max(0.0, (cov - 0.5) / (self.coverage_target - 0.5))) if self.coverage_target > 0.5 else cov
        rb_bonus = 0.1 if assess.rollback_ready else -0.15

        # Aesthetic coherence proxy: lower risk and full rails → higher coherence
        rails_ok = all(p.ok for p in awp.proofs if p.name in ("consent","apophatic","externalities"))
        coherence = max(0.0, min(1.0, 1.0 - awp.risk + (0.1 if rails_ok else -0.1)))

        G = max(0.0, min(1.0, 0.55*cov_term + 0.25*coherence + rb_bonus - 0.25*dignity_pen))

        comps = {
            "coverage_term": round(cov_term,4),
            "rollback_bonus": round(rb_bonus,4),
            "coherence": round(coherence,4),
            "dignity_penalty": round(dignity_pen,4),
            "H": round(hidx.H,4),
            "dignity_debt": round(hidx.dignity_debt,4)
        }
        return GraceSnapshot(G=G, components=comps,
                             notes="Grace from coverage/coherence/rollback minus dignity pressure.")
