"""AVCS DNA Industrial Monitor - Main Application"""
import streamlit as st
import time
from datetime import datetime

# Local imports
from config.settings import settings
from config.constants import SystemStatus, AlertLevel, IndustrialConfig
from core.data_manager import DataManager
from core.ai_model import AIModelManager
from core.sensor_simulator import SensorSimulator
from ui.components import UIComponents
from utils.logger import setup_logger

# Initialize logger
logger = setup_logger()

class ThermalDNAApp:
    """Main application class"""
    
    def __init__(self):
        self.config = IndustrialConfig()
        self.data_manager = DataManager()
        self.ai_model = AIModelManager(model_path="models/isolation_forest.pkl")
        self.simulator = SensorSimulator()
        self.ui = UIComponents()
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize session state"""
        if "app" not in st.session_state:
            st.session_state.app = self
            st.session_state.system_running = False
            st.session_state.system_status = SystemStatus.STANDBY
            st.session_state.error_count = 0
            st.session_state.start_time = None
    
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
        """Configure page settings"""
        st.set_page_config(
            page_title=f"{settings.APP_ICON} {settings.APP_NAME} v{settings.APP_VERSION}",
            page_icon=settings.APP_ICON,
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            margin-bottom: 20px;
        }
        .metric-container {
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .status-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            display: inline-block;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """Render application header"""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"""
            <div class="main-header">
                <h1>{settings.APP_ICON} {settings.APP_NAME}</h1>
                <p>Version {settings.APP_VERSION} | Active Vibration Control with AI</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            status = st.session_state.system_status.value
            if st.session_state.system_status == SystemStatus.CRITICAL:
                st.error(f"## {status}")
            elif st.session_state.system_status == SystemStatus.WARNING:
                st.warning(f"## {status}")
            else:
                st.success(f"## {status}")
    
    def render_sidebar(self):
        """Render sidebar controls"""
        with st.sidebar:
            st.image("https://via.placeholder.com/300x100/1e3c72/ffffff?text=YERUSLAN+TECHNOLOGIES")
            
            st.header("🎛️ Control Panel")
            
            # Control buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⚡ Start", type="primary", use_container_width=True):
                    self.start_system()
            with col2:
                if st.button("🛑 Stop", type="secondary", use_container_width=True):
                    self.emergency_stop()
            
            # System info
            if st.session_state.system_running:
                st.markdown("---")
                st.subheader("📊 Live Statistics")
                
                stats = self.data_manager.get_statistics()
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Readings", stats['total_readings'])
                with col2:
                    st.metric("Current Risk", f"{stats['current_risk']}%")
                
                # Recent alerts
                alerts = self.data_manager.get_recent_alerts(3)
                if alerts:
                    st.markdown("---")
                    st.subheader("⚠️ Recent Alerts")
                    for alert in alerts:
                        st.caption(f"{alert['time'].strftime('%H:%M:%S')} - {alert['message']}")
            
            # System info
            st.markdown("---")
            st.subheader("🏭 System Info")
            st.info("""
            **Sensors:**
            • 4x Vibration (PCB 603C01)
            • 4x Thermal (FLIR A500f)
            • 1x Acoustic (NI 9234)
            
            **Actuators:**
            • 4x MR Dampers (LORD RD-8040)
            
            **AI Engine:**
            • Isolation Forest v2.0
            """)
    
    def start_system(self):
        """Start monitoring system"""
        st.session_state.system_running = True
        st.session_state.system_status = SystemStatus.NORMAL
        st.session_state.error_count = 0
        st.session_state.start_time = datetime.now()
        self.data_manager.reset()
        self.data_manager.add_alert(AlertLevel.SUCCESS.value, "System started")
        logger.info("System started")
        st.rerun()
    
    def emergency_stop(self):
        """Emergency stop procedure"""
        st.session_state.system_running = False
        st.session_state.system_status = SystemStatus.STANDBY
        self.data_manager.add_alert(AlertLevel.WARNING.value, "Emergency stop activated")
        logger.warning("Emergency stop activated")
        st.rerun()
    
    def calculate_risk_index(self, vibration: Dict, temperature: Dict, 
                           noise: float, ai_prediction: int, 
                           ai_confidence: float) -> int:
        """Calculate comprehensive risk index"""
        try:
            # Sensor-based risk (0-75)
            vib_risk = np.mean([v / 6.0 for v in vibration.values()]) * 25
            temp_risk = np.mean([(t - 20) / 80 for t in temperature.values()]) * 25
            noise_risk = (noise - 30) / 70 * 25
            
            # AI-based risk (0-25)
            if ai_prediction == -1:  # Anomaly detected
                ai_risk = (1 - abs(ai_confidence)) * 25
            else:
                ai_risk = abs(ai_confidence) * 25
            
            # Combine and normalize
            total_risk = min(100, max(0, vib_risk + temp_risk + noise_risk + ai_risk))
            
            return int(total_risk)
            
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
            st.write("Click 'Start' in the sidebar to begin monitoring")
        
        with col2:
            st.success("### ✅ System Check")
            st.write(f"AI Model: {'Ready' if self.ai_model.is_trained else 'Not Ready'}")
        
        with col3:
            st.warning("### 📊 Demo Mode")
            st.write("Running in demonstration mode with simulated data")
    
    def run_monitoring_loop(self):
        """Main monitoring loop"""
        try:
            # Initialize progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Main loop
            for cycle in range(settings.SIMULATION_CYCLES):
                if not st.session_state.system_running:
                    break
                
                # Generate data
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
                
                # Calculate RUL
                rul_hours = max(0, int(100 - risk_index * 0.9))
                
                # Save data
                self.data_manager.add_reading(
                    cycle, vibration, temperature, noise, damper_forces, risk_index
                )
                
                # Check for alerts
                self.check_alerts(vibration, temperature, noise, risk_index)
                
                # Render dashboard
                self.render_dashboard(
                    cycle, vibration, temperature, noise,
                    risk_index, ai_confidence, rul_hours
                )
                
                # Update progress
                progress = (cycle + 1) / settings.SIMULATION_CYCLES
                progress_bar.progress(progress)
                status_text.text(f"Cycle: {cycle+1}/{settings.SIMULATION_CYCLES}")
                
                # Wait
                time.sleep(settings.UPDATE_INTERVAL)
            
            # Cleanup
            progress_bar.empty()
            status_text.empty()
            
            if cycle >= settings.SIMULATION_CYCLES - 1:
                st.success("✅ Simulation completed!")
                self.data_manager.add_alert(AlertLevel.SUCCESS.value, "Simulation completed")
                
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")
            st.error(f"System error: {str(e)}")
            self.data_manager.add_alert(AlertLevel.ERROR.value, f"System error: {str(e)}")
            st.session_state.system_running = False
    
    def check_alerts(self, vibration: Dict, temperature: Dict, noise: float, risk_index: int):
        """Check for alert conditions"""
        # Check vibration sensors
        for sensor_id, (sensor_name, limits) in self.config.VIBRATION_SENSORS.items():
            value = vibration.get(sensor_id, 0)
            if value > limits.critical:
                self.data_manager.add_alert(
                    AlertLevel.CRITICAL.value,
                    f"{sensor_name} critical: {value:.1f} mm/s"
                )
            elif value > limits.warning:
                self.data_manager.add_alert(
                    AlertLevel.WARNING.value,
                    f"{sensor_name} high: {value:.1f} mm/s"
                )
        
        # Check overall risk
        if risk_index > 80:
            self.data_manager.add_alert(
                AlertLevel.CRITICAL.value,
                f"Critical risk level: {risk_index}%"
            )
        elif risk_index > 50:
            self.data_manager.add_alert(
                AlertLevel.WARNING.value,
                f"Elevated risk: {risk_index}%"
            )
    
    def render_dashboard(self, cycle: int, vibration: Dict, temperature: Dict, 
                        noise: float, risk_index: int, ai_confidence: float, 
                        rul_hours: int):
        """Render main dashboard"""
        
        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Overview", "📈 Trends", "🔧 Diagnostics", "📋 Reports"
        ])
        
        with tab1:
            self.render_overview_tab(vibration, temperature, noise, risk_index, rul_hours)
        
        with tab2:
            self.render_trends_tab()
        
        with tab3:
            self.render_diagnostics_tab(ai_confidence, risk_index)
        
        with tab4:
            self.render_reports_tab()
    
    def render_overview_tab(self, vibration: Dict, temperature: Dict, 
                           noise: float, risk_index: int, rul_hours: int):
        """Render overview tab"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Vibration section
            st.subheader("📈 Vibration Monitoring")
            self.ui.sensor_status_section(
                self.config.VIBRATION_SENSORS, vibration, ""
            )
            
            # Temperature section
            st.subheader("🌡️ Thermal Monitoring")
            self.ui.sensor_status_section(
                self.config.THERMAL_SENSORS, temperature, ""
            )
        
        with col2:
            # Noise section
            st.subheader("🔊 Acoustic Monitoring")
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
            st.plotly_chart(gauge_fig, use_container_width=True, key="gauge_main")
            
            # RUL
            st.metric("⏳ Remaining Useful Life", f"{rul_hours} hours")
    
    def render_trends_tab(self):
        """Render trends tab"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Vibration Trends")
            if not self.data_manager.vibration_data.empty:
                st.line_chart(self.data_manager.vibration_data)
        
        with col2:
            st.subheader("Temperature Trends")
            if not self.data_manager.temperature_data.empty:
                st.line_chart(self.data_manager.temperature_data)
        
        st.subheader("Risk History")
        if self.data_manager.risk_history:
            risk_df = pd.DataFrame({
                'Risk Index': self.data_manager.risk_history,
                'Critical': [80] * len(self.data_manager.risk_history),
                'Warning': [50] * len(self.data_manager.risk_history)
            })
            st.line_chart(risk_df)
    
    def render_diagnostics_tab(self, ai_confidence: float, risk_index: int):
        """Render diagnostics tab"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("AI Confidence", f"{abs(ai_confidence):.2f}")
            st.metric("Risk Level", f"{risk_index}%")
        
        with col2:
            st.metric("Data Points", len(self.data_manager.vibration_data))
            st.metric("Alert Count", len(self.data_manager.alerts))
        
        with col3:
            if self.ai_model.is_trained:
                st.success("✅ AI Model: Ready")
                st.info(f"Features: {len(self.ai_model.feature_names)}")
    
    def render_reports_tab(self):
        """Render reports tab"""
        st.subheader("System Report")
        
        if st.button("Generate Report"):
            stats = self.data_manager.get_statistics()
            
            report = f"""
            ### System Report
            - **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            - **Total Readings:** {stats['total_readings']}
            - **Current Risk:** {stats['current_risk']}%
            - **Average Risk:** {stats['avg_risk']:.1f}%
            - **Maximum Risk:** {stats['max_risk']}%
            - **Total Alerts:** {stats['alert_count']}
            - **Uptime:** {stats['uptime_seconds']:.0f} seconds
            """
            
            st.markdown(report)
            
            # Export buttons
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "📥 Download CSV",
                    data=self.data_manager.vibration_data.to_csv(),
                    file_name=f"vibration_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            with col2:
                st.download_button(
                    "📥 Download Report",
                    data=report,
                    file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )

# Application entry point
if __name__ == "__main__":
    app = ThermalDNAApp()
    app.run()
