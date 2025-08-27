"""
PCA Store Adapter
----------------
Provides a compatibility layer between decision_core's expected store() function
and the ProofCarryingAdvice class-based API. This allows decision_core to continue
using its function-based approach while leveraging the PCA implementation.
"""

from typing import Any, Dict, Optional
import time

from core.proofs.proof_carrying_advice import ProofCarryingAdvice, AdviceDraft, AdviceWithProof, Proof

# Global PCA instance for the store function to use
_PCA = None

def get_pca() -> ProofCarryingAdvice:
    """Get or create the global PCA instance."""
    global _PCA
    if _PCA is None:
        _PCA = ProofCarryingAdvice()
    return _PCA

def store(answer: str, proofs: Any) -> str:
    """
    Hash and store proof-carrying advice; return ledger id.
    This implements the API expected by decision_core.attach_pca().
    
    Args:
        answer: The answer text
        proofs: ProofBundle or Dict containing proof information
        
    Returns:
        ledger_id: ID in the ledger for the stored advice
    """
    pca = get_pca()
    
    # Convert proofs object to format expected by PCA
    draft_id = f"decision:{int(time.time() * 1000)}"
    
    # Extract information from proofs bundle
    context = {}
    params = {}
    plan = {}
    
    if hasattr(proofs, "consent"):
        context["consent"] = proofs.consent
    
    if hasattr(proofs, "logic"):
        params["apophatic_check"] = proofs.logic.get("apophatic_ok", True)
        
    if hasattr(proofs, "ethics"):
        plan = proofs.ethics.get("plan", {})
        params["externality_priced"] = proofs.ethics.get("externality_priced", False)
        params["coverage"] = proofs.ethics.get("coverage", 0.0)
        
    if hasattr(proofs, "phenomenology"):
        params["shadow_signals"] = proofs.phenomenology.get("signals", {})
        
    # Create a draft from the available information
    draft = AdviceDraft(
        id=draft_id,
        query=context.get("query", "Decision query"),
        plan=plan,
        params=params,
        context=context
    )
    
    # Build proofs for this answer
    advice_with_proof = pca.build(draft, answer)
    
    # Commit to the ledger
    ledger_id = pca.commit(advice_with_proof)
    
    return str(ledger_id)

# Also provide direct access to store as a module-level function
# This allows `from core.proofs.proof_carrying_advice import store`
# to work as expected in decision_core.py
def init():
    """
    Initialize the module by setting up the store function in the
    proof_carrying_advice module namespace.
    """
    import core.proofs.proof_carrying_advice as pca_module
    pca_module.store = store

# Auto-initialize when imported
init()
