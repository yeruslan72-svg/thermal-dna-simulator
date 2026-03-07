# app.py - AVCS DNA Industrial Monitor v6.1 (Fixed)
"""Main application entry point for AVCS DNA Industrial Monitoring System"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

# Add modules to path
sys.path.append(str(Path(__file__).parent))

# Local imports
from modules.config import settings, SystemStatus, AlertLevel, industrial_config
from modules.data_manager import data_manager
from modules.ai_model import ai_model
from modules.sensor_simulator import sensor_simulator
from modules.alert_system import alert_system, render_alert_panel
from modules.ui_components import ui_components
from utils.logger import logger
from utils.helpers import format_number, calculate_trend, safe_division

# Page config
st.set_page_config(
    page_title=f"{settings.APP_ICON} {settings.APP_NAME}",
    page_icon=settings.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

class ThermalDNAApp:
    """Main application class"""
    
    def __init__(self):
        """Initialize application"""
        self.config = industrial_config
        self.data_manager = data_manager
        self.ai_model = ai_model
        self.simulator = sensor_simulator
        self.ui = ui_components
        self.alert_system = alert_system  # Это объект AlertSystem
        self.init_session_state()
        
        logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} initialized")
    
    def init_session_state(self):
        """Initialize session state"""
        if "app_initialized" not in st.session_state:
            st.session_state.app_initialized = True
            st.session_state.system_running = False
            st.session_state.system_status = SystemStatus.STANDBY
            st.session_state.error_count = 0
            st.session_state.start_time = None
            st.session_state.current_cycle = 0
            st.session_state.refresh_rate = settings.UPDATE_INTERVAL
            st.session_state.show_alerts = True
            st.session_state.max_points = 50
            
            logger.info("Session state initialized")
    
    def run(self):
        """Main application entry point"""
        self.render_header()
        self.render_sidebar()
        
        if st.session_state.system_running:
            self.run_monitoring_loop()
        else:
            self.render_idle_state()
        
        self.render_footer()
    
    def render_header(self):
        """Render application header"""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"""
            <div style="padding: 0.5rem 0;">
                <h2>{settings.APP_ICON} {settings.APP_NAME}</h2>
                <p style="color: #666; font-size: 0.8rem;">v{settings.APP_VERSION}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            status = st.session_state.system_status.value
            if st.session_state.system_status == SystemStatus.CRITICAL:
                st.error(f"### {status}")
            elif st.session_state.system_status == SystemStatus.WARNING:
                st.warning(f"### {status}")
            else:
                st.success(f"### {status}")
        
        with col3:
            if st.session_state.system_running and st.session_state.start_time:
                uptime = datetime.now() - st.session_state.start_time
                minutes = int(uptime.total_seconds() / 60)
                seconds = int(uptime.total_seconds() % 60)
                st.metric("⏱️ Uptime", f"{minutes}m {seconds}s")
    
    def render_sidebar(self):
        """Render sidebar controls"""
        with st.sidebar:
            st.image("https://via.placeholder.com/250x60/1e3c72/ffffff?text=YERUSLAN", 
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
                st.subheader("📊 Live Statistics")
                
                stats = self.data_manager.get_statistics()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Readings", stats['total_readings'])
                    st.metric("Current Risk", f"{stats['current_risk']}%")
                with col2:
                    st.metric("Active Alerts", stats['active_alerts'])
                    st.metric("Data Points", stats['data_points'])
                
                st.markdown("---")
                
                if st.session_state.show_alerts:
                    render_alert_panel()
    
    def start_system(self):
        """Start the monitoring system"""
        st.session_state.system_running = True
        st.session_state.system_status = SystemStatus.NORMAL
        st.session_state.error_count = 0
        st.session_state.start_time = datetime.now()
        st.session_state.current_cycle = 0
        
        self.data_manager.reset()
        # ✅ ИСПРАВЛЕНО: правильный метод add_alert (без подчеркивания)
        self.alert_system.add_alert("success", "System started successfully")
        
        logger.info("System started")
        st.rerun()
    
    def emergency_stop(self):
        """Emergency stop procedure"""
        st.session_state.system_running = False
        st.session_state.system_status = SystemStatus.STANDBY
        
        # Set all dampers to zero
        self.data_manager.damper_forces = {d: 0 for d in self.config.MR_DAMPERS.keys()}
        
        # ✅ ИСПРАВЛЕНО: правильный метод add_alert (без подчеркивания)
        self.alert_system.add_alert("warning", "Emergency stop activated")
        
        logger.warning("Emergency stop activated")
        st.rerun()
    
    def calculate_risk_index(self, vibration: Dict, temperature: Dict, 
                           noise: float, ai_prediction: int, 
                           ai_confidence: float) -> int:
        """Calculate comprehensive risk index"""
        try:
            vib_avg = sum(vibration.values()) / len(vibration)
            temp_avg = sum(temperature.values()) / len(temperature)
            
            vib_risk = min(vib_avg / 6.0, 1.0) * 30
            temp_risk = min((temp_avg - 20) / 80, 1.0) * 30
            noise_risk = min((noise - 30) / 70, 1.0) * 20
            
            if ai_prediction == -1:
                ai_risk = 20
            else:
                ai_risk = ai_confidence * 10
            
            total = vib_risk + temp_risk + noise_risk + ai_risk
            return int(max(0, min(100, total)))
            
        except Exception:
            return 50
    
    def determine_damper_force(self, risk_index: int) -> int:
        """Determine appropriate damper force"""
        if risk_index > 80:
            return self.config.DAMPER_FORCES['critical']
        elif risk_index > 50:
            return self.config.DAMPER_FORCES['warning']
        elif risk_index > 20:
            return self.config.DAMPER_FORCES['normal']
        else:
            return self.config.DAMPER_FORCES['standby']
    
    def determine_system_status(self, risk_index: int) -> SystemStatus:
        """Determine system status based on risk index"""
        if risk_index > 80:
            return SystemStatus.CRITICAL
        elif risk_index > 50:
            return SystemStatus.WARNING
        elif risk_index > 20:
            return SystemStatus.NORMAL
        else:
            return SystemStatus.STANDBY
    
    def render_idle_state(self):
        """Render idle state"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("### 🚀 Ready to Start")
            st.write("Click **Start** in sidebar to begin monitoring")
        
        with col2:
            st.success("### ✅ System Check")
            checks = {
                "AI Model": self.ai_model.is_trained,
                "Data Manager": True,
                "Alert System": True
            }
            for check, status in checks.items():
                st.write(f"{'✅' if status else '❌'} {check}: {'Ready' if status else 'Not Ready'}")
        
        with col3:
            st.warning("### 📊 Demo Mode")
            st.write("Running with simulated data")
            st.metric("Simulation Cycles", settings.SIMULATION_CYCLES)
    
    def render_footer(self):
        """Render application footer"""
        st.markdown("---")
        st.caption(f"© 2024 Yeruslan Technologies | v{settings.APP_VERSION}")
    
    def run_monitoring_loop(self):
        """Main monitoring loop"""
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            tab1, tab2 = st.tabs(["📊 Live", "📈 Trends"])
            
            for cycle in range(settings.SIMULATION_CYCLES):
                if not st.session_state.system_running:
                    break
                
                st.session_state.current_cycle = cycle
                
                # Generate data
                vibration, temperature, noise = self.simulator.generate_data(cycle)
                
                if not vibration:
                    st.session_state.error_count += 1
                    continue
                
                # AI prediction
                features = list(vibration.values()) + list(temperature.values()) + [noise]
                ai_prediction, ai_confidence = self.ai_model.predict(features)
                
                # Calculate risk
                risk_index = self.calculate_risk_index(
                    vibration, temperature, noise, ai_prediction, ai_confidence
                )
                
                # Update status
                st.session_state.system_status = self.determine_system_status(risk_index)
                
                # Damper forces
                damper_force = self.determine_damper_force(risk_index)
                damper_forces = {d: damper_force for d in self.config.MR_DAMPERS.keys()}
                self.data_manager.damper_forces = damper_forces
                
                # Calculate RUL
                rul_hours = max(0, int(100 - risk_index * 0.9))
                
                # Save data
                self.data_manager.add_reading(
                    cycle, vibration, temperature, noise, damper_forces, risk_index,
                    {'prediction': ai_prediction, 'confidence': ai_confidence}
                )
                
                # Check alerts (every 5 cycles)
                if cycle % 5 == 0:
                    alert_data = {
                        'vibration': vibration,
                        'temperature': temperature,
                        'noise': noise,
                        'risk_index': risk_index,
                        'cycle': cycle
                    }
                    self.alert_system.check_alerts(alert_data)
                
                # Update tabs
                with tab1:
                    self.render_live_tab(cycle, vibration, temperature, noise,
                                        risk_index, ai_confidence, rul_hours, damper_forces)
                
                with tab2:
                    self.render_trends_tab()
                
                # Progress
                progress = (cycle + 1) / settings.SIMULATION_CYCLES
                progress_bar.progress(progress)
                status_text.text(f"🔄 Cycle: {cycle+1}/{settings.SIMULATION_CYCLES}")
                
                time.sleep(st.session_state.refresh_rate)
            
            progress_bar.empty()
            status_text.empty()
            
            if cycle >= settings.SIMULATION_CYCLES - 1:
                st.success("✅ Simulation completed!")
                # ✅ ИСПРАВЛЕНО: правильный метод add_alert
                self.alert_system.add_alert("success", "Simulation completed")
                
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")
            st.error(f"System error: {str(e)}")
            # ✅ ИСПРАВЛЕНО: правильный метод add_alert
            self.alert_system.add_alert("error", f"System error: {str(e)}")
            st.session_state.system_running = False
    
    def render_live_tab(self, cycle: int, vibration: Dict, temperature: Dict,
                       noise: float, risk_index: int, ai_confidence: float,
                       rul_hours: int, damper_forces: Dict):
        """Render live monitoring tab"""
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Risk", f"{risk_index}%")
        with col2:
            st.metric("🤖 AI", f"{ai_confidence:.2f}")
        with col3:
            st.metric("⏳ RUL", f"{rul_hours}h")
        with col4:
            st.metric("🔄 Cycle", f"{cycle}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Vibration")
            if not self.data_manager.vibration_data.empty:
                st.line_chart(self.data_manager.vibration_data.tail(20), height=150)
            
            for sensor, value in vibration.items():
                name = self.config.VIBRATION_SENSORS[sensor][0]
                color = "🟢" if value < 2 else "🟡" if value < 4 else "🔴"
                st.write(f"{color} {name}: {value:.1f} mm/s")
            
            st.subheader("🌡️ Temperature")
            if not self.data_manager.temperature_data.empty:
                st.line_chart(self.data_manager.temperature_data.tail(20), height=150)
            
            for sensor, value in temperature.items():
                name = self.config.THERMAL_SENSORS[sensor][0]
                color = "🟢" if value < 70 else "🟡" if value < 85 else "🔴"
                st.write(f"{color} {name}: {value:.0f}°C")
        
        with col2:
            st.subheader("🔊 Noise")
            if not self.data_manager.noise_data.empty:
                st.line_chart(self.data_manager.noise_data.tail(20), height=150)
            
            color = "🟢" if noise < 70 else "🟡" if noise < 85 else "🔴"
            st.write(f"{color} Level: {noise:.1f} dB")
            
            st.subheader("🔄 Dampers")
            cols = st.columns(4)
            for i, (damper_id, damper_name) in enumerate(self.config.MR_DAMPERS.items()):
                with cols[i]:
                    force = damper_forces[damper_id]
                    if force >= 4000:
                        st.error(f"🔴\n{force}N")
                    elif force >= 1000:
                        st.warning(f"🟡\n{force}N")
                    else:
                        st.success(f"🟢\n{force}N")
                    st.caption(damper_name.split()[0])
    
    def render_trends_tab(self):
        """Render trends tab"""
        if self.data_manager.vibration_data.empty:
            st.info("No data yet")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Vibration Trends")
            st.line_chart(self.data_manager.vibration_data.tail(50))
            
            st.subheader("Temperature Trends")
            st.line_chart(self.data_manager.temperature_data.tail(50))
        
        with col2:
            st.subheader("Noise Trend")
            st.line_chart(self.data_manager.noise_data.tail(50))
            
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
    try:
        app = ThermalDNAApp()
        app.run()
    except Exception as e:
        st.error(f"Error: {str(e)}")
