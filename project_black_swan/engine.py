import numpy as np
from collections import defaultdict, deque
from typing import Tuple, Dict, List, Callable
from math import prod
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
        self.total_elements = prod(dims)
        
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
    def run_ripple(self, start_coord: Coord4D, new_value: float, epsilon: float = 1e-9, limit: int = 1_000_000):
        """
        Propagates the delta from start_coord through the dependency graph.
        
        Args:
            start_coord: The 4D coordinate where the shock originates.
            new_value: The new absolute value for that coordinate.
            epsilon: The minimum change magnitude to propagate.
            limit: Maximum iterations to prevent infinite loops in cyclic graphs.
        """
        old_val = self.cube.get_val(start_coord)
        delta = new_value - old_val
        
        # Exit if the initial change is below the floor
        if abs(delta) <= epsilon:
            return
            
        self.cube.set_val(start_coord, new_value)
        
        # Impact aggregation: maps node -> current accumulated delta for this wave
        pending_impacts = defaultdict(float)
        queue = deque([start_coord])
        pending_impacts[start_coord] = delta
        
        steps = 0
        
        # Cache method references to avoid dot-lookup overhead in tight loop
        get_val = self.cube.get_val
        set_val = self.cube.set_val
        graph_get = self.graph.get
        
        while queue and steps < limit:
            current_coord = queue.popleft()
            current_delta = pending_impacts.pop(current_coord)
            steps += 1
            
            # Retrieve downstream dependencies
            dependencies = graph_get(current_coord)
            if not dependencies:
                continue
                
            for target_coord, weight in dependencies:
                impact = current_delta * weight
                
                # Sensible floor check: skip microscopic noise
                if abs(impact) > epsilon:
                    # Update the cube state
                    current_target_val = get_val(target_coord)
                    set_val(target_coord, current_target_val + impact)
                    
                    # If target is already in queue, just add to its pending impact
                    # If not, add it to the queue to process its children later
                    if target_coord not in pending_impacts:
                        queue.append(target_coord)
                    
                    pending_impacts[target_coord] += impact