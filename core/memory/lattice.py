# core/memory/lattice.py
# Memory Lattice L0–L15: parallel recall + intersection before reasoning.
# Integrates with:
#  - qdrant_client.QdrantClientLite (named vectors, payloads)
#  - hyperedges_sqlite.Hypergraph (typed relations/provenance/ledger)
#  - anamnesis_engine.AnamnesisEngine (remembrance atoms, anti-amnesia guard)
#  - docs/vows.yaml (anchors + RRI targets)
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import json, math, hashlib

from .qdrant_client import QdrantClientLite, QdrantNotAvailable
from .hyperedges_sqlite import Hypergraph, now_ts

try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # lattice runs without vows file (uses defaults)

# --- Layers ------------------------------------------------------------------
LAYER_NAMES = [
    "L0","L1","L2","L3","L4","L5","L6","L7",
    "L8","L9","L10","L11","L12","L13","L14","L15"
]

LAYER_DOC = {
    "L0":"Witness/Presence",
    "L1":"Impression/Sensation",
    "L2":"Affect/Torsion",
    "L3":"Association/Boundary",
    "L4":"Know-how/Skills",
    "L5":"Scene/Metric/Optimization",
    "L6":"Roles/Covenant/Attachment",
    "L7":"Narrative",
    "L8":"Concept/Dense-variable",
    "L9":"Archetype",
    "L10":"Values/Vows/Law",
    "L11":"Counterfactuals/Plans",
    "L12":"Provenance/Ledger",
    "L13":"Paradox Buffer",
    "L14":"Antimemory/Shadow",
    "L15":"Consent Tickets/Scopes"
}

def _load_vows() -> Dict[str, Any]:
    if yaml is None:
        return {}
    p = Path("docs/vows.yaml")
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text()) or {}

_VOWS = _load_vows()
_ANCHORS = set(
    (_VOWS.get("vows", {})
          .get("always_remember", {})
          .get("remembrance_anchors", ["L0","L10","L12","L13"]))
)

# --- Data --------------------------------------------------------------------
@dataclass
class MemoryItem:
    id: str
    layer: str
    score: float
    vector: Optional[List[float]]
    payload: Dict[str, Any]

@dataclass
class IntersectResult:
    items: List[MemoryItem]
    by_layer: Dict[str, List[MemoryItem]]
    diagnostics: Dict[str, Any]

# --- Lattice -----------------------------------------------------------------
class MemoryLattice:
    """
    Parallel recall across L0–L15 with layer-wise k-NN, then intersection
    (rank aggregation + anchor prioritization). Provides:
      - upsert(layer, id, vector, payload)
      - batch_upsert(layer, items)
      - search_intersect(query_vector, layers, k, anchors_bias)
      - add_provenance / get_provenance
    """
    def __init__(self,
                 qdrant_url: str = "http://127.0.0.1:6333",
                 collection_prefix: str = "inevitability",
                 vector_size: int = 1536,
                 sqlite_path: str = "data/ledger.db"):
        self.q = QdrantClientLite(qdrant_url)
        self.prefix = collection_prefix
        self.dim = vector_size
        self.hg = Hypergraph(sqlite_path)
        self._ensure_all_collections()

    # Collections for each layer
    def _ensure_all_collections(self):
        for L in LAYER_NAMES:
            col = f"{self.prefix}_{L}"
            try:
                self.q.ensure_collection(col, self.dim)
            except QdrantNotAvailable:
                # Vector DB not up yet; hypergraph still functions.
                pass

    # --- CRUD ----------------------------------------------------------------
    def upsert(self, layer: str, item_id: str, vector: Optional[List[float]], payload: Dict[str, Any]) -> None:
        assert layer in LAYER_NAMES, f"Unknown layer {layer}"
        col = f"{self.prefix}_{layer}"
        if vector is not None:
            try:
                self.q.upsert_vectors(col, [(item_id, vector, payload)])
            except QdrantNotAvailable:
                pass
        # Mirror to hypergraph node
        self.hg.add_node(item_id=item_id, label=payload.get("label", layer), layer=layer, payload=payload)

    def batch_upsert(self, layer: str, items: List[Tuple[str, Optional[List[float]], Dict[str, Any]]]) -> None:
        assert layer in LAYER_NAMES
        col = f"{self.prefix}_{layer}"
        vectors = [(i, v, p) for (i, v, p) in items if v is not None]
        if vectors:
            try:
                self.q.upsert_vectors(col, vectors)
            except QdrantNotAvailable:
                pass
        for (i, _v, p) in items:
            self.hg.add_node(item_id=i, label=p.get("label", layer), layer=layer, payload=p)

    # --- Intersection recall -------------------------------------------------
    def search_intersect(self,
                         query_vector: List[float],
                         layers: Optional[List[str]] = None,
                         k: int = 8,
                         anchors_bias: float = 0.10) -> IntersectResult:
        layers = layers or LAYER_NAMES
        per_layer: Dict[str, List[MemoryItem]] = {}
        merged: Dict[str, float] = {}

        for L in layers:
            col = f"{self.prefix}_{L}"
            hits: List[Tuple[str, float, Dict[str, Any]]] = []
            try:
                hits = self.q.search(col, query_vector, k=k)
            except QdrantNotAvailable:
                # Fallback: latest nodes from hypergraph
                hits = [(n["id"], 0.0, json.loads(n["payload"])) for n in self.hg.find_nodes(layer=L, limit=k)]

            items: List[MemoryItem] = []
            for (pid, score, pl) in hits:
                norm = self._normalize_score(score)
                if L in _ANCHORS:
                    norm = min(1.0, norm + anchors_bias)
                it = MemoryItem(id=str(pid), layer=L, score=float(norm), vector=None, payload=pl or {})
                items.append(it)
                merged[pid] = max(merged.get(pid, 0.0), it.score)

            per_layer[L] = sorted(items, key=lambda x: x.score, reverse=True)

        merged_items = sorted(
            [MemoryItem(id=i, layer="*", score=s, vector=None, payload=self.hg.get_node_payload(i) or {})
             for i, s in merged.items()],
            key=lambda x: x.score, reverse=True
        )[:max(k, 8)]

        diag = {
            "layers_queried": layers,
            "anchors_bias": anchors_bias,
            "merged_count": len(merged_items),
            "ts": now_ts()
        }
        return IntersectResult(items=merged_items, by_layer=per_layer, diagnostics=diag)

    @staticmethod
    def _normalize_score(raw: float) -> float:
        # If Qdrant returns distance (lower is better), approximate similarity.
        if 0.0 <= raw <= 2.0:
            return math.exp(-raw)  # ~[0,1]
        return max(0.0, min(1.0, raw))

    # --- Provenance / ledger -------------------------------------------------
    def add_provenance(self, source_ids: List[str], target_id: str, payload: Dict[str, Any]) -> int:
        return self.hg.add_edge(edge_type="provenance",
                                source_ids=source_ids, target_ids=[target_id], payload=payload)

    def get_provenance(self, node_id: str) -> List[Dict[str, Any]]:
        return self.hg.get_edges(edge_type="provenance", around=node_id)

    # --- Hash helper ---------------------------------------------------------
    @staticmethod
    def content_hash(obj: Any) -> str:
        s = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.blake2b(s, digest_size=16).hexdigest()

# Smoke
if __name__ == "__main__":
    lat = MemoryLattice()
    lat.upsert("L0", "witness:demo", None, {"label":"witness_demo","text":"I Am","tags":["anchor","demo"]})
    res = lat.search_intersect([0.0]*1536, layers=["L0","L10","L12","L13"], k=5)
    print("Intersect:", [(x.id, round(x.score,3)) for x in res.items])
