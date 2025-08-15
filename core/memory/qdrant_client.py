# core/memory/qdrant_client.py
# Minimal Qdrant HTTP client wrapper (Apple Silicon friendly). Provides:
#  - ensure_collection(name, size)
#  - upsert_vectors(name, [(id, vector, payload)])
#  - search(name, query_vector, k)
from __future__ import annotations
from typing import Any, Dict, List, Tuple
import requests

class QdrantNotAvailable(Exception):
    pass

class QdrantClientLite:
    def __init__(self, url: str = "http://127.0.0.1:6333", timeout: float = 3.0):
        self.url = url.rstrip("/")
        self.timeout = timeout

    # --- Collections ---------------------------------------------------------
    def ensure_collection(self, name: str, vector_size: int, distance: str = "Cosine") -> None:
        try:
            r = requests.get(f"{self.url}/collections/{name}", timeout=self.timeout)
            if r.status_code == 200:
                return
        except Exception as e:
            raise QdrantNotAvailable(str(e))
        spec = {
            "vectors": {"size": vector_size, "distance": distance},
            "optimizers_config": {"default_segment_number": 2}
        }
        try:
            cr = requests.put(f"{self.url}/collections/{name}", json=spec, timeout=self.timeout)
            if cr.status_code not in (200, 201):
                raise QdrantNotAvailable(f"Create collection failed: {cr.text}")
        except Exception as e:
            raise QdrantNotAvailable(str(e))

    # --- Upsert --------------------------------------------------------------
    def upsert_vectors(self, name: str, points: List[Tuple[str, List[float], Dict[str, Any]]]) -> None:
        payload = {"points": [{"id": pid, "vector": vec, "payload": pl} for (pid, vec, pl) in points]}
        try:
            r = requests.put(f"{self.url}/collections/{name}/points", json=payload, timeout=self.timeout)
            if r.status_code not in (200, 202):
                raise QdrantNotAvailable(f"Upsert failed: {r.text}")
        except Exception as e:
            raise QdrantNotAvailable(str(e))

    # --- Search --------------------------------------------------------------
    def search(self, name: str, query_vector: List[float], k: int = 8) -> List[Tuple[str, float, Dict[str, Any]]]:
        body = {"vector": query_vector, "limit": k, "with_payload": True}
        try:
            r = requests.post(f"{self.url}/collections/{name}/points/search", json=body, timeout=self.timeout)
            if r.status_code != 200:
                raise QdrantNotAvailable(f"Search failed: {r.text}")
            data = r.json()
            out: List[Tuple[str, float, Dict[str, Any]]] = []
            for hit in data.get("result", []):
                pid = hit.get("id")
                score = float(hit.get("score", 0.0))  # similarity or distance depending on config
                payload = hit.get("payload", {}) or {}
                out.append((str(pid), score, payload))
            return out
        except Exception as e:
            raise QdrantNotAvailable(str(e))
