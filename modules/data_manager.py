# modules/data_manager.py
"""Data management module for AVCS DNA Industrial Monitor"""
import pandas as pd
import numpy as np
from datetime import datetime
from threading import Lock
from typing import Dict, List, Optional, Any
import json
from pathlib import Path

from modules.config import settings, industrial_config
from utils.logger import logger

class DataManager:
    """Thread-safe data manager for sensor readings"""
    
    def __init__(self):
        self.lock = Lock()
        self.data_file = settings.DATA_DIR / "readings.json"
        self.reset()
        logger.info("DataManager initialized")
    
    def reset(self):
        """Reset all data storage"""
        with self.lock:
            # Initialize DataFrames
            self.vibration_data = pd.DataFrame(
                columns=[k for k in industrial_config.VIBRATION_SENSORS.keys()]
            )
            self.temperature_data = pd.DataFrame(
                columns=[k for k in industrial_config.THERMAL_SENSORS.keys()]
            )
            self.noise_data = pd.DataFrame(
                columns=[industrial_config.ACOUSTIC_SENSOR[0]]
            )
            
            # Damper data
            self.damper_forces = {
                damper: 0 for damper in industrial_config.MR_DAMPERS.keys()
            }
            self.damper_history = pd.DataFrame(
                columns=list(industrial_config.MR_DAMPERS.keys())
            )
            
            # Risk and alerts
            self.risk_history = []
            self.alerts = []
            self.predictions = []
            
            # Metadata
            self.last_update = datetime.now()
            self.total_readings = 0
            self.error_count = 0
            
            logger.info("Data manager reset")
    
    def add_reading(self, cycle: int, vibration: Dict, temperature: Dict, 
                   noise: float, damper_forces: Dict, risk_index: int,
                   prediction: Optional[Dict] = None):
        """Add new sensor readings"""
        with self.lock:
            try:
                # Add to DataFrames
                self.vibration_data.loc[cycle] = vibration
                self.temperature_data.loc[cycle] = temperature
                self.noise_data.loc[cycle] = [noise]
                self.damper_history.loc[cycle] = damper_forces
                self.risk_history.append(risk_index)
                
                if prediction:
                    self.predictions.append(prediction)
                
                # Update metadata
                self.total_readings += 1
                self.last_update = datetime.now()
                
                # Trim history to prevent memory issues
                max_points = settings.MAX_HISTORY_POINTS
                if len(self.vibration_data) > max_points:
                    self.vibration_data = self.vibration_data.iloc[-max_points:]
                    self.temperature_data = self.temperature_data.iloc[-max_points:]
                    self.noise_data = self.noise_data.iloc[-max_points:]
                    self.damper_history = self.damper_history.iloc[-max_points:]
                    self.risk_history = self.risk_history[-max_points:]
                    self.predictions = self.predictions[-max_points:]
                
            except Exception as e:
                logger.error(f"Error adding reading: {e}")
                self.error_count += 1
    
    def add_alert(self, level: str, message: str, data: Optional[Dict] = None):
        """Add system alert"""
        with self.lock:
            alert = {
                'id': f"alert_{datetime.now().timestamp()}",
                'time': datetime.now().isoformat(),
                'level': level,
                'message': message,
                'data': data or {},
                'acknowledged': False,
                'resolved': False
            }
            self.alerts.append(alert)
            
            # Keep last 100 alerts
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
            
            logger.warning(f"Alert [{level}]: {message}")
    
    def get_recent_alerts(self, count: int = 5, include_resolved: bool = False) -> List[Dict]:
        """Get most recent alerts"""
        with self.lock:
            if include_resolved:
                return self.alerts[-count:] if self.alerts else []
            else:
                active = [a for a in self.alerts if not a.get('resolved', False)]
                return active[-count:] if active else []
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        with self.lock:
            for alert in self.alerts:
                if alert['id'] == alert_id:
                    alert['acknowledged'] = True
                    logger.info(f"Alert {alert_id} acknowledged")
                    break
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        with self.lock:
            for alert in self.alerts:
                if alert['id'] == alert_id:
                    alert['resolved'] = True
                    alert['resolved_at'] = datetime.now().isoformat()
                    logger.info(f"Alert {alert_id} resolved")
                    break
    
    def get_statistics(self) -> Dict:
        """Get system statistics"""
        with self.lock:
            active_alerts = len([a for a in self.alerts if not a.get('resolved', False)])
            
            stats = {
                'total_readings': self.total_readings,
                'current_risk': self.risk_history[-1] if self.risk_history else 0,
                'avg_risk': sum(self.risk_history) / len(self.risk_history) if self.risk_history else 0,
                'max_risk': max(self.risk_history) if self.risk_history else 0,
                'min_risk': min(self.risk_history) if self.risk_history else 0,
                'alert_count': len(self.alerts),
                'active_alerts': active_alerts,
                'uptime_seconds': (datetime.now() - self.last_update).total_seconds() if self.last_update else 0,
                'error_count': self.error_count,
                'data_points': len(self.vibration_data)
            }
            
            # Add sensor statistics
            if not self.vibration_data.empty:
                stats['avg_vibration'] = self.vibration_data.mean().mean()
                stats['max_vibration'] = self.vibration_data.max().max()
            
            if not self.temperature_data.empty:
                stats['avg_temperature'] = self.temperature_data.mean().mean()
                stats['max_temperature'] = self.temperature_data.max().max()
            
            return stats
    
    def get_latest_readings(self) -> Dict:
        """Get latest sensor readings"""
        with self.lock:
            readings = {}
            
            if not self.vibration_data.empty:
                readings['vibration'] = self.vibration_data.iloc[-1].to_dict()
            
            if not self.temperature_data.empty:
                readings['temperature'] = self.temperature_data.iloc[-1].to_dict()
            
            if not self.noise_data.empty:
                readings['noise'] = self.noise_data.iloc[-1].iloc[0]
            
            readings['damper_forces'] = self.damper_forces
            readings['risk'] = self.risk_history[-1] if self.risk_history else 0
            
            return readings
    
    def get_data_range(self, start: int, end: int) -> Dict:
        """Get data within range"""
        with self.lock:
            return {
                'vibration': self.vibration_data.iloc[start:end] if not self.vibration_data.empty else pd.DataFrame(),
                'temperature': self.temperature_data.iloc[start:end] if not self.temperature_data.empty else pd.DataFrame(),
                'noise': self.noise_data.iloc[start:end] if not self.noise_data.empty else pd.DataFrame(),
                'risk': self.risk_history[start:end] if self.risk_history else []
            }
    
    def save_to_file(self):
        """Save data to file"""
        try:
            data = {
                'metadata': {
                    'last_update': self.last_update.isoformat(),
                    'total_readings': self.total_readings,
                    'error_count': self.error_count
                },
                'alerts': self.alerts[-50:],  # Save last 50 alerts
                'statistics': self.get_statistics()
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Data saved to {self.data_file}")
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def load_from_file(self):
        """Load data from file"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                # Restore alerts
                if 'alerts' in data:
                    self.alerts = data['alerts']
                
                logger.info(f"Data loaded from {self.data_file}")
                
        except Exception as e:
            logger.error(f"Error loading data: {e}")
    
    def clear_history(self, keep_last: int = 100):
        """Clear old history data"""
        with self.lock:
            if len(self.vibration_data) > keep_last:
                self.vibration_data = self.vibration_data.iloc[-keep_last:]
                self.temperature_data = self.temperature_data.iloc[-keep_last:]
                self.noise_data = self.noise_data.iloc[-keep_last:]
                self.damper_history = self.damper_history.iloc[-keep_last:]
                self.risk_history = self.risk_history[-keep_last:]
                self.predictions = self.predictions[-keep_last:]
            
            logger.info(f"History cleared, kept last {keep_last} points")

# Create singleton instance
data_manager = DataManager()
