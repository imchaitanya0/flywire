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
