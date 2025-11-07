"""
Raspberry Pi Client for WiFi/Bluetooth Device Scanning
Uses FIND3-inspired fingerprinting technology for accurate triangulation
"""

import time
import json
import hashlib
import requests
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    """Represents a single device scan result"""
    mac_address: str
    device_type: str  # 'wifi' or 'bluetooth'
    rssi: int  # Signal strength in dBm
    timestamp: float
    node_id: str
    node_position: Dict[str, float]  # {'x': 0, 'y': 0, 'z': 0}
    ssid: Optional[str] = None
    frequency: Optional[int] = None
    
    def to_dict(self):
        return asdict(self)


class WiFiScanner:
    """
    WiFi scanner using monitor mode and passive scanning
    Inspired by FIND3's fingerprinting approach
    """
    
    def __init__(self, interface: str = "wlan0"):
        self.interface = interface
        self.logger = logging.getLogger(f"{__name__}.WiFiScanner")
        
    def enable_monitor_mode(self) -> bool:
        """
        Enable monitor mode on the WiFi interface
        Works with standard Raspberry Pi WiFi (no extra antennas needed)
        Falls back gracefully to managed mode if monitor mode fails
        """
        try:
            import subprocess
            
            self.logger.info("Attempting to enable monitor mode...")
            
            # Method 1: Try using iw (modern approach, works with standard Pi WiFi)
            try:
                # Check if interface supports monitor mode
                result = subprocess.run(
                    ["iw", "phy", "phy0", "info"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if "monitor" in result.stdout.lower():
                    self.logger.info("Interface supports monitor mode")
                    
                    # Create a monitor interface
                    subprocess.run(["sudo", "iw", "dev", self.interface, "interface", "add", "mon0", "type", "monitor"],
                                 capture_output=True, timeout=5)
                    subprocess.run(["sudo", "ip", "link", "set", "mon0", "up"],
                                 capture_output=True, timeout=5)
                    
                    # Check if it worked
                    result = subprocess.run(["ip", "link", "show", "mon0"],
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        self.interface = "mon0"
                        self.logger.info(f"Monitor mode enabled on {self.interface}")
                        return True
            except Exception as e:
                self.logger.debug(f"iw method failed: {e}")
            
            # Method 2: Try using ip commands (alternative approach)
            try:
                subprocess.run(["sudo", "ip", "link", "set", self.interface, "down"], 
                             capture_output=True, timeout=5)
                subprocess.run(["sudo", "iw", self.interface, "set", "type", "monitor"], 
                             capture_output=True, timeout=5)
                subprocess.run(["sudo", "ip", "link", "set", self.interface, "up"], 
                             capture_output=True, timeout=5)
                
                # Verify it worked
                result = subprocess.run(["iw", self.interface, "info"],
                                      capture_output=True, text=True, timeout=5)
                if "type monitor" in result.stdout:
                    self.logger.info(f"Monitor mode enabled on {self.interface} using iw")
                    return True
            except Exception as e:
                self.logger.debug(f"iw method (alternative) failed: {e}")
            
            # If we get here, monitor mode failed
            self.logger.warning("Monitor mode not available")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to enable monitor mode: {e}")
            self.logger.warning("Falling back to managed mode scanning (still works!)")
            return False
    
    def scan_wifi_devices(self) -> List[Dict]:
        """
        Scan for WiFi devices and return signal strength data
        Uses scapy for packet sniffing in monitor mode, or falls back to managed mode
        Works with standard Raspberry Pi WiFi (no extra antennas needed)
        """
        try:
            from scapy.all import sniff, Dot11, Dot11Elt, RadioTap
            
            devices = {}
            scan_count = 0
            
            def packet_handler(pkt):
                nonlocal scan_count
                scan_count += 1
                
                if pkt.haslayer(Dot11):
                    # Get MAC address - try multiple fields
                    mac = None
                    if pkt.addr2 and pkt.addr2 != "ff:ff:ff:ff:ff:ff":
                        mac = pkt.addr2
                    elif pkt.addr1 and pkt.addr1 != "ff:ff:ff:ff:ff:ff":
                        mac = pkt.addr1
                    
                    if not mac:
                        return
                    
                    # Get RSSI (signal strength)
                    rssi = -100  # Default weak signal
                    try:
                        # Try RadioTap layer first (most accurate)
                        if pkt.haslayer(RadioTap):
                            rssi = pkt[RadioTap].dBm_AntSignal
                        # Fallback to Dot11 layer
                        elif hasattr(pkt, 'dBm_AntSignal'):
                            rssi = pkt.dBm_AntSignal
                    except (AttributeError, IndexError):
                        pass
                    
                    # Get SSID if available (for probe requests or beacons)
                    ssid = None
                    try:
                        if pkt.haslayer(Dot11Elt):
                            ssid = pkt[Dot11Elt].info.decode('utf-8', errors='ignore')
                            if ssid == "":
                                ssid = None
                    except:
                        pass
                    
                    # Update device info (keep strongest signal)
                    if mac not in devices or devices[mac]['rssi'] < rssi:
                        devices[mac] = {
                            'mac': mac,
                            'rssi': rssi,
                            'ssid': ssid,
                            'timestamp': time.time()
                        }
            
            # Sniff for 3 seconds
            self.logger.info(f"Starting WiFi scan on {self.interface}...")
            try:
                sniff(iface=self.interface, prn=packet_handler, timeout=3, store=False)
            except PermissionError:
                self.logger.error("Permission denied - run with sudo!")
                return []
            
            self.logger.info(f"Captured {scan_count} packets, found {len(devices)} unique devices")
            
            # If we found very few devices in monitor mode, supplement with managed mode
            if len(devices) < 3:
                self.logger.info("Few devices found, supplementing with managed mode scan...")
                managed_devices = self._scan_wifi_managed_mode()
                # Merge results
                for dev in managed_devices:
                    if dev['mac'] not in devices:
                        devices[dev['mac']] = dev
            
            return list(devices.values())
            
        except ImportError:
            self.logger.warning("Scapy not available, using iw fallback")
            return self._scan_wifi_managed_mode()
        except Exception as e:
            self.logger.error(f"WiFi scan failed: {e}")
            # Always fallback to managed mode
            self.logger.info("Falling back to managed mode...")
            return self._scan_wifi_managed_mode()
    
    def _scan_wifi_managed_mode(self) -> List[Dict]:
        """Fallback scanning using iw in managed mode (replaces deprecated iwlist)"""
        try:
            import subprocess
            
            # Trigger scan
            subprocess.run(
                ["sudo", "iw", "dev", self.interface, "scan"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Get scan results
            result = subprocess.run(
                ["sudo", "iw", "dev", self.interface, "scan", "dump"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            devices = []
            current_device = {}
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                
                # BSS line contains MAC address
                if line.startswith("BSS "):
                    if current_device:
                        devices.append(current_device)
                    # Extract MAC address from "BSS aa:bb:cc:dd:ee:ff(on wlan0)"
                    mac = line.split()[1].split('(')[0]
                    current_device = {'mac': mac, 'timestamp': time.time()}
                
                # Signal strength line
                elif line.startswith("signal:"):
                    # Extract signal strength
                    try:
                        rssi_str = line.split(":")[1].strip().split()[0]
                        rssi = float(rssi_str)
                        current_device['rssi'] = int(rssi)
                    except:
                        current_device['rssi'] = -100
                elif "ESSID:" in line:
                    ssid = line.split("ESSID:")[1].strip('"')
                    current_device['ssid'] = ssid
            
            if current_device:
                devices.append(current_device)
            
            return devices
            
        except Exception as e:
            self.logger.error(f"Managed mode scan failed: {e}")
            return []


class BluetoothScanner:
    """Bluetooth Low Energy scanner for device detection"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.BluetoothScanner")
    
    def scan_bluetooth_devices(self, duration: int = 5) -> List[Dict]:
        """Scan for Bluetooth devices"""
        try:
            from bluepy.btle import Scanner, DefaultDelegate
            
            class ScanDelegate(DefaultDelegate):
                def __init__(self):
                    DefaultDelegate.__init__(self)
            
            scanner = Scanner().withDelegate(ScanDelegate())
            self.logger.info(f"Starting Bluetooth scan for {duration} seconds...")
            devices_raw = scanner.scan(duration)
            
            devices = []
            for dev in devices_raw:
                devices.append({
                    'mac': dev.addr,
                    'rssi': dev.rssi,
                    'timestamp': time.time()
                })
            
            return devices
            
        except ImportError:
            self.logger.warning("bluepy not available, trying pybluez fallback")
            return self._scan_bluetooth_pybluez()
        except Exception as e:
            self.logger.error(f"Bluetooth scan failed: {e}")
            return []
    
    def _scan_bluetooth_pybluez(self) -> List[Dict]:
        """Fallback Bluetooth scanning using system commands"""
        try:
            import subprocess
            result = subprocess.run(
                ["sudo", "hcitool", "scan", "--flush"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            devices = []
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 1:
                        devices.append({
                            'mac': parts[0],
                            'rssi': -70,  # Default value, need lescan for RSSI
                            'timestamp': time.time()
                        })
            
            return devices
            
        except Exception as e:
            self.logger.error(f"Bluetooth fallback scan failed: {e}")
            return []


class TriangulationClient:
    """
    Main client that combines WiFi and Bluetooth scanning
    and sends data to the server for triangulation
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.node_id = config['node_id']
        self.node_position = config['position']  # {'x': 0, 'y': 0, 'z': 0}
        self.server_url = config['server_url']
        self.scan_interval = config.get('scan_interval', 5)  # seconds
        
        self.wifi_scanner = WiFiScanner(config.get('wifi_interface', 'wlan0'))
        self.bluetooth_scanner = BluetoothScanner()
        
        self.logger = logging.getLogger(f"{__name__}.TriangulationClient")
        
        # FIND3-inspired: Keep history for better accuracy
        self.scan_history = []
        self.max_history = 100
    
    def anonymize_mac(self, mac: str) -> str:
        """
        Anonymize MAC address using hash for privacy
        Can be disabled if not needed
        """
        if self.config.get('anonymize_mac', False):
            return hashlib.sha256(mac.encode()).hexdigest()[:16]
        return mac
    
    def scan_all_devices(self) -> List[ScanResult]:
        """Perform a complete scan of WiFi and Bluetooth devices"""
        results = []
        timestamp = time.time()
        
        # Scan WiFi devices
        wifi_devices = self.wifi_scanner.scan_wifi_devices()
        for device in wifi_devices:
            result = ScanResult(
                mac_address=self.anonymize_mac(device['mac']),
                device_type='wifi',
                rssi=device['rssi'],
                timestamp=timestamp,
                node_id=self.node_id,
                node_position=self.node_position,
                ssid=device.get('ssid'),
                frequency=device.get('frequency')
            )
            results.append(result)
        
        # Scan Bluetooth devices
        bt_devices = self.bluetooth_scanner.scan_bluetooth_devices()
        for device in bt_devices:
            result = ScanResult(
                mac_address=self.anonymize_mac(device['mac']),
                device_type='bluetooth',
                rssi=device['rssi'],
                timestamp=timestamp,
                node_id=self.node_id,
                node_position=self.node_position
            )
            results.append(result)
        
        self.logger.info(f"Scanned {len(wifi_devices)} WiFi and {len(bt_devices)} Bluetooth devices")
        return results
    
    def send_to_server(self, results: List[ScanResult]) -> bool:
        """Send scan results to the server"""
        try:
            data = {
                'node_id': self.node_id,
                'timestamp': time.time(),
                'results': [r.to_dict() for r in results]
            }
            
            response = requests.post(
                f"{self.server_url}/api/scan",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully sent {len(results)} scan results to server")
                return True
            else:
                self.logger.error(f"Server returned status {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send data to server: {e}")
            return False
    
    def run(self):
        """Main loop: scan and send data continuously"""
        self.logger.info(f"Starting triangulation client {self.node_id}")
        self.logger.info(f"Node position: {self.node_position}")
        self.logger.info(f"Server URL: {self.server_url}")
        
        # Try to enable monitor mode for better WiFi scanning
        self.wifi_scanner.enable_monitor_mode()
        
        try:
            while True:
                # Perform scan
                results = self.scan_all_devices()
                
                # Add to history (FIND3-inspired smoothing)
                self.scan_history.append(results)
                if len(self.scan_history) > self.max_history:
                    self.scan_history.pop(0)
                
                # Send to server
                if results:
                    self.send_to_server(results)
                
                # Wait before next scan
                time.sleep(self.scan_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Shutting down client...")
        except Exception as e:
            self.logger.error(f"Client error: {e}")


def main():
    """Entry point for the client"""
    import yaml
    import sys
    
    # Load configuration
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'client_config.yml'
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        # Create default config
        config = {
            'node_id': 'node_1',
            'position': {'x': 0, 'y': 0, 'z': 0},
            'server_url': 'http://localhost:5000',
            'wifi_interface': 'wlan0',
            'scan_interval': 5,
            'anonymize_mac': False
        }
        logger.warning(f"Config file not found, using defaults")
    
    # Start client
    client = TriangulationClient(config)
    client.run()


if __name__ == '__main__':
    main()
