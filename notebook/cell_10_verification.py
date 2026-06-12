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
