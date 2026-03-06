# thermal_dna_app.py - AVCS DNA Industrial Monitor v6.0 (Enterprise Edition)
import streamlit as st
import numpy as np
import pandas as pd
import time
import logging
from datetime import datetime
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from sklearn.ensemble import IsolationForest
import plotly.graph_objects as go
import plotly.express as px
from threading import Lock

# --- LOGGING CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ENUMS & CONSTANTS ---
class SystemStatus(Enum):
    STANDBY = "🟢 STANDBY"
    NORMAL = "✅ NORMAL"
    WARNING = "⚠️ WARNING"
    CRITICAL = "🚨 CRITICAL"
    ERROR = "❌ ERROR"
    MAINTENANCE = "🔧 MAINTENANCE"

class AlertLevel(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

@dataclass
class SensorLimits:
    """Data class for sensor limits"""
    normal: float
    warning: float
    critical: float
    
    def get_level(self, value: float) -> AlertLevel:
        if value < self.normal:
            return AlertLevel.SUCCESS
        elif value < self.warning:
            return AlertLevel.INFO
        elif value < self.critical:
            return AlertLevel.WARNING
        else:
            return AlertLevel.ERROR

# --- INDUSTRIAL CONFIGURATION ---
class IndustrialConfig:
    """Industrial system configuration with validation"""
    
    # Sensor configurations with limits
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
    
    # Simulation parameters
    SIMULATION_CYCLES = 100
    UPDATE_INTERVAL = 0.5  # seconds
    MAX_HISTORY_POINTS = 1000

# --- DATA MANAGER ---
class DataManager:
    """Manages all data storage and retrieval with thread safety"""
    
    def __init__(self):
        self.lock = Lock()
        self.reset()
    
    def reset(self):
        """Reset all data"""
        with self.lock:
            self.vibration_data = pd.DataFrame(columns=[k for k in IndustrialConfig.VIBRATION_SENSORS.keys()])
            self.temperature_data = pd.DataFrame(columns=[k for k in IndustrialConfig.THERMAL_SENSORS.keys()])
            self.noise_data = pd.DataFrame(columns=[IndustrialConfig.ACOUSTIC_SENSOR[0]])
            self.damper_forces = {damper: 0 for damper in IndustrialConfig.MR_DAMPERS.keys()}
            self.damper_history = pd.DataFrame(columns=list(IndustrialConfig.MR_DAMPERS.keys()))
            self.risk_history = []
            self.alerts = []
            self.last_update = datetime.now()
    
    def add_reading(self, cycle: int, vibration: Dict, temperature: Dict, noise: float, 
                    damper_forces: Dict, risk_index: int):
        """Add new sensor readings"""
        with self.lock:
            # Limit history size to prevent memory issues
            max_points = IndustrialConfig.MAX_HISTORY_POINTS
            
            # Add new data
            self.vibration_data.loc[cycle] = vibration
            self.temperature_data.loc[cycle] = temperature
            self.noise_data.loc[cycle] = [noise]
            self.damper_history.loc[cycle] = damper_forces
            self.risk_history.append(risk_index)
            
            # Trim history if needed
            if len(self.vibration_data) > max_points:
                self.vibration_data = self.vibration_data.iloc[-max_points:]
                self.temperature_data = self.temperature_data.iloc[-max_points:]
                self.noise_data = self.noise_data.iloc[-max_points:]
                self.damper_history = self.damper_history.iloc[-max_points:]
                self.risk_history = self.risk_history[-max_points:]
    
    def add_alert(self, level: AlertLevel, message: str):
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

# --- AI MODEL MANAGER ---
class AIModelManager:
    """Manages AI model lifecycle and predictions"""
    
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.training_data = None
        self.initialize_model()
    
    def initialize_model(self):
        """Initialize and train the Isolation Forest model"""
        try:
            # Generate synthetic training data
            normal_vibration = np.random.normal(1.0, 0.3, (500, 4))
            normal_temperature = np.random.normal(65, 5, (500, 4))
            normal_noise = np.random.normal(65, 3, (500, 1))
            self.training_data = np.column_stack([normal_vibration, normal_temperature, normal_noise])
            
            # Train model
            self.model = IsolationForest(
                contamination=0.08, 
                random_state=42, 
                n_estimators=150,
                warm_start=True
            )
            self.model.fit(self.training_data)
            self.is_trained = True
            logger.info("AI Model initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI model: {e}")
            self.is_trained = False
    
    def predict(self, features) -> Tuple[int, float]:
        """Make prediction with error handling"""
        if not self.is_trained or self.model is None:
            return 1, 0.0  # Default to normal operation
        
        try:
            prediction = self.model.predict([features])[0]
            confidence = self.model.decision_function([features])[0]
            return prediction, confidence
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return 1, 0.0

# --- UI COMPONENTS ---
class UIComponents:
    """Factory for creating reusable UI components"""
    
    @staticmethod
    def sensor_status_section(sensors: Dict, values: Dict, title: str):
        """Create a sensor status section"""
        st.markdown(f"**{title}**")
        cols = st.columns(2)
        for i, (sensor_id, (sensor_name, limits)) in enumerate(sensors.items()):
            with cols[i % 2]:
                value = values.get(sensor_id, 0)
                level = limits.get_level(value)
                
                if level == AlertLevel.SUCCESS:
                    st.success(f"✅ {sensor_name}: {value:.1f}")
                elif level == AlertLevel.INFO:
                    st.info(f"ℹ️ {sensor_name}: {value:.1f}")
                elif level == AlertLevel.WARNING:
                    st.warning(f"⚠️ {sensor_name}: {value:.1f}")
                else:
                    st.error(f"🔴 {sensor_name}: {value:.1f}")
    
    @staticmethod
    def create_gauge(value: float, title: str, min_val: float = 0, max_val: float = 100):
        """Create a gauge chart"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            title={'text': title},
            delta={'reference': 50},
            gauge={
                'axis': {'range': [min_val, max_val]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [min_val, 50], 'color': "lightgreen"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, max_val], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': value
                }
            }
        ))
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
        return fig

# --- MAIN APPLICATION ---
class ThermalDNAApp:
    """Main application class"""
    
    def __init__(self):
        self.config = IndustrialConfig()
        self.data_manager = DataManager()
        self.ai_model = AIModelManager()
        self.ui = UIComponents()
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize Streamlit session state"""
        if "app_instance" not in st.session_state:
            st.session_state.app_instance = self
            st.session_state.system_running = False
            st.session_state.system_status = SystemStatus.STANDBY
            st.session_state.error_count = 0
            st.session_state.maintenance_mode = False
    
    def run(self):
        """Main application entry point"""
        self.setup_page()
        self.render_header()
        self.render_sidebar()
        
        if st.session_state.system_running:
            self.run_monitoring_loop()
        else:
            self.render_idle_state()
    
    def setup_page(self):
        """Configure Streamlit page"""
        st.set_page_config(
            page_title="AVCS DNA Industrial Monitor v6.0",
            page_icon="🏭",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS
        st.markdown("""
        <style>
        .stAlert {
            border-radius: 10px;
        }
        .css-1aumxhk {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 20px;
        }
        .reportview-container {
            background: linear-gradient(to right, #f8f9fa, #e9ecef);
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """Render application header"""
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title("🏭 AVCS DNA - Industrial Monitoring System v6.0")
            st.markdown("*Active Vibration Control System with Enterprise-Grade AI*")
        with col2:
            status_color = {
                SystemStatus.STANDBY: "blue",
                SystemStatus.NORMAL: "green",
                SystemStatus.WARNING: "orange",
                SystemStatus.CRITICAL: "red",
                SystemStatus.ERROR: "darkred",
                SystemStatus.MAINTENANCE: "purple"
            }.get(st.session_state.system_status, "gray")
            
            st.markdown(f"<h3 style='color: {statusColor}; text-align: right;'>{st.session_state.system_status.value}</h3>", 
                       unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Render sidebar controls"""
        with st.sidebar:
            st.header("🎛️ AVCS DNA Control Panel")
            
            # Control buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⚡ Start System", type="primary", use_container_width=True):
                    self.start_system()
            with col2:
                if st.button("🛑 Emergency Stop", type="secondary", use_container_width=True):
                    self.emergency_stop()
            
            # Maintenance mode
            st.session_state.maintenance_mode = st.checkbox("🔧 Maintenance Mode", 
                                                           value=st.session_state.maintenance_mode)
            
            st.markdown("---")
            
            # System metrics
            st.subheader("📊 System Metrics")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Uptime", f"{len(self.data_manager.risk_history) * 0.5:.0f}s" if self.data_manager.risk_history else "0s")
            with col2:
                st.metric("Data Points", len(self.data_manager.risk_history))
            
            # Alert log
            if self.data_manager.alerts:
                st.subheader("⚠️ Recent Alerts")
                for alert in self.data_manager.alerts[-5:]:
                    alert_func = {
                        AlertLevel.INFO: st.info,
                        AlertLevel.SUCCESS: st.success,
                        AlertLevel.WARNING: st.warning,
                        AlertLevel.ERROR: st.error
                    }.get(alert['level'], st.info)
                    
                    alert_func(f"{alert['time'].strftime('%H:%M:%S')} - {alert['message']}")
            
            st.markdown("---")
            
            # System info
            st.subheader("🏭 System Architecture")
            st.info("""
            **Sensors:**
            • 4x Vibration (PCB 603C01)
            • 4x Thermal (FLIR A500f)
            • 1x Acoustic (NI 9234)
            
            **Actuators:**
            • 4x MR Dampers (LORD RD-8040)
            
            **AI Engine:**
            • Isolation Forest + Fusion Logic
            """)
    
    def start_system(self):
        """Start the monitoring system"""
        st.session_state.system_running = True
        st.session_state.system_status = SystemStatus.NORMAL
        st.session_state.error_count = 0
        self.data_manager.reset()
        self.data_manager.add_alert(AlertLevel.SUCCESS, "System started successfully")
        logger.info("System started")
        st.rerun()
    
    def emergency_stop(self):
        """Emergency stop procedure"""
        st.session_state.system_running = False
        st.session_state.system_status = SystemStatus.STANDBY
        self.data_manager.damper_forces = {damper: 0 for damper in IndustrialConfig.MR_DAMPERS.keys()}
        self.data_manager.add_alert(AlertLevel.WARNING, "Emergency stop activated")
        logger.warning("Emergency stop activated")
        st.rerun()
    
    def render_idle_state(self):
        """Render idle state when system is not running"""
        st.info("🚀 System is ready. Click 'Start System' in the sidebar to begin monitoring.")
        
        # Show preview of capabilities
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("AI Model Status", "Ready" if self.ai_model.is_trained else "Not Ready")
        with col2:
            st.metric("Max Data Points", IndustrialConfig.MAX_HISTORY_POINTS)
        with col3:
            st.metric("Update Rate", f"{1/IndustrialConfig.UPDATE_INTERVAL:.0f} Hz")
    
    def generate_sensor_data(self, cycle: int) -> Tuple[Dict, Dict, float]:
        """Generate realistic sensor data based on cycle"""
        try:
            if cycle < 30:
                # Normal operation
                vibration = {k: max(0.1, 1.0 + np.random.normal(0, 0.2)) 
                           for k in IndustrialConfig.VIBRATION_SENSORS.keys()}
                temperature = {k: max(20, 65 + np.random.normal(0, 3)) 
                             for k in IndustrialConfig.THERMAL_SENSORS.keys()}
                noise = max(30, 65 + np.random.normal(0, 2))
                
            elif cycle < 60:
                # Gradual degradation
                degradation = (cycle - 30) * 0.05
                vibration = {k: max(0.1, 1.0 + degradation + np.random.normal(0, 0.3)) 
                           for k in IndustrialConfig.VIBRATION_SENSORS.keys()}
                temperature = {k: max(20, 65 + degradation * 2 + np.random.normal(0, 4)) 
                             for k in IndustrialConfig.THERMAL_SENSORS.keys()}
                noise = max(30, 70 + degradation * 2 + np.random.normal(0, 3))
                
            else:
                # Critical condition
                vibration = {k: max(0.1, 5.0 + np.random.normal(0, 0.5)) 
                           for k in IndustrialConfig.VIBRATION_SENSORS.keys()}
                temperature = {k: max(20, 95 + np.random.normal(0, 5)) 
                             for k in IndustrialConfig.THERMAL_SENSORS.keys()}
                noise = max(30, 95 + np.random.normal(0, 5))
            
            return vibration, temperature, noise
            
        except Exception as e:
            logger.error(f"Data generation error: {e}")
            return {}, {}, 0
    
    def calculate_risk_index(self, vibration: Dict, temperature: Dict, noise: float, 
                            ai_prediction: int, ai_confidence: float) -> int:
        """Calculate comprehensive risk index"""
        try:
            # Sensor-based risk
            vib_risk = np.mean([v / 2.0 for v in vibration.values()]) * 25
            temp_risk = np.mean([(t - 65) / 35 for t in temperature.values()]) * 25
            noise_risk = (noise - 65) / 35 * 25
            
            # AI-based risk
            ai_risk = (1 - abs(ai_confidence)) * 25 if ai_prediction == -1 else abs(ai_confidence) * 25
            
            # Combine risks
            total_risk = min(100, max(0, vib_risk + temp_risk + noise_risk + ai_risk))
            
            return int(total_risk)
            
        except Exception as e:
            logger.error(f"Risk calculation error: {e}")
            return 50  # Default moderate risk
    
    def determine_system_status(self, risk_index: int) -> SystemStatus:
        """Determine system status based on risk index"""
        if st.session_state.maintenance_mode:
            return SystemStatus.MAINTENANCE
        elif risk_index > 80:
            return SystemStatus.CRITICAL
        elif risk_index > 50:
            return SystemStatus.WARNING
        elif risk_index > 20:
            return SystemStatus.NORMAL
        else:
            return SystemStatus.STANDBY
    
    def determine_damper_force(self, risk_index: int) -> int:
        """Determine appropriate damper force"""
        if risk_index > 80:
            return IndustrialConfig.DAMPER_FORCES['critical']
        elif risk_index > 50:
            return IndustrialConfig.DAMPER_FORCES['warning']
        elif risk_index > 20:
            return IndustrialConfig.DAMPER_FORCES['normal']
        else:
            return IndustrialConfig.DAMPER_FORCES['standby']
    
    def check_alerts(self, vibration: Dict, temperature: Dict, noise: float, risk_index: int):
        """Check for alert conditions"""
        # Check individual sensors
        for sensor_id, (sensor_name, limits) in IndustrialConfig.VIBRATION_SENSORS.items():
            value = vibration.get(sensor_id, 0)
            if value > limits.critical:
                self.data_manager.add_alert(AlertLevel.ERROR, f"{sensor_name} vibration critical: {value:.1f} mm/s")
            elif value > limits.warning:
                self.data_manager.add_alert(AlertLevel.WARNING, f"{sensor_name} vibration high: {value:.1f} mm/s")
        
        for sensor_id, (sensor_name, limits) in IndustrialConfig.THERMAL_SENSORS.items():
            value = temperature.get(sensor_id, 0)
            if value > limits.critical:
                self.data_manager.add_alert(AlertLevel.ERROR, f"{sensor_name} temperature critical: {value:.0f}°C")
            elif value > limits.warning:
                self.data_manager.add_alert(AlertLevel.WARNING, f"{sensor_name} temperature high: {value:.0f}°C")
        
        # Check noise
        sensor_name, limits = IndustrialConfig.ACOUSTIC_SENSOR
        if noise > limits.critical:
            self.data_manager.add_alert(AlertLevel.ERROR, f"{sensor_name} critical: {noise:.1f} dB")
        elif noise > limits.warning:
            self.data_manager.add_alert(AlertLevel.WARNING, f"{sensor_name} high: {noise:.1f} dB")
        
        # Check overall risk
        if risk_index > 80:
            self.data_manager.add_alert(AlertLevel.ERROR, f"Critical risk level: {risk_index}%")
        elif risk_index > 50:
            self.data_manager.add_alert(AlertLevel.WARNING, f"Elevated risk level: {risk_index}%")
    
    def render_dashboard(self, cycle: int, vibration: Dict, temperature: Dict, noise: float,
                        risk_index: int, ai_confidence: float, rul_hours: int):
        """Render main dashboard"""
        
        # Create main dashboard layout
        col1, col2 = st.columns(2)
        
        with col1:
            # Vibration monitoring
            with st.expander("📈 Vibration Monitoring", expanded=True):
                if not self.data_manager.vibration_data.empty:
                    st.line_chart(self.data_manager.vibration_data, height=200)
                self.ui.sensor_status_section(IndustrialConfig.VIBRATION_SENSORS, vibration, "")
            
            # Temperature monitoring
            with st.expander("🌡️ Thermal Monitoring", expanded=True):
                if not self.data_manager.temperature_data.empty:
                    st.line_chart(self.data_manager.temperature_data, height=200)
                self.ui.sensor_status_section(IndustrialConfig.THERMAL_SENSORS, temperature, "")
        
        with col2:
            # Acoustic monitoring
            with st.expander("🔊 Acoustic Monitoring", expanded=True):
                if not self.data_manager.noise_data.empty:
                    st.line_chart(self.data_manager.noise_data, height=200)
                
                sensor_name, limits = IndustrialConfig.ACOUSTIC_SENSOR
                level = limits.get_level(noise)
                
                if level == AlertLevel.SUCCESS:
                    st.success(f"✅ {sensor_name}: {noise:.1f} dB")
                elif level == AlertLevel.INFO:
                    st.info(f"ℹ️ {sensor_name}: {noise:.1f} dB")
                elif level == AlertLevel.WARNING:
                    st.warning(f"⚠️ {sensor_name}: {noise:.1f} dB")
                else:
                    st.error(f"🔴 {sensor_name}: {noise:.1f} dB")
            
            # MR Dampers control
            with st.expander("🔄 MR Dampers Control", expanded=True):
                if not self.data_manager.damper_history.empty:
                    st.line_chart(self.data_manager.damper_history, height=200)
                
                cols = st.columns(4)
                for i, (damper_id, damper_name) in enumerate(IndustrialConfig.MR_DAMPERS.items()):
                    with cols[i]:
                        force = self.data_manager.damper_forces[damper_id]
                        if force >= 4000:
                            st.error(f"🔴 {damper_name}\n{force} N")
                        elif force >= 1000:
                            st.warning(f"🟡 {damper_name}\n{force} N")
                        else:
                            st.success(f"🟢 {damper_name}\n{force} N")
        
        st.markdown("---")
        
        # AI Fusion Analysis
        st.subheader("🤖 AI Fusion Analysis")
        fusion_cols = st.columns([2, 1, 1, 1])
        
        with fusion_cols[0]:
            # Risk trend chart
            if len(self.data_manager.risk_history) > 0:
                risk_df = pd.DataFrame({
                    'Risk Index': self.data_manager.risk_history,
                    'Critical': [80] * len(self.data_manager.risk_history),
                    'Warning': [50] * len(self.data_manager.risk_history)
                })
                st.line_chart(risk_df, height=200)
        
        with fusion_cols[1]:
            # Risk gauge
            gauge_fig = self.ui.create_gauge(risk_index, "Risk Index")
            st.plotly_chart(gauge_fig, use_container_width=True, key="gauge_main")
        
        with fusion_cols[2]:
            # AI metrics
            st.metric("🤖 AI Confidence", f"{abs(ai_confidence):.2f}")
            st.metric("🎯 Risk Level", f"{risk_index}%")
        
        with fusion_cols[3]:
            # RUL
            st.metric("⏳ Remaining Useful Life", f"{rul_hours} hours")
            
            if rul_hours < 24:
                st.error("🔴 Immediate maintenance required!")
            elif rul_hours < 72:
                st.warning("🟡 Schedule maintenance soon")
            else:
                st.success("🟢 Normal operation")
    
    def run_monitoring_loop(self):
        """Main monitoring loop"""
        try:
            # Initialize placeholders
            progress_bar = st.sidebar.progress(0)
            status_text = st.sidebar.empty()
            
            # Main loop
            for cycle in range(IndustrialConfig.SIMULATION_CYCLES):
                if not st.session_state.system_running:
                    break
                
                # Generate sensor data
                vibration, temperature, noise = self.generate_sensor_data(cycle)
                
                if not vibration or not temperature:
                    st.session_state.error_count += 1
                    if st.session_state.error_count > 5:
                        st.error("Too many errors. Stopping system.")
                        self.emergency_stop()
                        break
                    continue
                
                # AI prediction
                features = list(vibration.values()) + list(temperature.values()) + [noise]
                ai_prediction, ai_confidence = self.ai_model.predict(features)
                
                # Calculate risk
                risk_index = self.calculate_risk_index(vibration, temperature, noise, 
                                                       ai_prediction, ai_confidence)
                
                # Update system status
                st.session_state.system_status = self.determine_system_status(risk_index)
                
                # Determine damper forces
                damper_force = self.determine_damper_force(risk_index)
                damper_forces = {d: damper_force for d in IndustrialConfig.MR_DAMPERS.keys()}
                self.data_manager.damper_forces = damper_forces
                
                # Calculate RUL
                rul_hours = max(0, int(100 - risk_index * 0.9))
                
                # Save data
                self.data_manager.add_reading(cycle, vibration, temperature, noise, 
                                             damper_forces, risk_index)
                
                # Check for alerts
                self.check_alerts(vibration, temperature, noise, risk_index)
                
                # Render dashboard
                self.render_dashboard(cycle, vibration, temperature, noise,
                                     risk_index, ai_confidence, rul_hours)
                
                # Update progress
                progress_bar.progress((cycle + 1) / IndustrialConfig.SIMULATION_CYCLES)
                status_text.text(f"🔄 Cycle: {cycle+1}/{IndustrialConfig.SIMULATION_CYCLES}")
                
                # Wait for next cycle
                time.sleep(IndustrialConfig.UPDATE_INTERVAL)
            
            # Simulation complete
            if cycle >= IndustrialConfig.SIMULATION_CYCLES - 1:
                st.success("✅ Simulation cycle completed successfully!")
                self.data_manager.add_alert(AlertLevel.SUCCESS, "Simulation cycle completed")
                
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")
            st.error(f"System error: {str(e)}")
            self.data_manager.add_alert(AlertLevel.ERROR, f"System error: {str(e)}")
            st.session_state.system_running = False

# --- APPLICATION ENTRY POINT ---
if __name__ == "__main__":
    try:
        app = ThermalDNAApp()
        app.run()
    except Exception as e:
        logger.critical(f"Fatal application error: {e}")
        st.error(f"Fatal error: {str(e)}. Please restart the application.")
