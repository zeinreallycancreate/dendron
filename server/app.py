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
    method = Column(String(50))  # 'trilateration', 'ml', 'bayesian'


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
        Combines multiple methods for best accuracy (FIND3 approach)
        """
        if len(readings) < 2:
            self.logger.warning(f"Not enough readings for {device_mac}")
            return None
        
        # Extract node positions and RSSI values
        node_positions = [(r['node_x'], r['node_y'], r['node_z']) for r in readings]
        rssi_values = [r['rssi'] for r in readings]
        
        # Method 1: Trilateration (if 3+ nodes)
        trilateration_result = None
        if len(readings) >= 3:
            distances = [self.rssi_to_distance(rssi) for rssi in rssi_values]
            trilateration_result = self.trilateration(node_positions, distances)
        
        # Method 2: Weighted centroid (always available)
        centroid_result = self.weighted_centroid(node_positions, rssi_values)
        
        # Method 3: Bayesian inference (if history available)
        bayesian_result = self.bayesian_inference(device_mac, readings)
        
        # Combine methods with confidence weighting
        results = []
        confidences = []
        
        if trilateration_result:
            results.append(trilateration_result)
            confidences.append(0.5)  # High confidence for trilateration
        
        results.append(centroid_result)
        confidences.append(0.3)  # Medium confidence for centroid
        
        if bayesian_result:
            results.append(bayesian_result)
            confidences.append(0.2)  # Lower confidence for prediction
        
        # Weighted average of all methods
        total_conf = sum(confidences)
        final_position = np.zeros(3)
        for pos, conf in zip(results, confidences):
            final_position += (conf / total_conf) * np.array(pos)
        
        return {
            'device_mac': device_mac,
            'x': float(final_position[0]),
            'y': float(final_position[1]),
            'z': float(final_position[2]),
            'confidence': min(len(readings) / 3.0, 1.0),  # More nodes = higher confidence
            'num_nodes': len(readings),
            'method': 'combined',
            'timestamp': time.time()
        }


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
    """Get all tracked devices with their latest locations"""
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
                    devices[loc.device_mac] = {
                        'mac': loc.device_mac,
                        'type': loc.device_type,
                        'x': loc.x,
                        'y': loc.y,
                        'z': loc.z,
                        'confidence': loc.confidence,
                        'timestamp': loc.timestamp,
                        'method': loc.method
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
                    loc = DeviceLocation(
                        device_mac=device_mac,
                        device_type=device_type,
                        x=location['x'],
                        y=location['y'],
                        z=location['z'],
                        confidence=location['confidence'],
                        timestamp=location['timestamp'],
                        method=location['method']
                    )
                    session.add(loc)
                    
                    # Send update via WebSocket
                    socketio.emit('device_update', {
                        'mac': device_mac,
                        'type': device_type,
                        'position': {
                            'x': location['x'],
                            'y': location['y'],
                            'z': location['z']
                        },
                        'confidence': location['confidence'],
                        'timestamp': location['timestamp']
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
