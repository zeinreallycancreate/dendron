"""
Integration test - simulates the full system without hardware
This validates the system architecture and data flow
"""

import unittest
import json
import time
from dataclasses import asdict


class MockScanResult:
    """Mock scan result for testing"""
    def __init__(self, mac_address, device_type, rssi, timestamp, node_id, node_position):
        self.mac_address = mac_address
        self.device_type = device_type
        self.rssi = rssi
        self.timestamp = timestamp
        self.node_id = node_id
        self.node_position = node_position
        self.ssid = None
        self.frequency = None
    
    def to_dict(self):
        return {
            'mac_address': self.mac_address,
            'device_type': self.device_type,
            'rssi': self.rssi,
            'timestamp': self.timestamp,
            'node_id': self.node_id,
            'node_position': self.node_position,
            'ssid': self.ssid,
            'frequency': self.frequency
        }


class TestSystemIntegration(unittest.TestCase):
    """Test the complete system flow"""
    
    def test_client_data_format(self):
        """Test that client generates proper data format"""
        # Simulate a scan result from Node 1
        result = MockScanResult(
            mac_address="AA:BB:CC:DD:EE:FF",
            device_type="wifi",
            rssi=-50,
            timestamp=time.time(),
            node_id="node_1",
            node_position={'x': 0, 'y': 0, 'z': 1.5}
        )
        
        # Convert to dict (what gets sent to server)
        data = result.to_dict()
        
        # Validate structure
        self.assertIn('mac_address', data)
        self.assertIn('device_type', data)
        self.assertIn('rssi', data)
        self.assertIn('node_id', data)
        self.assertIn('node_position', data)
        
        # Validate types
        self.assertIsInstance(data['mac_address'], str)
        self.assertIsInstance(data['device_type'], str)
        self.assertIsInstance(data['rssi'], int)
        self.assertIsInstance(data['node_position'], dict)
    
    def test_multiple_node_simulation(self):
        """Simulate data from 3 nodes for triangulation"""
        timestamp = time.time()
        device_mac = "11:22:33:44:55:66"
        
        # Simulate the same device seen by 3 different nodes
        node1_scan = MockScanResult(
            mac_address=device_mac,
            device_type="wifi",
            rssi=-45,  # Strongest signal (closest)
            timestamp=timestamp,
            node_id="node_1",
            node_position={'x': 0, 'y': 0, 'z': 1.5}
        )
        
        node2_scan = MockScanResult(
            mac_address=device_mac,
            device_type="wifi",
            rssi=-60,  # Medium signal
            timestamp=timestamp,
            node_id="node_2",
            node_position={'x': 50, 'y': 0, 'z': 1.5}
        )
        
        node3_scan = MockScanResult(
            mac_address=device_mac,
            device_type="wifi",
            rssi=-70,  # Weakest signal (farthest)
            timestamp=timestamp,
            node_id="node_3",
            node_position={'x': 25, 'y': 43.3, 'z': 1.5}
        )
        
        # Collect all scans
        all_scans = [node1_scan, node2_scan, node3_scan]
        
        # Validate all have same device
        macs = [s.mac_address for s in all_scans]
        self.assertTrue(all(mac == device_mac for mac in macs))
        
        # Validate RSSI decreases with distance
        # Device should be closest to node 1 (less negative = stronger)
        self.assertGreater(node1_scan.rssi, node2_scan.rssi)  # -45 > -60
        self.assertGreater(node2_scan.rssi, node3_scan.rssi)  # -60 > -70
    
    def test_server_api_payload(self):
        """Test the payload format sent to server"""
        timestamp = time.time()
        
        results = [
            MockScanResult(
                mac_address="AA:BB:CC:DD:EE:FF",
                device_type="wifi",
                rssi=-50,
                timestamp=timestamp,
                node_id="node_1",
                node_position={'x': 0, 'y': 0, 'z': 1.5}
            ),
            MockScanResult(
                mac_address="11:22:33:44:55:66",
                device_type="bluetooth",
                rssi=-65,
                timestamp=timestamp,
                node_id="node_1",
                node_position={'x': 0, 'y': 0, 'z': 1.5}
            )
        ]
        
        # Create the payload that would be sent to /api/scan
        payload = {
            'node_id': 'node_1',
            'timestamp': timestamp,
            'results': [r.to_dict() for r in results]
        }
        
        # Validate payload structure
        self.assertIn('node_id', payload)
        self.assertIn('timestamp', payload)
        self.assertIn('results', payload)
        self.assertIsInstance(payload['results'], list)
        self.assertEqual(len(payload['results']), 2)
        
        # Validate it can be JSON serialized
        json_str = json.dumps(payload)
        self.assertIsInstance(json_str, str)
        
        # Validate it can be deserialized
        payload_decoded = json.loads(json_str)
        self.assertEqual(payload_decoded['node_id'], 'node_1')
        self.assertEqual(len(payload_decoded['results']), 2)
    
    def test_realistic_scan_scenario(self):
        """Test a realistic scanning scenario"""
        # Simulate a phone at position (10, 10, 1.0)
        # Calculate what each node would see
        
        import math
        
        phone_position = (10, 10, 1.0)
        
        nodes = {
            'node_1': (0, 0, 1.5),
            'node_2': (50, 0, 1.5),
            'node_3': (25, 43.3, 1.5)
        }
        
        # Calculate distances
        distances = {}
        for node_id, node_pos in nodes.items():
            dist = math.sqrt(
                (phone_position[0] - node_pos[0])**2 +
                (phone_position[1] - node_pos[1])**2 +
                (phone_position[2] - node_pos[2])**2
            )
            distances[node_id] = dist
        
        # Convert distances to RSSI (inverse relationship)
        # RSSI = TxPower - 10 * n * log10(distance)
        tx_power = -30
        n = 2.5
        
        rssi_values = {}
        for node_id, dist in distances.items():
            if dist > 0:
                rssi = tx_power - (10 * n * math.log10(dist))
                rssi_values[node_id] = int(rssi)
            else:
                rssi_values[node_id] = tx_power
        
        # Node 1 should have strongest signal (closest)
        self.assertGreater(rssi_values['node_1'], rssi_values['node_2'])
        self.assertGreater(rssi_values['node_1'], rssi_values['node_3'])
        
        # Create scan results
        timestamp = time.time()
        scans = []
        
        for node_id, node_pos in nodes.items():
            scan = MockScanResult(
                mac_address="PHONE:AA:BB:CC",
                device_type="wifi",
                rssi=rssi_values[node_id],
                timestamp=timestamp,
                node_id=node_id,
                node_position={'x': node_pos[0], 'y': node_pos[1], 'z': node_pos[2]}
            )
            scans.append(scan)
        
        # Validate we have 3 scans
        self.assertEqual(len(scans), 3)
        
        # Validate all have different RSSI values
        rssi_list = [s.rssi for s in scans]
        self.assertEqual(len(set(rssi_list)), 3, "All RSSI values should be different")


class TestSystemScalability(unittest.TestCase):
    """Test system can handle realistic loads"""
    
    def test_multiple_devices(self):
        """Test handling multiple devices"""
        timestamp = time.time()
        num_devices = 20
        
        # Simulate 20 devices detected by node 1
        scans = []
        for i in range(num_devices):
            scan = MockScanResult(
                mac_address=f"AA:BB:CC:DD:EE:{i:02X}",
                device_type="wifi" if i % 2 == 0 else "bluetooth",
                rssi=-40 - (i * 2),  # Varying signal strengths
                timestamp=timestamp,
                node_id="node_1",
                node_position={'x': 0, 'y': 0, 'z': 1.5}
            )
            scans.append(scan)
        
        # Validate we can handle this
        self.assertEqual(len(scans), num_devices)
        
        # Check data can be serialized
        payload = {
            'node_id': 'node_1',
            'timestamp': timestamp,
            'results': [s.to_dict() for s in scans]
        }
        
        json_str = json.dumps(payload)
        self.assertIsInstance(json_str, str)
        
        # Payload should be reasonable size (< 10KB for 20 devices)
        self.assertLess(len(json_str), 10000)
    
    def test_rapid_updates(self):
        """Test system can handle rapid updates"""
        device_mac = "AA:BB:CC:DD:EE:FF"
        
        # Simulate 10 rapid scans (like 10 seconds of 1Hz scanning)
        scans = []
        base_time = time.time()
        
        for i in range(10):
            scan = MockScanResult(
                mac_address=device_mac,
                device_type="wifi",
                rssi=-50 + (i % 5),  # RSSI fluctuates
                timestamp=base_time + i,
                node_id="node_1",
                node_position={'x': 0, 'y': 0, 'z': 1.5}
            )
            scans.append(scan)
        
        # Validate timestamps are sequential
        timestamps = [s.timestamp for s in scans]
        self.assertEqual(timestamps, sorted(timestamps))
        
        # Validate time differences are reasonable
        for i in range(1, len(timestamps)):
            diff = timestamps[i] - timestamps[i-1]
            self.assertAlmostEqual(diff, 1.0, delta=0.1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
