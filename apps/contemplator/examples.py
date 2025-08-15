# Minimal usage example for PCA + Shadow Twin

from core.proofs.proof_carrying_advice import ProofCarryingAdvice, AdviceDraft
from apps.contemplator.shadow_twin import ShadowTwin

pca = ProofCarryingAdvice()
twin = ShadowTwin(pca)

draft = AdviceDraft(
    id="plan:001",
    query="Should we enable autonomous inbox triage for the org?",
    plan={
        "data_kind":"personal",
        "deployment_scope":"org",
        "automation_level":"agentic",
        "environmental":"med",
        "budget_lines":{"privacy":0.9,"safety":0.8,"technical_debt":0.6}
    },
    params={"will":"Expansion", "no_image": True},
    context={"consent":{"valid": True, "scope":"org"}}
)

res = twin.contemplate(draft, primary_answer="Enable, but gate with reversible micro-moves.")
print("Selection:", res.selection)
print("Primary risk:", res.primary.risk)
print("Counter risk:", res.counter.risk)
