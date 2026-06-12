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
