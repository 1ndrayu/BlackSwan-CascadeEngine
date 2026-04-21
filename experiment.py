import numpy as np
import random
import time
import matplotlib.pyplot as plt
from engine import RiskCube, RippleEngine
from telemetry import track_memory_drift, us_timer

def generate_random_coord(dims):
    return tuple(random.randint(0, d - 1) for d in dims)

def run_experiment():
    densities = [0.1, 0.5, 1.0, 2.0, 5.0]  # average edges per active node
    dimension_scales = [10, 50, 100, 250, 500] # Number of assets
    
    plt.figure(figsize=(12, 8))
    
    for dim_scale in dimension_scales:
        dims = (dim_scale, 20, 10, 12) # Fixed Reg=20, Scen=10, Time=12
        
        # Calculate full integer space instead of relying on np.prod to avoid warnings/overflows
        space = 1
        for d in dims: space *= d
            
        latencies = []
        
        print(f"\n--- Dimension Scale: {dims} (Total Space: {space:,}) ---")
        
        for density in densities:
            try:
                cube = RiskCube(dims, use_sparse=True)
                engine = RippleEngine(cube)
            except Exception as e:
                print(f"Failed to allocate RiskCube for dim_scale={dim_scale}, error: {e}")
                latencies.append(0)
                continue
            
            num_active_nodes = 500
            active_nodes = [generate_random_coord(dims) for _ in range(num_active_nodes)]
            
            # Build DAG
            num_links = int(num_active_nodes * density)
            for _ in range(num_links):
                src = random.choice(active_nodes)
                tgt = random.choice(active_nodes)
                # Weights strictly scaled by density to prevent diverging ripples
                weight = random.uniform(0.001, 0.5 / max(1.0, density))
                engine.add_dependency(src, tgt, weight)
                
            start_node = active_nodes[0]
            
            with track_memory_drift(label=f"Scale: {dim_scale}, Density: {density}"):
                # Trigger a ripple with a large initial value
                engine.run_ripple(start_node, 1000000.0)
                
            latencies.append(engine.run_ripple.latest_latency_us)
            print(f"Density: {density} -> Latency: {latencies[-1]:.2f} µs")
            
        plt.plot(densities, latencies, marker='o', linestyle='-', label=f"{dim_scale} Assets")
        
    plt.title("Project Black-Swan: Calculation Time vs. Linkage Density", fontsize=14, fontweight="bold")
    plt.xlabel("Linkage Density (Avg Edges per Node)", fontsize=12)
    plt.ylabel("Latency (µs)", fontsize=12)
    plt.legend(title="Dimension Scale")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    
    plt.savefig("performance_cliff.png", dpi=300)
    print("\n[SUCCESS] Plot saved to performance_cliff.png")

if __name__ == "__main__":
    run_experiment()
