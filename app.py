# app.py - AVCS DNA Industrial Monitor v10.1 (No PDF Dependencies)
"""System that ASSISTS the operator but NEVER makes decisions"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import sys
from pathlib import Path
import plotly.graph_objects as go
import io
import base64

# PDF generation is commented out until reportlab is installed
# from reportlab.lib import colors
# from reportlab.lib.pagesizes import landscape, A4
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

sys.path.append(str(Path(__file__).parent))
from modules.config import settings, SystemStatus, industrial_config
from modules.data_manager import data_manager
from modules.ai_model import ai_model
from modules.sensor_simulator import sensor_simulator
from modules.alert_system import alert_system
from utils.logger import logger

st.set_page_config(
    page_title="AVCS - CCR CONTROL",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Industrial CSS (same as before)
st.markdown("""
<style>
    .main > div { padding: 0rem; max-width: 100%; }
    
    .status-bar {
        background-color: #1a1a1a;
        color: #00ff00;
        font-family: 'Courier New', monospace;
        padding: 5px 20px;
        font-size: 14px;
        border-bottom: 2px solid #333;
    }
    
    .main-status {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
        padding: 20px;
        margin: 10px 0;
        font-family: 'Courier New', monospace;
    }
    
    .status-critical { background-color: #ff4444; color: white; animation: blink 1s infinite; }
    .status-warning { background-color: #ffaa00; color: black; }
    .status-normal { background-color: #00C851; color: white; }
    .status-standby { background-color: #33b5e5; color: white; }
    
    .sensor-panel {
        background-color: #1e1e1e;
        border: 1px solid #333;
        padding: 15px;
        margin: 2px;
        font-family: 'Courier New', monospace;
    }
    
    .sensor-label {
        color: #888;
        font-size: 12px;
        text-transform: uppercase;
    }
    
    .sensor-value {
        color: #00ff00;
        font-size: 28px;
        font-weight: bold;
    }
    
    .sensor-critical .sensor-value { color: #ff4444; animation: blink 1s infinite; }
    .sensor-warning .sensor-value { color: #ffaa00; }
    
    .big-number {
        font-size: 72px;
        font-weight: bold;
        font-family: 'Courier New', monospace;
        text-align: center;
        line-height: 1;
    }
    
    .recommendation-panel {
        background-color: #2a2a2a;
        border-left: 5px solid #33b5e5;
        padding: 15px;
        margin: 10px 0;
        font-family: 'Courier New', monospace;
    }
    
    .recommendation-critical {
        border-left-color: #ff4444;
        background-color: #440000;
    }
    
    .recommendation-warning {
        border-left-color: #ffaa00;
        background-color: #443300;
    }
    
    .recommendation-title {
        color: #888;
        font-size: 14px;
        text-transform: uppercase;
    }
    
    .recommendation-text {
        color: white;
        font-size: 18px;
        margin: 10px 0;
    }
    
    .alarm-panel {
        background-color: #2a2a2a;
        padding: 10px;
        margin: 2px 0;
        border-left: 5px solid;
        font-family: 'Courier New', monospace;
    }
    
    .alarm-critical { border-left-color: #ff4444; background-color: #440000; animation: blink 1s infinite; }
    .alarm-warning { border-left-color: #ffaa00; background-color: #443300; }
    .alarm-info { border-left-color: #33b5e5; background-color: #003344; }
    
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .stDeployButton, footer, header { display: none !important; }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #1a1a1a;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #2a2a2a;
        color: white;
        font-family: 'Courier New', monospace;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #00C851 !important;
        color: black !important;
    }
</style>
""", unsafe_allow_html=True)

class HumanCenteredControlSystem:
    """System that RESPECTS operator decisions"""
    
    def __init__(self):
        self.config = industrial_config
        self.data_manager = data_manager
        self.ai_model = ai_model
        self.simulator = sensor_simulator
        self.alert_system = alert_system
        self.init_session()
        logger.info("Human-Centered Control System initialized")
    
    def init_session(self):
        if "system_running" not in st.session_state:
            st.session_state.system_running = False
            st.session_state.system_status = SystemStatus.STANDBY
            st.session_state.cycle = 0
            st.session_state.start_time = None
            st.session_state.current_risk = 0
            st.session_state.alarm_history = []
            st.session_state.operator_actions = []
            st.session_state.operator_notes = ""
    
    def run(self):
        """Main control screen"""
        self.render_status_bar()
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "🎯 MONITOR", 
            "📋 ALARMS", 
            "📊 REPORTS",
            "📝 NOTES"
        ])
        
        with tab1:
            if st.session_state.system_running:
                self.render_monitoring()
            else:
                self.render_ready_screen()
        
        with tab2:
            self.render_alarms()
        
        with tab3:
            self.render_reports()
        
        with tab4:
            self.render_operator_notes()
        
        if st.session_state.system_running:
            time.sleep(0.5)
            st.rerun()
    
    def render_status_bar(self):
        cols = st.columns([2, 1, 1, 1, 2])
        
        with cols[0]:
            st.markdown(f"<div class='status-bar'>🏭 AVCS v{settings.APP_VERSION}</div>", 
                       unsafe_allow_html=True)
        
        with cols[1]:
            if st.session_state.start_time:
                uptime = datetime.now() - st.session_state.start_time
                uptime_str = str(uptime).split('.')[0]
                st.markdown(f"<div class='status-bar'>⏱️ {uptime_str}</div>", 
                           unsafe_allow_html=True)
        
        with cols[2]:
            st.markdown(f"<div class='status-bar'>🔄 {st.session_state.cycle}</div>", 
                       unsafe_allow_html=True)
        
        with cols[3]:
            active = len([a for a in st.session_state.alarm_history if not a.get('acknowledged')])
            color = "#ff4444" if active > 0 else "#00ff00"
            st.markdown(f"<div class='status-bar' style='color: {color};'>⚠️ {active}</div>", 
                       unsafe_allow_html=True)
        
        with cols[4]:
            st.markdown(f"<div class='status-bar'>🕐 {datetime.now().strftime('%H:%M:%S')} UTC</div>", 
                       unsafe_allow_html=True)
    
    def render_ready_screen(self):
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style='text-align: center; padding: 50px;'>
                <div style='font-size: 120px; color: #333;'>⏸️</div>
                <div style='font-size: 36px; color: #666;'>SYSTEM STANDBY</div>
                <div style='font-size: 18px; color: #888; margin: 20px;'>Press START to begin monitoring</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚀 START", type="primary", use_container_width=True):
                self.start_system()
    
    def start_system(self):
        st.session_state.system_running = True
        st.session_state.system_status = SystemStatus.NORMAL
        st.session_state.start_time = datetime.now()
        st.session_state.cycle = 0
        self.data_manager.reset()
        self.log_operator_action("System started")
        st.rerun()
    
    def stop_system(self):
        st.session_state.system_running = False
        st.session_state.system_status = SystemStatus.STANDBY
        self.log_operator_action("EMERGENCY STOP")
        st.rerun()
    
    def render_monitoring(self):
        # Generate live data
        self.generate_live_data()
        
        if len(self.data_manager.vibration_data) == 0:
            return
        
        latest_vib = self.data_manager.vibration_data.iloc[-1].to_dict()
        latest_temp = self.data_manager.temperature_data.iloc[-1].to_dict()
        latest_noise = self.data_manager.noise_data.iloc[-1].iloc[0]
        risk = st.session_state.current_risk
        
        # Main status
        status = st.session_state.system_status.value
        status_class = "status-critical" if risk > 80 else "status-warning" if risk > 50 else "status-normal"
        
        st.markdown(f"""
        <div class='main-status {status_class}'>
            {status} | RISK: {risk}%
        </div>
        """, unsafe_allow_html=True)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            rul = max(0, 100 - risk)
            st.markdown(f"""
            <div class='sensor-panel'>
                <div class='sensor-label'>REMAINING LIFE</div>
                <div class='big-number'>{rul}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            force = self.data_manager.damper_forces.get('DAMPER_FL', 0)
            color = "#ff4444" if force > 4000 else "#ffaa00" if force > 1000 else "#00ff00"
            st.markdown(f"""
            <div class='sensor-panel'>
                <div class='sensor-label'>DAMPER FORCE</div>
                <div class='big-number' style='color: {color};'>{force}</div>
                <div class='sensor-unit'>N</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class='sensor-panel'>
                <div class='sensor-label'>ACOUSTIC NOISE</div>
                <div class='big-number'>{latest_noise:.0f}</div>
                <div class='sensor-unit'>dB</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            if st.button("🛑 STOP", type="secondary", use_container_width=True):
                self.stop_system()
        
        # Vibration sensors
        st.markdown("### VIBRATION [mm/s]")
        vcols = st.columns(4)
        vib_sensors = [
            ('VIB_MOTOR_DRIVE', 'MOTOR DRIVE'),
            ('VIB_MOTOR_NONDRIVE', 'MOTOR N/DRIVE'),
            ('VIB_PUMP_INLET', 'PUMP INLET'),
            ('VIB_PUMP_OUTLET', 'PUMP OUTLET')
        ]
        
        for i, (sensor_id, label) in enumerate(vib_sensors):
            with vcols[i]:
                val = latest_vib.get(sensor_id, 0)
                sensor_class = "sensor-critical" if val > 4 else "sensor-warning" if val > 2 else ""
                
                st.markdown(f"""
                <div class='sensor-panel {sensor_class}'>
                    <div class='sensor-label'>{label}</div>
                    <div class='sensor-value'>{val:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Temperature sensors
        st.markdown("### TEMPERATURE [°C]")
        tcols = st.columns(4)
        temp_sensors = [
            ('TEMP_MOTOR_WINDING', 'MOTOR WINDING'),
            ('TEMP_MOTOR_BEARING', 'MOTOR BEARING'),
            ('TEMP_PUMP_BEARING', 'PUMP BEARING'),
            ('TEMP_PUMP_CASING', 'PUMP CASING')
        ]
        
        for i, (sensor_id, label) in enumerate(temp_sensors):
            with tcols[i]:
                val = latest_temp.get(sensor_id, 0)
                sensor_class = "sensor-critical" if val > 85 else "sensor-warning" if val > 70 else ""
                
                st.markdown(f"""
                <div class='sensor-panel {sensor_class}'>
                    <div class='sensor-label'>{label}</div>
                    <div class='sensor-value'>{val:.0f}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # MR Dampers
        st.markdown("### MR DAMPERS [N]")
        dcols = st.columns(4)
        dampers = [
            ('DAMPER_FL', 'FRONT LEFT'),
            ('DAMPER_FR', 'FRONT RIGHT'),
            ('DAMPER_RL', 'REAR LEFT'),
            ('DAMPER_RR', 'REAR RIGHT')
        ]
        
        for i, (damper_id, label) in enumerate(dampers):
            with dcols[i]:
                force = self.data_manager.damper_forces.get(damper_id, 0)
                color = "#ff4444" if force > 4000 else "#ffaa00" if force > 1000 else "#00ff00"
                
                st.markdown(f"""
                <div class='sensor-panel'>
                    <div class='sensor-label'>{label}</div>
                    <div class='sensor-value' style='color: {color};'>{force}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Recommendations
        recommendations = self.generate_recommendations(risk, latest_vib, latest_temp, latest_noise)
        if recommendations:
            st.markdown("### 💡 OPERATOR RECOMMENDATIONS")
            for rec in recommendations:
                rec_class = "recommendation-critical" if rec['priority'] == "high" else "recommendation-warning"
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"""
                    <div class='recommendation-panel {rec_class}'>
                        <div class='recommendation-title'>⚠️ {rec['title']}</div>
                        <div class='recommendation-text'>{rec['message']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button(f"✅ ACK", key=f"rec_{rec['id']}", use_container_width=True):
                        self.log_operator_action(f"Followed: {rec['message']}")
                        st.success("Action logged")
        
        # Active alarms
        active = [a for a in st.session_state.alarm_history if not a.get('acknowledged')]
        if active:
            st.markdown("### 🚨 ACTIVE ALARMS")
            for alarm in active:
                alarm_class = "alarm-critical" if alarm['level'] == "critical" else "alarm-warning"
                
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"""
                    <div class='alarm-panel {alarm_class}'>
                        <strong>{alarm['time'].strftime('%H:%M:%S')}</strong> | {alarm['message']}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("✓ ACK", key=f"ack_{alarm['id']}", use_container_width=True):
                        self.acknowledge_alarm(alarm['id'])
                
                with col3:
                    if st.button("📝 NOTE", key=f"note_{alarm['id']}", use_container_width=True):
                        st.session_state[f"show_note_{alarm['id']}"] = True
    
    def render_alarms(self):
        st.markdown("## 📋 ALARM HISTORY")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            period = st.selectbox("Period", ["Last 24h", "Last 7d", "Last 30d", "All"], index=0)
        with col2:
            level = st.multiselect("Level", ["critical", "warning", "info"], default=["critical", "warning"])
        with col3:
            if st.button("CLEAR HISTORY", use_container_width=True):
                st.session_state.alarm_history = []
                st.rerun()
        
        filtered = st.session_state.alarm_history.copy()
        
        if period != "All":
            days = int(period.split()[1].replace('d', '').replace('h', ''))
            if 'h' in period:
                hours = days
                cutoff = datetime.now() - timedelta(hours=hours)
            else:
                cutoff = datetime.now() - timedelta(days=days)
            filtered = [a for a in filtered if a['time'] > cutoff]
        
        if level:
            filtered = [a for a in filtered if a['level'] in level]
        
        if filtered:
            data = []
            for alarm in reversed(filtered[-100:]):
                status = "✅" if alarm.get('acknowledged') else "⏳"
                note = alarm.get('note', '')
                data.append([
                    alarm['time'].strftime('%Y-%m-%d %H:%M:%S'),
                    alarm['level'].upper(),
                    alarm['message'],
                    status,
                    note
                ])
            
            df = pd.DataFrame(data, columns=["Time", "Level", "Message", "Status", "Note"])
            st.dataframe(df, use_container_width=True)
            
            if st.button("📥 EXPORT TO CSV", use_container_width=True):
                csv = df.to_csv(index=False)
                st.download_button("Download CSV", csv, "alarms.csv", "text/csv")
        else:
            st.info("No alarms in selected period")
    
    def render_reports(self):
        st.markdown("## 📊 GENERATE REPORT")
        st.info("PDF generation requires reportlab library. Install with: pip install reportlab")
        
        # Simple CSV export instead
        if st.button("📥 EXPORT DATA TO CSV", use_container_width=True):
            if len(self.data_manager.vibration_data) > 0:
                # Combine all data
                df = pd.concat([
                    self.data_manager.vibration_data.add_prefix('VIB_'),
                    self.data_manager.temperature_data.add_prefix('TEMP_'),
                    self.data_manager.noise_data.rename(columns={self.config.ACOUSTIC_SENSOR[0]: 'NOISE'})
                ], axis=1)
                df['RISK'] = self.data_manager.risk_history
                
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    f"data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    "text/csv"
                )
    
    def render_operator_notes(self):
        st.markdown("## 📝 OPERATOR NOTES")
        st.markdown(f"**Shift:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        notes = st.text_area("", value=st.session_state.operator_notes, height=200)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 SAVE NOTES", use_container_width=True):
                st.session_state.operator_notes = notes
                self.log_operator_action("Notes updated")
                st.success("Notes saved")
        
        with col2:
            if st.button("📥 EXPORT NOTES", use_container_width=True):
                st.download_button(
                    "Download Notes",
                    notes,
                    f"notes_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    "text/plain"
                )
        
        if st.session_state.operator_actions:
            st.markdown("### 📋 Action Log")
            for action in reversed(st.session_state.operator_actions[-20:]):
                st.caption(f"{action['time'].strftime('%H:%M:%S')} - {action['message']}")
    
    def generate_recommendations(self, risk, vibration, temperature, noise):
        recommendations = []
        
        if risk > 80:
            recommendations.append({
                'id': 'risk_high',
                'priority': 'high',
                'title': 'CRITICAL RISK',
                'message': 'Consider reducing load and inspecting equipment'
            })
        elif risk > 50:
            recommendations.append({
                'id': 'risk_medium',
                'priority': 'medium',
                'title': 'ELEVATED RISK',
                'message': 'Schedule maintenance review'
            })
        
        for sensor, value in vibration.items():
            if value > 4:
                name = self.config.VIBRATION_SENSORS[sensor][0]
                recommendations.append({
                    'id': f'vib_{sensor}',
                    'priority': 'high' if value > 5 else 'medium',
                    'title': 'HIGH VIBRATION',
                    'message': f'{name}: {value:.1f} mm/s. Consider bearing inspection'
                })
        
        for sensor, value in temperature.items():
            if value > 85:
                name = self.config.THERMAL_SENSORS[sensor][0]
                recommendations.append({
                    'id': f'temp_{sensor}',
                    'priority': 'high',
                    'title': 'CRITICAL TEMPERATURE',
                    'message': f'{name}: {value:.0f}°C. Check cooling system'
                })
            elif value > 70:
                name = self.config.THERMAL_SENSORS[sensor][0]
                recommendations.append({
                    'id': f'temp_{sensor}',
                    'priority': 'medium',
                    'title': 'HIGH TEMPERATURE',
                    'message': f'{name}: {value:.0f}°C. Monitor closely'
                })
        
        return recommendations[:5]
    
    def generate_live_data(self):
        vibration, temperature, noise = self.simulator.generate_data(st.session_state.cycle)
        
        if vibration:
            risk = self.calculate_risk(vibration, temperature, noise)
            st.session_state.current_risk = risk
            
            self.check_alarms(vibration, temperature, noise, risk)
            
            force = self.get_damper_force(risk)
            forces = {d: force for d in self.config.MR_DAMPERS.keys()}
            
            self.data_manager.add_reading(
                st.session_state.cycle, vibration, temperature, noise, forces, risk, {}
            )
            
            st.session_state.cycle += 1
            if st.session_state.cycle >= settings.SIMULATION_CYCLES:
                st.session_state.cycle = 0
    
    def check_alarms(self, vibration, temperature, noise, risk):
        for sensor, value in vibration.items():
            if value > 4:
                self.add_alarm('critical', f"High vibration: {self.config.VIBRATION_SENSORS[sensor][0]} = {value:.1f} mm/s")
            elif value > 2:
                self.add_alarm('warning', f"Elevated vibration: {self.config.VIBRATION_SENSORS[sensor][0]} = {value:.1f} mm/s")
        
        for sensor, value in temperature.items():
            if value > 85:
                self.add_alarm('critical', f"High temperature: {self.config.THERMAL_SENSORS[sensor][0]} = {value:.0f}°C")
            elif value > 70:
                self.add_alarm('warning', f"Elevated temperature: {self.config.THERMAL_SENSORS[sensor][0]} = {value:.0f}°C")
        
        if risk > 80:
            self.add_alarm('critical', f"Critical risk level: {risk}%")
        elif risk > 50:
            self.add_alarm('warning', f"Elevated risk level: {risk}%")
    
    def add_alarm(self, level, message):
        alarm_id = f"{level}_{datetime.now().timestamp()}"
        
        recent = [a for a in st.session_state.alarm_history 
                 if a['message'] == message 
                 and (datetime.now() - a['time']).total_seconds() < 600]
        
        if not recent:
            st.session_state.alarm_history.append({
                'id': alarm_id,
                'time': datetime.now(),
                'level': level,
                'message': message,
                'acknowledged': False
            })
            
            if len(st.session_state.alarm_history) > 1000:
                st.session_state.alarm_history = st.session_state.alarm_history[-1000:]
    
    def acknowledge_alarm(self, alarm_id):
        for alarm in st.session_state.alarm_history:
            if alarm['id'] == alarm_id:
                alarm['acknowledged'] = True
                alarm['acknowledged_at'] = datetime.now()
                self.log_operator_action(f"Acknowledged: {alarm['message']}")
                break
    
    def log_operator_action(self, message):
        st.session_state.operator_actions.append({
            'time': datetime.now(),
            'message': message
        })
        if len(st.session_state.operator_actions) > 100:
            st.session_state.operator_actions = st.session_state.operator_actions[-100:]
    
    def calculate_risk(self, vibration, temperature, noise):
        vib_avg = sum(vibration.values()) / len(vibration)
        temp_avg = sum(temperature.values()) / len(temperature)
        
        vib_risk = min(vib_avg / 6.0, 1.0) * 40
        temp_risk = min((temp_avg - 20) / 80, 1.0) * 40
        noise_risk = min((noise - 30) / 70, 1.0) * 20
        
        return int(min(100, vib_risk + temp_risk + noise_risk))
    
    def get_damper_force(self, risk):
        if risk > 80:
            return self.config.DAMPER_FORCES['critical']
        elif risk > 50:
            return self.config.DAMPER_FORCES['warning']
        elif risk > 20:
            return self.config.DAMPER_FORCES['normal']
        return self.config.DAMPER_FORCES['standby']

if __name__ == "__main__":
    system = HumanCenteredControlSystem()
    system.run()
