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
