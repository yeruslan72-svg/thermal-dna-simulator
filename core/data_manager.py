"""Data management module"""
import pandas as pd
from datetime import datetime
from threading import Lock
from typing import Dict, List, Optional
from config.settings import settings
from utils.logger import logger

class DataManager:
    """Thread-safe data manager for sensor readings"""
    
    def __init__(self):
        self.lock = Lock()
        self.reset()
    
    def reset(self):
        """Reset all data storage"""
        with self.lock:
            from config.constants import IndustrialConfig
            
            self.vibration_data = pd.DataFrame(
                columns=[k for k in IndustrialConfig.VIBRATION_SENSORS.keys()]
            )
            self.temperature_data = pd.DataFrame(
                columns=[k for k in IndustrialConfig.THERMAL_SENSORS.keys()]
            )
            self.noise_data = pd.DataFrame(
                columns=[IndustrialConfig.ACOUSTIC_SENSOR[0]]
            )
            self.damper_forces = {
                damper: 0 for damper in IndustrialConfig.MR_DAMPERS.keys()
            }
            self.damper_history = pd.DataFrame(
                columns=list(IndustrialConfig.MR_DAMPERS.keys())
            )
            self.risk_history = []
            self.alerts = []
            self.last_update = datetime.now()
            
            logger.info("Data manager reset")
    
    def add_reading(self, cycle: int, vibration: Dict, temperature: Dict, 
                   noise: float, damper_forces: Dict, risk_index: int):
        """Add new sensor readings"""
        with self.lock:
            # Add new data
            self.vibration_data.loc[cycle] = vibration
            self.temperature_data.loc[cycle] = temperature
            self.noise_data.loc[cycle] = [noise]
            self.damper_history.loc[cycle] = damper_forces
            self.risk_history.append(risk_index)
            
            # Trim history
            max_points = settings.MAX_HISTORY_POINTS
            if len(self.vibration_data) > max_points:
                self.vibration_data = self.vibration_data.iloc[-max_points:]
                self.temperature_data = self.temperature_data.iloc[-max_points:]
                self.noise_data = self.noise_data.iloc[-max_points:]
                self.damper_history = self.damper_history.iloc[-max_points:]
                self.risk_history = self.risk_history[-max_points:]
    
    def add_alert(self, level: str, message: str):
        """Add system alert"""
        with self.lock:
            self.alerts.append({
                'time': datetime.now(),
                'level': level,
                'message': message
            })
            # Keep last 100 alerts
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
            
            logger.warning(f"Alert [{level}]: {message}")
    
    def get_recent_alerts(self, count: int = 5) -> List[Dict]:
        """Get most recent alerts"""
        with self.lock:
            return self.alerts[-count:] if self.alerts else []
    
    def get_statistics(self) -> Dict:
        """Get system statistics"""
        with self.lock:
            return {
                'total_readings': len(self.vibration_data),
                'current_risk': self.risk_history[-1] if self.risk_history else 0,
                'avg_risk': sum(self.risk_history) / len(self.risk_history) if self.risk_history else 0,
                'max_risk': max(self.risk_history) if self.risk_history else 0,
                'alert_count': len(self.alerts),
                'uptime_seconds': (datetime.now() - self.last_update).total_seconds()
            }
