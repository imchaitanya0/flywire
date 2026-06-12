# ===== CELL 11: CSV Output =====

print("=" * 70)
print("PHASE 6: Writing solution CSV")
print("=" * 70)

if overall_best is not None and verified:
    a_name, b_name, c_name = overall_best_triplet
    
    output_path = os.path.join(OUTPUT_DIR, 'solution.csv')
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([a_name, b_name, c_name])
        for m in overall_best:
            writer.writerow([m[0], m[1], m[2]])
    
    print(f"\n  📄 Wrote solution to: {output_path}")
    print(f"     Columns: {a_name}, {b_name}, {c_name}")
    print(f"     Rows: {len(overall_best)} (N = {len(overall_best)})")
    
    # Verify by re-reading
    print(f"\n  Verification re-read:")
    df_check = pd.read_csv(output_path)
    print(f"     Shape: {df_check.shape}")
    print(f"     Columns: {list(df_check.columns)}")
    print(f"\n  First 10 rows:")
    print(df_check.head(10).to_string(index=False))
    
    # Also print all neuron IDs for Codex lookup
    print(f"\n  {'─' * 50}")
    print(f"  Neuron IDs for FlyWire Codex lookup:")
    print(f"  {'─' * 50}")
    for col in df_check.columns:
        ids = df_check[col].tolist()
        print(f"\n  {col}: {ids}")
    
else:
    print("\n  ⚠️ No verified solution to write.")
    print("  Check search results and verification output above.")

print("\n✅ Phase 6 complete")
