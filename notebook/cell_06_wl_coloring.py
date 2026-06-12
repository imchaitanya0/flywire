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
