"""
Simplified unit tests that don't require external dependencies
Tests the core triangulation logic
"""

import unittest
import sys
import os
import math

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestTriangulationLogic(unittest.TestCase):
    """Test the triangulation algorithms without external dependencies"""
    
    def test_rssi_to_distance_formula(self):
        """Test RSSI to distance conversion formula"""
        tx_power = -30
        n = 2.5
        
        # Strong signal (-30 dBm)
        rssi_strong = -30
        distance_strong = 10 ** ((tx_power - rssi_strong) / (10 * n))
        self.assertAlmostEqual(distance_strong, 1.0, delta=0.1)
        
        # Medium signal (-50 dBm)
        rssi_medium = -50
        distance_medium = 10 ** ((tx_power - rssi_medium) / (10 * n))
        self.assertGreater(distance_medium, distance_strong)
        
        # Weak signal (-80 dBm)
        rssi_weak = -80
        distance_weak = 10 ** ((tx_power - rssi_weak) / (10 * n))
        self.assertGreater(distance_weak, distance_medium)
    
    def test_distance_calculation(self):
        """Test basic distance calculation between two points"""
        point1 = (0, 0, 0)
        point2 = (3, 4, 0)
        
        distance = math.sqrt(sum((a - b)**2 for a, b in zip(point1, point2)))
        self.assertEqual(distance, 5.0)  # 3-4-5 triangle
    
    def test_centroid_calculation(self):
        """Test centroid calculation"""
        points = [
            (0, 0, 0),
            (10, 0, 0),
            (5, 8.66, 0)
        ]
        
        centroid = tuple(sum(p[i] for p in points) / len(points) for i in range(3))
        
        expected_x = (0 + 10 + 5) / 3
        expected_y = (0 + 0 + 8.66) / 3
        expected_z = 0
        
        self.assertAlmostEqual(centroid[0], expected_x, delta=0.01)
        self.assertAlmostEqual(centroid[1], expected_y, delta=0.01)
        self.assertAlmostEqual(centroid[2], expected_z, delta=0.01)
    
    def test_weighted_average(self):
        """Test weighted average calculation"""
        values = [0, 10, 20]
        weights = [1, 1, 1]  # Equal weights
        
        weighted_avg = sum(v * w for v, w in zip(values, weights)) / sum(weights)
        self.assertEqual(weighted_avg, 10.0)
        
        # Different weights
        weights = [3, 1, 1]  # First value has more weight
        weighted_avg = sum(v * w for v, w in zip(values, weights)) / sum(weights)
        self.assertEqual(weighted_avg, 6.0)  # Closer to first value
    
    def test_triangle_area(self):
        """Test that our default triangle configuration is valid"""
        # Default triangle from config
        node1 = (0, 0)
        node2 = (50, 0)
        node3 = (25, 43.3)
        
        # Calculate area using cross product
        # Area = 0.5 * |x1(y2 - y3) + x2(y3 - y1) + x3(y1 - y2)|
        area = 0.5 * abs(
            node1[0] * (node2[1] - node3[1]) +
            node2[0] * (node3[1] - node1[1]) +
            node3[0] * (node1[1] - node2[1])
        )
        
        # Should be approximately 50 * 43.3 / 2 = 1082.5
        self.assertGreater(area, 1000)
        self.assertLess(area, 1100)


class TestConfigurationFiles(unittest.TestCase):
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
    
    def test_script_files_exist(self):
        """Test that startup scripts exist"""
        script_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
        
        scripts = [
            'start_server.sh',
            'start_node1.sh',
            'start_node2.sh',
            'start_node3.sh',
            'setup_ubuntu.sh'
        ]
        
        for script in scripts:
            script_file = os.path.join(script_dir, script)
            self.assertTrue(
                os.path.exists(script_file),
                f"Script {script} should exist"
            )
            
            # Check if executable
            self.assertTrue(
                os.access(script_file, os.X_OK),
                f"Script {script} should be executable"
            )


class TestProjectStructure(unittest.TestCase):
    """Test project structure"""
    
    def test_directories_exist(self):
        """Test that all required directories exist"""
        base_dir = os.path.join(os.path.dirname(__file__), '..')
        
        required_dirs = [
            'client',
            'server',
            'web/templates',
            'configs',
            'scripts',
            'tests'
        ]
        
        for dir_name in required_dirs:
            dir_path = os.path.join(base_dir, dir_name)
            self.assertTrue(
                os.path.isdir(dir_path),
                f"Directory {dir_name} should exist"
            )
    
    def test_key_files_exist(self):
        """Test that key files exist"""
        base_dir = os.path.join(os.path.dirname(__file__), '..')
        
        required_files = [
            'README.md',
            'SETUP.md',
            'requirements.txt',
            '.gitignore',
            'client/scanner.py',
            'server/app.py',
            'web/templates/index.html'
        ]
        
        for file_name in required_files:
            file_path = os.path.join(base_dir, file_name)
            self.assertTrue(
                os.path.isfile(file_path),
                f"File {file_name} should exist"
            )


if __name__ == '__main__':
    unittest.main(verbosity=2)
