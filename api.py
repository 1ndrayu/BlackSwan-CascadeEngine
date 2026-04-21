import json
import random
import time
import sys
import numpy as np
import bisect
from datetime import datetime
from collections import defaultdict, deque
from typing import Tuple, Dict, List, Callable
from telemetry import us_timer
from engine import RiskCube, RippleEngine

def run_simulation(densities, dimension_scales, regions, scenarios, time_units, initial_shock, num_nodes, mode='custom'):
    results = {
        "labels": densities,
        "datasets": []
    }
    
    total_scales = len(dimension_scales)
    total_densities = len(densities)
    
    print(f"\n[SIMULATION START] {time.strftime('%H:%M:%S')}")
    print(f"Parameters: Regions={regions}, Scenarios={scenarios}, Time Units={time_units}, Shock={initial_shock}, Ceiling={num_nodes}, Densities={densities}")
    print(f"Processing {total_scales} scales across {total_densities} density points...")
    print(f"\n[SIMULATION START] {datetime.now().strftime('%H:%M:%S')}")
    print(f"Parameters: Regions={regions}, Scenarios={scenarios}, Time Units={time_units}, Shock={initial_shock}, Ceiling={num_nodes}, Mode={mode.upper()}")
    print(f"Processing {len(dimension_scales)} scales across {len(densities)} density points...")

    for i, dim_scale in enumerate(dimension_scales):
        scale_start = time.time()
        print(f"\n[SCALE {i+1}/{len(dimension_scales)}] Dimension: {dim_scale}")
        impacts = []
        
        for density in densities:
            try:
                cube = RiskCube((dim_scale, regions, scenarios, time_units), use_sparse=True)
                engine = RippleEngine(cube)
                
                # Pre-calculate nodes to avoid coordinate generation overhead
                active_nodes = []
                for _ in range(num_nodes):
                    node = (
                        random.randint(0, dim_scale - 1),
                        random.randint(0, regions - 1),
                        random.randint(0, scenarios - 1),
                        random.randint(0, time_units - 1)
                    )
                    active_nodes.append(node)
                
                # Efficient temporal link generation
                node_times = sorted([n[-1] for n in active_nodes])
                active_nodes.sort(key=lambda x: x[-1])
                time_start_indices = [bisect.bisect_left(node_times, t) for t in range(time_units + 1)]

                num_links = int(num_nodes * density)
                
                # Mode-Specific Link Generation Logic
                for _ in range(num_links):
                    src_idx = random.randrange(num_nodes)
                    src = active_nodes[src_idx]
                    src_time = src[-1]
                    src_region = src[1]
                    
                    first_valid_idx = time_start_indices[src_time]
                    if first_valid_idx >= num_nodes: continue

                    # Select target based on mode
                    if mode == 'isolated':
                        # Short range, same region, LOW WEIGHTS (Safe Outcome)
                        valid_range = active_nodes[first_valid_idx : min(first_valid_idx + 50, num_nodes)]
                        tgt = random.choice([n for n in valid_range if n[1] == src_region] or [random.choice(valid_range)])
                        weight = random.uniform(0.01, 0.3) 
                    
                    elif mode == 'regional':
                        # Regional clustering (70% intra-region), MODERATE WEIGHTS (Contained Outcome)
                        if random.random() < 0.7:
                            regional_nodes = [n for n in active_nodes[first_valid_idx:] if n[1] == src_region]
                            tgt = random.choice(regional_nodes) if regional_nodes else random.choice(active_nodes[first_valid_idx:])
                        else:
                            tgt = random.choice(active_nodes[first_valid_idx:])
                        weight = random.uniform(0.05, 0.7)
                    
                    elif mode == 'systemic':
                        # Hub-and-Spoke (highly connected hubs), HIGH WEIGHTS (Fragile Outcome)
                        if src_idx % 10 == 0: # 10% are hubs
                            tgt = random.choice(active_nodes[first_valid_idx:])
                            weight = random.uniform(0.5, 2.5)
                        else:
                            tgt = random.choice(active_nodes[first_valid_idx:])
                            weight = random.uniform(0.1, 0.8)
                    
                    elif mode == 'black_swan':
                        # Non-linear jumps (10% jumps, 90% high-connectivity)
                        if random.random() < 0.1: 
                            tgt = random.choice(active_nodes[first_valid_idx:])
                            weight = random.uniform(1.5, 5.0) 
                        else:
                            tgt = random.choice(active_nodes[first_valid_idx:])
                            weight = random.uniform(0.1, 1.2)
                    
                    else: # Custom / Default
                        tgt = random.choice(active_nodes[first_valid_idx:])
                        weight = random.uniform(0.01, 1.5 / max(1.0, density))

                    engine.add_dependency(src, tgt, weight)

                # Execute simulation - shock ALL nodes at t=0 for broad systemic stress
                start_nodes = [n for n in active_nodes if n[-1] == 0]
                if not start_nodes: start_nodes = [active_nodes[0]]
                
                # Dynamic threshold: allow for larger cascades before capping
                threshold = float(initial_shock) * len(start_nodes) * 20
                sim_res = engine.run_ripple(start_nodes, float(initial_shock), systemic_threshold=threshold)
                impact = sim_res["impact"]
                
                if not np.isfinite(impact):
                    impact = threshold * 1.1
                
                impacts.append(impact)
            except Exception as e:
                impacts.append(0)
            
            sys.stdout.flush()
            
        scale_duration = (time.time() - scale_start) * 1000
        print(f"[SCALE {i+1} COMPLETE] Duration: {scale_duration:.2f}ms")
        
        results["datasets"].append({
            "label": f"{dim_scale}",
            "data": impacts
        })
        
    # Aggregate Global Metrics for Outcome Analyst
    all_impacts = [val for ds in results["datasets"] for val in ds["data"]]
    initial_shock_val = float(initial_shock)
    
    # Calculate Total Systemic Initial Shock (sum of all patient zero nodes)
    # We use a representative len(start_nodes) from the last run
    total_initial_shock = initial_shock_val * len(start_nodes)
    
    # Heuristic: If any scale at any density hit the threshold, the system is 'Broken'
    # 'Broken' means the cascade grew more than 5x the total initial shock
    systemic_trigger = total_initial_shock * 5.0
    results["hasBroken"] = any(imp > systemic_trigger for imp in all_impacts)
    
    # Find the density where it first hit a high multiplier
    results["breakPointDensity"] = "Safe"
    if results["hasBroken"]:
        for d_idx, d_label in enumerate(densities):
            if any(ds["data"][d_idx] > systemic_trigger for ds in results["datasets"]):
                results["breakPointDensity"] = d_label
                break
    
    max_impact = max(all_impacts) if all_impacts else total_initial_shock
    results["factor"] = max_impact / total_initial_shock if total_initial_shock > 0 else 1.0

    print(f"\n[SIMULATION COMPLETE] {time.strftime('%H:%M:%S')}\n")
    sys.stdout.flush()
    return results
