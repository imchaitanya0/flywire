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
