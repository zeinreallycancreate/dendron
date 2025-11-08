"""
Auto-detection and geometry mapping for scanner nodes
Automatically discovers node positions and adapts triangulation math
"""

import math
import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
from scipy.spatial import ConvexHull, Delaunay


logger = logging.getLogger(__name__)


class NodeGeometry:
    """
    Automatically detect and map node positions
    Adapts triangulation to any number of nodes in any configuration
    """
    
    def __init__(self):
        self.nodes = {}  # {node_id: {'x': float, 'y': float, 'z': float}}
        self.geometry_type = None  # 'single', 'line', 'triangle', 'polygon'
        self.coverage_area = None
        self.logger = logging.getLogger(f"{__name__}.NodeGeometry")
    
    def update_nodes(self, node_data: List[Dict]):
        """
        Update node positions from database
        Auto-detects geometry when nodes change
        """
        self.nodes = {}
        for node in node_data:
            self.nodes[node['node_id']] = {
                'x': node['x'],
                'y': node['y'],
                'z': node['z'],
                'last_seen': node.get('last_seen', 0),
                'status': node.get('status', 'unknown')
            }
        
        if len(self.nodes) > 0:
            self._detect_geometry()
            self._calculate_coverage_area()
    
    def _detect_geometry(self):
        """
        Automatically detect the geometric configuration of nodes
        """
        num_nodes = len(self.nodes)
        
        if num_nodes == 1:
            self.geometry_type = 'single'
            self.logger.info("Detected geometry: Single node")
        
        elif num_nodes == 2:
            self.geometry_type = 'line'
            self.logger.info("Detected geometry: Line (2 nodes)")
        
        elif num_nodes == 3:
            # Check if collinear (on a line) or triangle
            positions = [list(n.values())[:3] for n in self.nodes.values()]
            if self._are_collinear(positions):
                self.geometry_type = 'line'
                self.logger.info("Detected geometry: Line (3 collinear nodes)")
            else:
                self.geometry_type = 'triangle'
                self.logger.info("Detected geometry: Triangle")
        
        else:  # 4+ nodes
            positions = [list(n.values())[:3] for n in self.nodes.values()]
            if self._are_collinear(positions):
                self.geometry_type = 'line'
                self.logger.info(f"Detected geometry: Line ({num_nodes} collinear nodes)")
            else:
                self.geometry_type = 'polygon'
                self.logger.info(f"Detected geometry: Polygon ({num_nodes} nodes)")
    
    def _are_collinear(self, positions: List[List[float]], tolerance: float = 1.0) -> bool:
        """
        Check if points are collinear (on the same line)
        """
        if len(positions) < 3:
            return True
        
        # Use cross product to check collinearity
        # For 2D (x, y)
        p1 = np.array(positions[0][:2])
        p2 = np.array(positions[1][:2])
        
        for i in range(2, len(positions)):
            p3 = np.array(positions[i][:2])
            # Calculate cross product
            v1 = p2 - p1
            v2 = p3 - p1
            cross = v1[0] * v2[1] - v1[1] * v2[0]
            
            if abs(cross) > tolerance:
                return False
        
        return True
    
    def _calculate_coverage_area(self):
        """
        Calculate the coverage area based on node positions
        """
        if len(self.nodes) == 0:
            self.coverage_area = None
            return
        
        positions = [[n['x'], n['y']] for n in self.nodes.values()]
        
        # Calculate bounding box with margin
        margin = 20  # meters
        min_x = min(p[0] for p in positions) - margin
        max_x = max(p[0] for p in positions) + margin
        min_y = min(p[1] for p in positions) - margin
        max_y = max(p[1] for p in positions) + margin
        
        self.coverage_area = {
            'min_x': min_x,
            'max_x': max_x,
            'min_y': min_y,
            'max_y': max_y,
            'center_x': (min_x + max_x) / 2,
            'center_y': (min_y + max_y) / 2,
            'width': max_x - min_x,
            'height': max_y - min_y
        }
        
        self.logger.info(f"Coverage area: {self.coverage_area['width']:.1f}m x {self.coverage_area['height']:.1f}m")
    
    def get_optimal_search_grid(self) -> Tuple[float, float, float, float]:
        """
        Get optimal grid boundaries for position search
        Adapts to current node configuration
        """
        if self.coverage_area is None:
            return (-20, 20, -20, 20)
        
        return (
            self.coverage_area['min_x'],
            self.coverage_area['max_x'],
            self.coverage_area['min_y'],
            self.coverage_area['max_y']
        )
    
    def calculate_node_quality_score(self) -> float:
        """
        Calculate quality score based on node distribution
        Better distribution = higher score
        Returns 0.0 (poor) to 1.0 (excellent)
        """
        num_nodes = len(self.nodes)
        
        if num_nodes == 0:
            return 0.0
        elif num_nodes == 1:
            return 0.2
        elif num_nodes == 2:
            return 0.4
        
        # For 3+ nodes, analyze distribution
        positions = [[n['x'], n['y']] for n in self.nodes.values()]
        
        if self.geometry_type == 'line':
            # Collinear nodes - poor quality
            return 0.3
        
        elif self.geometry_type == 'triangle':
            # Check if equilateral (best), isosceles (good), or scalene (ok)
            score = self._calculate_triangle_quality(positions)
            return 0.6 + (score * 0.4)  # 0.6 to 1.0
        
        else:  # polygon
            # Check convex hull and distribution
            try:
                hull = ConvexHull(positions)
                # More points on hull = better coverage
                hull_ratio = len(hull.vertices) / len(positions)
                return 0.7 + (hull_ratio * 0.3)  # 0.7 to 1.0
            except:
                return 0.7
    
    def _calculate_triangle_quality(self, positions: List[List[float]]) -> float:
        """
        Calculate how good a triangle is (1.0 = equilateral, 0.0 = degenerate)
        """
        if len(positions) != 3:
            return 0.5
        
        # Calculate all three side lengths
        distances = []
        for i in range(3):
            p1 = np.array(positions[i])
            p2 = np.array(positions[(i + 1) % 3])
            dist = np.linalg.norm(p1 - p2)
            distances.append(dist)
        
        # For equilateral, all sides equal
        avg_dist = np.mean(distances)
        if avg_dist == 0:
            return 0.0
        
        # Calculate coefficient of variation
        std_dist = np.std(distances)
        cv = std_dist / avg_dist
        
        # Map CV to quality score (0 = equilateral, higher = worse)
        quality = max(0.0, 1.0 - cv * 3)  # Scale factor 3
        return quality
    
    def auto_position_nodes(self, rssi_measurements: Dict[str, Dict[str, int]]) -> Dict[str, Dict]:
        """
        Automatically determine node positions based on RSSI between nodes
        Uses multidimensional scaling (MDS) to map distances to positions
        
        rssi_measurements: {node_id_1: {node_id_2: rssi, node_id_3: rssi, ...}}
        """
        node_ids = list(rssi_measurements.keys())
        num_nodes = len(node_ids)
        
        if num_nodes < 2:
            self.logger.warning("Need at least 2 nodes for auto-positioning")
            return {}
        
        # Convert RSSI to distances
        distance_matrix = np.zeros((num_nodes, num_nodes))
        for i, node_i in enumerate(node_ids):
            for j, node_j in enumerate(node_ids):
                if i != j and node_j in rssi_measurements.get(node_i, {}):
                    rssi = rssi_measurements[node_i][node_j]
                    distance = self._rssi_to_distance(rssi)
                    distance_matrix[i, j] = distance
                    distance_matrix[j, i] = distance  # Symmetric
        
        # Use MDS to get 2D positions from distances
        try:
            from sklearn.manifold import MDS
            mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
            positions_2d = mds.fit_transform(distance_matrix)
            
            # Create position dictionary
            auto_positions = {}
            for i, node_id in enumerate(node_ids):
                auto_positions[node_id] = {
                    'x': float(positions_2d[i, 0]),
                    'y': float(positions_2d[i, 1]),
                    'z': 1.5,  # Default height
                    'auto_detected': True
                }
            
            self.logger.info(f"Auto-positioned {num_nodes} nodes using RSSI measurements")
            return auto_positions
            
        except ImportError:
            self.logger.warning("sklearn not available for MDS, using fallback positioning")
            return self._fallback_auto_positioning(node_ids, distance_matrix)
    
    def _fallback_auto_positioning(self, node_ids: List[str], distance_matrix: np.ndarray) -> Dict:
        """
        Simple fallback positioning when sklearn is not available
        """
        num_nodes = len(node_ids)
        positions = {}
        
        if num_nodes == 2:
            # Place on a line
            positions[node_ids[0]] = {'x': 0, 'y': 0, 'z': 1.5}
            positions[node_ids[1]] = {'x': distance_matrix[0, 1], 'y': 0, 'z': 1.5}
        
        elif num_nodes == 3:
            # Place in a triangle
            d01 = distance_matrix[0, 1]
            d02 = distance_matrix[0, 2]
            d12 = distance_matrix[1, 2]
            
            positions[node_ids[0]] = {'x': 0, 'y': 0, 'z': 1.5}
            positions[node_ids[1]] = {'x': d01, 'y': 0, 'z': 1.5}
            
            # Calculate third point position using law of cosines
            cos_angle = (d01**2 + d02**2 - d12**2) / (2 * d01 * d02)
            cos_angle = max(-1, min(1, cos_angle))  # Clamp
            angle = math.acos(cos_angle)
            
            positions[node_ids[2]] = {
                'x': d02 * math.cos(angle),
                'y': d02 * math.sin(angle),
                'z': 1.5
            }
        
        else:
            # Distribute in a circle
            radius = np.mean(distance_matrix[distance_matrix > 0]) / 2
            for i, node_id in enumerate(node_ids):
                angle = (2 * math.pi * i) / num_nodes
                positions[node_id] = {
                    'x': radius * math.cos(angle),
                    'y': radius * math.sin(angle),
                    'z': 1.5
                }
        
        for node_id in positions:
            positions[node_id]['auto_detected'] = True
        
        return positions
    
    def _rssi_to_distance(self, rssi: int) -> float:
        """Convert RSSI to distance estimate"""
        tx_power = -30
        n = 2.5
        if rssi == 0:
            return 10.0
        distance = 10 ** ((tx_power - rssi) / (10 * n))
        return max(distance, 1.0)  # Minimum 1 meter
