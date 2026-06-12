# ===== CELL 2: Imports =====
import pandas as pd
import numpy as np
import networkx as nx
from networkx.algorithms.isomorphism import DiGraphMatcher
from collections import defaultdict, Counter
from itertools import combinations, product
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import time
import gc
import csv
import os
import warnings
warnings.filterwarnings('ignore')

print("✅ All imports successful")
print(f"   NetworkX: {nx.__version__}")
print(f"   Pandas: {pd.__version__}")
print(f"   NumPy: {np.__version__}")
