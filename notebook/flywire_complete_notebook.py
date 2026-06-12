# ===== CELL 2: Imports =====
import pandas as pd
import numpy as np
import networkx as nx
from networkx.algorithms.isomorphism import DiGraphMatcher
from collections import defaultdict, Counter
from itertools import combinations, product
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import time
import gc
import csv
import os
import warnings
warnings.filterwarnings('ignore')

print("✅ All imports successful")
print(f"   NetworkX: {nx.__version__}")
print(f"   Pandas: {pd.__version__}")
print(f"   NumPy: {np.__version__}")


# ===== CELL 3: Configuration =====
# ⚠️ CHANGE THIS to match your Kaggle dataset name!
DATA_DIR = '/kaggle/input/flywire-edgelists/'

# Output directory (Kaggle working directory)
OUTPUT_DIR = '/kaggle/working/'

# Dataset file mapping
FILES = {
    'BANC': 'banc_626_edge_list.csv',
    'FAFB': 'fafb_783_edge_list.csv',
    'MANC': 'manc_1.2.1_edge_list.csv',
    'MAOL': 'maol_1.1_edge_list.csv',
    'MCNS': 'mcns_0.9_edge_list.csv',
}

# Algorithm parameters
WL_ROUNDS = 2          # Weisfeiler-Leman refinement depth
TOP_K_TRIPLETS = 3     # Number of top triplets to search
GROW_TIME_LIMIT = 300  # Seconds per grow attempt
PERTURB_ROUNDS = 5     # Number of perturbation attempts after initial grow

# Verify data exists
print("📁 Checking data files...")
for name, fname in FILES.items():
    path = os.path.join(DATA_DIR, fname)
    if os.path.exists(path):
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"   ✅ {name}: {fname} ({size_mb:.1f} MB)")
    else:
        print(f"   ❌ {name}: {fname} NOT FOUND at {path}")
        print(f"      Check your DATA_DIR setting!")


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


# ===== CELL 5: Load All Graphs + Profile =====

print("=" * 70)
print("PHASE 1: Loading and profiling all 5 connectomic datasets")
print("=" * 70)

t_start = time.time()
graphs = {}
for name, filename in FILES.items():
    filepath = os.path.join(DATA_DIR, filename)
    graphs[name] = ConnectomeGraph.from_csv(name, filepath)

print(f"\nTotal loading time: {time.time() - t_start:.1f}s")

# Print summary table
print(f"\n{'─' * 75}")
print(f"{'Dataset':<8} {'Nodes':>10} {'Edges':>12} {'Density':>12} "
      f"{'Avg In':>8} {'Avg Out':>8} {'Max In':>8} {'Max Out':>8}")
print(f"{'─' * 75}")
for name in FILES.keys():
    g = graphs[name]
    s = g.degree_stats()
    print(f"{name:<8} {g.n_nodes:>10,} {g.n_edges:>12,} {g.density():>12.8f} "
          f"{s['avg_in']:>8.1f} {s['avg_out']:>8.1f} "
          f"{s['max_in']:>8,} {s['max_out']:>8,}")
print(f"{'─' * 75}")

# Memory estimate
import sys
total_nodes = sum(g.n_nodes for g in graphs.values())
total_edges = sum(g.n_edges for g in graphs.values())
print(f"\nTotal: {total_nodes:,} nodes, {total_edges:,} edges across 5 datasets")
print(f"Estimated memory: ~{total_edges * 100 / 1e9:.1f} GB")

gc.collect()
print("\n✅ Phase 1 complete")


# ===== CELL 6: Weisfeiler-Leman Structural Coloring =====

def wl_coloring(graph, max_rounds=2):
    """
    Compute Weisfeiler-Leman (WL) node coloring for a connectome graph.
    
    The WL algorithm is a classical graph invariant test that iteratively
    refines node colors based on neighborhood structure:
    
      Round 0: color(v) = (in_degree(v), out_degree(v))
      Round k: color(v) = hash(color_{k-1}(v), 
                                sorted(color_{k-1}(u) for u in predecessors(v)),
                                sorted(color_{k-1}(u) for u in successors(v)))
    
    KEY PROPERTY: Two nodes in different graphs can ONLY be isomorphically
    matched if they have the same WL color at every depth. This is a necessary
    (but not sufficient) condition, providing massive search space pruning.
    
    Returns:
        dict: {round_number: {node: color}} for rounds 0 through max_rounds
    """
    colors_by_round = {}
    
    # Round 0: degree signature (baseline fingerprint)
    color = {}
    for n in graph.nodes:
        color[n] = (graph.in_degree(n), graph.out_degree(n))
    
    colors_by_round[0] = dict(color)
    n_unique_prev = len(set(color.values()))
    print(f"    Round 0 (degree sig): {n_unique_prev:,} unique colors")
    
    # Iterative refinement
    for r in range(1, max_rounds + 1):
        t0 = time.time()
        new_color = {}
        
        for n in graph.nodes:
            # Collect neighbor colors and sort for canonical ordering
            pred_colors = tuple(sorted(color[p] for p in graph.pred[n]))
            succ_colors = tuple(sorted(color[s] for s in graph.succ[n]))
            # Hash to keep colors as compact integers
            new_color[n] = hash((color[n], pred_colors, succ_colors))
        
        color = new_color
        colors_by_round[r] = dict(color)
        
        n_unique = len(set(color.values()))
        elapsed = time.time() - t0
        print(f"    Round {r} (k-hop):    {n_unique:,} unique colors "
              f"(+{n_unique - n_unique_prev:,}) [{elapsed:.1f}s]")
        
        # Early stopping: convergence detected
        if n_unique == n_unique_prev:
            print(f"    ⚡ Converged at round {r} — stable partition reached")
            # Copy converged colors to remaining rounds
            for remaining in range(r + 1, max_rounds + 1):
                colors_by_round[remaining] = dict(color)
            break
        
        n_unique_prev = n_unique
    
    return colors_by_round


print("=" * 70)
print("PHASE 2: Weisfeiler-Leman structural node coloring")
print("=" * 70)
print(f"Running WL algorithm with {WL_ROUNDS} refinement rounds per graph...\n")

all_colors = {}  # {graph_name: {round: {node: color}}}

t_total = time.time()
for name in FILES.keys():
    g = graphs[name]
    print(f"  {name} ({g.n_nodes:,} nodes, {g.n_edges:,} edges):")
    all_colors[name] = wl_coloring(g, max_rounds=WL_ROUNDS)
    print()

print(f"Total WL coloring time: {time.time() - t_total:.1f}s")
print("✅ Phase 2 complete")


# ===== CELL 7: Triplet Ranking =====

def rank_triplets(graphs, all_colors, wl_round=2):
    """
    Systematically rank all C(5,3)=10 dataset triplets by structural overlap.
    
    We score each triplet on:
    1. Forced matches: WL colors appearing exactly once in each graph (guaranteed correspondences)
    2. Shared color classes: WL colors present in all 3 graphs (candidate match pool)
    3. Candidate nodes: Total matchable nodes across shared color classes
    
    This data-driven ranking avoids ad-hoc triplet selection and ensures
    we focus compute on the most promising combinations.
    """
    dataset_names = list(graphs.keys())
    triplets = list(combinations(dataset_names, 3))
    
    results = []
    
    for trip in triplets:
        a, b, c = trip
        
        # Use the deepest available WL round
        rd = min(wl_round, max(all_colors[a].keys()),
                 max(all_colors[b].keys()), max(all_colors[c].keys()))
        
        colors_a = all_colors[a][rd]
        colors_b = all_colors[b][rd]
        colors_c = all_colors[c][rd]
        
        # Group nodes by WL color
        groups_a = defaultdict(list)
        groups_b = defaultdict(list)
        groups_c = defaultdict(list)
        
        for n, clr in colors_a.items(): groups_a[clr].append(n)
        for n, clr in colors_b.items(): groups_b[clr].append(n)
        for n, clr in colors_c.items(): groups_c[clr].append(n)
        
        # Find colors present in ALL 3 graphs
        shared_colors = set(groups_a.keys()) & set(groups_b.keys()) & set(groups_c.keys())
        
        n_forced = 0      # Colors with exactly 1 node in each graph
        n_small = 0        # Colors with ≤5 nodes in each graph (tractable matching)
        n_candidates = 0   # Total matchable nodes
        
        for clr in shared_colors:
            na, nb, nc = len(groups_a[clr]), len(groups_b[clr]), len(groups_c[clr])
            if na == 1 and nb == 1 and nc == 1:
                n_forced += 1
            if na <= 5 and nb <= 5 and nc <= 5:
                n_small += 1
            n_candidates += min(na, nb, nc)
        
        results.append({
            'triplet': trip,
            'shared_colors': len(shared_colors),
            'forced_matches': n_forced,
            'small_classes': n_small,
            'candidate_nodes': n_candidates,
            'wl_round': rd,
        })
    
    # Sort by forced matches (primary), then small classes, then shared colors
    results.sort(key=lambda x: (x['forced_matches'], x['small_classes'], 
                                 x['shared_colors']), reverse=True)
    return results


print("=" * 70)
print("PHASE 3: Ranking all C(5,3) = 10 dataset triplets")
print("=" * 70)

triplet_ranking = rank_triplets(graphs, all_colors, wl_round=WL_ROUNDS)

print(f"\n{'Triplet':<22} {'Shared':>8} {'Forced':>8} {'Small≤5':>8} {'Candidates':>11} {'WL':>4}")
print(f"{'─' * 65}")
for i, r in enumerate(triplet_ranking):
    trip_str = "+".join(r['triplet'])
    marker = " ⭐" if i < TOP_K_TRIPLETS else ""
    print(f"{trip_str:<22} {r['shared_colors']:>8,} {r['forced_matches']:>8,} "
          f"{r['small_classes']:>8,} {r['candidate_nodes']:>11,} {r['wl_round']:>4}{marker}")

print(f"\n🎯 Top {TOP_K_TRIPLETS} triplets selected for deep search")
print("✅ Phase 3 complete")


# ===== CELL 8: Core Search Functions =====

def extract_forced_matches(all_colors, triplet, wl_round=2):
    """
    Extract forced node correspondences: nodes whose WL color appears
    exactly once in each of the 3 graphs — meaning they MUST correspond
    in any valid isomorphism involving those structural positions.
    """
    a_name, b_name, c_name = triplet
    
    rd = min(wl_round, max(all_colors[a_name].keys()),
             max(all_colors[b_name].keys()), max(all_colors[c_name].keys()))
    
    colors_a = all_colors[a_name][rd]
    colors_b = all_colors[b_name][rd]
    colors_c = all_colors[c_name][rd]
    
    groups_a, groups_b, groups_c = defaultdict(list), defaultdict(list), defaultdict(list)
    for n, c in colors_a.items(): groups_a[c].append(n)
    for n, c in colors_b.items(): groups_b[c].append(n)
    for n, c in colors_c.items(): groups_c[c].append(n)
    
    forced = []
    shared = set(groups_a.keys()) & set(groups_b.keys()) & set(groups_c.keys())
    
    for clr in shared:
        if len(groups_a[clr]) == 1 and len(groups_b[clr]) == 1 and len(groups_c[clr]) == 1:
            forced.append((groups_a[clr][0], groups_b[clr][0], groups_c[clr][0]))
    
    return forced


def extract_small_class_matches(all_colors, triplet, max_class_size=3, wl_round=2):
    """
    Extract candidate matches from small WL color classes (2-5 nodes per graph).
    Returns all possible mappings for each class (to be filtered by consistency).
    """
    a_name, b_name, c_name = triplet
    rd = min(wl_round, max(all_colors[a_name].keys()),
             max(all_colors[b_name].keys()), max(all_colors[c_name].keys()))
    
    colors_a, colors_b, colors_c = all_colors[a_name][rd], all_colors[b_name][rd], all_colors[c_name][rd]
    groups_a, groups_b, groups_c = defaultdict(list), defaultdict(list), defaultdict(list)
    for n, c in colors_a.items(): groups_a[c].append(n)
    for n, c in colors_b.items(): groups_b[c].append(n)
    for n, c in colors_c.items(): groups_c[c].append(n)
    
    shared = set(groups_a.keys()) & set(groups_b.keys()) & set(groups_c.keys())
    small_classes = {}
    for clr in shared:
        na, nb, nc = len(groups_a[clr]), len(groups_b[clr]), len(groups_c[clr])
        if 1 <= na <= max_class_size and 1 <= nb <= max_class_size and 1 <= nc <= max_class_size:
            small_classes[clr] = (groups_a[clr], groups_b[clr], groups_c[clr])
    
    return small_classes


def build_adj_matrices(mapping, ga, gb, gc):
    """
    Build adjacency matrices for the induced subgraphs defined by the mapping.
    Uses set intersection for O(degree) instead of O(N²) construction.
    """
    n = len(mapping)
    nodes_a = [m[0] for m in mapping]
    nodes_b = [m[1] for m in mapping]
    nodes_c = [m[2] for m in mapping]
    
    idx_a = {nodes_a[i]: i for i in range(n)}
    idx_b = {nodes_b[i]: i for i in range(n)}
    idx_c = {nodes_c[i]: i for i in range(n)}
    
    set_a = set(nodes_a)
    set_b = set(nodes_b)
    set_c = set(nodes_c)
    
    adj_a = np.zeros((n, n), dtype=np.int8)
    adj_b = np.zeros((n, n), dtype=np.int8)
    adj_c = np.zeros((n, n), dtype=np.int8)
    
    # O(sum_of_degrees) instead of O(N²)
    for i, na in enumerate(nodes_a):
        for neighbor in ga.succ.get(na, set()) & set_a:
            adj_a[i, idx_a[neighbor]] = 1
    
    for i, nb in enumerate(nodes_b):
        for neighbor in gb.succ.get(nb, set()) & set_b:
            adj_b[i, idx_b[neighbor]] = 1
    
    for i, nc in enumerate(nodes_c):
        for neighbor in gc.succ.get(nc, set()) & set_c:
            adj_c[i, idx_c[neighbor]] = 1
    
    return adj_a, adj_b, adj_c


def check_consistency(forced_matches, ga, gb, gc):
    """
    Find the largest subset of forced matches with consistent edge patterns.
    
    Two matches (a1↔b1↔c1) and (a2↔b2↔c2) are CONSISTENT iff:
      edge(a1,a2) in A == edge(b1,b2) in B == edge(c1,c2) in C  (both directions)
    
    We build adjacency matrices and greedily remove nodes with the most
    edge conflicts until the remaining set is fully consistent.
    """
    n = len(forced_matches)
    if n <= 1:
        return forced_matches
    
    print(f"    Building adjacency matrices for {n} forced matches...", end=" ", flush=True)
    adj_a, adj_b, adj_c = build_adj_matrices(forced_matches, ga, gb, gc)
    print("done")
    
    # Mismatch matrix: True where edges don't agree across all 3 graphs
    mismatch = (adj_a != adj_b) | (adj_a != adj_c)
    n_mismatches = mismatch.sum()
    print(f"    Total edge mismatches: {n_mismatches} / {n*(n-1)} possible edges")
    
    if n_mismatches == 0:
        print(f"    ✅ All {n} forced matches are consistent!")
        return forced_matches
    
    # Greedy removal: iteratively remove the node involved in most mismatches
    active = np.ones(n, dtype=bool)
    removed_count = 0
    
    while True:
        # Restrict to active nodes
        active_idx = np.where(active)[0]
        if len(active_idx) == 0:
            break
        
        sub_mismatch = mismatch[np.ix_(active_idx, active_idx)]
        if sub_mismatch.sum() == 0:
            break
        
        # Conflict score = row + column mismatches
        conflict_scores = sub_mismatch.sum(axis=0) + sub_mismatch.sum(axis=1)
        worst_local = np.argmax(conflict_scores)
        worst_global = active_idx[worst_local]
        
        active[worst_global] = False
        removed_count += 1
    
    consistent = [forced_matches[i] for i in range(n) if active[i]]
    print(f"    Removed {removed_count} conflicting nodes → {len(consistent)} consistent matches remain")
    
    return consistent


def grow_mapping(mapping, ga, gb, gc, all_colors, triplet, 
                 wl_round=2, time_limit=300):
    """
    Greedily grow the mapping by adding consistent neighbor nodes.
    
    Strategy:
    1. Find unmapped nodes in graph A adjacent to the current mapped set
    2. For each candidate, find WL-color-matching nodes in B and C
    3. Check full consistency (all edges and non-edges match)
    4. Add the most constrained candidates first (fewer color matches = more certain)
    
    This is a greedy heuristic — not guaranteed to find the global maximum,
    but practical for large connectomes within a time budget.
    """
    a_name, b_name, c_name = triplet
    rd = min(wl_round, max(all_colors[a_name].keys()))
    colors_a = all_colors[a_name][rd]
    colors_b = all_colors[b_name][rd]
    colors_c = all_colors[c_name][rd]
    
    # Build reverse color lookup for B and C
    color_to_b = defaultdict(list)
    color_to_c = defaultdict(list)
    for n, c in colors_b.items(): color_to_b[c].append(n)
    for n, c in colors_c.items(): color_to_c[c].append(n)
    
    # Initialize mapping dicts
    map_ab = {m[0]: m[1] for m in mapping}
    map_ac = {m[0]: m[2] for m in mapping}
    
    best_size = len(mapping)
    best_ab = dict(map_ab)
    best_ac = dict(map_ac)
    
    start_time = time.time()
    total_added = 0
    pass_num = 0
    
    while (time.time() - start_time) < time_limit:
        pass_num += 1
        added_this_pass = 0
        
        # Get frontier: unmapped nodes in A adjacent to mapped nodes
        mapped_a = set(map_ab.keys())
        mapped_b = set(map_ab.values())
        mapped_c = set(map_ac.values())
        
        frontier = set()
        for a in mapped_a:
            frontier.update(ga.succ.get(a, set()) - mapped_a)
            frontier.update(ga.pred.get(a, set()) - mapped_a)
        
        if not frontier:
            break
        
        # Score candidates by constrainedness (fewer matches = try first)
        scored = []
        for a_new in frontier:
            ca = colors_a.get(a_new)
            if ca is None:
                continue
            nb = sum(1 for b in color_to_b.get(ca, []) if b not in mapped_b)
            nc = sum(1 for c in color_to_c.get(ca, []) if c not in mapped_c)
            if nb > 0 and nc > 0:
                scored.append((nb * nc, a_new))
        
        scored.sort()  # Most constrained first
        
        for _, a_new in scored:
            if (time.time() - start_time) > time_limit:
                break
            
            ca = colors_a[a_new]
            b_cands = [b for b in color_to_b.get(ca, []) if b not in mapped_b]
            c_cands = [c for c in color_to_c.get(ca, []) if c not in mapped_c]
            
            found = False
            for b_new in b_cands:
                if found:
                    break
                for c_new in c_cands:
                    # Check consistency with ALL mapped nodes
                    consistent = True
                    for a_old in mapped_a:
                        b_old = map_ab[a_old]
                        c_old = map_ac[a_old]
                        
                        # Check edge a_old → a_new
                        ea = ga.has_edge(a_old, a_new)
                        eb = gb.has_edge(b_old, b_new)
                        ec = gc.has_edge(c_old, c_new)
                        if not (ea == eb == ec):
                            consistent = False
                            break
                        
                        # Check edge a_new → a_old
                        ea = ga.has_edge(a_new, a_old)
                        eb = gb.has_edge(b_new, b_old)
                        ec = gc.has_edge(c_new, c_old)
                        if not (ea == eb == ec):
                            consistent = False
                            break
                    
                    if consistent:
                        map_ab[a_new] = b_new
                        map_ac[a_new] = c_new
                        mapped_a.add(a_new)
                        mapped_b.add(b_new)
                        mapped_c.add(c_new)
                        added_this_pass += 1
                        total_added += 1
                        found = True
                        break
        
        current_size = len(map_ab)
        if current_size > best_size:
            best_size = current_size
            best_ab = dict(map_ab)
            best_ac = dict(map_ac)
            print(f"      Pass {pass_num}: N = {current_size} (+{added_this_pass})")
        
        if added_this_pass == 0:
            break
    
    elapsed = time.time() - start_time
    print(f"    Growth complete: {total_added} nodes added in {elapsed:.1f}s")
    
    # Convert back to list of tuples
    result = [(a, best_ab[a], best_ac[a]) for a in best_ab]
    return result


def perturb_and_regrow(mapping, ga, gb, gc, all_colors, triplet, 
                       rounds=5, remove_frac=0.15, time_limit_per=120):
    """
    Perturbation strategy to escape local optima:
    1. Remove a random fraction of the mapping
    2. Re-grow from the remaining core
    3. Keep the result if it's larger than before
    
    This is a simple but effective meta-heuristic.
    """
    best = list(mapping)
    print(f"\n    Perturbation search ({rounds} rounds, removing {remove_frac:.0%} each time):")
    
    for r in range(rounds):
        # Remove random nodes
        n_remove = max(1, int(len(best) * remove_frac))
        indices = np.random.choice(len(best), size=n_remove, replace=False)
        remaining = [best[i] for i in range(len(best)) if i not in indices]
        
        # Re-grow
        result = grow_mapping(remaining, ga, gb, gc, all_colors, triplet,
                             time_limit=time_limit_per)
        
        if len(result) > len(best):
            print(f"      Round {r+1}: ✅ Improved! N = {len(result)} (was {len(best)})")
            best = result
        else:
            print(f"      Round {r+1}: No improvement (N = {len(result)} vs {len(best)})")
    
    return best


print("✅ Core search functions defined")


# ===== CELL 9: Run Core Search on Top Triplets =====

print("=" * 70)
print("PHASE 4: Running core search on top triplets")
print("=" * 70)

overall_best = None
overall_best_triplet = None
overall_best_size = 0

for rank_idx in range(min(TOP_K_TRIPLETS, len(triplet_ranking))):
    info = triplet_ranking[rank_idx]
    triplet = info['triplet']
    a_name, b_name, c_name = triplet
    ga, gb, gc = graphs[a_name], graphs[b_name], graphs[c_name]
    
    print(f"\n{'━' * 70}")
    print(f"  Triplet #{rank_idx+1}: {a_name} + {b_name} + {c_name}")
    print(f"  Forced matches: {info['forced_matches']}, "
          f"Small classes: {info['small_classes']}, "
          f"Shared colors: {info['shared_colors']}")
    print(f"{'━' * 70}")
    
    t_triplet = time.time()
    
    # Step 1: Extract forced matches (unique WL colors)
    print(f"\n  Step 1: Extracting forced matches...")
    forced = extract_forced_matches(all_colors, triplet, wl_round=WL_ROUNDS)
    print(f"    Found {len(forced)} forced matches")
    
    if len(forced) == 0:
        # Fallback: try WL depth 1
        print(f"    No forced matches at WL depth {WL_ROUNDS}, trying depth 1...")
        forced = extract_forced_matches(all_colors, triplet, wl_round=1)
        print(f"    Found {len(forced)} forced matches at depth 1")
    
    if len(forced) == 0:
        # Fallback: try WL depth 0 (degree signatures only)
        print(f"    No forced matches at depth 1, trying depth 0 (degree sigs)...")
        forced = extract_forced_matches(all_colors, triplet, wl_round=0)
        print(f"    Found {len(forced)} forced matches at depth 0")
    
    if len(forced) == 0:
        print(f"    ⚠️ No forced matches found at any depth. Skipping triplet.")
        continue
    
    # Step 2: Check edge consistency
    print(f"\n  Step 2: Checking edge consistency...")
    consistent = check_consistency(forced, ga, gb, gc)
    
    if len(consistent) < 2:
        print(f"    ⚠️ Only {len(consistent)} consistent matches — too few. Skipping.")
        continue
    
    # Step 3: Grow the mapping
    print(f"\n  Step 3: Growing mapping from {len(consistent)} consistent matches...")
    grown = grow_mapping(consistent, ga, gb, gc, all_colors, triplet,
                         wl_round=WL_ROUNDS, time_limit=GROW_TIME_LIMIT)
    
    # Step 4: Perturbation to escape local optima (if we have enough nodes)
    if len(grown) >= 3 and PERTURB_ROUNDS > 0:
        print(f"\n  Step 4: Perturbation search...")
        grown = perturb_and_regrow(grown, ga, gb, gc, all_colors, triplet,
                                    rounds=PERTURB_ROUNDS, 
                                    remove_frac=0.15,
                                    time_limit_per=60)
    
    elapsed = time.time() - t_triplet
    print(f"\n  Result: N = {len(grown)} nodes in {elapsed:.1f}s")
    
    # Track best across all triplets
    if len(grown) > overall_best_size:
        overall_best_size = len(grown)
        overall_best = grown
        overall_best_triplet = triplet
        print(f"  🏆 New best! N = {overall_best_size}")

print(f"\n{'=' * 70}")
if overall_best is not None:
    print(f"🏆 BEST RESULT: N = {overall_best_size} in triplet "
          f"{'+'.join(overall_best_triplet)}")
else:
    print("❌ No valid circuit found across any triplet.")
print(f"{'=' * 70}")
print("✅ Phase 4 complete")


# ===== CELL 10: Verification =====

print("=" * 70)
print("PHASE 5: Rigorous isomorphism verification")
print("=" * 70)

def verify_solution(mapping, ga, gb, gc, triplet):
    """
    Independently verify that the discovered mapping defines
    mutually isomorphic directed induced subgraphs.
    
    Three-level verification:
    1. Edge-by-edge: every edge/non-edge in A matches B and C at mapped positions
    2. Edge count: all 3 induced subgraphs have identical edge counts
    3. NetworkX DiGraphMatcher: formal isomorphism test
    """
    n = len(mapping)
    a_name, b_name, c_name = triplet
    
    nodes_a = [m[0] for m in mapping]
    nodes_b = [m[1] for m in mapping]
    nodes_c = [m[2] for m in mapping]
    
    print(f"\n  Verifying circuit of N = {n} nodes across {a_name}, {b_name}, {c_name}")
    
    # Build adjacency matrices
    adj_a, adj_b, adj_c = build_adj_matrices(mapping, ga, gb, gc)
    
    # Level 1: Edge-by-edge verification
    print(f"\n  Level 1: Edge-by-edge consistency check")
    mismatches = 0
    mismatch_details = []
    for i in range(n):
        for j in range(n):
            if i != j:
                ea, eb, ec = adj_a[i,j], adj_b[i,j], adj_c[i,j]
                if not (ea == eb == ec):
                    mismatches += 1
                    if len(mismatch_details) < 5:
                        mismatch_details.append(
                            f"    pos ({i},{j}): A={ea}, B={eb}, C={ec}")
    
    if mismatches == 0:
        print(f"    ✅ All {n*(n-1)} directed pairs are consistent")
    else:
        print(f"    ❌ {mismatches} mismatches found!")
        for d in mismatch_details:
            print(d)
        return False, None
    
    # Level 2: Edge count verification
    edges_a = adj_a.sum()
    edges_b = adj_b.sum()
    edges_c = adj_c.sum()
    print(f"\n  Level 2: Edge count verification")
    print(f"    {a_name}: {edges_a} edges")
    print(f"    {b_name}: {edges_b} edges")
    print(f"    {c_name}: {edges_c} edges")
    
    if edges_a == edges_b == edges_c:
        print(f"    ✅ Edge counts match")
    else:
        print(f"    ❌ Edge count mismatch!")
        return False, None
    
    # Level 3: NetworkX formal isomorphism
    print(f"\n  Level 3: NetworkX DiGraphMatcher formal verification")
    
    # Build NX graphs using canonical indices (0..n-1)
    # Since our mapping uses the SAME index ordering, the identity
    # mapping on indices should be a valid isomorphism
    G_a = nx.DiGraph()
    G_b = nx.DiGraph()
    G_c = nx.DiGraph()
    
    for g_nx, adj in [(G_a, adj_a), (G_b, adj_b), (G_c, adj_c)]:
        g_nx.add_nodes_from(range(n))
        for i in range(n):
            for j in range(n):
                if adj[i, j]:
                    g_nx.add_edge(i, j)
    
    iso_ab = DiGraphMatcher(G_a, G_b).is_isomorphic()
    iso_ac = DiGraphMatcher(G_a, G_c).is_isomorphic()
    iso_bc = DiGraphMatcher(G_b, G_c).is_isomorphic()
    
    print(f"    {a_name} ≅ {b_name}: {iso_ab}")
    print(f"    {a_name} ≅ {c_name}: {iso_ac}")
    print(f"    {b_name} ≅ {c_name}: {iso_bc}")
    
    all_iso = iso_ab and iso_ac and iso_bc
    
    if all_iso:
        print(f"\n  ✅ ✅ ✅  FULL VERIFICATION PASSED!")
        print(f"  The {n}-node circuit is a valid isomorphic induced subgraph")
        print(f"  across {a_name}, {b_name}, and {c_name}.")
    else:
        print(f"\n  ❌ Formal isomorphism check failed!")
    
    # Print the adjacency matrix for documentation
    print(f"\n  Adjacency matrix of the shared circuit ({n}×{n}):")
    print(f"  (This matrix is IDENTICAL across all 3 datasets)\n")
    if n <= 30:
        header = "     " + " ".join(f"{i:2d}" for i in range(n))
        print(f"  {header}")
        for i in range(n):
            row = " ".join(f"{adj_a[i,j]:2d}" for j in range(n))
            print(f"  {i:3d}: {row}")
    else:
        print(f"  (Matrix too large to display, {n}×{n})")
    
    return all_iso, G_a


if overall_best is not None:
    verified, circuit_nx = verify_solution(overall_best, 
                                            graphs[overall_best_triplet[0]],
                                            graphs[overall_best_triplet[1]],
                                            graphs[overall_best_triplet[2]],
                                            overall_best_triplet)
else:
    verified = False
    circuit_nx = None
    print("No solution to verify.")

print("\n✅ Phase 5 complete")


# ===== CELL 11: CSV Output =====

print("=" * 70)
print("PHASE 6: Writing solution CSV")
print("=" * 70)

if overall_best is not None and verified:
    a_name, b_name, c_name = overall_best_triplet
    
    output_path = os.path.join(OUTPUT_DIR, 'solution.csv')
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([a_name, b_name, c_name])
        for m in overall_best:
            writer.writerow([m[0], m[1], m[2]])
    
    print(f"\n  📄 Wrote solution to: {output_path}")
    print(f"     Columns: {a_name}, {b_name}, {c_name}")
    print(f"     Rows: {len(overall_best)} (N = {len(overall_best)})")
    
    # Verify by re-reading
    print(f"\n  Verification re-read:")
    df_check = pd.read_csv(output_path)
    print(f"     Shape: {df_check.shape}")
    print(f"     Columns: {list(df_check.columns)}")
    print(f"\n  First 10 rows:")
    print(df_check.head(10).to_string(index=False))
    
    # Also print all neuron IDs for Codex lookup
    print(f"\n  {'─' * 50}")
    print(f"  Neuron IDs for FlyWire Codex lookup:")
    print(f"  {'─' * 50}")
    for col in df_check.columns:
        ids = df_check[col].tolist()
        print(f"\n  {col}: {ids}")
    
else:
    print("\n  ⚠️ No verified solution to write.")
    print("  Check search results and verification output above.")

print("\n✅ Phase 6 complete")


# ===== CELL 12: Visualization =====

print("=" * 70)
print("PHASE 7: Circuit visualization")
print("=" * 70)

if circuit_nx is not None and len(overall_best) > 0:
    a_name, b_name, c_name = overall_best_triplet
    n = len(overall_best)
    
    # --- Figure 1: Network graph of the shared circuit ---
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    
    # Layout
    if n <= 8:
        pos = nx.circular_layout(circuit_nx)
    elif n <= 20:
        pos = nx.kamada_kawai_layout(circuit_nx)
    else:
        pos = nx.spring_layout(circuit_nx, seed=42, k=2.5/np.sqrt(n))
    
    # Compute node properties for sizing
    in_degs = dict(circuit_nx.in_degree())
    out_degs = dict(circuit_nx.out_degree())
    total_degs = {n: in_degs[n] + out_degs[n] for n in circuit_nx.nodes()}
    
    node_sizes = [300 + total_degs[n] * 100 for n in circuit_nx.nodes()]
    
    # Color by in/out balance (blue = more inputs, red = more outputs)
    balance = []
    for node in circuit_nx.nodes():
        total = total_degs[node]
        if total > 0:
            b = (out_degs[node] - in_degs[node]) / total
        else:
            b = 0
        balance.append(b)
    
    # Draw edges
    nx.draw_networkx_edges(circuit_nx, pos, ax=ax,
                           edge_color='#4a90d9',
                           arrows=True,
                           arrowsize=20,
                           arrowstyle='-|>',
                           width=2,
                           alpha=0.7,
                           connectionstyle='arc3,rad=0.1',
                           min_source_margin=15,
                           min_target_margin=15)
    
    # Draw nodes
    nodes = nx.draw_networkx_nodes(circuit_nx, pos, ax=ax,
                                    node_size=node_sizes,
                                    node_color=balance,
                                    cmap=plt.cm.RdYlBu_r,
                                    vmin=-1, vmax=1,
                                    edgecolors='white',
                                    linewidths=2)
    
    # Labels
    nx.draw_networkx_labels(circuit_nx, pos, ax=ax,
                            font_size=10,
                            font_weight='bold',
                            font_color='white')
    
    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=plt.cm.RdYlBu_r, 
                                norm=plt.Normalize(vmin=-1, vmax=1))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label('Node role: ← Input-heavy | Output-heavy →', 
                   color='white', fontsize=10)
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
    
    ax.set_title(f'Shared Neuronal Circuit (N={n})\n'
                 f'Datasets: {a_name} + {b_name} + {c_name}\n'
                 f'Edges: {circuit_nx.number_of_edges()} directed connections',
                 fontsize=16, fontweight='bold', color='white', pad=20)
    
    # Legend
    legend_elements = [
        mpatches.Patch(facecolor='#4a6fa5', label=f'N = {n} neurons'),
        mpatches.Patch(facecolor='#4a90d9', label=f'E = {circuit_nx.number_of_edges()} synaptic connections'),
    ]
    legend = ax.legend(handles=legend_elements, loc='lower left', 
                       fontsize=10, facecolor='#16213e', edgecolor='white',
                       labelcolor='white')
    
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'circuit_network_graph.png'), 
                dpi=300, bbox_inches='tight', facecolor='#1a1a2e')
    plt.show()
    print(f"  Saved: circuit_network_graph.png")
    
    # --- Figure 2: Adjacency matrix heatmap ---
    if n <= 50:
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.patch.set_facecolor('#1a1a2e')
        
        adj_a, adj_b, adj_c = build_adj_matrices(overall_best,
            graphs[a_name], graphs[b_name], graphs[c_name])
        
        for ax, adj, dname in zip(axes, [adj_a, adj_b, adj_c], 
                                   [a_name, b_name, c_name]):
            ax.set_facecolor('#1a1a2e')
            im = ax.imshow(adj, cmap='YlOrRd', aspect='equal', 
                          interpolation='nearest')
            ax.set_title(f'{dname}', color='white', fontsize=14, fontweight='bold')
            ax.set_xlabel('Target neuron', color='white')
            ax.set_ylabel('Source neuron', color='white')
            ax.tick_params(colors='white')
            
            # Grid
            for i in range(n + 1):
                ax.axhline(i - 0.5, color='#333', linewidth=0.5)
                ax.axvline(i - 0.5, color='#333', linewidth=0.5)
        
        fig.suptitle(f'Adjacency Matrices — Identical Across All 3 Datasets (N={n})',
                     color='white', fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, 'adjacency_matrices.png'),
                    dpi=300, bbox_inches='tight', facecolor='#1a1a2e')
        plt.show()
        print(f"  Saved: adjacency_matrices.png")
    
    # --- Figure 3: Degree distribution of circuit nodes ---
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    
    x = np.arange(n)
    width = 0.35
    in_vals = [in_degs[i] for i in range(n)]
    out_vals = [out_degs[i] for i in range(n)]
    
    ax.bar(x - width/2, in_vals, width, label='In-degree', color='#3498db', alpha=0.8)
    ax.bar(x + width/2, out_vals, width, label='Out-degree', color='#e74c3c', alpha=0.8)
    
    ax.set_xlabel('Neuron index', color='white', fontsize=12)
    ax.set_ylabel('Degree', color='white', fontsize=12)
    ax.set_title(f'Degree Distribution of Circuit Neurons (N={n})',
                 color='white', fontsize=14, fontweight='bold')
    ax.legend(facecolor='#16213e', edgecolor='white', labelcolor='white')
    ax.tick_params(colors='white')
    ax.set_xticks(x)
    
    for spine in ax.spines.values():
        spine.set_color('#333')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'degree_distribution.png'),
                dpi=300, bbox_inches='tight', facecolor='#1a1a2e')
    plt.show()
    print(f"  Saved: degree_distribution.png")

else:
    print("  No circuit to visualize.")

print("\n✅ Phase 7 complete")


# ===== CELL 13: Summary & Report Template =====

print("=" * 70)
print("FINAL SUMMARY")
print("=" * 70)

if overall_best is not None:
    a_name, b_name, c_name = overall_best_triplet
    
    print(f"""
┌──────────────────────────────────────────────────────────┐
│  RESULT                                                  │
│                                                          │
│  Circuit size (N):     {len(overall_best):<35}│
│  Datasets:             {a_name + ', ' + b_name + ', ' + c_name:<35}│
│  Internal edges:       {circuit_nx.number_of_edges() if circuit_nx else 'N/A':<35}│
│  Verified:             {'✅ YES' if verified else '❌ NO':<35}│
│  Solution file:        solution.csv{' ' * 24}│
└──────────────────────────────────────────────────────────┘
""")
    
    print("📋 Neuron ID mapping (for Codex lookup):")
    print(f"{'Row':<5} {a_name:<25} {b_name:<25} {c_name:<25}")
    print("─" * 80)
    for i, (na, nb, nc) in enumerate(overall_best):
        print(f"{i:<5} {str(na):<25} {str(nb):<25} {str(nc):<25}")
    
    print(f"""
{'─' * 70}
NEXT STEPS FOR BIOLOGICAL REPORT:
{'─' * 70}

1. Go to https://codex.flywire.ai
2. Look up each neuron ID from ONE of the datasets above
3. Record: cell type, neurotransmitter, brain region, annotations
4. Use the visualizations saved in /kaggle/working/:
   - circuit_network_graph.png (network topology)
   - adjacency_matrices.png (edge patterns)
   - degree_distribution.png (node roles)
5. Write 1-page report (template below)

{'─' * 70}
REPORT TEMPLATE:
{'─' * 70}

# Shared Neuronal Circuit in the Drosophila Connectome

## Circuit Identification
We identified a conserved {len(overall_best)}-neuron circuit shared across 
{a_name}, {b_name}, and {c_name} datasets using Weisfeiler-Leman 
structural fingerprinting followed by greedy isomorphism growth.

## Circuit Structure
[Insert circuit_network_graph.png]
The circuit contains {circuit_nx.number_of_edges() if circuit_nx else 'N'} 
directed connections among {len(overall_best)} neurons...

## Constituent Neurons
| Neuron ID | Cell Type | Neurotransmitter | Brain Region |
|-----------|-----------|------------------|--------------|
| [fill from Codex] | | | |

## Biological Interpretation
[Description of what this circuit likely does]
[Hypothesis about its computational role]

## 3D Visualization
[Insert Codex 3D mesh screenshots]

## References
[1] ...
[2] ...
""")
    
else:
    print("No solution found. Review output above for debugging.")

print("=" * 70)
print("🎉 Pipeline complete!")
print("=" * 70)
