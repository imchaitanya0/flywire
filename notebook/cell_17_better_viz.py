# ===== CELL 17: Better Degree Distribution (Global degrees of the 259 neurons) =====
# The induced subgraph has 0 internal edges, so internal degree = 0 for all nodes.
# The biologically meaningful plot is the GLOBAL degree (in the full connectome).

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

n = len(final_mapping)

# Get global degrees from the full graphs
maol_ids = [m[2] for m in final_mapping]
banc_ids = [m[0] for m in final_mapping]
fafb_ids = [m[1] for m in final_mapping]

# MAOL global degrees
maol_in  = [gc_g.in_degree(nid)  for nid in maol_ids]
maol_out = [gc_g.out_degree(nid) for nid in maol_ids]
maol_total = [maol_in[i] + maol_out[i] for i in range(n)]

# Sort by total degree for cleaner plot
sort_idx = np.argsort(maol_total)[::-1]
maol_in_s  = [maol_in[i]  for i in sort_idx]
maol_out_s = [maol_out[i] for i in sort_idx]

# --- Figure 2: Global degree distribution ---
fig, ax = plt.subplots(1, 1, figsize=(16, 6))
fig.patch.set_facecolor('#1a1a2e')
ax.set_facecolor('#1a1a2e')

x = np.arange(n)
width = 0.4

ax.bar(x - width/2, maol_in_s,  width, label='In-degree (global)',  color='#3498db', alpha=0.85)
ax.bar(x + width/2, maol_out_s, width, label='Out-degree (global)', color='#e74c3c', alpha=0.85)

ax.set_xlabel('Neuron rank (sorted by total degree)', color='white', fontsize=12)
ax.set_ylabel('Synaptic connections (global)', color='white', fontsize=12)
ax.set_title(f'Global Degree Distribution of the 259 Matched Neurons (MAOL dataset)\n'
             f'Each neuron has a unique (in-degree, out-degree) signature — the basis for cross-dataset matching',
             color='white', fontsize=13, fontweight='bold')
ax.legend(facecolor='#16213e', edgecolor='white', labelcolor='white', fontsize=11)
ax.tick_params(colors='white')
for spine in ax.spines.values():
    spine.set_color('#444')
ax.set_xticks(x[::20])
ax.set_xticklabels(range(0, n, 20), color='white')

# Annotate stats
avg_in  = np.mean(maol_in)
avg_out = np.mean(maol_out)
max_total = max(maol_total)
ax.text(0.99, 0.97, f'Mean in-degree: {avg_in:.1f}\nMean out-degree: {avg_out:.1f}\nMax total: {max_total}',
        transform=ax.transAxes, color='white', fontsize=10,
        verticalalignment='top', horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='#16213e', alpha=0.8, edgecolor='white'))

plt.tight_layout()
plt.savefig('/kaggle/working/degree_distribution_global.png', dpi=300, bbox_inches='tight', facecolor='#1a1a2e')
plt.show()
print("✅ Saved degree_distribution_global.png")

# --- Figure 3: Degree balance scatter (in vs out) for MAOL ---
fig, ax = plt.subplots(1, 1, figsize=(9, 9))
fig.patch.set_facecolor('#1a1a2e')
ax.set_facecolor('#1a1a2e')

scatter = ax.scatter(maol_in, maol_out, 
                     c=[i/n for i in range(n)], 
                     cmap='plasma', s=60, alpha=0.85, edgecolors='white', linewidths=0.5)

# y=x line (balanced neurons)
max_val = max(max(maol_in), max(maol_out))
ax.plot([0, max_val], [0, max_val], '--', color='#888', linewidth=1.5, label='Balanced (in = out)')

ax.set_xlabel('Global in-degree (synaptic inputs received)', color='white', fontsize=12)
ax.set_ylabel('Global out-degree (synaptic outputs sent)', color='white', fontsize=12)
ax.set_title(f'Synaptic Input vs Output Balance — 259 Matched Neurons (MAOL)\n'
             f'Each point is a unique (in, out) degree signature',
             color='white', fontsize=13, fontweight='bold')
ax.tick_params(colors='white')
ax.legend(facecolor='#16213e', edgecolor='white', labelcolor='white')
for spine in ax.spines.values():
    spine.set_color('#444')

cbar = plt.colorbar(scatter, ax=ax, shrink=0.7)
cbar.set_label('Neuron index (arbitrary)', color='white')
cbar.ax.yaxis.set_tick_params(color='white')
plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')

plt.tight_layout()
plt.savefig('/kaggle/working/degree_scatter.png', dpi=300, bbox_inches='tight', facecolor='#1a1a2e')
plt.show()
print("✅ Saved degree_scatter.png")
print("\nDownload both from Kaggle Output and add to outputs/ folder.")
