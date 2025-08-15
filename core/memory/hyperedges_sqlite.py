# core/memory/hyperedges_sqlite.py
# Hypergraph store for typed relations and provenance chains.
# A hyperedge connects multiple sources to multiple targets:
#   (src1, src2, ...) -[edge_type]-> (tgt1, tgt2, ...)
from __future__ import annotations
import json
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

# --- Time ----------------------------------------------------------------
def now_ts() -> int:
    """Current unix timestamp in seconds."""
    return int(time.time())

# --- Hypergraph -----------------------------------------------------------
class Hypergraph:
    """
    SQLite-backed hypergraph for:
     - Nodes (id, label, layer, payload)
     - Hyperedges (edge_type, source_ids, target_ids, payload)
     
    Typical usage:
      - add_node / find_nodes / get_node_payload
      - add_edge / get_edges / find_paths
    
    Integral to the Anamnesis memory architecture:
      - L0-L15 nodes from Memory Lattice
      - Provenance edges (one source -> multiple derived memories)
      - Re-implication edges (from vow-AR + core)
      - Consent edges (tickets)
      - Contradiction/paradox edges (internal dialectics)
    """
    
    def __init__(self, db_path: str = "data/ledger.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(exist_ok=True, parents=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
    
    def _init_schema(self) -> None:
        """Create tables if they don't exist."""
        c = self.conn.cursor()
        # Nodes table
        c.execute('''
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            layer TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_ts INTEGER NOT NULL,
            modified_ts INTEGER NOT NULL
        )
        ''')
        
        # Edges table (hyperedges)
        c.execute('''
        CREATE TABLE IF NOT EXISTS edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            edge_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_ts INTEGER NOT NULL
        )
        ''')
        
        # Edge connections (for hyperedges)
        c.execute('''
        CREATE TABLE IF NOT EXISTS edge_connections (
            edge_id INTEGER NOT NULL,
            node_id TEXT NOT NULL,
            is_source INTEGER NOT NULL, -- 1=source, 0=target
            FOREIGN KEY (edge_id) REFERENCES edges(id),
            FOREIGN KEY (node_id) REFERENCES nodes(id),
            PRIMARY KEY (edge_id, node_id, is_source)
        )
        ''')
        
        # Indices for common queries
        c.execute('CREATE INDEX IF NOT EXISTS idx_nodes_layer ON nodes(layer)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(edge_type)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_connections_node ON edge_connections(node_id)')
        
        self.conn.commit()
    
    # --- Node operations -------------------------------------------------
    def add_node(self, item_id: str, label: str, layer: str, payload: Dict[str, Any]) -> str:
        """Add or update a node."""
        now = now_ts()
        c = self.conn.cursor()
        
        # Check if node exists
        c.execute('SELECT id FROM nodes WHERE id = ?', (item_id,))
        exists = c.fetchone() is not None
        
        if exists:
            c.execute('''
            UPDATE nodes SET 
                label = ?,
                layer = ?,
                payload = ?,
                modified_ts = ?
            WHERE id = ?
            ''', (label, layer, json.dumps(payload), now, item_id))
        else:
            c.execute('''
            INSERT INTO nodes (id, label, layer, payload, created_ts, modified_ts)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (item_id, label, layer, json.dumps(payload), now, now))
        
        self.conn.commit()
        return item_id
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node by ID."""
        c = self.conn.cursor()
        c.execute('SELECT * FROM nodes WHERE id = ?', (node_id,))
        row = c.fetchone()
        if row is None:
            return None
        return dict(row)
    
    def get_node_payload(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node's payload by ID."""
        c = self.conn.cursor()
        c.execute('SELECT payload FROM nodes WHERE id = ?', (node_id,))
        row = c.fetchone()
        if row is None:
            return None
        return json.loads(row['payload'])
    
    def find_nodes(self, layer: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Find nodes, optionally filtered by layer."""
        c = self.conn.cursor()
        if layer:
            c.execute('''
            SELECT * FROM nodes 
            WHERE layer = ? 
            ORDER BY modified_ts DESC
            LIMIT ?
            ''', (layer, limit))
        else:
            c.execute('''
            SELECT * FROM nodes 
            ORDER BY modified_ts DESC
            LIMIT ?
            ''', (limit,))
        
        return [dict(row) for row in c.fetchall()]
    
    # --- Edge operations -------------------------------------------------
    def add_edge(self, 
                edge_type: str,
                source_ids: List[str],
                target_ids: List[str],
                payload: Dict[str, Any]) -> int:
        """Add a hyperedge connecting source nodes to target nodes."""
        now = now_ts()
        c = self.conn.cursor()
        
        # Insert edge
        c.execute('''
        INSERT INTO edges (edge_type, payload, created_ts)
        VALUES (?, ?, ?)
        ''', (edge_type, json.dumps(payload), now))
        
        edge_id = c.lastrowid
        assert edge_id is not None
        
        # Add source connections
        for src_id in source_ids:
            c.execute('''
            INSERT INTO edge_connections (edge_id, node_id, is_source)
            VALUES (?, ?, 1)
            ''', (edge_id, src_id))
        
        # Add target connections
        for tgt_id in target_ids:
            c.execute('''
            INSERT INTO edge_connections (edge_id, node_id, is_source)
            VALUES (?, ?, 0)
            ''', (edge_id, tgt_id))
        
        self.conn.commit()
        return edge_id
    
    def get_edge(self, edge_id: int) -> Optional[Dict[str, Any]]:
        """Get a hyperedge by ID with its connections."""
        c = self.conn.cursor()
        
        # Get the edge
        c.execute('SELECT * FROM edges WHERE id = ?', (edge_id,))
        edge = c.fetchone()
        if edge is None:
            return None
        
        edge_dict = dict(edge)
        edge_dict['payload'] = json.loads(edge_dict['payload'])
        
        # Get sources
        c.execute('''
        SELECT n.* FROM nodes n
        JOIN edge_connections ec ON n.id = ec.node_id
        WHERE ec.edge_id = ? AND ec.is_source = 1
        ''', (edge_id,))
        sources = [dict(row) for row in c.fetchall()]
        
        # Get targets
        c.execute('''
        SELECT n.* FROM nodes n
        JOIN edge_connections ec ON n.id = ec.node_id
        WHERE ec.edge_id = ? AND ec.is_source = 0
        ''', (edge_id,))
        targets = [dict(row) for row in c.fetchall()]
        
        edge_dict['sources'] = sources
        edge_dict['targets'] = targets
        return edge_dict
    
    def get_edges(self, 
                edge_type: Optional[str] = None,
                around: Optional[str] = None,
                limit: int = 100) -> List[Dict[str, Any]]:
        """Get edges filtered by type and/or connected node."""
        c = self.conn.cursor()
        
        query = 'SELECT DISTINCT e.* FROM edges e'
        params: List[Any] = []
        
        if around:
            query += '''
            JOIN edge_connections ec ON e.id = ec.edge_id
            WHERE ec.node_id = ?
            '''
            params.append(around)
            
            if edge_type:
                query += ' AND e.edge_type = ?'
                params.append(edge_type)
        elif edge_type:
            query += ' WHERE e.edge_type = ?'
            params.append(edge_type)
        
        query += ' ORDER BY e.created_ts DESC LIMIT ?'
        params.append(limit)
        
        c.execute(query, params)
        edges = []
        
        for edge_row in c.fetchall():
            edge_id = edge_row['id']
            edge = dict(edge_row)
            edge['payload'] = json.loads(edge['payload'])
            
            # Get sources for this edge
            c.execute('''
            SELECT n.id FROM nodes n
            JOIN edge_connections ec ON n.id = ec.node_id
            WHERE ec.edge_id = ? AND ec.is_source = 1
            ''', (edge_id,))
            sources = [row[0] for row in c.fetchall()]
            
            # Get targets for this edge
            c.execute('''
            SELECT n.id FROM nodes n
            JOIN edge_connections ec ON n.id = ec.node_id
            WHERE ec.edge_id = ? AND ec.is_source = 0
            ''', (edge_id,))
            targets = [row[0] for row in c.fetchall()]
            
            edge['source_ids'] = sources
            edge['target_ids'] = targets
            edges.append(edge)
        
        return edges
    
    def find_paths(self, start_id: str, end_id: str, max_depth: int = 3) -> List[List[Dict[str, Any]]]:
        """Find paths between two nodes up to max_depth edges."""
        # This is a breadth-first search implementation
        visited_edges: set[int] = set()
        paths: List[List[Tuple[Dict[str, Any], bool]]] = [[({"id": start_id}, False)]]  # [(node, is_via_target)]
        found_paths: List[List[Dict[str, Any]]] = []
        
        for _ in range(max_depth):
            new_paths = []
            for path in paths:
                last_node, _ = path[-1]
                last_id = last_node["id"]
                
                # Find all edges where this node is a source
                out_edges = self._get_connected_edges(last_id, is_source=True)
                for edge in out_edges:
                    edge_id = edge["id"]
                    if edge_id in visited_edges:
                        continue
                    visited_edges.add(edge_id)
                    
                    for target_id in edge["target_ids"]:
                        target_node = self.get_node(target_id)
                        if not target_node:
                            continue
                            
                        new_path = path + [(edge, False), (target_node, False)]
                        if target_id == end_id:
                            found_paths.append([item[0] for item in new_path])
                        else:
                            new_paths.append(new_path)
                
                # Find all edges where this node is a target
                in_edges = self._get_connected_edges(last_id, is_source=False)
                for edge in in_edges:
                    edge_id = edge["id"]
                    if edge_id in visited_edges:
                        continue
                    visited_edges.add(edge_id)
                    
                    for source_id in edge["source_ids"]:
                        source_node = self.get_node(source_id)
                        if not source_node:
                            continue
                            
                        new_path = path + [(edge, True), (source_node, True)]
                        if source_id == end_id:
                            found_paths.append([item[0] for item in new_path])
                        else:
                            new_paths.append(new_path)
            
            if found_paths:
                return found_paths
            
            paths = new_paths
            if not paths:
                break
                
        return []
    
    def _get_connected_edges(self, node_id: str, is_source: bool) -> List[Dict[str, Any]]:
        """Get edges connected to a node."""
        return self.get_edges(around=node_id)
        
    # --- Backup / maintenance --------------------------------------------
    def backup(self, target_path: Optional[str] = None) -> str:
        """Create a backup of the DB."""
        import shutil
        from datetime import datetime
        
        if not target_path:
            dt = datetime.now().strftime('%Y%m%d_%H%M%S')
            target_path = f"{self.db_path}.backup_{dt}"
        
        self.conn.commit()  # Ensure all changes are written
        shutil.copy2(self.db_path, target_path)
        return target_path
    
    def close(self) -> None:
        """Close the connection."""
        self.conn.close()
        
    def __del__(self) -> None:
        """Ensure connection is closed on garbage collection."""
        try:
            self.conn.close()
        except:
            pass

# --- Test -----------------------------------------------------------------
if __name__ == "__main__":
    # Quick smoke test
    hg = Hypergraph(":memory:")  # In-memory for testing
    
    # Add some nodes
    hg.add_node("A", "Source", "L0", {"data": "source node"})
    hg.add_node("B", "Target1", "L1", {"data": "target node 1"})
    hg.add_node("C", "Target2", "L1", {"data": "target node 2"})
    
    # Add an edge
    edge_id = hg.add_edge(
        edge_type="derives",
        source_ids=["A"],
        target_ids=["B", "C"],
        payload={"reason": "test"}
    )
    
    # Get the edge
    edge = hg.get_edge(edge_id)
    print(f"Edge {edge_id}: {edge['edge_type']} with {len(edge['sources'])} sources and {len(edge['targets'])} targets")
