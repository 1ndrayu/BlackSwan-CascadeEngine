import json
import random
import time
import sys
import numpy as np
from collections import defaultdict, deque
from typing import Tuple, Dict, List, Callable
from telemetry import us_timer
from engine import RiskCube, RippleEngine

def run_simulation(densities, dimension_scales, regions, scenarios, time_units, initial_shock, num_nodes):
    results = {
        "labels": densities,
        "datasets": []
    }
    
    total_scales = len(dimension_scales)
    total_densities = len(densities)
    
    print(f"\n[SIMULATION START] {time.strftime('%H:%M:%S')}")
    print(f"Parameters: Regions={regions}, Scenarios={scenarios}, Time Units={time_units}, Shock={initial_shock}, Ceiling={num_nodes}, Densities={densities}")
    print(f"Processing {total_scales} scales across {total_densities} density points...")
    sys.stdout.flush()

    for i, dim_scale in enumerate(dimension_scales):
        scale_start = time.time()
        print(f"\n[SCALE {i+1}/{total_scales}] Dimension: {dim_scale}")
        
        dims = (dim_scale, regions, scenarios, time_units)
        impacts = []
        
        for j, density in enumerate(densities):
            # Map density to a visual description
            density_desc = "Low" if density < 0.5 else ("Moderate" if density < 2.0 else "High")
            print(f"  > Density {density:.2f} ({density_desc}): ", end="")
            sys.stdout.flush()
            
            try:
                cube = RiskCube(dims, use_sparse=True)
                engine = RippleEngine(cube)
            except Exception as e:
                print(f"FAILED (Cube Error: {e})")
                impacts.append(0)
                continue
                
            # Topological bounds: Assets x Regions x Scenarios x Time
            max_possible_nodes = dim_scale * regions * scenarios * time_units
            actual_nodes = min(num_nodes, max_possible_nodes)
            
            if actual_nodes == 0:
                print("SKIPPED (No Nodes)")
                impacts.append(0)
                continue
                
            active_nodes = [tuple(random.randint(0, d - 1) for d in dims) for _ in range(actual_nodes)]
            # Sort for efficient temporal slicing
            active_nodes.sort(key=lambda x: x[-1])
            node_times = [n[-1] for n in active_nodes]
            
            # Temporal Linking: Connectivity flows from t to t+n
            num_links = int(actual_nodes * density)
            print(f"Generating {num_links:,} logical links... ", end="")
            sys.stdout.flush()

            # Optimization: Pre-calculate target ranges for each time step
            import bisect
            # Since node_times is sorted, we can find the first index for each time unit once
            time_start_indices = [bisect.bisect_left(node_times, t) for t in range(time_units + 1)]

            for _ in range(num_links):
                src_idx = random.randrange(actual_nodes)
                src_time = active_nodes[src_idx][-1]
                
                # Targets must be at current time or future
                first_valid_idx = time_start_indices[src_time]
                
                if first_valid_idx < actual_nodes:
                    tgt_idx = random.randrange(first_valid_idx, actual_nodes)
                    tgt = active_nodes[tgt_idx]
                    weight = random.uniform(0.01, 1.5 / max(1.0, density))
                    engine.add_dependency(active_nodes[src_idx], tgt, weight)
                
            start_node = random.choice(active_nodes)
             
            try:
                # Use a systemic threshold relative to the initial shock
                threshold = float(initial_shock) * 10 
                sim_res = engine.run_ripple(start_node, float(initial_shock), systemic_threshold=threshold)
                impact = sim_res["impact"]
                print(f"DONE (Impact: {impact:,.0f})")
                impacts.append(impact)
            except Exception as e:
                print(f"ERROR ({e})")
                impacts.append(0)
            
            sys.stdout.flush()
            
        scale_duration = (time.time() - scale_start) * 1000
        print(f"[SCALE {i+1} COMPLETE] Duration: {scale_duration:.2f}ms")
        
        results["datasets"].append({
            "label": f"{dim_scale}",
            "data": impacts
        })
        
    print(f"\n[SIMULATION COMPLETE] {time.strftime('%H:%M:%S')}\n")
    sys.stdout.flush()
    return results
