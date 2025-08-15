# core/memory/anamnesis_engine.py
# Anamnesis Engine: remembrance as core cognitive function.
# Implements the Second Vow "Always Remember", enforcing:
#  - Temporal anti-amnesia (no net forgetting)
#  - Recall reverberations (spreading activation across L0-L15)
#  - Re-implication: memories forge new connections over time
#  - Auditability through provenance chains
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
import json, time
from pathlib import Path

from .lattice import MemoryLattice, MemoryItem, IntersectResult, LAYER_NAMES, LAYER_DOC
from .hyperedges_sqlite import now_ts

try:
    import numpy as np
    from numpy.typing import NDArray
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    # Type aliases for when numpy not available
    class NDArray:  # type: ignore
        pass

# --- Settings --------------------------------------------------------------
@dataclass
class AnamnesisSettings:
    # Reverberation settings
    max_reverb_depth: int = 2  # How many hops to follow for recall spread
    reverb_decay: float = 0.3  # Score decay per hop
    
    # Re-implication settings
    reimplic_threshold: float = 0.75  # Minimum score to trigger re-implication
    max_connections_per_item: int = 5  # Maximum new connections per memory
    
    # Anti-amnesia settings
    forgetting_window_days: int = 30  # Time window for checking net forgetting
    anchor_ratio: float = 0.10  # Portion of memories to anchor
    
    # Paradox handling
    paradox_detect_threshold: float = 0.85  # Score to consider contradiction
    paradox_buffer_ttl_days: int = 7  # How long to keep paradox in L13
    
    # Cache settings
    max_cache_items: int = 1000  # Maximum items in memory cache
    
    @classmethod
    def from_yaml(cls, path: str = "config/memory.yaml") -> AnamnesisSettings:
        """Load settings from YAML, with defaults."""
        try:
            import yaml
            p = Path(path)
            if p.exists():
                data = yaml.safe_load(p.read_text())
                return cls(**data)
        except Exception:
            pass
        return cls()  # Default settings

# --- Data -----------------------------------------------------------------
@dataclass
class RemembranceAtom:
    """An atomic memory unit with recall metadata."""
    id: str
    layer: str
    content: Dict[str, Any]  # Original memory payload
    vector: Optional[List[float]]  # Embedding
    timestamp: int = field(default_factory=now_ts)
    score: float = 1.0  # Default importance
    sources: List[str] = field(default_factory=list)  # Source memory IDs

@dataclass
class RecallResult:
    """Result of a recall operation with reverberations."""
    primary: List[MemoryItem]  # Direct recall from lattice
    reverberations: Dict[str, List[MemoryItem]]  # Indirect recall
    provenance: Dict[str, List[Dict[str, Any]]]  # Memory provenance
    diagnostics: Dict[str, Any]  # Metadata

@dataclass
class ReImplicationResult:
    """Result of memory re-implication process."""
    new_edges: List[int]  # New edge IDs created
    new_memories: List[str]  # New memory IDs created
    diagnostics: Dict[str, Any]  # Processing metadata

# --- Engine ---------------------------------------------------------------
class AnamnesisEngine:
    """
    Anamnesis Engine implements the "Always Remember" vow:
    - store_memory: add a new memory to the lattice
    - recall: retrieve memories with reverberations
    - reverberate: spread activation through memory graph
    - reimplic: derive new connections/memories
    - check_amnesia: detect & prevent forgetting
    
    Used by:
    - Contemplator service for long-term memory
    - Counsel service for client session memory
    - Will Engine for action provenance
    - Decision Core for paradox buffering
    """
    
    def __init__(self,
                 lattice: Optional[MemoryLattice] = None,
                 settings: Optional[AnamnesisSettings] = None):
        """Initialize with memory lattice and settings."""
        self.lattice = lattice or MemoryLattice()
        self.settings = settings or AnamnesisSettings()
        self.cache: Dict[str, RemembranceAtom] = {}
        
    # --- Memory Storage ----------------------------------------------------
    def store_memory(self,
                    content: Dict[str, Any],
                    layer: str,
                    vector: Optional[List[float]] = None,
                    source_ids: Optional[List[str]] = None) -> str:
        """Store a new memory in the lattice with provenance."""
        # Generate ID if not provided
        mem_id = content.get("id") or f"{layer}:{self.lattice.content_hash(content)}"
        
        # Store in lattice
        self.lattice.upsert(layer, mem_id, vector, content)
        
        # Add provenance if sources provided
        if source_ids:
            self.lattice.add_provenance(
                source_ids=source_ids,
                target_id=mem_id,
                payload={"operation": "store_memory", "ts": now_ts()}
            )
        
        # Cache the memory
        self._cache_memory(RemembranceAtom(
            id=mem_id,
            layer=layer,
            content=content,
            vector=vector,
            sources=source_ids or []
        ))
        
        return mem_id
    
    def batch_store(self,
                   items: List[Tuple[Dict[str, Any], str, Optional[List[float]], Optional[List[str]]]]) -> List[str]:
        """Batch store multiple memories."""
        results = []
        for content, layer, vector, sources in items:
            mem_id = self.store_memory(content, layer, vector, sources)
            results.append(mem_id)
        return results
    
    # --- Memory Retrieval -------------------------------------------------
    def recall(self,
              query_vector: List[float],
              layers: Optional[List[str]] = None,
              k: int = 8,
              reverberate: bool = True,
              get_provenance: bool = True) -> RecallResult:
        """
        Recall memories across layers with optional reverberations.
        1. Get direct matches from the lattice
        2. If reverberate, follow connections to related memories
        3. If get_provenance, include origin chains
        """
        # Step 1: Direct lattice recall
        layers = layers or LAYER_NAMES
        res = self.lattice.search_intersect(query_vector, layers, k)
        
        reverbs: Dict[str, List[MemoryItem]] = {}
        prov: Dict[str, List[Dict[str, Any]]] = {}
        diag = {"direct_count": len(res.items), "ts": now_ts()}
        
        # Step 2: Reverberations (if requested)
        if reverberate and res.items:
            top_ids = [item.id for item in res.items[:min(3, len(res.items))]]
            reverbs = self.reverberate(top_ids, depth=self.settings.max_reverb_depth)
            diag["reverb_count"] = sum(len(items) for items in reverbs.values())
        
        # Step 3: Provenance (if requested)
        if get_provenance and res.items:
            for item in res.items:
                prov[item.id] = self.lattice.get_provenance(item.id)
        
        return RecallResult(
            primary=res.items,
            reverberations=reverbs,
            provenance=prov,
            diagnostics=diag
        )
    
    def reverberate(self, 
                   memory_ids: List[str], 
                   depth: int = 2) -> Dict[str, List[MemoryItem]]:
        """
        Follow connections to find related memories, with spreading activation.
        Returns dict mapping layer names to memories activated in that layer.
        """
        if depth <= 0 or not memory_ids:
            return {}
        
        # Get immediate connections
        connected: Dict[str, Set[str]] = {}
        reverbs: Dict[str, List[MemoryItem]] = {}
        
        for mem_id in memory_ids:
            # Get outgoing and incoming edges
            edges = self.lattice.hg.get_edges(around=mem_id)
            for edge in edges:
                edge_type = edge["edge_type"]
                all_nodes = edge["source_ids"] + edge["target_ids"]
                
                # Skip self-connections
                related = [n for n in all_nodes if n != mem_id]
                if not related:
                    continue
                
                # Group by layer
                for related_id in related:
                    node = self.lattice.hg.get_node(related_id)
                    if not node:
                        continue
                    
                    layer = node["layer"]
                    if layer not in connected:
                        connected[layer] = set()
                    connected[layer].add(related_id)
        
        # Convert to MemoryItems
        for layer, ids in connected.items():
            items = []
            for item_id in ids:
                payload = self.lattice.hg.get_node_payload(item_id) or {}
                items.append(MemoryItem(
                    id=item_id,
                    layer=layer,
                    score=self.settings.reverb_decay,  # Decayed score
                    vector=None,
                    payload=payload
                ))
            
            reverbs[layer] = items
        
        # Recurse with decaying score if more depth remains
        if depth > 1:
            next_ids = [item for layer_items in reverbs.values() 
                       for item in layer_items]
            next_reverbs = self.reverberate([i.id for i in next_ids], depth=depth-1)
            
            # Merge results with decayed scores
            for layer, items in next_reverbs.items():
                decayed_items = []
                for item in items:
                    # Further decay scores by level
                    decayed_items.append(MemoryItem(
                        id=item.id,
                        layer=item.layer,
                        score=item.score * self.settings.reverb_decay,
                        vector=item.vector,
                        payload=item.payload
                    ))
                
                if layer in reverbs:
                    reverbs[layer].extend(decayed_items)
                else:
                    reverbs[layer] = decayed_items
        
        return reverbs
    
    # --- Re-implication ---------------------------------------------------
    def reimplic(self, 
                memories: List[MemoryItem],
                max_edges: int = 10) -> ReImplicationResult:
        """
        Re-implication process: forge new connections and memories.
        This implements the creative/generative aspect of Anamnesis.
        """
        new_edge_ids = []
        new_memory_ids = []
        ts = now_ts()
        
        # Filter memories above threshold
        high_score = [m for m in memories if m.score >= self.settings.reimplic_threshold]
        if not high_score:
            return ReImplicationResult(
                new_edges=[],
                new_memories=[],
                diagnostics={"status": "no_high_score_items", "threshold": self.settings.reimplic_threshold}
            )
        
        # Group by layer
        by_layer: Dict[str, List[MemoryItem]] = {}
        for m in high_score:
            if m.layer not in by_layer:
                by_layer[m.layer] = []
            by_layer[m.layer].append(m)
        
        # Connect items within same layer (max N connections to avoid explosion)
        for layer, items in by_layer.items():
            if len(items) < 2:
                continue
                
            # Limit connections per item
            max_per_item = min(self.settings.max_connections_per_item, len(items) - 1)
            
            for i, item in enumerate(items):
                # Connect to at most max_per_item others
                for j in range(min(max_per_item, len(items) - 1)):
                    other_idx = (i + j + 1) % len(items)  # Avoid self-connection
                    other = items[other_idx]
                    
                    # Create edge
                    edge_id = self.lattice.hg.add_edge(
                        edge_type="reimplic_assoc",
                        source_ids=[item.id],
                        target_ids=[other.id],
                        payload={
                            "operation": "reimplic",
                            "scores": [item.score, other.score],
                            "ts": ts
                        }
                    )
                    new_edge_ids.append(edge_id)
                    
                    # Stop if reached max edges
                    if len(new_edge_ids) >= max_edges:
                        break
                
                # Stop if reached max edges
                if len(new_edge_ids) >= max_edges:
                    break
        
        # Create synthetic memories (layer L11 counterfactuals)
        if len(high_score) >= 2 and "L8" in by_layer:
            # Create a synthetic concept from related concepts
            concepts = by_layer.get("L8", [])
            if concepts:
                # Take up to 3 top concepts
                top_concepts = sorted(concepts, key=lambda x: x.score, reverse=True)[:3]
                
                # Create synthetic memory
                synth_payload = {
                    "label": "synthetic_concept",
                    "derived_from": [c.id for c in top_concepts],
                    "components": [c.payload.get("label", "concept") for c in top_concepts],
                    "ts": ts
                }
                
                # Store in L11 (counterfactuals/plans)
                synth_id = self.store_memory(
                    content=synth_payload,
                    layer="L11",
                    vector=None,  # No embedding yet
                    source_ids=[c.id for c in top_concepts]
                )
                new_memory_ids.append(synth_id)
        
        return ReImplicationResult(
            new_edges=new_edge_ids,
            new_memories=new_memory_ids,
            diagnostics={
                "memories_processed": len(memories),
                "high_score_count": len(high_score),
                "layers_processed": list(by_layer.keys()),
                "ts": ts
            }
        )
    
    # --- Anti-amnesia enforcement -----------------------------------------
    def check_amnesia(self) -> Dict[str, Any]:
        """
        Check for net forgetting within the time window.
        This implements the anti-amnesia guarantee of vow-AR.
        """
        now = now_ts()
        window_start = now - (self.settings.forgetting_window_days * 86400)
        
        # Count memories per layer in window
        total = 0
        by_layer: Dict[str, int] = {}
        
        for layer in LAYER_NAMES:
            nodes = self.lattice.hg.find_nodes(layer=layer)
            in_window = [n for n in nodes if n["created_ts"] >= window_start]
            by_layer[layer] = len(in_window)
            total += len(in_window)
        
        # Get L10 anchors (values/vows/laws)
        anchor_count = by_layer.get("L10", 0)
        anchor_target = max(3, int(total * self.settings.anchor_ratio))
        
        # Check if we need more anchors
        need_anchors = anchor_count < anchor_target
        
        return {
            "window_days": self.settings.forgetting_window_days,
            "total_memories": total,
            "by_layer": by_layer,
            "anchor_ratio": self.settings.anchor_ratio,
            "anchor_target": anchor_target,
            "anchor_count": anchor_count,
            "need_anchors": need_anchors,
            "ts": now
        }
    
    # --- Utility functions ------------------------------------------------
    def _cache_memory(self, mem: RemembranceAtom) -> None:
        """Add to memory cache, evicting if needed."""
        self.cache[mem.id] = mem
        
        # Evict if over limit
        if len(self.cache) > self.settings.max_cache_items:
            # Simple LRU: remove oldest items
            items = sorted(self.cache.values(), key=lambda m: m.timestamp)
            to_evict = len(items) - self.settings.max_cache_items
            for i in range(to_evict):
                if i < len(items):
                    del self.cache[items[i].id]
    
    def get_layer_info(self) -> Dict[str, str]:
        """Get documentation for memory layers."""
        return LAYER_DOC

# --- Embedding generation ------------------------------------------------
def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding for text (placeholder for real embedding)."""
    if not NUMPY_AVAILABLE:
        return None
        
    # Placeholder - in reality would call embedding API
    # For now, just hash the content to a pseudo-random vector
    import hashlib
    
    hash_obj = hashlib.sha256(text.encode("utf-8"))
    hash_bytes = hash_obj.digest()
    
    # Use the hash to seed a random generator
    seed = int.from_bytes(hash_bytes[:4], byteorder="little")
    rng = np.random.RandomState(seed)
    
    # Generate a random vector of size 1536 (typical for embeddings)
    vec: NDArray = rng.randn(1536).astype(np.float32)
    
    # Normalize to unit length
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
        
    return vec.tolist()

# --- Test ----------------------------------------------------------------
if __name__ == "__main__":
    engine = AnamnesisEngine()
    
    # Store a few test memories
    mid1 = engine.store_memory(
        {"text": "Memory is the treasury and guardian of all things.", "author": "Cicero"},
        layer="L10"
    )
    
    mid2 = engine.store_memory(
        {"text": "Memory is a way of holding onto things you love.", "source": "test"},
        layer="L7"
    )
    
    # Connect them
    edge_id = engine.lattice.hg.add_edge(
        edge_type="quotes",
        source_ids=[mid1],
        target_ids=[mid2],
        payload={"relation": "philosophical_basis"}
    )
    
    # Reverberate
    reverbs = engine.reverberate([mid1])
    print(f"Found {sum(len(items) for items in reverbs.values())} reverberations")
    
    # Test anti-amnesia
    status = engine.check_amnesia()
    print(f"Memory status: {status['total_memories']} memories, need anchors: {status['need_anchors']}")
