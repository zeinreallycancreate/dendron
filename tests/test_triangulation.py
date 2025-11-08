"""
Unit tests for the triangulation engine
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.app import TriangulationEngine
import numpy as np


class TestTriangulationEngine(unittest.TestCase):
    """Test the triangulation algorithms"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = TriangulationEngine()
    
    def test_rssi_to_distance(self):
        """Test RSSI to distance conversion"""
        # Strong signal should give small distance
        distance_strong = self.engine.rssi_to_distance(-30)
        self.assertLess(distance_strong, 5)
        
        # Weak signal should give larger distance
        distance_weak = self.engine.rssi_to_distance(-80)
        self.assertGreater(distance_weak, distance_strong)
        
        # Zero RSSI should return -1
        distance_zero = self.engine.rssi_to_distance(0)
        self.assertEqual(distance_zero, -1.0)
    
    def test_trilateration_basic(self):
        """Test basic trilateration with known positions"""
        # Set up 3 nodes in a triangle
        node_positions = [
            (0, 0, 0),    # Bottom-left
            (10, 0, 0),   # Bottom-right
            (5, 8.66, 0)  # Top (equilateral triangle)
        ]
        
        # Device at center should be ~5m from all nodes
        center_position = (5, 2.89, 0)
        
        # Calculate distances from center to each node
        distances = []
        for node_pos in node_positions:
            dist = np.sqrt(sum((a - b)**2 for a, b in zip(center_position, node_pos)))
            distances.append(dist)
        
        # Run trilateration
        result = self.engine.trilateration(node_positions, distances)
        
        self.assertIsNotNone(result)
        # Should be close to the center position
        self.assertAlmostEqual(result[0], center_position[0], delta=1.0)
        self.assertAlmostEqual(result[1], center_position[1], delta=1.0)
    
    def test_weighted_centroid(self):
        """Test weighted centroid calculation"""
        node_positions = [
            (0, 0, 0),
            (10, 0, 0),
            (5, 8.66, 0)
        ]
        
        # All equal weights (all same RSSI)
        rssi_equal = [-50, -50, -50]
        centroid = self.engine.weighted_centroid(node_positions, rssi_equal)
        
        # Should be at the centroid of the triangle
        expected_x = (0 + 10 + 5) / 3
        expected_y = (0 + 0 + 8.66) / 3
        
        self.assertAlmostEqual(centroid[0], expected_x, delta=0.5)
        self.assertAlmostEqual(centroid[1], expected_y, delta=0.5)
        
        # One node much stronger signal (closer)
        rssi_weighted = [-30, -80, -80]  # First node much stronger
        centroid_weighted = self.engine.weighted_centroid(node_positions, rssi_weighted)
        
        # Result should be closer to first node
        dist_to_first = np.sqrt((centroid_weighted[0] - 0)**2 + (centroid_weighted[1] - 0)**2)
        dist_to_second = np.sqrt((centroid_weighted[0] - 10)**2 + (centroid_weighted[1] - 0)**2)
        
        self.assertLess(dist_to_first, dist_to_second)
    
    def test_trilateration_insufficient_nodes(self):
        """Test trilateration with insufficient nodes"""
        node_positions = [(0, 0, 0), (10, 0, 0)]  # Only 2 nodes
        distances = [5.0, 5.0]
        
        result = self.engine.trilateration(node_positions, distances)
        self.assertIsNone(result)


class TestScanResult(unittest.TestCase):
    """Test the ScanResult data structure"""
    
    def test_scan_result_creation(self):
        """Test creating a ScanResult"""
        from client.scanner import ScanResult
        
        result = ScanResult(
            mac_address="AA:BB:CC:DD:EE:FF",
            device_type="wifi",
            rssi=-50,
            timestamp=1234567890.0,
            node_id="node_1",
            node_position={'x': 0, 'y': 0, 'z': 1.5},
            ssid="TestNetwork"
        )
        
        self.assertEqual(result.mac_address, "AA:BB:CC:DD:EE:FF")
        self.assertEqual(result.device_type, "wifi")
        self.assertEqual(result.rssi, -50)
        self.assertEqual(result.ssid, "TestNetwork")
        
        # Test to_dict conversion
        result_dict = result.to_dict()
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict['mac_address'], "AA:BB:CC:DD:EE:FF")


class TestConfiguration(unittest.TestCase):
    """Test configuration file handling"""
    
    def test_config_files_exist(self):
        """Test that all config files exist"""
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'configs')
        
        for i in range(1, 4):
            config_file = os.path.join(config_dir, f'node{i}_config.yml')
            self.assertTrue(
                os.path.exists(config_file),
                f"Config file {config_file} should exist"
            )


if __name__ == '__main__':
    unittest.main()
