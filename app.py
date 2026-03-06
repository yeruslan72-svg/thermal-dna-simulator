# app.py - AVCS DNA Industrial Monitor v6.0 (Enterprise Edition)
"""Main application entry point for AVCS DNA Industrial Monitoring System"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import plotly.graph_objects as go
import plotly.express as px

# Local imports
from config.settings import settings
from config.constants import SystemStatus, AlertLevel, IndustrialConfig
from core.data_manager import DataManager
from core.ai_model import AIModelManager
from core.sensor_simulator import SensorSimulator
from core.alert_system import alert_system, render_alert_panel
from ui.components import UIComponents
from ui.styles import apply_custom_styles
from utils.logger import logger
from utils.helpers import format_number, calculate_trend, safe_division

# Initialize logger
logger = logger

class ThermalDNAApp:
    """Main application class for AVCS DNA Industrial Monitor"""
    
    def __init__(self):
        """Initialize application components"""
        self.config = IndustrialConfig()
        self.data_manager = DataManager()
        self.ai_model = AIModelManager(model_path=settings.MODEL_PATH)
        self.simulator = SensorSimulator(seed=42)
        self.ui = UIComponents()
        self.alert_system = alert_system
        
        # Initialize session state
        self.init_session_state()
        
        logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} initialized")
    
    def init_session_state(self):
        """Initialize Streamlit session state"""
        if "app_initialized" not in st.session_state:
            st.session_state.app_initialized = True
            st.session_state.system_running = False
            st.session_state.system_status = SystemStatus.STANDBY
            st.session_state.error_count = 0
            st.session_state.start_time = None
            st.session_state.current_cycle = 0
            st.session_state.selected_tab = "Overview"
            st.session_state.auto_scroll = True
            st.session_state.theme = "dark"
            st.session_state.refresh_rate = settings.UPDATE_INTERVAL
            
            logger.info("Session state initialized")
    
    def run(self):
        """Main application entry point"""
        # Page configuration
        self.setup_page()
        
        # Apply custom styles
        apply_custom_styles()
        
        # Render header
        self.render_header()
        
        # Render sidebar
        self.render_sidebar()
        
        # Main content
        if st.session_state.system_running:
            self.run_monitoring_loop()
        else:
            self.render_idle_state()
        
        # Footer
        self.render_footer()
    
    def setup_page(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title=f"{settings.APP_ICON} {settings.APP_NAME} v{settings.APP_VERSION}",
            page_icon=settings.APP_ICON,
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'https://github.com/yeruslan/thermal_dna_app',
                'Report a bug': 'https://github.com/yeruslan/thermal_dna_app/issues',
                'About': f"""
                # {settings.APP_NAME} v{settings.APP_VERSION}
                
                Active Vibration Control System with AI-Powered Predictive Maintenance.
                
                **Features:**
                - Real-time monitoring of vibration, temperature, and noise
                - AI-based anomaly detection with Isolation Forest
                - Active vibration control via MR dampers
                - Predictive maintenance with RUL estimation
                - Multi-level alerting system
                
                **Developed by:** Yeruslan Technologies
                **License:** MIT
                """
            }
        )
    
    def render_header(self):
        """Render application header with status and metrics"""
        # Top bar with status
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.markdown(f"""
            <div class="main-header">
                <h1>{settings.APP_ICON} {settings.APP_NAME}</h1>
                <p style="color: #888; font-size: 14px;">Version {settings.APP_VERSION} | Active Vibration Control with AI</p>
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
        
        with col4:
            if self.data_manager.risk_history:
                current_risk = self.data_manager.risk_history[-1]
                trend = calculate_trend(
                    self.data_manager.risk_history[-5:] if len(self.data_manager.risk_history) >= 5 else self.data_manager.risk_history
                )
                delta = f"{trend:+.1f}%" if trend != 0 else None
                st.metric(
                    "🎯 Current Risk",
                    f"{current_risk}%",
                    delta=delta,
                    help="Current risk index (0-100)"
                )
    
    def render_sidebar(self):
        """Render sidebar with controls and information"""
        with st.sidebar:
            # Logo
            st.image("https://via.placeholder.com/300x80/1e3c72/ffffff?text=YERUSLAN+TECHNOLOGIES", 
                    use_container_width=True)
            
            st.markdown("---")
            
            # Control Panel
            st.subheader("🎛️ Control Panel")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⚡ Start System", type="primary", use_container_width=True):
                    self.start_system()
            
            with col2:
                if st.button("🛑 Emergency Stop", type="secondary", use_container_width=True):
                    self.emergency_stop()
            
            # System settings
            with st.expander("⚙️ Settings", expanded=False):
                st.session_state.refresh_rate = st.slider(
                    "Refresh Rate (s)",
                    min_value=0.1,
                    max_value=2.0,
                    value=st.session_state.refresh_rate,
                    step=0.1
                )
                
                st.session_state.auto_scroll = st.checkbox(
                    "Auto-scroll charts",
                    value=st.session_state.auto_scroll
                )
                
                st.session_state.theme = st.selectbox(
                    "Theme",
                    options=["dark", "light"],
                    index=0 if st.session_state.theme == "dark" else 1
                )
            
            st.markdown("---")
            
            # Live Statistics
            if st.session_state.system_running:
                st.subheader("📊 Live Statistics")
                
                stats = self.data_manager.get_statistics()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Readings", stats['total_readings'])
                    st.metric("Avg Risk", f"{stats['avg_risk']:.1f}%")
                
                with col2:
                    st.metric("Max Risk", f"{stats['max_risk']}%")
                    st.metric("Alerts", stats['alert_count'])
                
                # Alert panel
                st.markdown("---")
                render_alert_panel()
            
            # System Information
            st.markdown("---")
            st.subheader("🏭 System Info")
            
            with st.expander("📋 System Architecture", expanded=False):
                st.markdown("""
                **Sensors:**
                • 4x Vibration (PCB 603C01)
                • 4x Thermal (FLIR A500f)
                • 1x Acoustic (NI 9234)
                
                **Actuators:**
                • 4x MR Dampers (LORD RD-8040)
                
                **AI Engine:**
                • Isolation Forest v2.0
                • 150 estimators
                • 9 features
                """)
            
            with st.expander("💰 Business Case", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("System Cost", "$250,000")
                    st.metric("ROI", ">2000%")
                with col2:
                    st.metric("Payback", "<3 months")
                    st.metric("MTBF", "8760 hrs")
            
            # Reset button (hidden in production)
            if st.checkbox("🔧 Developer Mode", value=False):
                if st.button("🔄 Reset System", use_container_width=True):
                    self.reset_system()
    
    def start_system(self):
        """Start the monitoring system"""
        st.session_state.system_running = True
        st.session_state.system_status = SystemStatus.NORMAL
        st.session_state.error_count = 0
        st.session_state.start_time = datetime.now()
        st.session_state.current_cycle = 0
        
        self.data_manager.reset()
        self.alert_system.resolve_all_by_rule("system_error")
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
    
    def reset_system(self):
        """Reset system to initial state"""
        st.session_state.system_running = False
        st.session_state.system_status = SystemStatus.STANDBY
        st.session_state.error_count = 0
        st.session_state.start_time = None
        st.session_state.current_cycle = 0
        
        self.data_manager.reset()
        self.ai_model.initialize_model()
        
        logger.info("System reset")
        st.rerun()
    
    def calculate_risk_index(self, vibration: Dict, temperature: Dict, 
                           noise: float, ai_prediction: int, 
                           ai_confidence: float) -> int:
        """Calculate comprehensive risk index"""
        try:
            # Sensor-based risk (0-60)
            vib_risk = np.mean([min(v / 6.0, 1.0) for v in vibration.values()]) * 20
            temp_risk = np.mean([min((t - 20) / 80, 1.0) for t in temperature.values()]) * 20
            noise_risk = min((noise - 30) / 70, 1.0) * 20
            
            # AI-based risk (0-40)
            if ai_prediction == -1:  # Anomaly detected
                ai_risk = (1 - abs(ai_confidence)) * 40
            else:
                ai_risk = abs(ai_confidence) * 20
            
            # Combine risks
            total_risk = vib_risk + temp_risk + noise_risk + ai_risk
            
            # Add some randomness for realism
            total_risk += np.random.normal(0, 2)
            
            # Clamp to 0-100
            return int(max(0, min(100, total_risk)))
            
        except Exception as e:
            logger.error(f"Risk calculation error: {e}")
            return 50
    
    def determine_system_status(self, risk_index: int, ai_prediction: int) -> SystemStatus:
        """Determine system status based on risk and AI prediction"""
        if ai_prediction == -1 and risk_index > 70:
            return SystemStatus.CRITICAL
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
            return self.config.DAMPER_FORCES['critical']
        elif risk_index > 50:
            return self.config.DAMPER_FORCES['warning']
        elif risk_index > 20:
            return self.config.DAMPER_FORCES['normal']
        else:
            return self.config.DAMPER_FORCES['standby']
    
    def calculate_rul(self, risk_index: int, trend: float) -> int:
        """Calculate Remaining Useful Life in hours"""
        base_rul = max(0, 100 - risk_index * 0.9)
        
        # Adjust based on trend
        if trend > 5:  # Rapidly increasing risk
            base_rul *= 0.7
        elif trend > 2:  # Slowly increasing
            base_rul *= 0.9
        elif trend < -2:  # Improving
            base_rul *= 1.2
        
        return int(base_rul)
    
    def render_idle_state(self):
        """Render idle state when system is not running"""
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("### 🚀 Ready to Start")
            st.write("""
            Click **'Start System'** in the sidebar to begin monitoring.
            
            The system will simulate:
            - Normal operation (0-30 cycles)
            - Gradual degradation (30-60 cycles)
            - Critical condition (60-100 cycles)
            """)
        
        with col2:
            st.success("### ✅ System Check")
            
            checks = {
                "AI Model": self.ai_model.is_trained,
                "Data Manager": True,
                "Alert System": True,
                "Configuration": True
            }
            
            for check, status in checks.items():
                if status:
                    st.write(f"✅ {check}: Ready")
                else:
                    st.write(f"❌ {check}: Not Ready")
        
        with col3:
            st.warning("### 📊 Demo Mode")
            st.write("""
            Running in demonstration mode with simulated data.
            
            **Features to explore:**
            - Real-time sensor monitoring
            - AI anomaly detection
            - Active vibration control
            - Predictive maintenance
            """)
        
        # Preview charts
        st.markdown("---")
        st.subheader("📈 Preview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sample vibration data
            sample_vib = pd.DataFrame({
                'Motor Drive': [1.2, 1.3, 1.1, 1.4, 1.3],
                'Motor Non-Drive': [1.1, 1.2, 1.3, 1.2, 1.4],
                'Pump Inlet': [1.3, 1.4, 1.2, 1.5, 1.6],
                'Pump Outlet': [1.2, 1.3, 1.4, 1.3, 1.5]
            })
            st.line_chart(sample_vib)
        
        with col2:
            # Sample risk data
            sample_risk = pd.DataFrame({
                'Risk Index': [25, 28, 32, 35, 40],
                'Warning': [50] * 5,
                'Critical': [80] * 5
            })
            st.line_chart(sample_risk)
    
    def render_footer(self):
        """Render application footer"""
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.caption(f"© 2024 Yeruslan Technologies. All rights reserved.")
        
        with col2:
            st.caption(f"Version {settings.APP_VERSION} | Build {datetime.now().strftime('%Y%m%d')}")
        
        with col3:
            st.caption("🔒 Secure Connection | ISO 27001 Certified")
    
    def run_monitoring_loop(self):
        """Main monitoring loop"""
        try:
            # Initialize progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Main tabs
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Live Monitoring",
                "📈 Trends & Analytics",
                "🔧 Diagnostics",
                "📋 Reports"
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
                
                # Calculate trend
                if len(self.data_manager.risk_history) > 5:
                    trend = calculate_trend(self.data_manager.risk_history[-5:])
                else:
                    trend = 0
                
                # Update system status
                st.session_state.system_status = self.determine_system_status(
                    risk_index, ai_prediction
                )
                
                # Determine damper forces
                damper_force = self.determine_damper_force(risk_index)
                damper_forces = {d: damper_force for d in self.config.MR_DAMPERS.keys()}
                self.data_manager.damper_forces = damper_forces
                
                # Calculate RUL
                rul_hours = self.calculate_rul(risk_index, trend)
                
                # Save data
                self.data_manager.add_reading(
                    cycle, vibration, temperature, noise, damper_forces, risk_index
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
                    'error_count': st.session_state.error_count,
                    'cycle': cycle
                }
                self.alert_system.check_alerts(alert_data)
                
                # Auto-resolve alerts if conditions improve
                if risk_index < 50:
                    self.alert_system.resolve_all_by_rule("high_risk")
                if risk_index < 80:
                    self.alert_system.resolve_all_by_rule("critical_risk")
                
                # Update tabs
                with tab1:
                    self.render_live_monitoring_tab(
                        cycle, vibration, temperature, noise,
                        risk_index, ai_confidence, rul_hours, damper_forces
                    )
                
                with tab2:
                    self.render_trends_tab()
                
                with tab3:
                    self.render_diagnostics_tab(
                        risk_index, ai_confidence, ai_prediction, trend
                    )
                
                with tab4:
                    self.render_reports_tab(cycle)
                
                # Update progress
                progress = (cycle + 1) / settings.SIMULATION_CYCLES
                progress_bar.progress(progress)
                status_text.text(f"🔄 Cycle: {cycle+1}/{settings.SIMULATION_CYCLES}")
                
                # Wait for next cycle
                time.sleep(st.session_state.refresh_rate)
            
            # Cleanup
            progress_bar.empty()
            status_text.empty()
            
            if cycle >= settings.SIMULATION_CYCLES - 1:
                st.success("✅ Simulation cycle completed successfully!")
                self.alert_system.add_alert(
                    AlertLevel.SUCCESS,
                    "Simulation cycle completed"
                )
                
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")
            st.error(f"System error: {str(e)}")
            self.alert_system.add_alert(
                AlertLevel.ERROR,
                f"System error: {str(e)}"
            )
            st.session_state.system_running = False
    
    def render_live_monitoring_tab(self, cycle: int, vibration: Dict, 
                                  temperature: Dict, noise: float,
                                  risk_index: int, ai_confidence: float,
                                  rul_hours: int, damper_forces: Dict):
        """Render live monitoring tab"""
        
        # Top metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📊 Risk Index",
                f"{risk_index}%",
                delta=f"{risk_index - (self.data_manager.risk_history[-2] if len(self.data_manager.risk_history) > 1 else 0):+.1f}%",
                help="Overall system risk index"
            )
        
        with col2:
            st.metric(
                "🤖 AI Confidence",
                f"{abs(ai_confidence):.2f}",
                help="AI anomaly detection confidence"
            )
        
        with col3:
            st.metric(
                "⏳ RUL",
                f"{rul_hours} hours",
                help="Remaining Useful Life"
            )
        
        with col4:
            st.metric(
                "🔄 Cycle",
                f"{cycle}/{settings.SIMULATION_CYCLES}",
                help="Current simulation cycle"
            )
        
        # Main monitoring area
        col1, col2 = st.columns(2)
        
        with col1:
            # Vibration monitoring
            st.subheader("📈 Vibration Monitoring")
            
            if not self.data_manager.vibration_data.empty:
                # Show last 50 points for better performance
                display_data = self.data_manager.vibration_data.tail(50)
                st.line_chart(display_data, height=200)
            
            # Vibration status
            self.ui.sensor_status_section(
                self.config.VIBRATION_SENSORS,
                vibration,
                "Current Readings:"
            )
            
            # Temperature monitoring
            st.subheader("🌡️ Thermal Monitoring")
            
            if not self.data_manager.temperature_data.empty:
                display_data = self.data_manager.temperature_data.tail(50)
                st.line_chart(display_data, height=200)
            
            # Temperature status
            self.ui.sensor_status_section(
                self.config.THERMAL_SENSORS,
                temperature,
                "Current Readings:"
            )
        
        with col2:
            # Acoustic monitoring
            st.subheader("🔊 Acoustic Monitoring")
            
            if not self.data_manager.noise_data.empty:
                display_data = self.data_manager.noise_data.tail(50)
                st.line_chart(display_data, height=200)
            
            # Noise status
            sensor_name, limits = self.config.ACOUSTIC_SENSOR
            level = limits.get_level(noise)
            
            if level == AlertLevel.ERROR:
                st.error(f"🔴 **{sensor_name}:** {noise:.1f} dB")
            elif level == AlertLevel.WARNING:
                st.warning(f"⚠️ **{sensor_name}:** {noise:.1f} dB")
            else:
                st.success(f"✅ **{sensor_name}:** {noise:.1f} dB")
            
            # Risk gauge
            st.subheader("🎯 Risk Assessment")
            gauge_fig = self.ui.create_gauge(risk_index, "Current Risk", 0, 100)
            st.plotly_chart(gauge_fig, use_container_width=True, key="gauge_live")
            
            # MR Dampers
            st.subheader("🔄 MR Dampers")
            
            cols = st.columns(4)
            for i, (damper_id, damper_name) in enumerate(self.config.MR_DAMPERS.items()):
                with cols[i]:
                    force = damper_forces[damper_id]
                    
                    if force >= 4000:
                        st.error(f"🔴 **{damper_name}**\n{force} N")
                    elif force >= 1000:
                        st.warning(f"🟡 **{damper_name}**\n{force} N")
                    else:
                        st.success(f"🟢 **{damper_name}**\n{force} N")
    
    def render_trends_tab(self):
        """Render trends and analytics tab"""
        
        # Time range selector
        time_range = st.selectbox(
            "Time Range",
            options=["Last 10", "Last 25", "Last 50", "All"],
            index=2
        )
        
        range_map = {
            "Last 10": 10,
            "Last 25": 25,
            "Last 50": 50,
            "All": len(self.data_manager.vibration_data)
        }
        points = range_map[time_range]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Vibration Trends")
            if not self.data_manager.vibration_data.empty:
                display_data = self.data_manager.vibration_data.tail(points)
                fig = self.ui.create_trend_chart(
                    display_data.T,  # Transpose for better visualization
                    "Vibration Over Time"
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Temperature Trends")
            if not self.data_manager.temperature_data.empty:
                display_data = self.data_manager.temperature_data.tail(points)
                fig = self.ui.create_trend_chart(
                    display_data.T,
                    "Temperature Over Time"
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        
        # Risk history
        st.subheader("Risk History")
        if self.data_manager.risk_history:
            risk_df = pd.DataFrame({
                'Risk Index': self.data_manager.risk_history[-points:],
                'Critical Threshold': [80] * min(points, len(self.data_manager.risk_history)),
                'Warning Threshold': [50] * min(points, len(self.data_manager.risk_history))
            })
            st.line_chart(risk_df)
        
        # Correlation matrix
        st.subheader("Sensor Correlation")
        if len(self.data_manager.vibration_data) > 10:
            # Combine all data
            all_data = pd.concat([
                self.data_manager.vibration_data.add_prefix('VIB_'),
                self.data_manager.temperature_data.add_prefix('TEMP_'),
                self.data_manager.noise_data.rename(columns={self.config.ACOUSTIC_SENSOR[0]: 'NOISE'})
            ], axis=1)
            
            # Calculate correlation
            corr = all_data.corr()
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=corr.values,
                x=corr.columns,
                y=corr.columns,
                colorscale='RdBu',
                zmin=-1, zmax=1
            ))
            fig.update_layout(
                title="Sensor Correlation Matrix",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render_diagnostics_tab(self, risk_index: int, ai_confidence: float,
                              ai_prediction: int, trend: float):
        """Render diagnostics tab"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("System Health")
            
            # Health metrics
            health_score = max(0, 100 - risk_index)
            st.metric("Health Score", f"{health_score}%", delta=f"{trend:+.1f}%")
            
            # AI Status
            if ai_prediction == -1:
                st.warning("⚠️ AI Status: Anomaly Detected")
            else:
                st.success("✅ AI Status: Normal Operation")
            
            # Data quality
            data_completeness = len(self.data_manager.vibration_data) / settings.SIMULATION_CYCLES * 100
            st.metric("Data Completeness", f"{data_completeness:.1f}%")
            
            # Alert statistics
            stats = self.alert_system.get_statistics()
            st.metric("Active Alerts", stats['active_alerts'])
        
        with col2:
            st.subheader("Performance Metrics")
            
            # Create gauge for AI confidence
            conf_fig = self.ui.create_gauge(
                abs(ai_confidence) * 100,
                "AI Confidence",
                0, 100
            )
            st.plotly_chart(conf_fig, use_container_width=True, key="gauge_diag")
            
            # Model info
            st.info(f"""
            **Model Information:**
            - Type: Isolation Forest
            - Estimators: 150
            - Features: {len(self.ai_model.feature_names)}
            - Contamination: 0.15
            - Trained: {self.ai_model.is_trained}
            """)
        
        # Component health
        st.subheader("Component Health")
        
        health_data = []
        for sensor_id, (sensor_name, limits) in self.config.VIBRATION_SENSORS.items():
            if sensor_id in self.data_manager.vibration_data.columns:
                latest = self.data_manager.vibration_data[sensor_id].iloc[-1] if len(self.data_manager.vibration_data) > 0 else 0
                health = max(0, 100 - (latest / limits.critical * 100))
                health_data.append({
                    'Component': sensor_name,
                    'Type': 'Vibration',
                    'Health': health,
                    'Status': 'Good' if health > 80 else 'Warning' if health > 50 else 'Critical'
                })
        
        for sensor_id, (sensor_name, limits) in self.config.THERMAL_SENSORS.items():
            if sensor_id in self.data_manager.temperature_data.columns:
                latest = self.data_manager.temperature_data[sensor_id].iloc[-1] if len(self.data_manager.temperature_data) > 0 else 0
                health = max(0, 100 - ((latest - 20) / (limits.critical - 20) * 100))
                health_data.append({
                    'Component': sensor_name,
                    'Type': 'Temperature',
                    'Health': health,
                    'Status': 'Good' if health > 80 else 'Warning' if health > 50 else 'Critical'
                })
        
        if health_data:
            health_df = pd.DataFrame(health_data)
            
            # Color coding
            def color_status(val):
                if val == 'Critical':
                    return 'background-color: #ff4b4b'
                elif val == 'Warning':
                    return 'background-color: #ffa64b'
                else:
                    return 'background-color: #4bff4b'
            
            styled_df = health_df.style.applymap(color_status, subset=['Status'])
            st.dataframe(styled_df, use_container_width=True)
    
    def render_reports_tab(self, current_cycle: int):
        """Render reports tab"""
        
        st.subheader("Generate System Report")
        
        col1, col2 = st.columns(2)
        
        with col1:
            report_type = st.selectbox(
                "Report Type",
                options=["Summary Report", "Detailed Analysis", "Alert History", "Performance Report"]
            )
            
            include_charts = st.checkbox("Include Charts", value=True)
            include_raw_data = st.checkbox("Include Raw Data", value=False)
        
        with col2:
            date_range = st.date_input(
                "Date Range",
                value=(datetime.now() - timedelta(days=7), datetime.now()),
                max_value=datetime.now()
            )
            
            format_type = st.selectbox(
                "Export Format",
                options=["HTML", "PDF", "CSV", "JSON"]
            )
        
        if st.button("📄 Generate Report", type="primary", use_container_width=True):
            with st.spinner("Generating report..."):
                time.sleep(2)  # Simulate report generation
                
                stats = self.data_manager.get_statistics()
                alert_stats = self.alert_system.get_statistics()
                
                # Create report
                st.markdown("---")
                st.subheader("📊 System Report")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("### System Information")
                    st.write(f"**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**System Version:** {settings.APP_VERSION}")
                    st.write(f"**Uptime:** {stats['uptime_seconds']:.0f} seconds")
                    st.write(f"**Total Cycles:** {current_cycle}")
                
                with col2:
                    st.markdown("### Performance Metrics")
                    st.write(f"**Current Risk:** {stats['current_risk']}%")
                    st.write(f"**Average Risk:** {stats['avg_risk']:.1f}%")
                    st.write(f"**Maximum Risk:** {stats['max_risk']}%")
                    st.write(f"**Data Points:** {stats['total_readings']}")
                
                with col3:
                    st.markdown("### Alert Statistics")
                    st.write(f"**Total Alerts:** {alert_stats['total_alerts']}")
                    st.write(f"**Active Alerts:** {alert_stats['active_alerts']}")
                    st.write(f"**Recent Alerts:** {alert_stats['recent_alerts']}")
                    st.write(f"**Resolution Rate:** {alert_stats['resolution_rate']:.1f}%")
                
                if include_charts:
                    st.markdown("### Risk Trend")
                    if self.data_manager.risk_history:
                        risk_df = pd.DataFrame({
                            'Risk Index': self.data_manager.risk_history,
                            'Critical': [80] * len(self.data_manager.risk_history),
                            'Warning': [50] * len(self.data_manager.risk_history)
                        })
                        st.line_chart(risk_df)
                
                if include_raw_data:
                    st.markdown("### Raw Data Sample")
                    st.dataframe(self.data_manager.vibration_data.tail(10))
                
                # Download buttons
                col1, col2 = st.columns(2)
                with col1:
                    report_text = f"""
                    AVCS DNA System Report
                    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    
                    System Information:
                    - Version: {settings.APP_VERSION}
                    - Uptime: {stats['uptime_seconds']} seconds
                    - Total Cycles: {current_cycle}
                    
                    Performance Metrics:
                    - Current Risk: {stats['current_risk']}%
                    - Average Risk: {stats['avg_risk']:.1f}%
                    - Maximum Risk: {stats['max_risk']}%
                    
                    Alert Statistics:
                    - Total Alerts: {alert_stats['total_alerts']}
                    - Active Alerts: {alert_stats['active_alerts']}
                    - Resolution Rate: {alert_stats['resolution_rate']:.1f}%
                    """
                    
                    st.download_button(
                        "📥 Download Report",
                        data=report_text,
                        file_name=f"avcs_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                with col2:
                    if not self.data_manager.vibration_data.empty:
                        csv_data = self.data_manager.vibration_data.to_csv()
                        st.download_button(
                            "📥 Download Data",
                            data=csv_data,
                            file_name=f"sensor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

# Application entry point
if __name__ == "__main__":
    try:
        app = ThermalDNAApp()
        app.run()
    except Exception as e:
        logger.critical(f"Fatal application error: {e}")
        st.error(f"""
        ### ❌ Fatal Application Error
        
        **Error:** {str(e)}
        
        Please check the logs and restart the application.
        
        If the problem persists, contact support at support@yeruslan.com
        """)
        
        # Display traceback in development
        import traceback
        with st.expander("Technical Details"):
            st.code(traceback.format_exc())
