# core/metrics/energy.py
# 𝓔 — Energy Integrity: measures structural cleanliness (consent, truth rails),
# harm pressure, and paradox proximity penalties. Outputs [0..1], higher is cleaner.

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

from core.ethics.harms_ledger import HarmsLedger, HarmIndex
from core.proofs.proof_carrying_advice import AdviceWithProof

@dataclass
class EnergySnapshot:
    E: float
    components: Dict[str, float]
    notes: str

class Energy:
    def __init__(self, harms: Optional[HarmsLedger] = None):
        self.harms = harms or HarmsLedger()

    def from_proofs(self, awp: AdviceWithProof, hidx: Optional[HarmIndex] = None) -> EnergySnapshot:
        # Defaults
        consent_ok = self._proof_ok(awp, "consent")
        apoph_ok   = self._proof_ok(awp, "apophatic")
        ext_ok     = self._proof_ok(awp, "externalities")

        # Harms penalties
        if hidx is None:
            hidx = self.harms.compute_index()
        penalties = self.harms.penalties(hidx)
        harm_penalty = penalties["energy_penalty"]  # 0..1

        # Base: start clean, subtract penalties and failed rails
        E = 1.0
        rail_penalty = 0.0
        if not consent_ok: rail_penalty += 0.35
        if not apoph_ok:   rail_penalty += 0.25
        if not ext_ok:     rail_penalty += 0.20
        E -= min(1.0, harm_penalty + rail_penalty + 0.15 * float(awp.risk))

        comps = {
            "rail_penalty": round(rail_penalty, 4),
            "harm_penalty": round(harm_penalty, 4),
            "risk_blend":   round(0.15 * float(awp.risk), 4),
            "consent_ok":   1.0 if consent_ok else 0.0,
            "apoph_ok":     1.0 if apoph_ok else 0.0,
            "externalities_ok": 1.0 if ext_ok else 0.0,
            "H": round(hidx.H, 4),
            "consent_debt": round(hidx.consent_debt, 4)
        }
        return EnergySnapshot(E=max(0.0, min(1.0, E)), components=comps,
                              notes="Energy derived from PCA proofs + harms penalties.")

    @staticmethod
    def _proof_ok(awp: AdviceWithProof, name: str) -> bool:
        for p in awp.proofs:
            if p.name == name:
                return bool(p.ok)
        return False
