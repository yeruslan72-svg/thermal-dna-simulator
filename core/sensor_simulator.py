"""Sensor data simulation module"""
import numpy as np
from typing import Dict, Tuple
from config.constants import IndustrialConfig
from utils.logger import logger

class SensorSimulator:
    """Generates realistic sensor data"""
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        self.cycle = 0
    
    def generate_data(self, cycle: int) -> Tuple[Dict, Dict, float]:
        """Generate sensor data based on cycle"""
        try:
            if cycle < 30:
                # Normal operation
                data = self._normal_operation()
            elif cycle < 60:
                # Gradual degradation
                data = self._degradation_phase(cycle - 30)
            else:
                # Critical condition
                data = self._critical_condition()
            
            self.cycle = cycle
            return data
            
        except Exception as e:
            logger.error(f"Data generation error: {e}")
            return {}, {}, 0
    
    def _normal_operation(self) -> Tuple[Dict, Dict, float]:
        """Generate normal operation data"""
        vibration = {
            k: max(0.1, 1.0 + np.random.normal(0, 0.2))
            for k in IndustrialConfig.VIBRATION_SENSORS.keys()
        }
        
        temperature = {
            k: max(20, 65 + np.random.normal(0, 3))
            for k in IndustrialConfig.THERMAL_SENSORS.keys()
        }
        
        noise = max(30, 65 + np.random.normal(0, 2))
        
        return vibration, temperature, noise
    
    def _degradation_phase(self, degradation_index: int) -> Tuple[Dict, Dict, float]:
        """Generate degradation phase data"""
        degradation = degradation_index * 0.05
        
        vibration = {
            k: max(0.1, 1.0 + degradation + np.random.normal(0, 0.3))
            for k in IndustrialConfig.VIBRATION_SENSORS.keys()
        }
        
        temperature = {
            k: max(20, 65 + degradation * 2 + np.random.normal(0, 4))
            for k in IndustrialConfig.THERMAL_SENSORS.keys()
        }
        
        noise = max(30, 70 + degradation * 2 + np.random.normal(0, 3))
        
        return vibration, temperature, noise
    
    def _critical_condition(self) -> Tuple[Dict, Dict, float]:
        """Generate critical condition data"""
        vibration = {
            k: max(0.1, 5.0 + np.random.normal(0, 0.5))
            for k in IndustrialConfig.VIBRATION_SENSORS.keys()
        }
        
        temperature = {
            k: max(20, 95 + np.random.normal(0, 5))
            for k in IndustrialConfig.THERMAL_SENSORS.keys()
        }
        
        noise = max(30, 95 + np.random.normal(0, 5))
        
        return vibration, temperature, noise
    
    def inject_fault(self, sensor_type: str, severity: float = 1.0):
        """Inject fault for testing"""
        # Implementation for fault injection
        pass
