# core/proofs/proof_carrying_advice.py
# Proof-Carrying Advice (PCA): every recommendation carries verifiable proofs
# that gates (consent, apophatic, externalities, harms, remembrance) are satisfied.
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import json, time, hashlib

from core.memory.anamnesis_engine import AnamnesisEngine
from core.memory.lattice import MemoryLattice
from core.ethics.harms_ledger import HarmsLedger, HarmIndex
from core.ethics.externality_pricer import ExternalityPricer, Assessment

# --------- Utilities ----------
def blake(obj: Any) -> str:
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.blake2b(s, digest_size=16).hexdigest()

# Minimal local apophatic check (Python mirror of TS guard)
FORBID_KEYS = {"ground_is","ultimate_name","final_owner","sovereign_claim"}
CONSTRAINT_ONLY = {"no_image","no_totalization","no_equivalence","no_exchange"}
def apophatic_ok(params: Dict[str, Any]) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    # explicit forbiddens
    for k in params.keys():
        if k in FORBID_KEYS:
            reasons.append(f"forbidden:{k}")
    # constraint-only must be boolean/affirmed
    for k in CONSTRAINT_ONLY:
        if k in params and params[k] not in (True, "enforced"):
            reasons.append(f"constraint_only_violation:{k}")
    return (len(reasons) == 0), reasons

# Placeholder consent checker; replace with real linear-ticket verifier if present.
def consent_ok(ctx: Dict[str, Any]) -> Tuple[bool, str]:
    c = (ctx or {}).get("consent", {})
    if c.get("valid") is True and c.get("scope") in {"self","dyad","group","org","public"}:
        return True, "consent:validated"
    return False, "consent:missing_or_invalid"

# --------- Data types ----------
@dataclass
class Proof:
    name: str
    ok: bool
    details: Dict[str, Any]
    token: str  # BLAKE2b hash of details

@dataclass
class AdviceDraft:
    id: str
    query: str
    plan: Dict[str, Any]          # free-form plan spec (used by ExternalityPricer)
    params: Dict[str, Any]        # knobs (may include apophatic/phenomenology hints)
    context: Dict[str, Any]       # includes consent info, user, scope, etc.

@dataclass
class AdviceWithProof:
    id: str
    answer: str
    risk: float
    proofs: List[Proof]
    assessment: Dict[str, Any]     # includes externalities/harms snapshots
    decided_at: float

# --------- PCA Engine ----------
class ProofCarryingAdvice:
    def __init__(self,
                 lattice: Optional[MemoryLattice] = None,
                 anamnesis: Optional[AnamnesisEngine] = None,
                 harms: Optional[HarmsLedger] = None,
                 pricer: Optional[ExternalityPricer] = None,
                 coverage_threshold: float = 0.95):
        self.lat = lattice or MemoryLattice()
        self.ae  = anamnesis or AnamnesisEngine(self.lat)
        self.hl  = harms or HarmsLedger()
        self.ep  = pricer or ExternalityPricer(coverage_threshold=coverage_threshold)
        self.coverage_threshold = coverage_threshold

    # Build proofs for an advice draft (without committing decision yet)
    def build(self, draft: AdviceDraft, answer: str) -> AdviceWithProof:
        proofs: List[Proof] = []

        # 1) Consent
        c_ok, c_msg = consent_ok(draft.context)
        proofs.append(self._mk_proof("consent", c_ok, {"msg": c_msg, "context_scope": draft.context.get("consent",{}).get("scope")}))

        # 2) Apophatic
        a_ok, a_reasons = apophatic_ok(draft.params or {})
        proofs.append(self._mk_proof("apophatic", a_ok, {"reasons": a_reasons}))

        # 3) Externalities (pricing + rollback)
        assess: Assessment = self.ep.assess({
            **(draft.plan or {}),
            "id": draft.id,
            "rollback_recipe": draft.plan.get("rollback_recipe"),
        })
        ext_ok = assess.coverage >= self.coverage_threshold and assess.rollback_ready
        proofs.append(self._mk_proof("externalities", ext_ok, {
            "coverage": assess.coverage,
            "rollback_ready": assess.rollback_ready,
            "externals": [asdict(e) for e in assess.externals]
        }))

        # 4) Harms snapshot → penalties
        hidx: HarmIndex = self.hl.compute_index()
        penalties = self.hl.penalties(hidx)
        # policy: harms acceptable if energy_penalty+grace_penalty within bound (soft gate)
        hp = penalties["energy_penalty"] + penalties["grace_penalty"]
        harms_ok = hp <= 0.75  # tunable
        proofs.append(self._mk_proof("harms_ledger", harms_ok, {
            "H": hidx.H,
            "consent_debt": hidx.consent_debt,
            "dignity_debt": hidx.dignity_debt,
            "reversibility": hidx.reversibility_score,
            "penalties": penalties
        }))

        # 5) Remembrance (RRI)
        rri = self.ae.compute_rri()
        rri_ok = rri >= 0.70  # default target; read from vows.yaml if present
        proofs.append(self._mk_proof("remembrance", rri_ok, {"RRI": rri}))

        # Summarize risk (lower is better)
        # Risk draws from externality expected costs + harms penalties; capped [0,1]
        ext_cost = sum(e.expected_cost() for e in assess.externals) if assess.externals else 0.0
        risk = min(1.0, 0.6*ext_cost + 0.4*hp)

        return AdviceWithProof(
            id=draft.id,
            answer=answer,
            risk=risk,
            proofs=proofs,
            assessment={"externalities": asdict(assess), "harms": {"penalties": penalties, "H": hidx.H}},
            decided_at=time.time()
        )

    # Commit the decision (write ledger, cite lessons)
    def commit(self, awp: AdviceWithProof, cite_lessons: Optional[List[str]] = None) -> int:
        decision = {
            "id": f"advice:{awp.id}",
            "risk": awp.risk,
            "proofs": [asdict(p) for p in awp.proofs],
            "assessment": awp.assessment,
            "ts": awp.decided_at
        }
        did = self.ae.register_decision(decision)
        if cite_lessons:
            self.ae.cite_lessons(did, cite_lessons)
        return did

    # Helper
    def _mk_proof(self, name: str, ok: bool, details: Dict[str, Any]) -> Proof:
        tok = blake({"name": name, "ok": ok, "details": details})
        return Proof(name=name, ok=ok, details=details, token=tok)
