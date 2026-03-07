# app.py - AVCS DNA Industrial Monitor v6.0
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

# Local imports - используем новую структуру
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
        self.alert_system = alert_system
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
            st.session_state.selected_tab = "Overview"
            st.session_state.auto_scroll = True
            st.session_state.refresh_rate = settings.UPDATE_INTERVAL
            st.session_state.show_alerts = True
            
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
            <div style="padding: 1rem 0;">
                <h1>{settings.APP_ICON} {settings.APP_NAME}</h1>
                <p style="color: #666; font-size: 0.9rem;">
                    Version {settings.APP_VERSION} | Active Vibration Control with AI
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            status = st.session_state.system_status.value
            if st.session_state.system_status == SystemStatus.CRITICAL:
                st.error(f"## {status}")
            elif st.session_state.system_status == SystemStatus.WARNING:
                st.warning(f"## {status}")
            elif st.session_state.system_status == SystemStatus.ERROR:
                st.error(f"## {status}")
            else:
                st.success(f"## {status}")
        
        with col3:
            if st.session_state.system_running and st.session_state.start_time:
                uptime = datetime.now() - st.session_state.start_time
                hours, remainder = divmod(uptime.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                st.metric(
                    "⏱️ Uptime",
                    f"{hours:02d}:{minutes:02d}:{seconds:02d}",
                    help="System uptime"
                )
    
    def render_sidebar(self):
        """Render sidebar controls"""
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
            
            st.markdown("---")
            
            if st.session_state.system_running:
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
                
                # Alert panel
                if st.session_state.show_alerts:
                    render_alert_panel()
            
            # System info
            with st.expander("ℹ️ System Info", expanded=False):
                st.markdown("""
                **Sensors:**
                • 4x Vibration (PCB 603C01)
                • 4x Thermal (FLIR A500f)
                • 1x Acoustic (NI 9234)
                
                **Actuators:**
                • 4x MR Dampers (LORD RD-8040)
                
                **AI Engine:**
                • Isolation Forest
                • 200 estimators
                • 9 features
                """)
    
    def start_system(self):
        """Start the monitoring system"""
        st.session_state.system_running = True
        st.session_state.system_status = SystemStatus.NORMAL
        st.session_state.error_count = 0
        st.session_state.start_time = datetime.now()
        st.session_state.current_cycle = 0
        
        self.data_manager.reset()
        self.alert_system.add_alert(AlertLevel.SUCCESS, "System started successfully")
        
        logger.info("System started")
        st.rerun()
    
    def emergency_stop(self):
        """Emergency stop procedure"""
        st.session_state.system_running = False
        st.session_state.system_status = SystemStatus.STANDBY
        
        # Set all dampers to zero
        self.data_manager.damper_forces = {d: 0 for d in self.config.MR_DAMPERS.keys()}
        
        self.alert_system.add_alert(AlertLevel.WARNING, "Emergency stop activated")
        
        logger.warning("Emergency stop activated")
        st.rerun()
    
    def calculate_risk_index(self, vibration: Dict, temperature: Dict, 
                           noise: float, ai_prediction: int, 
                           ai_confidence: float) -> int:
        """Calculate comprehensive risk index"""
        try:
            # Sensor-based risk (0-75)
            vib_risk = np.mean([min(v / 6.0, 1.0) for v in vibration.values()]) * 25
            temp_risk = np.mean([min((t - 20) / 80, 1.0) for t in temperature.values()]) * 25
            noise_risk = min((noise - 30) / 70, 1.0) * 25
            
            # AI-based risk (0-25)
            if ai_prediction == -1:  # Anomaly detected
                ai_risk = (1 - ai_confidence) * 25
            else:
                ai_risk = ai_confidence * 15
            
            # Combine risks
            total_risk = vib_risk + temp_risk + noise_risk + ai_risk
            
            # Add small random variation
            total_risk += np.random.normal(0, 2)
            
            return int(max(0, min(100, total_risk)))
            
        except Exception as e:
            logger.error(f"Risk calculation error: {e}")
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
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption(f"© 2024 Yeruslan Technologies")
        with col2:
            st.caption(f"Version {settings.APP_VERSION}")
        with col3:
            st.caption("🔒 Secure Connection")
    
    def run_monitoring_loop(self):
        """Main monitoring loop"""
        try:
            # Initialize progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Create tabs
            tab1, tab2, tab3 = st.tabs([
                "📊 Live Monitoring",
                "📈 Trends",
                "🔧 Diagnostics"
            ])
            
            # Main loop
            for cycle in range(settings.SIMULATION_CYCLES):
                if not st.session_state.system_running:
                    break
                
                st.session_state.current_cycle = cycle
                
                # Generate sensor data
                vibration, temperature, noise = self.simulator.generate_data(cycle)
                
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
                risk_index = self.calculate_risk_index(
                    vibration, temperature, noise, ai_prediction, ai_confidence
                )
                
                # Update system status
                if risk_index > 80:
                    st.session_state.system_status = SystemStatus.CRITICAL
                elif risk_index > 50:
                    st.session_state.system_status = SystemStatus.WARNING
                elif risk_index > 20:
                    st.session_state.system_status = SystemStatus.NORMAL
                else:
                    st.session_state.system_status = SystemStatus.STANDBY
                
                # Determine damper forces
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
                
                # Check alerts
                alert_data = {
                    'vibration': vibration,
                    'temperature': temperature,
                    'noise': noise,
                    'risk_index': risk_index,
                    'ai_prediction': ai_prediction,
                    'ai_confidence': ai_confidence,
                    'rul_hours': rul_hours,
                    'cycle': cycle
                }
                self.alert_system.check_alerts(alert_data)
                
                # Update tabs
                with tab1:
                    self.render_live_tab(cycle, vibration, temperature, noise,
                                        risk_index, ai_confidence, rul_hours, damper_forces)
                
                with tab2:
                    self.render_trends_tab()
                
                with tab3:
                    self.render_diagnostics_tab(risk_index, ai_confidence, ai_prediction)
                
                # Update progress
                progress = (cycle + 1) / settings.SIMULATION_CYCLES
                progress_bar.progress(progress)
                status_text.text(f"🔄 Cycle: {cycle+1}/{settings.SIMULATION_CYCLES}")
                
                # Wait
                time.sleep(st.session_state.refresh_rate)
            
            # Cleanup
            progress_bar.empty()
            status_text.empty()
            
            if cycle >= settings.SIMULATION_CYCLES - 1:
                st.success("✅ Simulation completed!")
                self.alert_system.add_alert(AlertLevel.SUCCESS, "Simulation completed")
                
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")
            st.error(f"System error: {str(e)}")
            self.alert_system.add_alert(AlertLevel.ERROR, f"System error: {str(e)}")
            st.session_state.system_running = False
    
    def render_live_tab(self, cycle: int, vibration: Dict, temperature: Dict,
                       noise: float, risk_index: int, ai_confidence: float,
                       rul_hours: int, damper_forces: Dict):
        """Render live monitoring tab"""
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Risk Index", f"{risk_index}%")
        with col2:
            st.metric("🤖 AI Confidence", f"{ai_confidence:.2f}")
        with col3:
            st.metric("⏳ RUL", f"{rul_hours}h")
        with col4:
            st.metric("🔄 Cycle", f"{cycle}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Vibration
            st.subheader("📈 Vibration Monitoring")
            if not self.data_manager.vibration_data.empty:
                st.line_chart(self.data_manager.vibration_data.tail(50), height=200)
            self.ui.sensor_status_section(self.config.VIBRATION_SENSORS, vibration, "")
            
            # Temperature
            st.subheader("🌡️ Thermal Monitoring")
            if not self.data_manager.temperature_data.empty:
                st.line_chart(self.data_manager.temperature_data.tail(50), height=200)
            self.ui.sensor_status_section(self.config.THERMAL_SENSORS, temperature, "")
        
        with col2:
            # Noise
            st.subheader("🔊 Acoustic Monitoring")
            if not self.data_manager.noise_data.empty:
                st.line_chart(self.data_manager.noise_data.tail(50), height=200)
            
            sensor_name, limits = self.config.ACOUSTIC_SENSOR
            level = limits.get_level(noise)
            
            if level == AlertLevel.ERROR:
                st.error(f"🔴 {sensor_name}: {noise:.1f} dB")
            elif level == AlertLevel.WARNING:
                st.warning(f"⚠️ {sensor_name}: {noise:.1f} dB")
            else:
                st.success(f"✅ {sensor_name}: {noise:.1f} dB")
            
            # Risk gauge
            st.subheader("🎯 Risk Assessment")
            gauge_fig = self.ui.create_gauge(risk_index, "Current Risk")
            st.plotly_chart(gauge_fig, use_container_width=True, key="gauge_live")
            
            # Dampers
            st.subheader("🔄 MR Dampers")
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
            st.info("No data available yet")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Vibration Trends")
            st.line_chart(self.data_manager.vibration_data)
            
            st.subheader("Temperature Trends")
            st.line_chart(self.data_manager.temperature_data)
        
        with col2:
            st.subheader("Noise Trend")
            st.line_chart(self.data_manager.noise_data)
            
            st.subheader("Risk History")
            if self.data_manager.risk_history:
                risk_df = pd.DataFrame({
                    'Risk': self.data_manager.risk_history,
                    'Warning': [50] * len(self.data_manager.risk_history),
                    'Critical': [80] * len(self.data_manager.risk_history)
                })
                st.line_chart(risk_df)
    
    def render_diagnostics_tab(self, risk_index: int, ai_confidence: float, ai_prediction: int):
        """Render diagnostics tab"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("System Health")
            
            health_score = max(0, 100 - risk_index)
            st.metric("Health Score", f"{health_score}%")
            
            if ai_prediction == -1:
                st.warning("⚠️ AI Status: Anomaly Detected")
            else:
                st.success("✅ AI Status: Normal")
            
            stats = self.data_manager.get_statistics()
            st.metric("Total Readings", stats['total_readings'])
            st.metric("Active Alerts", stats['active_alerts'])
        
        with col2:
            st.subheader("Model Info")
            
            model_info = self.ai_model.get_model_info()
            st.info(f"""
            **Model:** Isolation Forest
            **Trained:** {model_info['training_date'] or 'Never'}
            **Samples:** {model_info['training_samples']}
            **Features:** {len(model_info['feature_names'])}
            """)
            
            # Feature importance
            if model_info['feature_importance']:
                st.subheader("Feature Importance")
                imp_df = pd.DataFrame(
                    model_info['feature_importance'].items(),
                    columns=['Feature', 'Importance']
                ).sort_values('Importance', ascending=False)
                st.dataframe(imp_df, use_container_width=True)

# Application entry point
if __name__ == "__main__":
    try:
        app = ThermalDNAApp()
        app.run()
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        st.error(f"""
        ### ❌ Fatal Error
        **{str(e)}**
        
        Please check logs and restart.
        """)
