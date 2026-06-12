# ===== CELL 4: Graph Class + Data Loading =====

class ConnectomeGraph:
    """
    Memory-efficient directed graph using adjacency sets.
    
    We avoid full NetworkX DiGraph for storage (uses ~500 bytes/edge overhead).
    Instead, dict-of-sets uses ~50 bytes/edge. For 24M total edges across
    5 datasets, this saves ~10 GB of RAM.
    
    NetworkX is used ONLY for final isomorphism verification on small subgraphs.
    """
    
    def __init__(self, name):
        self.name = name
        self.succ = {}   # node -> set of successors (outgoing edges)
        self.pred = {}   # node -> set of predecessors (incoming edges)
        self.nodes = set()
        self._n_edges = 0
    
    @classmethod
    def from_csv(cls, name, filepath):
        """Load a connectome edge list CSV into memory-efficient representation."""
        g = cls(name)
        
        print(f"  Loading {name}...", end=" ", flush=True)
        t0 = time.time()
        
        # Read CSV
        df = pd.read_csv(filepath)
        df.columns = ['src', 'tgt']
        
        # Clean: remove duplicates and self-loops
        n_raw = len(df)
        df = df.drop_duplicates()
        df = df[df['src'] != df['tgt']]
        n_clean = len(df)
        
        # Build adjacency using pandas groupby (vectorized, fast)
        succ_groups = df.groupby('src')['tgt'].apply(set).to_dict()
        pred_groups = df.groupby('tgt')['src'].apply(set).to_dict()
        
        g._n_edges = n_clean
        del df
        gc.collect()
        
        # Store adjacency
        g.succ = succ_groups
        g.pred = pred_groups
        g.nodes = set(succ_groups.keys()) | set(pred_groups.keys())
        
        # Ensure every node has entries in both dicts
        for n in g.nodes:
            g.succ.setdefault(n, set())
            g.pred.setdefault(n, set())
        
        elapsed = time.time() - t0
        removed = n_raw - n_clean
        print(f"✅ {elapsed:.1f}s | {len(g.nodes):,} nodes, {n_clean:,} edges"
              + (f" (removed {removed:,} dupes/self-loops)" if removed > 0 else ""))
        return g
    
    @property
    def n_nodes(self):
        return len(self.nodes)
    
    @property
    def n_edges(self):
        return self._n_edges
    
    def in_degree(self, n):
        return len(self.pred.get(n, set()))
    
    def out_degree(self, n):
        return len(self.succ.get(n, set()))
    
    def has_edge(self, u, v):
        return v in self.succ.get(u, set())
    
    def density(self):
        n = self.n_nodes
        if n <= 1:
            return 0.0
        return self.n_edges / (n * (n - 1))
    
    def degree_stats(self):
        in_degs = [len(self.pred[n]) for n in self.nodes]
        out_degs = [len(self.succ[n]) for n in self.nodes]
        return {
            'avg_in': np.mean(in_degs) if in_degs else 0,
            'avg_out': np.mean(out_degs) if out_degs else 0,
            'max_in': max(in_degs) if in_degs else 0,
            'max_out': max(out_degs) if out_degs else 0,
        }

print("✅ Graph class defined")
