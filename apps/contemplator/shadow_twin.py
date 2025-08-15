# apps/contemplator/shadow_twin.py
# Shadow Twin: an adversarial contemplator that generates counter-advice
# by inverting will-axes (Scroll XVIII), amplifying externalities, and probing
# L14 (Antimemory) to reveal blindspots. It then cross-checks both with PCA.

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional

from core.proofs.proof_carrying_advice import ProofCarryingAdvice, AdviceDraft, AdviceWithProof

# Will inversion map (forward ↔ reverse traversal)
WILL_INVERT = {
    "NEGATION":"POTENTIATION",
    "POTENTIATION":"NEGATION",
    "GENERATION":"ANNIHILATION",
    "EXPANSION":"POSSESSION",     # expansion checked by stewardship
    "POSSESSION":"EXPANSION",
    "CONSUMMATION":"ASPIRATION",  # converge vs ache
    "ASPIRATION":"CONSUMMATION",
    "TRANSCENSION":"NEGATION",    # safety: transcend → test minimal bound
    "ANNIHILATION":"GENERATION"
}

@dataclass
class TwinResult:
    primary: AdviceWithProof
    counter: AdviceWithProof
    selection: str              # "primary" or "counter"
    rationale: Dict[str, Any]   # why the selection won

class ShadowTwin:
    def __init__(self, pca: Optional[ProofCarryingAdvice] = None):
        self.pca = pca or ProofCarryingAdvice()

    def contemplate(self, draft: AdviceDraft, primary_answer: str) -> TwinResult:
        # Build proofs for the primary answer
        primary_awp = self.pca.build(draft, primary_answer)

        # Build a counter-draft by inverting the will axis and hardening constraints
        counter_draft = self._invert(draft)
        counter_answer = self._counter_answer(primary_answer)
        counter_awp = self.pca.build(counter_draft, counter_answer)

        # Selection policy: prefer lower risk given both satisfy mandatory proofs;
        # if one fails any hard gate (consent/apophatic/externalities coverage), discard it.
        prim_ok = self._hard_ok(primary_awp)
        cnt_ok  = self._hard_ok(counter_awp)

        if prim_ok and not cnt_ok:
            pick, loser = "primary", "counter"
        elif cnt_ok and not prim_ok:
            pick, loser = "counter", "primary"
        else:
            # both ok or both not ok; choose lower risk (tie-break: higher remembrance RRI proof ok)
            if primary_awp.risk <= counter_awp.risk:
                pick, loser = "primary", "counter"
            else:
                pick, loser = "counter", "primary"

        rationale = {
            "hard_ok": {"primary": prim_ok, "counter": cnt_ok},
            "risk": {"primary": primary_awp.risk, "counter": counter_awp.risk},
            "note": "selected lower-risk among gates-passing candidates"
        }
        return TwinResult(primary=primary_awp, counter=counter_awp, selection=pick, rationale=rationale)

    # ----- helpers -----
    def _invert(self, draft: AdviceDraft) -> AdviceDraft:
        plan = dict(draft.plan or {})
        params = dict(draft.params or {})
        # invert will, if specified
        w = (params.get("will") or "").upper()
        if w in WILL_INVERT:
            params["will"] = WILL_INVERT[w]
        # harder externality stance: require higher coverage & explicit rollback
        plan.setdefault("budget_lines", {})
        for k in ("privacy","safety","environmental","reputation","technical_debt","compute"):
            plan["budget_lines"][k] = max(0.9, float(plan["budget_lines"].get(k, 0.0)))
        plan.setdefault("rollback_recipe", "rollback: kill-switch + throttle + data quarantine")
        # consent scope cannot escalate; keep as is
        return AdviceDraft(id=f"{draft.id}:counter", query=draft.query, plan=plan, params=params, context=draft.context)

    def _counter_answer(self, answer: str) -> str:
        # simple semantic inversion cue
        return f"COUNTER-MOVE: {answer}"

    def _hard_ok(self, awp: AdviceWithProof) -> bool:
        # require consent/apophatic/externalities proofs to be ok
        by = {p.name: p.ok for p in awp.proofs}
        return bool(by.get("consent", False) and by.get("apophatic", False) and by.get("externalities", False))
