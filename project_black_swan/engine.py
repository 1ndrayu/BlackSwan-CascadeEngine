import numpy as np
import scipy.sparse as sp
from collections import defaultdict, deque
from typing import Tuple, Dict, List
from telemetry import us_timer

class RiskCube:
    """
    4D Tensor storage [Assets, Regions, Scenarios, Time]
    Supports dense (numpy) and sparse (COO/DOK) storage.
    """
    def __init__(self, dims: Tuple[int, int, int, int], use_sparse: bool = False):
        self.dims = dims
        self.use_sparse = use_sparse
        self.total_elements = 1
        for d in dims:
            self.total_elements *= d
        
        if not self.use_sparse:
            # Memory intensive for high dimensions
            self.data = np.zeros(dims, dtype=np.float64)
        else:
            # Sparse storage for 4D space via flattened indexing
            self.data = sp.dok_array((1, self.total_elements), dtype=np.float64)

    def _flat_idx(self, coord: Tuple[int, int, int, int]) -> int:
        i, j, k, l = coord
        d0, d1, d2, d3 = self.dims
        # Row-major flattening for 4D
        return i * (d1 * d2 * d3) + j * (d2 * d3) + k * d3 + l

    def get_val(self, coord: Tuple[int, int, int, int]) -> float:
        if self.use_sparse:
            return self.data[0, self._flat_idx(coord)]
        return self.data[coord]

    def set_val(self, coord: Tuple[int, int, int, int], val: float):
        if self.use_sparse:
            self.data[0, self._flat_idx(coord)] = val
        else:
            self.data[coord] = val

class RippleEngine:
    """
    Implements a Directed Acyclic Graph (DAG) for propagates risk shocks.
    """
    def __init__(self, cube: RiskCube):
        self.cube = cube
        self.graph: Dict[Tuple, List[Tuple[Tuple, float]]] = defaultdict(list)
        
    def add_dependency(self, source: Tuple, target: Tuple, weight: float):
        """Adds a weighted link from source to target coordinate."""
        self.graph[source].append((target, weight))

    @us_timer
    def run_ripple(self, start_coord: Tuple, new_value: float):
        """
        Calculates the cascade effect of a local change.
        Iterative BFS-like visitor to prevent recursion depth issues.
        """
        old_val = self.cube.get_val(start_coord)
        delta = new_value - old_val
        
        if abs(delta) < 1e-6:
            return
            
        self.cube.set_val(start_coord, new_value)
        queue = deque([(start_coord, delta)])
        
        # Propagation limit to prevent infinite loops if graph has cycles
        limit = 50000 
        steps = 0
        
        while queue and steps < limit:
            current_coord, current_delta = queue.popleft()
            steps += 1
            
            for target_coord, weight in self.graph.get(current_coord, []):
                impact = current_delta * weight
                
                if abs(impact) > 1e-6:
                    target_val = self.cube.get_val(target_coord)
                    self.cube.set_val(target_coord, target_val + impact)
                    queue.append((target_coord, impact))
