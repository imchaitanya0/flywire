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
