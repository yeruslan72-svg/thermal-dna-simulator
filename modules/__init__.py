# modules/__init__.py
"""Modules package for AVCS DNA Industrial Monitor v6.0

This package contains all core modules for the industrial monitoring system:
- config: Configuration and constants
- data_manager: Data management and storage
- ai_model: Machine learning models
- sensor_simulator: Sensor data simulation
- alert_system: Alert management
- ui_components: Reusable UI components
"""

# Version info
__version__ = "6.0.0"
__author__ = "Yeruslan Technologies"

# Import main classes and functions for easy access
from .config import (
    Settings,
    settings,
    AlertLevel,
    SystemStatus,
    SensorLimits,
    IndustrialConfig,
    industrial_config
)

from .data_manager import (
    DataManager,
    data_manager
)

from .ai_model import (
    AIModelManager,
    ai_model
)

from .sensor_simulator import (
    SensorSimulator,
    sensor_simulator
)

from .alert_system import (
    AlertSystem,
    AlertRule,
    Alert,
    alert_system,
    render_alert_panel
)

from .ui_components import (
    UIComponents,
    ui_components
)

# Define what gets imported with "from modules import *"
__all__ = [
    # Config
    'Settings',
    'settings',
    'AlertLevel',
    'SystemStatus',
    'SensorLimits',
    'IndustrialConfig',
    'industrial_config',
    
    # Data Manager
    'DataManager',
    'data_manager',
    
    # AI Model
    'AIModelManager',
    'ai_model',
    
    # Sensor Simulator
    'SensorSimulator',
    'sensor_simulator',
    
    # Alert System
    'AlertSystem',
    'AlertRule',
    'Alert',
    'alert_system',
    'render_alert_panel',
    
    # UI Components
    'UIComponents',
    'ui_components',
]

# Package metadata
__all__.extend(['__version__', '__author__'])

# Initialize package
def initialize_package():
    """Initialize all modules in the correct order"""
    # This ensures all singletons are created in the right order
    from .config import settings
    from .data_manager import data_manager
    from .ai_model import ai_model
    from .sensor_simulator import sensor_simulator
    from .alert_system import alert_system
    from .ui_components import ui_components
    
    return {
        'settings': settings,
        'data_manager': data_manager,
        'ai_model': ai_model,
        'sensor_simulator': sensor_simulator,
        'alert_system': alert_system,
        'ui_components': ui_components
    }

# Run initialization when package is imported
_initialized_modules = initialize_package()

# Helper function to get module info
def get_package_info():
    """Get information about the modules package"""
    return {
        'name': 'modules',
        'version': __version__,
        'author': __author__,
        'modules': list(__all__),
        'initialized': all(v is not None for v in _initialized_modules.values())
    }

# Helper function to reset all modules (useful for testing)
def reset_all_modules():
    """Reset all modules to initial state"""
    from .data_manager import data_manager
    from .ai_model import ai_model
    from .sensor_simulator import sensor_simulator
    from .alert_system import alert_system
    
    data_manager.reset()
    ai_model.initialize_model()
    # Sensor simulator doesn't need reset
    # Alert system doesn't need reset
    
    return True

# Context manager for temporary module configuration
class module_config:
    """Context manager for temporary module configuration"""
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.old_values = {}
    
    def __enter__(self):
        from .config import settings
        # Save old values and set new ones
        for key, value in self.kwargs.items():
            if hasattr(settings, key):
                self.old_values[key] = getattr(settings, key)
                setattr(settings, key, value)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        from .config import settings
        # Restore old values
        for key, value in self.old_values.items():
            setattr(settings, key, value)

# Log package initialization
try:
    from utils.logger import logger
    logger.info(f"Modules package v{__version__} initialized successfully")
    logger.info(f"Available modules: {', '.join(__all__)}")
except ImportError:
    # Logger not available yet
    print(f"Modules package v{__version__} initialized")
