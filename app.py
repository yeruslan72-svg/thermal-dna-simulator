"""
AVCS DNA Industrial Monitor v6.0
Main entry point for Streamlit Cloud deployment
"""
import sys
from pathlib import Path

# Add modules directory to path
modules_path = Path(__file__).parent / "modules"
sys.path.append(str(modules_path))

# Now import from modules
import streamlit as st
import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
import plotly.graph_objects as go

# Import local modules
from modules.config import settings, SystemStatus, AlertLevel, IndustrialConfig
from modules.data_manager import DataManager
from modules.ai_model import AIModelManager
from modules.sensor_simulator import SensorSimulator
from modules.alert_system import alert_system, render_alert_panel
from modules.ui_components import UIComponents
from utils.logger import logger
from utils.helpers import format_number, calculate_trend

class ThermalDNAApp:
    """Main application class"""
    
    def __init__(self):
        """Initialize application"""
        self.config = IndustrialConfig()
        self.data_manager = DataManager()
        self.ai_model = AIModelManager()
        self.simulator = SensorSimulator()
        self.ui = UIComponents()
        self.alert_system = alert_system
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize session state"""
        if "initialized" not in st.session_state:
            st.session_state.initialized = True
            st.session_state.system_running = False
            st.session_state.system_status = SystemStatus.STANDBY
            st.session_state.error_count = 0
            st.session_state.start_time = None
            st.session_state.current_cycle = 0
    
    def run(self):
        """Main application loop"""
        self.setup_page()
        self.render_header()
        self.render_sidebar()
        
        if st.session_state.system_running:
            self.run_monitoring_loop()
        else:
            self.render_idle_state()
        
        self.render_footer()
    
    def setup_page(self):
        """Configure Streamlit page"""
        st.set_page_config(
            page_title=f"{settings.APP_ICON} {settings.APP_NAME}",
            page_icon=settings.APP_ICON,
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def render_header(self):
        """Render header"""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.title(f"{settings.APP_ICON} {settings.APP_NAME}")
            st.caption(f"Version {settings.APP_VERSION} | Active Vibration Control with AI")
        
        with col2:
            status = st.session_state.system_status.value
            if st.session_state.system_status == SystemStatus.CRITICAL:
                st.error(f"## {status}")
            elif st.session_state.system_status == SystemStatus.WARNING:
                st.warning(f"## {status}")
            else:
                st.success(f"## {status}")
    
    def render_sidebar(self):
        """Render sidebar"""
        with st.sidebar:
            st.image("https://via.placeholder.com/300x80/1e3c72/ffffff?text=YERUSLAN+TECH", 
                    use_container_width=True)
            
            st.markdown("---")
            st.subheader("🎛️ Control Panel")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⚡ Start", type="primary", use_container_width=True):
                    self.start_system()
            with col2:
                if st.button("🛑 Stop", type="secondary", use_container_width=True):
                    self.emergency_stop()
            
            if st.session_state.system_running:
                st.markdown("---")
                st.subheader("📊 Live Stats")
                stats = self.data_manager.get_statistics()
                st.metric("Readings", stats['total_readings'])
                st.metric("Current Risk", f"{stats['current_risk']}%")
                
                render_alert_panel()
    
    def start_system(self):
        """Start system"""
        st.session_state.system_running = True
        st.session_state.system_status = SystemStatus.NORMAL
        st.session_state.start_time = datetime.now()
        self.data_manager.reset()
        st.rerun()
    
    def emergency_stop(self):
        """Emergency stop"""
        st.session_state.system_running = False
        st.session_state.system_status = SystemStatus.STANDBY
        st.rerun()
    
    def calculate_risk_index(self, vibration: Dict, temperature: Dict, 
                           noise: float, ai_prediction: int, 
                           ai_confidence: float) -> int:
        """Calculate risk index"""
        try:
            vib_risk = np.mean([min(v / 6.0, 1.0) for v in vibration.values()]) * 25
            temp_risk = np.mean([min((t - 20) / 80, 1.0) for t in temperature.values()]) * 25
            noise_risk = min((noise - 30) / 70, 1.0) * 25
            
            if ai_prediction == -1:
                ai_risk = (1 - abs(ai_confidence)) * 25
            else:
                ai_risk = abs(ai_confidence) * 25
            
            total = vib_risk + temp_risk + noise_risk + ai_risk
            return int(max(0, min(100, total)))
            
        except Exception:
            return 50
    
    def determine_damper_force(self, risk_index: int) -> int:
        """Determine damper force"""
        if risk_index > 80:
            return self.config.DAMPER_FORCES['critical']
        elif risk_index > 50:
            return self.config.DAMPER_FORCES['warning']
        elif risk_index > 20:
            return self.config.DAMPER_FORCES['normal']
        else:
            return self.config.DAMPER_FORCES['standby']
    
    def render_idle_state(self):
        """Render idle state"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("### 🚀 Ready to Start")
            st.write("Click **Start** in sidebar to begin monitoring")
        
        with col2:
            st.success("### ✅ System Ready")
            st.write(f"AI Model: {'Ready' if self.ai_model.is_trained else 'Loading'}")
        
        with col3:
            st.warning("### 📊 Demo Mode")
            st.write("Running with simulated data")
    
    def render_footer(self):
        """Render footer"""
        st.markdown("---")
        st.caption(f"© 2024 Yeruslan Technologies | Version {settings.APP_VERSION}")
    
    def run_monitoring_loop(self):
        """Main monitoring loop"""
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            tab1, tab2 = st.tabs(["📊 Live Monitoring", "📈 Trends"])
            
            for cycle in range(settings.SIMULATION_CYCLES):
                if not st.session_state.system_running:
                    break
                
                st.session_state.current_cycle = cycle
                
                # Generate data
                vibration, temperature, noise = self.simulator.generate_data(cycle)
                
                if not vibration:
                    continue
                
                # AI prediction
                features = list(vibration.values()) + list(temperature.values()) + [noise]
                ai_prediction, ai_confidence = self.ai_model.predict(features)
                
                # Calculate risk
                risk_index = self.calculate_risk_index(
                    vibration, temperature, noise, ai_prediction, ai_confidence
                )
                
                # Update status
                if risk_index > 80:
                    st.session_state.system_status = SystemStatus.CRITICAL
                elif risk_index > 50:
                    st.session_state.system_status = SystemStatus.WARNING
                
                # Damper forces
                damper_force = self.determine_damper_force(risk_index)
                damper_forces = {d: damper_force for d in self.config.MR_DAMPERS.keys()}
                
                # Calculate RUL
                rul_hours = max(0, int(100 - risk_index * 0.9))
                
                # Save data
                self.data_manager.add_reading(
                    cycle, vibration, temperature, noise, damper_forces, risk_index
                )
                
                # Update tabs
                with tab1:
                    self.render_live_tab(vibration, temperature, noise, 
                                       risk_index, ai_confidence, rul_hours, damper_forces)
                
                with tab2:
                    self.render_trends_tab()
                
                # Progress
                progress = (cycle + 1) / settings.SIMULATION_CYCLES
                progress_bar.progress(progress)
                status_text.text(f"Cycle: {cycle+1}/{settings.SIMULATION_CYCLES}")
                
                time.sleep(settings.UPDATE_INTERVAL)
            
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.session_state.system_running = False
    
    def render_live_tab(self, vibration: Dict, temperature: Dict, noise: float,
                       risk_index: int, ai_confidence: float, rul_hours: int,
                       damper_forces: Dict):
        """Render live monitoring tab"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Vibration")
            self.ui.sensor_status_section(
                self.config.VIBRATION_SENSORS, vibration, ""
            )
            
            st.subheader("🌡️ Temperature")
            self.ui.sensor_status_section(
                self.config.THERMAL_SENSORS, temperature, ""
            )
        
        with col2:
            st.subheader("🔊 Acoustic")
            sensor_name, limits = self.config.ACOUSTIC_SENSOR
            level = limits.get_level(noise)
            
            if level == AlertLevel.ERROR:
                st.error(f"🔴 {sensor_name}: {noise:.1f} dB")
            elif level == AlertLevel.WARNING:
                st.warning(f"⚠️ {sensor_name}: {noise:.1f} dB")
            else:
                st.success(f"✅ {sensor_name}: {noise:.1f} dB")
            
            # Risk gauge
            gauge_fig = self.ui.create_gauge(risk_index, "Risk Index")
            st.plotly_chart(gauge_fig, use_container_width=True, key="gauge")
            
            st.metric("⏳ RUL", f"{rul_hours} hours")
            st.metric("🤖 AI Confidence", f"{abs(ai_confidence):.2f}")
    
    def render_trends_tab(self):
        """Render trends tab"""
        if not self.data_manager.vibration_data.empty:
            st.subheader("Vibration Trends")
            st.line_chart(self.data_manager.vibration_data.tail(50))
            
            st.subheader("Temperature Trends")
            st.line_chart(self.data_manager.temperature_data.tail(50))
            
            if self.data_manager.risk_history:
                st.subheader("Risk History")
                risk_df = pd.DataFrame({
                    'Risk': self.data_manager.risk_history[-50:],
                    'Warning': [50] * min(50, len(self.data_manager.risk_history)),
                    'Critical': [80] * min(50, len(self.data_manager.risk_history))
                })
                st.line_chart(risk_df)

# Application entry point
if __name__ == "__main__":
    app = ThermalDNAApp()
    app.run()
