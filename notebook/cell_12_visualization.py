# ===== CELL 12: Visualization =====

print("=" * 70)
print("PHASE 7: Circuit visualization")
print("=" * 70)

if circuit_nx is not None and len(overall_best) > 0:
    a_name, b_name, c_name = overall_best_triplet
    n = len(overall_best)
    
    # --- Figure 1: Network graph of the shared circuit ---
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    
    # Layout
    if n <= 8:
        pos = nx.circular_layout(circuit_nx)
    elif n <= 20:
        pos = nx.kamada_kawai_layout(circuit_nx)
    else:
        pos = nx.spring_layout(circuit_nx, seed=42, k=2.5/np.sqrt(n))
    
    # Compute node properties for sizing
    in_degs = dict(circuit_nx.in_degree())
    out_degs = dict(circuit_nx.out_degree())
    total_degs = {n: in_degs[n] + out_degs[n] for n in circuit_nx.nodes()}
    
    node_sizes = [300 + total_degs[n] * 100 for n in circuit_nx.nodes()]
    
    # Color by in/out balance (blue = more inputs, red = more outputs)
    balance = []
    for node in circuit_nx.nodes():
        total = total_degs[node]
        if total > 0:
            b = (out_degs[node] - in_degs[node]) / total
        else:
            b = 0
        balance.append(b)
    
    # Draw edges
    nx.draw_networkx_edges(circuit_nx, pos, ax=ax,
                           edge_color='#4a90d9',
                           arrows=True,
                           arrowsize=20,
                           arrowstyle='-|>',
                           width=2,
                           alpha=0.7,
                           connectionstyle='arc3,rad=0.1',
                           min_source_margin=15,
                           min_target_margin=15)
    
    # Draw nodes
    nodes = nx.draw_networkx_nodes(circuit_nx, pos, ax=ax,
                                    node_size=node_sizes,
                                    node_color=balance,
                                    cmap=plt.cm.RdYlBu_r,
                                    vmin=-1, vmax=1,
                                    edgecolors='white',
                                    linewidths=2)
    
    # Labels
    nx.draw_networkx_labels(circuit_nx, pos, ax=ax,
                            font_size=10,
                            font_weight='bold',
                            font_color='white')
    
    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=plt.cm.RdYlBu_r, 
                                norm=plt.Normalize(vmin=-1, vmax=1))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label('Node role: ← Input-heavy | Output-heavy →', 
                   color='white', fontsize=10)
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
    
    ax.set_title(f'Shared Neuronal Circuit (N={n})\n'
                 f'Datasets: {a_name} + {b_name} + {c_name}\n'
                 f'Edges: {circuit_nx.number_of_edges()} directed connections',
                 fontsize=16, fontweight='bold', color='white', pad=20)
    
    # Legend
    legend_elements = [
        mpatches.Patch(facecolor='#4a6fa5', label=f'N = {n} neurons'),
        mpatches.Patch(facecolor='#4a90d9', label=f'E = {circuit_nx.number_of_edges()} synaptic connections'),
    ]
    legend = ax.legend(handles=legend_elements, loc='lower left', 
                       fontsize=10, facecolor='#16213e', edgecolor='white',
                       labelcolor='white')
    
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'circuit_network_graph.png'), 
                dpi=300, bbox_inches='tight', facecolor='#1a1a2e')
    plt.show()
    print(f"  Saved: circuit_network_graph.png")
    
    # --- Figure 2: Adjacency matrix heatmap ---
    if n <= 50:
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.patch.set_facecolor('#1a1a2e')
        
        adj_a, adj_b, adj_c = build_adj_matrices(overall_best,
            graphs[a_name], graphs[b_name], graphs[c_name])
        
        for ax, adj, dname in zip(axes, [adj_a, adj_b, adj_c], 
                                   [a_name, b_name, c_name]):
            ax.set_facecolor('#1a1a2e')
            im = ax.imshow(adj, cmap='YlOrRd', aspect='equal', 
                          interpolation='nearest')
            ax.set_title(f'{dname}', color='white', fontsize=14, fontweight='bold')
            ax.set_xlabel('Target neuron', color='white')
            ax.set_ylabel('Source neuron', color='white')
            ax.tick_params(colors='white')
            
            # Grid
            for i in range(n + 1):
                ax.axhline(i - 0.5, color='#333', linewidth=0.5)
                ax.axvline(i - 0.5, color='#333', linewidth=0.5)
        
        fig.suptitle(f'Adjacency Matrices — Identical Across All 3 Datasets (N={n})',
                     color='white', fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, 'adjacency_matrices.png'),
                    dpi=300, bbox_inches='tight', facecolor='#1a1a2e')
        plt.show()
        print(f"  Saved: adjacency_matrices.png")
    
    # --- Figure 3: Degree distribution of circuit nodes ---
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    
    x = np.arange(n)
    width = 0.35
    in_vals = [in_degs[i] for i in range(n)]
    out_vals = [out_degs[i] for i in range(n)]
    
    ax.bar(x - width/2, in_vals, width, label='In-degree', color='#3498db', alpha=0.8)
    ax.bar(x + width/2, out_vals, width, label='Out-degree', color='#e74c3c', alpha=0.8)
    
    ax.set_xlabel('Neuron index', color='white', fontsize=12)
    ax.set_ylabel('Degree', color='white', fontsize=12)
    ax.set_title(f'Degree Distribution of Circuit Neurons (N={n})',
                 color='white', fontsize=14, fontweight='bold')
    ax.legend(facecolor='#16213e', edgecolor='white', labelcolor='white')
    ax.tick_params(colors='white')
    ax.set_xticks(x)
    
    for spine in ax.spines.values():
        spine.set_color('#333')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'degree_distribution.png'),
                dpi=300, bbox_inches='tight', facecolor='#1a1a2e')
    plt.show()
    print(f"  Saved: degree_distribution.png")

else:
    print("  No circuit to visualize.")

print("\n✅ Phase 7 complete")
