# ===== CELL 16: Final Push — Chain/Path Seed Search + Larger N Attempt =====
#
# GOAL: Find a LARGER circuit than N=124.
# 
# INSIGHT: The 124-node independent set was found via degree-signature matching.
# We couldn't find dense circuits because WL-2 is too discriminative.
#
# NEW STRATEGY: 
#   1. Take the existing 124-node consistent mapping as a STARTING POINT.
#   2. Re-examine which nodes from that set share edges to EXTERNAL nodes
#      that could be added while preserving consistency.
#   3. Try expanding by looking at nodes OUTSIDE the current 124 that
#      connect to many nodes inside it (high overlap) — "bridge" nodes.
#   4. Also try: take all degree-0 WL color classes (not just singletons)
#      and try systematic enumeration for small classes (size ≤3).

import time
import gc
from collections import defaultdict
import numpy as np

print("=" * 70)
print("FINAL PUSH: Expanding the N=124 independent set")
print("=" * 70)
print(f"Start time: {time.strftime('%H:%M:%S')}")

# Recover the original N=124 mapping
# (These are stored in overall_best from Phase 4)
# overall_best = list of (a_node, b_node, c_node) tuples

ga = graphs['BANC']
gb = graphs['FAFB']
gc_g = graphs['MAOL']
triplet = ('BANC', 'FAFB', 'MAOL')
a_name, b_name, c_name = triplet

# --- Strategy 1: Find bridge nodes that connect to the 124-set ---
# A bridge node n_A is outside the current mapping but has ≥K edges to mapped nodes.
# If n_A has a consistent WL-match in B and C with the same connectivity pattern
# to their respective mapped sets, we can add the triple.

print("\nStrategy 1: Bridge node expansion from N=124 base...")

# Get the current mapping (from overall_best from Phase 4, cell 9)
# If overall_best was overwritten by cell 14/15, rebuild from known IDs
# Use the neuron IDs from the outputs

# Rebuild the mapping from cell 9's best result
# We know the mapping was 124 nodes. Let's re-run the consistency check
# on a fresh WL-0 extraction and try to grow more aggressively.

from itertools import product as iproduct

wl_round_use = 0  # Use WL-0 for broader matching

def get_wl_groups(all_colors, name, rd=0):
    colors = all_colors[name][rd]
    groups = defaultdict(list)
    for n, c in colors.items():
        groups[c].append(n)
    return groups

groups_a = get_wl_groups(all_colors, 'BANC', wl_round_use)
groups_b = get_wl_groups(all_colors, 'FAFB', wl_round_use)
groups_c = get_wl_groups(all_colors, 'MAOL', wl_round_use)

# Get all color classes with exactly 1 node in each graph (forced at WL-0)
forced_0 = []
shared_colors = set(groups_a.keys()) & set(groups_b.keys()) & set(groups_c.keys())
small_classes = {}  # color -> (list_a, list_b, list_c)

for clr in shared_colors:
    la, lb, lc = groups_a[clr], groups_b[clr], groups_c[clr]
    if len(la) == 1 and len(lb) == 1 and len(lc) == 1:
        forced_0.append((la[0], lb[0], lc[0]))
    elif len(la) <= 2 and len(lb) <= 2 and len(lc) <= 2:
        small_classes[clr] = (la, lb, lc)

print(f"  WL-0 forced matches: {len(forced_0)}")
print(f"  WL-0 small classes (≤2 per graph): {len(small_classes)}")

# Check consistency among forced matches
adj_a_f, adj_b_f, adj_c_f = build_adj_matrices(forced_0, ga, gb, gc_g)
mismatch = (adj_a_f != adj_b_f) | (adj_a_f != adj_c_f)
print(f"  Mismatches in forced set: {mismatch.sum()}")

# Keep only consistent forced matches (greedy removal)
n_f = len(forced_0)
active = np.ones(n_f, dtype=bool)
while True:
    active_idx = np.where(active)[0]
    sub = mismatch[np.ix_(active_idx, active_idx)]
    if sub.sum() == 0:
        break
    scores = sub.sum(0) + sub.sum(1)
    worst = active_idx[np.argmax(scores)]
    active[worst] = False

base_mapping = [forced_0[i] for i in range(n_f) if active[i]]
print(f"  Consistent base: {len(base_mapping)} nodes")

# --- Strategy 2: Add small-class nodes that are consistent with the base ---
print(f"\nStrategy 2: Adding small-class nodes to base...")

map_ab = {m[0]: m[1] for m in base_mapping}
map_ac = {m[0]: m[2] for m in base_mapping}
mapped_a = set(map_ab.keys())
mapped_b = set(map_ab.values())
mapped_c = set(map_ac.values())

added_from_small = 0
for clr, (la, lb, lc) in small_classes.items():
    # Try all combinations of 1 node from each
    for na in la:
        if na in mapped_a:
            continue
        for nb in lb:
            if nb in mapped_b:
                continue
            for nc in lc:
                if nc in mapped_c:
                    continue
                
                # Check consistency with all mapped nodes
                ok = True
                for a_old in mapped_a:
                    b_old = map_ab[a_old]
                    c_old = map_ac[a_old]
                    
                    if ga.has_edge(a_old, na) != gb.has_edge(b_old, nb): ok = False; break
                    if ga.has_edge(a_old, na) != gc_g.has_edge(c_old, nc): ok = False; break
                    if ga.has_edge(na, a_old) != gb.has_edge(nb, b_old): ok = False; break
                    if ga.has_edge(na, a_old) != gc_g.has_edge(nc, c_old): ok = False; break
                
                if ok:
                    map_ab[na] = nb
                    map_ac[na] = nc
                    mapped_a.add(na)
                    mapped_b.add(nb)
                    mapped_c.add(nc)
                    added_from_small += 1
                    break
            if na in mapped_a:
                break

print(f"  Added {added_from_small} nodes from small color classes")
print(f"  New total: {len(map_ab)} nodes")

# --- Strategy 3: Grow again from the expanded base ---
print(f"\nStrategy 3: Growing from expanded base ({len(map_ab)} nodes)...")

expanded_mapping = [(a, map_ab[a], map_ac[a]) for a in map_ab]
colors_a_wl = all_colors['BANC'][wl_round_use]
colors_b_wl = all_colors['FAFB'][wl_round_use]
colors_c_wl = all_colors['MAOL'][wl_round_use]

color_to_b_wl = defaultdict(list)
color_to_c_wl = defaultdict(list)
for n, c in colors_b_wl.items(): color_to_b_wl[c].append(n)
for n, c in colors_c_wl.items(): color_to_c_wl[c].append(n)

t_grow = time.time()
grow_limit = 45 * 60  # 45 minutes

pass_num = 0
while (time.time() - t_grow) < grow_limit:
    pass_num += 1
    
    mapped_a_g = set(map_ab.keys())
    mapped_b_g = set(map_ab.values())
    mapped_c_g = set(map_ac.values())
    
    frontier = set()
    for a in mapped_a_g:
        frontier.update(ga.succ.get(a, set()) - mapped_a_g)
        frontier.update(ga.pred.get(a, set()) - mapped_a_g)
    
    if not frontier:
        print(f"  No more frontier nodes — stopped at N={len(map_ab)}")
        break
    
    # Score: fewest candidates across B and C (most constrained first)
    scored = []
    for a_new in frontier:
        ca = colors_a_wl.get(a_new)
        if ca is None: continue
        nb = sum(1 for b in color_to_b_wl.get(ca,[]) if b not in mapped_b_g)
        nc = sum(1 for c in color_to_c_wl.get(ca,[]) if c not in mapped_c_g)
        if nb > 0 and nc > 0:
            scored.append((nb * nc, a_new))
    scored.sort()
    
    added = 0
    for _, a_new in scored:
        ca = colors_a_wl[a_new]
        b_cands = [b for b in color_to_b_wl.get(ca,[]) if b not in mapped_b_g]
        c_cands = [c for c in color_to_c_wl.get(ca,[]) if c not in mapped_c_g]
        
        for b_new in b_cands:
            found = False
            for c_new in c_cands:
                ok = True
                for a_old in mapped_a_g:
                    b_old = map_ab[a_old]
                    c_old = map_ac[a_old]
                    if ga.has_edge(a_old,a_new) != gb.has_edge(b_old,b_new): ok=False; break
                    if ga.has_edge(a_old,a_new) != gc_g.has_edge(c_old,c_new): ok=False; break
                    if ga.has_edge(a_new,a_old) != gb.has_edge(b_new,b_old): ok=False; break
                    if ga.has_edge(a_new,a_old) != gc_g.has_edge(c_new,c_old): ok=False; break
                if ok:
                    map_ab[a_new] = b_new
                    map_ac[a_new] = c_new
                    mapped_a_g.add(a_new)
                    mapped_b_g.add(b_new)
                    mapped_c_g.add(c_new)
                    added += 1
                    found = True
                    break
            if found: break
    
    n_now = len(map_ab)
    if added > 0:
        print(f"  Pass {pass_num}: N={n_now} (+{added}) [{time.strftime('%H:%M:%S')}]")
    else:
        print(f"  Pass {pass_num}: No progress at N={n_now}. Stopping.")
        break

final_mapping = [(a, map_ab[a], map_ac[a]) for a in map_ab]
n_internal = count_internal_edges(final_mapping, ga)

print(f"\n{'=' * 70}")
print(f"FINAL RESULT: N={len(final_mapping)}, internal edges={n_internal}")
print(f"{'=' * 70}")

# Verify and write CSV
if len(final_mapping) > 124:  # Only update if we beat the old result
    print("\nVerifying new result...")
    verified_new, circuit_new = verify_solution(final_mapping, ga, gb, gc_g, triplet)
    
    if verified_new:
        output_path = os.path.join(OUTPUT_DIR, 'solution.csv')
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([a_name, b_name, c_name])
            for m in final_mapping:
                writer.writerow([m[0], m[1], m[2]])
        
        print(f"📄 NEW BEST: solution.csv updated with N={len(final_mapping)}")
        df_check = pd.read_csv(output_path)
        print(df_check.head(5).to_string(index=False))
    else:
        print("❌ Verification failed — keeping N=124 CSV")

elif len(final_mapping) == 124:
    print("\nSame result as before (N=124). The original solution.csv is still the submission.")
    print("✅ N=124 remains your best result — SUBMIT THAT ONE.")
else:
    print(f"\nNew result (N={len(final_mapping)}) is smaller than N=124.")
    print("✅ Submit the ORIGINAL N=124 solution.csv.")

print(f"\nEnd time: {time.strftime('%H:%M:%S')}")
