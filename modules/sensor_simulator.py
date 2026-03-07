# modules/sensor_simulator.py
"""Sensor data simulation for AVCS DNA Industrial Monitor"""
import numpy as np
from typing import Dict, Tuple, Optional, List
from datetime import datetime, timedelta
import random

from modules.config import industrial_config
from utils.logger import logger

class SensorSimulator:
    """Generates realistic industrial sensor data"""
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        random.seed(seed)
        self.cycle = 0
        self.fault_mode = False
        self.fault_type = None
        self.fault_severity = 1.0
        
        # Sensor characteristics
        self.sensor_drift = {
            'vibration': 0.001,
            'temperature': 0.01,
            'noise': 0.005
        }
        
        # Noise levels
        self.noise_levels = {
            'vibration': 0.1,
            'temperature': 0.5,
            'noise': 0.2
        }
        
        logger.info("SensorSimulator initialized")
    
    def generate_data(self, cycle: int) -> Tuple[Dict, Dict, float]:
        """Generate sensor data based on cycle"""
        try:
            self.cycle = cycle
            
            # Determine operation phase
            if cycle < 30:
                # Normal operation
                data = self._normal_operation()
            elif cycle < 60:
                # Gradual degradation
                degradation = (cycle - 30) * 0.05
                data = self._degradation_phase(degradation)
            else:
                # Critical condition
                data = self._critical_condition()
            
            # Apply fault if in fault mode
            if self.fault_mode:
                data = self._apply_fault(data)
            
            # Add realistic noise
            data = self._add_noise(data)
            
            vibration, temperature, noise = data
            
            logger.debug(f"Generated data for cycle {cycle}: noise={noise:.1f}dB")
            
            return vibration, temperature, noise
            
        except Exception as e:
            logger.error(f"Data generation error: {e}")
            return self._fallback_data()
    
    def _normal_operation(self) -> Tuple[Dict, Dict, float]:
        """Generate normal operation data"""
        # Vibration sensors (mm/s)
        vibration = {}
        for sensor in industrial_config.VIBRATION_SENSORS.keys():
            base_value = 1.0 + 0.2 * np.sin(self.cycle * 0.1)  # Small oscillation
            vibration[sensor] = max(0.1, base_value + np.random.normal(0, 0.15))
        
        # Temperature sensors (°C)
        temperature = {}
        for sensor in industrial_config.THERMAL_SENSORS.keys():
            base_value = 65 + 2 * np.sin(self.cycle * 0.05)  # Small oscillation
            temperature[sensor] = max(20, base_value + np.random.normal(0, 2))
        
        # Acoustic noise (dB)
        noise = max(30, 65 + 2 * np.sin(self.cycle * 0.1) + np.random.normal(0, 1.5))
        
        return vibration, temperature, noise
    
    def _degradation_phase(self, degradation: float) -> Tuple[Dict, Dict, float]:
        """Generate degradation phase data"""
        # Vibration increases with degradation
        vibration = {}
        for sensor in industrial_config.VIBRATION_SENSORS.keys():
            base_value = 1.0 + degradation
            variation = 0.3 * np.sin(self.cycle * 0.15)
            vibration[sensor] = max(0.1, base_value + variation + np.random.normal(0, 0.2))
        
        # Temperature increases with degradation
        temperature = {}
        for sensor in industrial_config.THERMAL_SENSORS.keys():
            base_value = 65 + degradation * 2
            variation = 3 * np.sin(self.cycle * 0.1)
            temperature[sensor] = max(20, base_value + variation + np.random.normal(0, 3))
        
        # Noise increases with degradation
        noise = max(30, 70 + degradation * 2 + 2 * np.sin(self.cycle * 0.15) + np.random.normal(0, 2))
        
        return vibration, temperature, noise
    
    def _critical_condition(self) -> Tuple[Dict, Dict, float]:
        """Generate critical condition data"""
        # High vibration with spikes
        vibration = {}
        for sensor in industrial_config.VIBRATION_SENSORS.keys():
            if np.random.random() < 0.1:  # 10% chance of spike
                value = 7.0 + np.random.normal(0, 1)
            else:
                value = 5.0 + 1.5 * np.sin(self.cycle * 0.2) + np.random.normal(0, 0.4)
            vibration[sensor] = max(0.1, value)
        
        # High temperature with variation
        temperature = {}
        for sensor in industrial_config.THERMAL_SENSORS.keys():
            base_value = 95 + 3 * np.sin(self.cycle * 0.15)
            temperature[sensor] = max(20, base_value + np.random.normal(0, 4))
        
        # High noise
        noise = max(30, 95 + 3 * np.sin(self.cycle * 0.2) + np.random.normal(0, 3))
        
        return vibration, temperature, noise
    
    def _add_noise(self, data: Tuple[Dict, Dict, float]) -> Tuple[Dict, Dict, float]:
        """Add realistic noise to readings"""
        vibration, temperature, noise = data
        
        # Add noise to vibration
        for sensor in vibration:
            noise_level = self.noise_levels['vibration'] * (1 + vibration[sensor] / 10)
            vibration[sensor] += np.random.normal(0, noise_level)
        
        # Add noise to temperature
        for sensor in temperature:
            noise_level = self.noise_levels['temperature'] * (1 + temperature[sensor] / 100)
            temperature[sensor] += np.random.normal(0, noise_level)
        
        # Add noise to acoustic
        noise += np.random.normal(0, self.noise_levels['noise'])
        
        return vibration, temperature, noise
    
    def _apply_fault(self, data: Tuple[Dict, Dict, float]) -> Tuple[Dict, Dict, float]:
        """Apply fault to data"""
        vibration, temperature, noise = data
        
        if self.fault_type == 'vibration_spike':
            # Spike in random vibration sensor
            sensor = random.choice(list(vibration.keys()))
            vibration[sensor] *= (2 + self.fault_severity)
            
        elif self.fault_type == 'temperature_drift':
            # Temperature drift in all sensors
            for sensor in temperature:
                temperature[sensor] += 10 * self.fault_severity
                
        elif self.fault_type == 'sensor_failure':
            # Sensor failure (reading stuck or zero)
            sensor = random.choice(list(vibration.keys()))
            if random.random() < 0.5:
                vibration[sensor] = 0
            else:
                vibration[sensor] = vibration[sensor]  # Stuck value
                
        elif self.fault_type == 'noise_burst':
            # Burst of noise
            noise += 20 * self.fault_severity
        
        return vibration, temperature, noise
    
    def _fallback_data(self) -> Tuple[Dict, Dict, float]:
        """Generate fallback data in case of error"""
        vibration = {sensor: 1.0 for sensor in industrial_config.VIBRATION_SENSORS.keys()}
        temperature = {sensor: 65.0 for sensor in industrial_config.THERMAL_SENSORS.keys()}
        noise = 65.0
        return vibration, temperature, noise
    
    def inject_fault(self, fault_type: str, severity: float = 1.0, duration: Optional[int] = None):
        """Inject fault for testing"""
        self.fault_mode = True
        self.fault_type = fault_type
        self.fault_severity = min(2.0, max(0.1, severity))
        
        logger.warning(f"Fault injected: {fault_type} (severity: {severity})")
        
        if duration:
            # Schedule fault removal after duration
            import threading
            timer = threading.Timer(duration, self.clear_fault)
            timer.daemon = True
            timer.start()
    
    def clear_fault(self):
        """Clear current fault"""
        self.fault_mode = False
        self.fault_type = None
        self.fault_severity = 1.0
        logger.info("Fault cleared")
    
    def get_phase_name(self, cycle: int) -> str:
        """Get name of current simulation phase"""
        for phase, (start, end, name) in industrial_config.SIMULATION_PHASES.items():
            if start <= cycle < end:
                return name
        return "Unknown Phase"
    
    def get_sensor_trends(self, history_length: int = 10) -> Dict:
        """Get current sensor trends"""
        # This would normally use historical data
        # Simplified version
        return {
            'vibration': random.uniform(-0.5, 0.5),
            'temperature': random.uniform(-1, 1),
            'noise': random.uniform(-2, 2)
        }

# Create singleton instance
sensor_simulator = SensorSimulator()
