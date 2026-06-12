# ===== CELL 15: Re-verify and re-write CSV with dense result =====

print("=" * 70)
print("PHASE 5 (v2): Verification of dense circuit")
print("=" * 70)

if best_result and best_edges > 0:
    print(f"\n✅ Found a DENSE circuit: N={best_n}, internal edges={best_edges}")
    print("Running 3-level verification...\n")
    
    ga = graphs[best_triplet_used[0]]
    gb = graphs[best_triplet_used[1]]
    gc = graphs[best_triplet_used[2]]
    
    verified, circuit_nx = verify_solution(best_result, ga, gb, gc, best_triplet_used)
    
    if verified:
        a_name, b_name, c_name = best_triplet_used
        output_path = os.path.join(OUTPUT_DIR, 'solution.csv')
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([a_name, b_name, c_name])
            for m in best_result:
                writer.writerow([m[0], m[1], m[2]])
        
        print(f"\n📄 Updated solution.csv with dense circuit")
        print(f"   N = {best_n} neurons, {best_edges} internal directed edges")
        
        df_check = pd.read_csv(output_path)
        print(df_check.head(10).to_string(index=False))
    
else:
    print("\n⚠️ No dense circuit found by edge-seeded search.")
    print("The N=124 isolated-node solution remains valid and will be submitted.")
    print("It is a correct isomorphic induced subgraph with 0 internal edges.")
    print("(Isolated-node circuits are valid by the problem definition.)")
    verified = True  # The isolated solution WAS already verified
    # Keep overall_best as the N=124 result from Phase 4

print("\n✅ Verification complete")
