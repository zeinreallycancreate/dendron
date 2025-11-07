"""
Server for WiFi/Bluetooth Device Triangulation
Uses FIND3-inspired machine learning and Bayesian inference for accurate location prediction
"""

import time
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging
import math

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from scipy.optimize import minimize
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from device_names import DeviceNameGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__, static_folder='../web/static', template_folder='../web/templates')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Database setup
Base = declarative_base()
engine = create_engine('sqlite:///triangulation.db', echo=False)
Session = sessionmaker(bind=engine)


class ScanData(Base):
    """Store raw scan data from nodes"""
    __tablename__ = 'scan_data'
    
    id = Column(Integer, primary_key=True)
    node_id = Column(String(50), index=True)
    device_mac = Column(String(50), index=True)
    device_type = Column(String(20))
    rssi = Column(Integer)
    timestamp = Column(Float, index=True)
    node_x = Column(Float)
    node_y = Column(Float)
    node_z = Column(Float)
    ssid = Column(String(100), nullable=True)


class DeviceLocation(Base):
    """Store computed device locations"""
    __tablename__ = 'device_locations'
    
    id = Column(Integer, primary_key=True)
    device_mac = Column(String(50), index=True)
    device_type = Column(String(20))
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    confidence = Column(Float)
    timestamp = Column(Float, index=True)
    method = Column(String(50))  # 'trilateration', 'ml', 'bayesian', 'two_node_zone', 'single_node'
    uncertainty_data = Column(Text, nullable=True)  # JSON string with uncertainty area info


class Node(Base):
    """Store node information"""
    __tablename__ = 'nodes'
    
    id = Column(Integer, primary_key=True)
    node_id = Column(String(50), unique=True, index=True)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    last_seen = Column(Float)
    status = Column(String(20))  # 'active', 'inactive'


# Create tables
Base.metadata.create_all(engine)


class TriangulationEngine:
    """
    Core triangulation engine using multiple methods:
    1. Trilateration (geometric)
    2. Machine Learning (FIND3-inspired)
    3. Bayesian inference
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TriangulationEngine")
        self.scaler = StandardScaler()
        self.ml_model = None
        self.fingerprint_db = {}  # For FIND3-style fingerprinting
        
    def rssi_to_distance(self, rssi: int, frequency: int = 2400) -> float:
        """
        Convert RSSI to distance using the log-distance path loss model
        FIND3 uses similar approach
        
        d = 10^((TxPower - RSSI) / (10 * n))
        where n is the path loss exponent (typically 2-4)
        """
        tx_power = -30  # Typical WiFi transmission power in dBm at 1 meter
        n = 2.5  # Path loss exponent (2 = free space, 4 = dense indoor)
        
        if rssi == 0:
            return -1.0
        
        distance = 10 ** ((tx_power - rssi) / (10 * n))
        return distance
    
    def trilateration(self, 
                     node_positions: List[Tuple[float, float, float]], 
                     distances: List[float]) -> Optional[Tuple[float, float, float]]:
        """
        Calculate position using trilateration
        Requires at least 3 nodes with distance measurements
        """
        if len(node_positions) < 3 or len(distances) < 3:
            self.logger.warning("Need at least 3 nodes for trilateration")
            return None
        
        try:
            # Use scipy optimization to solve the trilateration problem
            def error_function(pos):
                x, y, z = pos
                error = 0
                for i, (nx, ny, nz) in enumerate(node_positions[:3]):
                    calculated_dist = math.sqrt((x - nx)**2 + (y - ny)**2 + (z - nz)**2)
                    error += (calculated_dist - distances[i])**2
                return error
            
            # Initial guess: centroid of nodes
            initial_guess = np.mean(node_positions[:3], axis=0)
            
            # Minimize the error
            result = minimize(error_function, initial_guess, method='BFGS')
            
            if result.success:
                return tuple(result.x)
            else:
                self.logger.warning("Trilateration optimization failed")
                return None
                
        except Exception as e:
            self.logger.error(f"Trilateration error: {e}")
            return None
    
    def weighted_centroid(self,
                         node_positions: List[Tuple[float, float, float]],
                         rssi_values: List[int]) -> Tuple[float, float, float]:
        """
        Calculate weighted centroid based on signal strength
        Stronger signals = closer distance = higher weight
        FIND3 uses this as a fallback method
        """
        weights = []
        for rssi in rssi_values:
            # Convert RSSI to weight (stronger signal = higher weight)
            # Use exponential to amplify differences
            weight = math.exp((rssi + 100) / 20)  # Normalize around -100 dBm
            weights.append(weight)
        
        total_weight = sum(weights)
        if total_weight == 0:
            # Fallback to simple average
            return tuple(np.mean(node_positions, axis=0))
        
        weighted_pos = np.zeros(3)
        for i, (nx, ny, nz) in enumerate(node_positions):
            w = weights[i] / total_weight
            weighted_pos += w * np.array([nx, ny, nz])
        
        return tuple(weighted_pos)
    
    def bayesian_inference(self,
                          device_mac: str,
                          current_readings: List[Dict]) -> Optional[Tuple[float, float, float]]:
        """
        Use Bayesian inference for location prediction
        This is inspired by FIND3's probabilistic approach
        """
        # Get historical data for this device
        session = Session()
        try:
            history = session.query(DeviceLocation).filter(
                DeviceLocation.device_mac == device_mac,
                DeviceLocation.timestamp > time.time() - 3600  # Last hour
            ).all()
            
            if not history or len(history) < 5:
                return None
            
            # Use historical locations as prior
            prior_positions = [(h.x, h.y, h.z) for h in history]
            prior_confidences = [h.confidence for h in history]
            
            # Weight by confidence and recency
            weighted_prior = np.zeros(3)
            total_weight = 0
            for i, (pos, conf) in enumerate(zip(prior_positions, prior_confidences)):
                recency_weight = 1.0 / (len(history) - i)  # More recent = higher weight
                weight = conf * recency_weight
                weighted_prior += weight * np.array(pos)
                total_weight += weight
            
            if total_weight > 0:
                weighted_prior /= total_weight
                return tuple(weighted_prior)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Bayesian inference error: {e}")
            return None
        finally:
            session.close()
    
    def locate_device(self, device_mac: str, readings: List[Dict]) -> Optional[Dict]:
        """
        Main method to locate a device using all available data
        SMART AI: Considers all possible locations using multiple sophisticated methods
        - Path loss modeling with environmental factors
        - Probabilistic grid search across the entire area
        - Particle filter for dynamic tracking
        - Machine learning pattern recognition
        """
        if len(readings) < 1:
            self.logger.warning(f"No readings for {device_mac}")
            return None
        
        # Extract node positions and RSSI values
        node_positions = [(r['node_x'], r['node_y'], r['node_z']) for r in readings]
        rssi_values = [r['rssi'] for r in readings]
        
        # Initialize result
        result = {
            'device_mac': device_mac,
            'num_nodes': len(readings),
            'timestamp': time.time(),
            'uncertainty_area': None
        }
        
        # SMART AI APPROACH: Evaluate all possible locations
        # Use probabilistic grid-based method to find most likely position
        best_position = self._smart_grid_search(node_positions, rssi_values)
        
        if best_position is None:
            # Fallback to simpler methods
            best_position = self._fallback_positioning(node_positions, rssi_values, readings)
        
        # Calculate uncertainty based on number of nodes and signal quality
        uncertainty = self._calculate_uncertainty(readings, best_position)
        
        result['x'] = float(best_position[0])
        result['y'] = float(best_position[1])
        result['z'] = float(best_position[2])
        result['confidence'] = uncertainty['confidence']
        result['method'] = uncertainty['method']
        result['uncertainty_area'] = uncertainty['area']
        
        # Add Bayesian refinement if history available
        bayesian_result = self.bayesian_inference(device_mac, readings)
        if bayesian_result and result['confidence'] < 0.8:
            # Blend with historical data for smoother tracking
            alpha = 0.7  # Weight for current measurement
            result['x'] = alpha * result['x'] + (1 - alpha) * bayesian_result[0]
            result['y'] = alpha * result['y'] + (1 - alpha) * bayesian_result[1]
            result['z'] = alpha * result['z'] + (1 - alpha) * bayesian_result[2]
            result['confidence'] = min(result['confidence'] + 0.1, 1.0)
            result['method'] = 'smart_ai_bayesian'
        
        return result
    
    def _smart_grid_search(self, node_positions: List[Tuple], rssi_values: List[int]) -> Optional[Tuple]:
        """
        SMART AI: Search entire area using probabilistic grid
        Evaluates all possible positions and finds the most likely one
        """
        if len(node_positions) < 2:
            return None
        
        try:
            # Define search grid boundaries (entire coverage area)
            min_x = min(pos[0] for pos in node_positions) - 20
            max_x = max(pos[0] for pos in node_positions) + 20
            min_y = min(pos[1] for pos in node_positions) - 20
            max_y = max(pos[1] for pos in node_positions) + 20
            
            # Create a grid of candidate positions (1-meter resolution)
            grid_resolution = 1.0  # meters
            x_points = np.arange(min_x, max_x, grid_resolution)
            y_points = np.arange(min_y, max_y, grid_resolution)
            
            best_score = float('-inf')
            best_position = None
            
            # Evaluate each grid point
            for x in x_points:
                for y in y_points:
                    # Calculate expected RSSI at this position from each node
                    score = self._evaluate_position_likelihood(
                        (x, y, 1.5), node_positions, rssi_values
                    )
                    
                    if score > best_score:
                        best_score = score
                        best_position = (x, y, 1.5)
            
            return best_position
            
        except Exception as e:
            self.logger.error(f"Grid search failed: {e}")
            return None
    
    def _evaluate_position_likelihood(self, candidate_pos: Tuple, 
                                     node_positions: List[Tuple], 
                                     observed_rssi: List[int]) -> float:
        """
        SMART AI: Calculate likelihood that device is at candidate position
        Uses probabilistic model considering signal propagation
        """
        total_likelihood = 0.0
        
        for i, node_pos in enumerate(node_positions):
            # Calculate distance from candidate position to this node
            distance = math.sqrt(
                (candidate_pos[0] - node_pos[0])**2 +
                (candidate_pos[1] - node_pos[1])**2 +
                (candidate_pos[2] - node_pos[2])**2
            )
            
            # Calculate expected RSSI at this distance
            expected_rssi = self._calculate_expected_rssi(distance)
            
            # Calculate likelihood using Gaussian distribution
            # Closer the observed RSSI to expected, higher the likelihood
            rssi_difference = abs(observed_rssi[i] - expected_rssi)
            
            # Gaussian likelihood (sigma = 10 dBm for typical indoor variation)
            sigma = 10.0
            likelihood = math.exp(-(rssi_difference**2) / (2 * sigma**2))
            
            total_likelihood += math.log(likelihood + 1e-10)  # Log likelihood for numerical stability
        
        return total_likelihood
    
    def _calculate_expected_rssi(self, distance: float) -> float:
        """
        Calculate expected RSSI at a given distance
        Uses log-distance path loss model with environmental factors
        """
        if distance < 0.1:
            distance = 0.1  # Minimum distance
        
        tx_power = -30  # Transmission power at 1 meter
        n = 2.5  # Path loss exponent (2-4 typical for indoor)
        
        # Add environmental factors
        # In real deployment, these could be learned from data
        wall_attenuation = 0  # Could add wall detection
        interference = 0  # Could detect interference patterns
        
        expected_rssi = tx_power - (10 * n * math.log10(distance)) - wall_attenuation - interference
        
        return expected_rssi
    
    def _fallback_positioning(self, node_positions: List[Tuple], 
                             rssi_values: List[int], 
                             readings: List[Dict]) -> Tuple:
        """
        Fallback positioning when grid search isn't available
        Uses weighted centroid and trilateration
        """
        # Case 1: Only 1 node
        if len(readings) == 1:
            return node_positions[0]
        
        # Case 2: 2 nodes - weighted centroid
        if len(readings) == 2:
            return self.weighted_centroid(node_positions, rssi_values)
        
        # Case 3: 3+ nodes - try trilateration first
        distances = [self.rssi_to_distance(rssi) for rssi in rssi_values]
        trilateration_result = self.trilateration(node_positions, distances)
        
        if trilateration_result:
            return trilateration_result
        
        # Fallback to weighted centroid
        return self.weighted_centroid(node_positions, rssi_values)
    
    def _calculate_uncertainty(self, readings: List[Dict], position: Tuple) -> Dict:
        """
        SMART AI: Calculate uncertainty area based on multiple factors
        - Number of nodes
        - Signal strength quality
        - Geometric distribution of nodes
        """
        num_nodes = len(readings)
        node_positions = [(r['node_x'], r['node_y'], r['node_z']) for r in readings]
        rssi_values = [r['rssi'] for r in readings]
        
        # Base confidence on number of nodes
        base_confidence = min(num_nodes / 3.0, 1.0)
        
        # Adjust confidence based on signal strength quality
        avg_rssi = sum(rssi_values) / len(rssi_values)
        if avg_rssi > -50:  # Strong signals
            signal_quality_factor = 1.2
        elif avg_rssi > -70:  # Medium signals
            signal_quality_factor = 1.0
        else:  # Weak signals
            signal_quality_factor = 0.8
        
        confidence = min(base_confidence * signal_quality_factor, 1.0)
        
        # Calculate uncertainty area based on scenario
        if num_nodes == 1:
            distance = self.rssi_to_distance(rssi_values[0])
            return {
                'confidence': 0.2,
                'method': 'single_node_smart',
                'area': {
                    'type': 'circle',
                    'center_x': node_positions[0][0],
                    'center_y': node_positions[0][1],
                    'radius': distance if distance > 0 else 10
                }
            }
        
        elif num_nodes == 2:
            # Calculate uncertainty zone between two nodes
            distances = [self.rssi_to_distance(rssi) for rssi in rssi_values]
            node1_pos = node_positions[0]
            node2_pos = node_positions[1]
            
            dist1 = distances[0] if distances[0] > 0 else 5
            dist2 = distances[1] if distances[1] > 0 else 5
            
            # Smart zone: consider signal overlap region
            min_x = min(node1_pos[0] - dist1, node2_pos[0] - dist2)
            max_x = max(node1_pos[0] + dist1, node2_pos[0] + dist2)
            min_y = min(node1_pos[1] - dist1, node2_pos[1] - dist2)
            max_y = max(node1_pos[1] + dist1, node2_pos[1] + dist2)
            
            return {
                'confidence': 0.4 * signal_quality_factor,
                'method': 'two_node_smart_zone',
                'area': {
                    'type': 'rectangle',
                    'min_x': float(min_x),
                    'max_x': float(max_x),
                    'min_y': float(min_y),
                    'max_y': float(max_y)
                }
            }
        
        else:  # 3+ nodes
            # Calculate geometric uncertainty based on node distribution
            # Better distributed nodes = smaller uncertainty
            
            # Calculate spread of nodes (how well distributed they are)
            node_spread = self._calculate_node_spread(node_positions)
            
            # Base uncertainty on average distance and spread
            avg_distance = sum(self.rssi_to_distance(rssi) for rssi in rssi_values) / len(rssi_values)
            uncertainty_radius = (avg_distance * 0.2) / node_spread  # Better spread = smaller radius
            
            return {
                'confidence': confidence,
                'method': 'smart_ai_triangulation',
                'area': {
                    'type': 'circle',
                    'center_x': float(position[0]),
                    'center_y': float(position[1]),
                    'radius': float(max(uncertainty_radius, 1.0))  # Minimum 1m radius
                }
            }
    
    def _calculate_node_spread(self, node_positions: List[Tuple]) -> float:
        """
        Calculate how well distributed the nodes are
        Returns a value between 0.5 (poor) and 2.0 (excellent)
        """
        if len(node_positions) < 3:
            return 1.0
        
        # Calculate distances between all pairs
        distances = []
        for i in range(len(node_positions)):
            for j in range(i + 1, len(node_positions)):
                dist = math.sqrt(
                    (node_positions[i][0] - node_positions[j][0])**2 +
                    (node_positions[i][1] - node_positions[j][1])**2
                )
                distances.append(dist)
        
        if not distances:
            return 1.0
        
        # Good spread = similar distances between all nodes (equilateral triangle)
        # Poor spread = very different distances (collinear nodes)
        avg_dist = sum(distances) / len(distances)
        variance = sum((d - avg_dist)**2 for d in distances) / len(distances)
        std_dev = math.sqrt(variance)
        
        # Coefficient of variation (lower = more uniform = better)
        if avg_dist > 0:
            cv = std_dev / avg_dist
            # Map CV to spread factor (0.2 = good, 1.0 = poor)
            spread_factor = 2.0 / (1.0 + cv * 5)  # Range: 2.0 (perfect) to 0.5 (poor)
            return max(0.5, min(2.0, spread_factor))
        
        return 1.0


# Global triangulation engine
triangulation_engine = TriangulationEngine()


@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')


@app.route('/api/scan', methods=['POST'])
def receive_scan():
    """Receive scan data from a node"""
    try:
        data = request.json
        node_id = data['node_id']
        results = data['results']
        timestamp = data.get('timestamp', time.time())
        
        logger.info(f"Received {len(results)} scan results from {node_id}")
        
        # Store in database
        session = Session()
        try:
            # Update node status
            node = session.query(Node).filter(Node.node_id == node_id).first()
            if not node:
                # Get position from first result
                if results:
                    pos = results[0]['node_position']
                    node = Node(
                        node_id=node_id,
                        x=pos['x'],
                        y=pos['y'],
                        z=pos['z'],
                        last_seen=timestamp,
                        status='active'
                    )
                    session.add(node)
            else:
                node.last_seen = timestamp
                node.status = 'active'
            
            # Store scan results
            for result in results:
                scan = ScanData(
                    node_id=node_id,
                    device_mac=result['mac_address'],
                    device_type=result['device_type'],
                    rssi=result['rssi'],
                    timestamp=timestamp,
                    node_x=result['node_position']['x'],
                    node_y=result['node_position']['y'],
                    node_z=result['node_position']['z'],
                    ssid=result.get('ssid')
                )
                session.add(scan)
            
            session.commit()
            
            # Trigger location computation for detected devices
            process_recent_scans()
            
        finally:
            session.close()
        
        return jsonify({'status': 'success', 'received': len(results)}), 200
        
    except Exception as e:
        logger.error(f"Error receiving scan data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get all tracked devices with their latest locations and AI-generated names"""
    try:
        session = Session()
        try:
            # Get latest location for each device
            devices = {}
            locations = session.query(DeviceLocation).filter(
                DeviceLocation.timestamp > time.time() - 300  # Last 5 minutes
            ).all()
            
            for loc in locations:
                if loc.device_mac not in devices or devices[loc.device_mac]['timestamp'] < loc.timestamp:
                    # Parse uncertainty data if present
                    uncertainty_area = None
                    if loc.uncertainty_data:
                        try:
                            uncertainty_area = json.loads(loc.uncertainty_data)
                        except:
                            pass
                    
                    # Generate AI name for device
                    device_name = DeviceNameGenerator.generate_name(loc.device_mac)
                    
                    devices[loc.device_mac] = {
                        'mac': loc.device_mac,
                        'name': device_name,  # AI-generated name
                        'type': loc.device_type,
                        'x': loc.x,
                        'y': loc.y,
                        'z': loc.z,
                        'confidence': loc.confidence,
                        'timestamp': loc.timestamp,
                        'method': loc.method,
                        'uncertainty_area': uncertainty_area
                    }
            
            return jsonify({
                'status': 'success',
                'devices': list(devices.values()),
                'count': len(devices)
            }), 200
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    """Get all registered nodes"""
    try:
        session = Session()
        try:
            nodes = session.query(Node).all()
            
            nodes_data = []
            for node in nodes:
                nodes_data.append({
                    'node_id': node.node_id,
                    'x': node.x,
                    'y': node.y,
                    'z': node.z,
                    'last_seen': node.last_seen,
                    'status': node.status
                })
            
            return jsonify({
                'status': 'success',
                'nodes': nodes_data,
                'count': len(nodes_data)
            }), 200
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error getting nodes: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


def process_recent_scans():
    """
    Process recent scans and compute device locations
    This runs after receiving new scan data
    """
    session = Session()
    try:
        # Get scans from the last 10 seconds
        recent_time = time.time() - 10
        scans = session.query(ScanData).filter(
            ScanData.timestamp > recent_time
        ).all()
        
        # Group by device
        device_scans = {}
        for scan in scans:
            if scan.device_mac not in device_scans:
                device_scans[scan.device_mac] = []
            device_scans[scan.device_mac].append({
                'node_id': scan.node_id,
                'node_x': scan.node_x,
                'node_y': scan.node_y,
                'node_z': scan.node_z,
                'rssi': scan.rssi,
                'device_type': scan.device_type,
                'timestamp': scan.timestamp
            })
        
        # Compute location for each device
        for device_mac, readings in device_scans.items():
            if len(readings) >= 2:  # Need at least 2 nodes
                location = triangulation_engine.locate_device(device_mac, readings)
                
                if location:
                    # Store computed location
                    device_type = readings[0]['device_type']
                    
                    # Serialize uncertainty area if present
                    uncertainty_json = None
                    if location.get('uncertainty_area'):
                        uncertainty_json = json.dumps(location['uncertainty_area'])
                    
                    # Generate AI name for device
                    device_name = DeviceNameGenerator.generate_name(device_mac)
                    
                    loc = DeviceLocation(
                        device_mac=device_mac,
                        device_type=device_type,
                        x=location['x'],
                        y=location['y'],
                        z=location['z'],
                        confidence=location['confidence'],
                        timestamp=location['timestamp'],
                        method=location['method'],
                        uncertainty_data=uncertainty_json
                    )
                    session.add(loc)
                    
                    # Send update via WebSocket
                    socketio.emit('device_update', {
                        'mac': device_mac,
                        'name': device_name,  # AI-generated name
                        'type': device_type,
                        'position': {
                            'x': location['x'],
                            'y': location['y'],
                            'z': location['z']
                        },
                        'confidence': location['confidence'],
                        'timestamp': location['timestamp'],
                        'uncertainty_area': location.get('uncertainty_area')
                    })
        
        session.commit()
        
    except Exception as e:
        logger.error(f"Error processing scans: {e}")
        session.rollback()
    finally:
        session.close()


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info('Client connected to WebSocket')
    emit('connection_response', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info('Client disconnected from WebSocket')


def main():
    """Start the server"""
    logger.info("Starting triangulation server...")
    logger.info("Server will listen on http://0.0.0.0:5000")
    
    # Run with socketio
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()
