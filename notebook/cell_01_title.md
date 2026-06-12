# FlyWire Codex Qualification Challenge — Largest Shared Neuronal Circuit

## Methodology

This notebook identifies the **largest neuronal circuit shared across ≥3 FlyWire connectomic datasets** using a rigorous, multi-stage structural fingerprinting pipeline:

1. **Load & Normalize** — Read 5 edge-list CSVs into memory-efficient adjacency representations
2. **Weisfeiler-Leman (WL) Structural Coloring** — Iteratively refine node fingerprints based on neighborhood topology (2 rounds). This is a classical graph invariant that captures local structure.
3. **Systematic Triplet Ranking** — Score all C(5,3)=10 dataset combinations by structural overlap (shared WL color classes, forced correspondences)
4. **Forced Match Extraction** — Identify nodes with *unique* WL colors across 3 datasets — these form provably correct correspondences
5. **Consistency Verification & Greedy Growth** — Remove conflicting matches, then greedily extend the mapping while preserving induced subgraph isomorphism
6. **Formal Verification** — Edge-by-edge and non-edge verification using NetworkX `DiGraphMatcher`
7. **Biological Analysis** — Interpret the circuit using FlyWire Codex metadata

### Key Design Decisions
- **WL coloring over naive degree matching**: WL captures k-hop neighborhood structure, not just local degree. This provides exponentially better pruning.
- **Forced matches first**: Nodes with unique structural fingerprints have *guaranteed* correspondences — no search needed.
- **Greedy growth with constrainedness ordering**: Candidates with fewer possible matches are tried first (most constrained first), which prunes the search tree dramatically.
- **Induced subgraph constraint**: We verify both edges AND non-edges match, ensuring true isomorphism.
