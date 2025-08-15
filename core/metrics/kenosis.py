# core/metrics/kenosis.py
# Kenosis Index — measures self-emptying readiness:
# reversible micro-moves, de-escalation choices, repair follow-through.

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional

from core.memory.hyperedges_sqlite import Hypergraph

@dataclass
class KenosisSnapshot:
    K: float
    components: Dict[str, float]
    notes: str

class Kenosis:
    def __init__(self, hg: Optional[Hypergraph] = None):
        self.hg = hg or Hypergraph("data/ledger.db")

    def compute(self, recent_limit: int = 300) -> KenosisSnapshot:
        # Scan recent ledger rows for markers:
        # - decisions with rollback recipes (externality_assessment entries)
        # - harm_repair edges following harm_event
        # - de-escalation notes in decisions (optional field)
        repairs = 0
        harms   = 0
        rb_ready= 0
        deesc   = 0
        total_d = 0

        for row in self.hg.iter_ledger_recent(limit=recent_limit):
            if row["kind"] == "harm_event":
                harms += 1
            elif row["kind"] == "externality_assessment":
                payload = row["payload"] or {}
                if payload.get("rollback_ready"):
                    rb_ready += 1
            elif row["kind"] == "decision":
                total_d += 1
                pay = row["payload"] or {}
                if str(pay).lower().find("de-escalat") >= 0:
                    deesc += 1

        # Count repair edges
        repair_edges = self.hg.get_edges(edge_type="harm_repair", around=None, limit=recent_limit)
        repairs = len(repair_edges)

        # Ratios
        harm_repair_rate = (repairs / harms) if harms else 1.0
        rollback_density = rb_ready / max(1, total_d)
        deesc_rate       = deesc / max(1, total_d)

        # Aggregate
        K = max(0.0, min(1.0, 0.45*harm_repair_rate + 0.35*rollback_density + 0.20*deesc_rate))
        comps = {
            "harm_repair_rate": round(harm_repair_rate,4),
            "rollback_density": round(rollback_density,4),
            "deescalation_rate": round(deesc_rate,4),
        }
        return KenosisSnapshot(K=K, components=comps,
                               notes="Kenosis from repair follow-through, rollback readiness, de-escalation.")
