Now here is the full explanation of every stage, what to code, and what to watch out for.

---

### The core problem, plainly stated

You have 5 directed graphs. Each node is a neuron, each edge is a synaptic connection. You want to find the largest set of N neurons such that, when you take those neurons and all edges between them in at least 3 graphs, the resulting subgraphs are structurally identical (isomorphic). The neuron IDs are different across datasets — so you're matching by  **graph structure** , not by ID.

---

### Stage 1 — Data loading

python

```python
import pandas as pd
import networkx as nx

defload_graph(path):
    df = pd.read_csv(path)
    df.columns =['src','tgt']
    df = df.drop_duplicates()# remove duplicate edges
    G = nx.DiGraph()
    G.add_edges_from(zip(df.src, df.tgt))
return G

graphs ={
'BANC': load_graph('banc.csv'),
'FAFB': load_graph('fafb.csv'),
'MANC': load_graph('manc.csv'),
'MAOL': load_graph('maol.csv'),
'MCNS': load_graph('mcns.csv'),
}
```

**Important:** BANC and FAFB use 18-digit IDs, the other three use small integers. This means you cannot match neurons by ID across datasets — you must match by structural role only.

---

### Stage 2 — Degree signature fingerprinting (the key speedup)

For every node in every graph, compute its  **degree signature** : `(in_degree, out_degree)`. Two nodes can only be matched if they have the same signature. This prunes the search space massively before any expensive isomorphism check.

python

```python
defdegree_sig(G):
return{n:(G.in_degree(n), G.out_degree(n))for n in G.nodes()}

sigs ={name: degree_sig(G)for name, G in graphs.items()}
```

Then group nodes by signature within each graph:

python

```python
from collections import defaultdict

defgroup_by_sig(sig_dict):
    groups = defaultdict(list)
for node, sig in sig_dict.items():
        groups[sig].append(node)
return groups
```

---

### Stage 3 — The search strategy (most critical part)

The naive approach of checking all possible node matchings is computationally impossible for 100MB graphs. Here's how to make it tractable:

**Step 1: Start small, grow greedily.** Don't try to find a large subgraph directly. Instead:

* Pick a "seed" — a pair of nodes (one from each graph) with the same degree signature
* Verify their immediate neighborhood structures match (1-hop neighbor signature sets)
* Greedily add one node at a time that extends the isomorphism

**Step 2: Use neighbor hashing.** For each node, compute a hash of the sorted degree signatures of its neighbors:

python

```python
import hashlib, json

defneighbor_hash(G, node, sig_dict):
    in_nb_sigs  =sorted(sig_dict[n]for n in G.predecessors(node))
    out_nb_sigs =sorted(sig_dict[n]for n in G.successors(node))
    key = json.dumps([in_nb_sigs, out_nb_sigs])
return hashlib.md5(key.encode()).hexdigest()
```

Nodes with the same neighbor hash are structurally equivalent and are the only valid matches.

**Step 3: Try all 10 dataset triplets.** There are C(5,3) = 10 possible triplets. Run the search on all of them and keep the best result.

python

```python
from itertools import combinations
triplets =list(combinations(graphs.keys(),3))
```

---

### Stage 4 — Verified isomorphism check

Once you have a candidate set of matched nodes across 3 graphs, use NetworkX's isomorphism tools to confirm:

python

```python
from networkx.algorithms import isomorphism

defverify_match(G1, G2, nodes1, nodes2):
    sub1 = G1.subgraph(nodes1)
    sub2 = G2.subgraph(nodes2)
    gm = isomorphism.DiGraphMatcher(sub1, sub2)
return gm.is_isomorphic()
```

For the final answer you also need the **explicit node mapping** (which neuron in dataset A corresponds to which in dataset B), so use `gm.isomorphisms_iter()` to extract the mapping.

---

### Stage 5 — Output CSV

python

```python
import csv

# mapping: {dataset_name: [neuron_id_1, neuron_id_2, ...]}
defwrite_csv(mapping, path):
    datasets =list(mapping.keys())
    rows =zip(*[mapping[d]for d in datasets])
withopen(path,'w')as f:
        w = csv.writer(f)
        w.writerow(datasets)
        w.writerows(rows)
```

---

### Stage 6 — Biological research (report component)

Once you have the circuit identified, go to [FlyWire Codex](https://codex.flywire.ai) and:

1. Look up each neuron ID in your chosen dataset
2. Note the **cell type** (e.g. visual projection neuron, interneuron, motor neuron)
3. Note **neurotransmitter** (GABA, acetylcholine, glutamate, etc.)
4. Check any existing **literature annotations**
5. Visualize the circuit using Codex's 3D mesh viewer (screenshot this)
6. Draw the circuit as a network graph using `matplotlib` or `pyvis`

For the report, structure it as:  **What is this circuit → What does it do → What do we know from literature → Your hypothesis** . One page, tight.

---

### Practical execution order

1. Write the data loader and degree-signature code first — run it, check node/edge counts
2. Run the neighbor-hash filtering on the most likely triplets (MANC + MAOL + MCNS are all small-integer ID graphs, so structurally they may share more — try these first)
3. Run the greedy grow search overnight if needed — set a time limit per seed
4. Validate the winning circuit with the isomorphism verifier
5. Write the CSV, then do the biological research in parallel

---

### What will impress the judges most

The instructions explicitly say "methodological rigor and clarity over circuit size." So document **why** each filtering step is correct, explain the degree-signature argument clearly, and in the biology section show genuine engagement with the neuroscience (don't just list cell types — make a hypothesis about what the circuit computes).

The trickiest part is the greedy grow search — if you want I can help you code that specifically, or help with the biology section once you've identified the circuit
