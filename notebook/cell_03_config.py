# ===== CELL 3: Configuration =====
# ⚠️ CHANGE THIS to match your Kaggle dataset name!
DATA_DIR = '/kaggle/input/flywire-edgelists/'

# Output directory (Kaggle working directory)
OUTPUT_DIR = '/kaggle/working/'

# Dataset file mapping
FILES = {
    'BANC': 'banc_626_edge_list.csv',
    'FAFB': 'fafb_783_edge_list.csv',
    'MANC': 'manc_1.2.1_edge_list.csv',
    'MAOL': 'maol_1.1_edge_list.csv',
    'MCNS': 'mcns_0.9_edge_list.csv',
}

# Algorithm parameters
WL_ROUNDS = 2          # Weisfeiler-Leman refinement depth
TOP_K_TRIPLETS = 3     # Number of top triplets to search
GROW_TIME_LIMIT = 300  # Seconds per grow attempt
PERTURB_ROUNDS = 5     # Number of perturbation attempts after initial grow

# Verify data exists
print("📁 Checking data files...")
for name, fname in FILES.items():
    path = os.path.join(DATA_DIR, fname)
    if os.path.exists(path):
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"   ✅ {name}: {fname} ({size_mb:.1f} MB)")
    else:
        print(f"   ❌ {name}: {fname} NOT FOUND at {path}")
        print(f"      Check your DATA_DIR setting!")
