import json
import random
from engine import RiskCube, RippleEngine

def run_simulation(densities, dimension_scales, regions, scenarios, time_units, initial_shock, num_nodes):
    results = {
        "labels": densities,
        "datasets": []
    }
    
    for dim_scale in dimension_scales:
        dims = (dim_scale, regions, scenarios, time_units)
        latencies = []
        
        for density in densities:
            try:
                cube = RiskCube(dims, use_sparse=True)
                engine = RippleEngine(cube)
            except Exception as e:
                print(f"Cube error: {e}")
                latencies.append(0)
                continue
                
            # Prevent nodes from exceeding real max topological bounds
            max_possible_nodes = dim_scale * regions * scenarios * time_units
            actual_nodes = min(num_nodes, max_possible_nodes)
            
            if actual_nodes == 0:
                latencies.append(0)
                continue
                
            active_nodes = [tuple(random.randint(0, d - 1) for d in dims) for _ in range(actual_nodes)]
            
            num_links = int(actual_nodes * density)
            for _ in range(num_links):
                src = random.choice(active_nodes)
                tgt = random.choice(active_nodes)
                weight = random.uniform(0.001, 0.5 / max(1.0, density))
                engine.add_dependency(src, tgt, weight)
                
            start_node = active_nodes[0]
            
            try:
                engine.run_ripple(start_node, float(initial_shock))
                latencies.append(engine.run_ripple.latest_latency_us)
            except Exception as e:
                print(f"Simulation Error: {e}")
                latencies.append(0)
            
        results["datasets"].append({
            "label": f"{dim_scale} Assets",
            "data": latencies
        })
        
    return results
