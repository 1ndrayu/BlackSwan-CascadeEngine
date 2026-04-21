import numpy as np
from collections import defaultdict, deque
from typing import Tuple, Dict, List, Callable
from telemetry import us_timer

# Type alias for 4D coordinate clarity
Coord4D = Tuple[int, int, int, int]

class RiskCube:
    """
    4D Tensor storage [Assets, Regions, Scenarios, Time].
    Dynamically binds accessors to eliminate runtime 'if' checks.
    """
    def __init__(self, dims: Coord4D, use_sparse: bool = False):
        self.dims = dims
        self.use_sparse = use_sparse
        self.total_elements = int(np.prod(dims))
        
        # Method binding for performance
        if not self.use_sparse:
            self.data = np.zeros(dims, dtype=np.float64)
            self.get_val: Callable[[Coord4D], float] = self._get_dense
            self.set_val: Callable[[Coord4D, float], None] = self._set_dense
        else:
            # DOK (Dictionary of Keys) implementation using native dict
            self.data = defaultdict(float)
            self.get_val = self._get_sparse
            self.set_val = self._set_sparse

    def _get_dense(self, coord: Coord4D) -> float:
        return self.data[coord]

    def _set_dense(self, coord: Coord4D, val: float):
        self.data[coord] = val

    def _get_sparse(self, coord: Coord4D) -> float:
        return self.data[coord]

    def _set_sparse(self, coord: Coord4D, val: float):
        self.data[coord] = val


class RippleEngine:
    """
    Graph-based propagation engine for risk shocks.
    Optimized for precision and traversal speed.
    """
    def __init__(self, cube: RiskCube):
        self.cube = cube
        self.graph: Dict[Coord4D, List[Tuple[Coord4D, float]]] = defaultdict(list)
        
    def add_dependency(self, source: Coord4D, target: Coord4D, weight: float):
        """Adds a weighted edge from source to target."""
        self.graph[source].append((target, weight))

    @us_timer
    def run_ripple(self, start_node: Coord4D, shock_value: float, systemic_threshold: float = 1_000_000, epsilon: float = 1e-9, limit: int = 1_000_000) -> Dict:
        """
        Propagates a shock and returns systemic impact telemetry.
        """
        old_val = self.cube.get_val(start_node)
        delta = shock_value - old_val
        
        if abs(delta) <= epsilon:
            return {"impact": 0.0, "fracture": False, "nodes_affected": 0}
            
        self.cube.set_val(start_node, shock_value)
        
        pending_impacts = defaultdict(float)
        queue = deque([start_node])
        pending_impacts[start_node] = delta
        
        total_systemic_impact = abs(delta)
        nodes_affected = 1
        fractured = False
        steps = 0
        
        # Cache references
        get_val = self.cube.get_val
        set_val = self.cube.set_val
        graph_get = self.graph.get
        
        while queue and steps < limit:
            current_node = queue.popleft()
            current_delta = pending_impacts.pop(current_node)
            steps += 1
            
            dependencies = graph_get(current_node)
            if not dependencies:
                continue
                
            for target_node, weight in dependencies:
                impact = current_delta * weight
                
                if abs(impact) > epsilon:
                    current_target_val = get_val(target_node)
                    new_target_val = current_target_val + impact
                    set_val(target_node, new_target_val)
                    
                    total_systemic_impact += abs(impact)
                    nodes_affected += 1
                    
                    if total_systemic_impact > systemic_threshold:
                        fractured = True
                    
                    if target_node not in pending_impacts:
                        queue.append(target_node)
                    
                    pending_impacts[target_node] += impact

        return {
            "impact": total_systemic_impact,
            "fracture": fractured,
            "nodes_affected": nodes_affected,
            "steps": steps
        }