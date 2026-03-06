"""Constants and enums for the application"""
from enum import Enum
from dataclasses import dataclass

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class SystemStatus(Enum):
    """System operational status"""
    STANDBY = "🟢 STANDBY"
    NORMAL = "✅ NORMAL"
    WARNING = "⚠️ WARNING"
    CRITICAL = "🚨 CRITICAL"
    ERROR = "❌ ERROR"
    MAINTENANCE = "🔧 MAINTENANCE"

@dataclass
class SensorLimits:
    """Sensor threshold limits"""
    normal: float
    warning: float
    critical: float
    
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

class IndustrialConfig:
    """Industrial system configuration"""
    
    # Sensors with their limits
    VIBRATION_SENSORS = {
        'VIB_MOTOR_DRIVE': ('Motor Drive End', SensorLimits(2.0, 4.0, 6.0)),
        'VIB_MOTOR_NONDRIVE': ('Motor Non-Drive End', SensorLimits(2.0, 4.0, 6.0)),
        'VIB_PUMP_INLET': ('Pump Inlet Bearing', SensorLimits(2.0, 4.0, 6.0)),
        'VIB_PUMP_OUTLET': ('Pump Outlet Bearing', SensorLimits(2.0, 4.0, 6.0))
    }

    THERMAL_SENSORS = {
        'TEMP_MOTOR_WINDING': ('Motor Winding', SensorLimits(70, 85, 100)),
        'TEMP_MOTOR_BEARING': ('Motor Bearing', SensorLimits(70, 85, 100)),
        'TEMP_PUMP_BEARING': ('Pump Bearing', SensorLimits(70, 85, 100)),
        'TEMP_PUMP_CASING': ('Pump Casing', SensorLimits(70, 85, 100))
    }

    MR_DAMPERS = {
        'DAMPER_FL': 'Front-Left (LORD RD-8040)',
        'DAMPER_FR': 'Front-Right (LORD RD-8040)',
        'DAMPER_RL': 'Rear-Left (LORD RD-8040)',
        'DAMPER_RR': 'Rear-Right (LORD RD-8040)'
    }

    ACOUSTIC_SENSOR = ('Pump Acoustic Noise (dB)', SensorLimits(70, 85, 100))
    
    # Damper force levels
    DAMPER_FORCES = {
        'standby': 500,
        'normal': 1000, 
        'warning': 4000,
        'critical': 8000
    }
