# modules/config.py
"""Configuration and constants for AVCS DNA Industrial Monitor"""
import os
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Optional

class Settings:
    """Application settings"""
    
    # App info
    APP_NAME = "AVCS DNA Industrial Monitor"
    APP_VERSION = "6.0.0"
    APP_ICON = "🏭"
    
    # Simulation settings
    SIMULATION_CYCLES = 100
    UPDATE_INTERVAL = 0.5
    MAX_HISTORY_POINTS = 1000
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    MODELS_DIR = BASE_DIR / "models"
    LOGS_DIR = BASE_DIR / "logs"
    DATA_DIR = BASE_DIR / "data"
    
    # Create directories if they don't exist
    MODELS_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
    
    # Model path
    MODEL_PATH = str(MODELS_DIR / "isolation_forest.pkl")
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = str(LOGS_DIR / "app.log")
    
    # Alert settings
    ENABLE_EMAIL_ALERTS = False
    ALERT_EMAIL = "admin@example.com"
    
    @classmethod
    def get_all(cls) -> Dict:
        """Get all settings as dictionary"""
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }

settings = Settings()

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    
    @property
    def color(self) -> str:
        """Get color for alert level"""
        colors = {
            "info": "#17a2b8",
            "success": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545",
            "critical": "#dc3545"
        }
        return colors.get(self.value, "#6c757d")
    
    @property
    def icon(self) -> str:
        """Get icon for alert level"""
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🔴"
        }
        return icons.get(self.value, "📢")

class SystemStatus(Enum):
    """System operational status"""
    STANDBY = ("🟢 STANDBY", "blue")
    NORMAL = ("✅ NORMAL", "green")
    WARNING = ("⚠️ WARNING", "orange")
    CRITICAL = ("🚨 CRITICAL", "red")
    ERROR = ("❌ ERROR", "darkred")
    MAINTENANCE = ("🔧 MAINTENANCE", "purple")
    
    def __init__(self, label: str, color: str):
        self.label = label
        self.color = color
    
    @property
    def value(self) -> str:
        return self.label

@dataclass
class SensorLimits:
    """Sensor threshold limits"""
    normal: float
    warning: float
    critical: float
    
    def __post_init__(self):
        """Validate limits"""
        if self.normal >= self.warning:
            raise ValueError("normal must be less than warning")
        if self.warning >= self.critical:
            raise ValueError("warning must be less than critical")
    
    def get_level(self, value: float) -> AlertLevel:
        """Get alert level based on value"""
        if value < self.normal:
            return AlertLevel.SUCCESS
        elif value < self.warning:
            return AlertLevel.INFO
        elif value < self.critical:
            return AlertLevel.WARNING
        else:
            return AlertLevel.ERROR
    
    def get_percentage(self, value: float) -> float:
        """Get percentage of critical threshold"""
        return min(100, (value / self.critical) * 100)

class IndustrialConfig:
    """Industrial system configuration"""
    
    # Vibration sensors with limits (mm/s)
    VIBRATION_SENSORS = {
        'VIB_MOTOR_DRIVE': ('Motor Drive End', SensorLimits(2.0, 4.0, 6.0)),
        'VIB_MOTOR_NONDRIVE': ('Motor Non-Drive End', SensorLimits(2.0, 4.0, 6.0)),
        'VIB_PUMP_INLET': ('Pump Inlet Bearing', SensorLimits(2.0, 4.0, 6.0)),
        'VIB_PUMP_OUTLET': ('Pump Outlet Bearing', SensorLimits(2.0, 4.0, 6.0))
    }

    # Thermal sensors with limits (°C)
    THERMAL_SENSORS = {
        'TEMP_MOTOR_WINDING': ('Motor Winding', SensorLimits(70, 85, 100)),
        'TEMP_MOTOR_BEARING': ('Motor Bearing', SensorLimits(70, 85, 100)),
        'TEMP_PUMP_BEARING': ('Pump Bearing', SensorLimits(70, 85, 100)),
        'TEMP_PUMP_CASING': ('Pump Casing', SensorLimits(70, 85, 100))
    }

    # MR Dampers
    MR_DAMPERS = {
        'DAMPER_FL': 'Front-Left (LORD RD-8040)',
        'DAMPER_FR': 'Front-Right (LORD RD-8040)',
        'DAMPER_RL': 'Rear-Left (LORD RD-8040)',
        'DAMPER_RR': 'Rear-Right (LORD RD-8040)'
    }

    # Acoustic sensor (dB)
    ACOUSTIC_SENSOR = ('Pump Acoustic Noise', SensorLimits(70, 85, 100))
    
    # Damper force levels (N)
    DAMPER_FORCES = {
        'standby': 500,
        'normal': 1000,
        'warning': 4000,
        'critical': 8000
    }
    
    # Simulation phases
    SIMULATION_PHASES = {
        'normal': (0, 30, "Normal Operation"),
        'degradation': (30, 60, "Gradual Degradation"),
        'critical': (60, 100, "Critical Condition")
    }
    
    @classmethod
    def get_sensor_by_id(cls, sensor_id: str) -> Tuple[str, SensorLimits]:
        """Get sensor info by ID"""
        if sensor_id in cls.VIBRATION_SENSORS:
            return cls.VIBRATION_SENSORS[sensor_id]
        elif sensor_id in cls.THERMAL_SENSORS:
            return cls.THERMAL_SENSORS[sensor_id]
        elif sensor_id == 'NOISE':
            return cls.ACOUSTIC_SENSOR
        raise KeyError(f"Sensor {sensor_id} not found")
    
    @classmethod
    def get_all_sensors(cls) -> Dict:
        """Get all sensors"""
        sensors = {}
        sensors.update(cls.VIBRATION_SENSORS)
        sensors.update(cls.THERMAL_SENSORS)
        sensors['NOISE'] = cls.ACOUSTIC_SENSOR
        return sensors

# Initialize config
industrial_config = IndustrialConfig()
