# app.py - AVCS DNA Industrial Monitor v7.0 (International Operator Interface)
"""Optimized for CCR Operator - Simple, Clear, No Stress - International Version"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from modules.config import settings, SystemStatus, industrial_config
from modules.data_manager import data_manager
from modules.ai_model import ai_model
from modules.sensor_simulator import sensor_simulator
from modules.alert_system import alert_system
from utils.logger import logger

# Page config
st.set_page_config(
    page_title=f"{settings.APP_ICON} AVCS Operator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for operator
st.markdown("""
<style>
    /* Full screen container */
    .main > div {
        padding: 0rem 1rem;
    }
    
    /* Large status indicators */
    .status-box {
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .status-critical {
        background-color: #ff4444;
        color: white;
        animation: pulse 1s infinite;
    }
    
    .status-warning {
        background-color: #ffaa00;
        color: white;
    }
    
    .status-normal {
        background-color: #00C851;
        color: white;
    }
    
    .status-standby {
        background-color: #33b5e5;
        color: white;
    }
    
    /* Sensor cards */
    .sensor-card {
        background: #f8f9fa;
        border-left: 5px solid #33b5e5;
        padding: 15px;
        border-radius: 5px;
        margin: 5px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .sensor-critical {
        border-left-color: #ff4444;
        background: #fff5f5;
    }
    
    .sensor-warning {
        border-left-color: #ffaa00;
        background: #fff9e6;
    }
    
    /* Large metrics */
    .big-metric {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .big-label {
        font-size: 18px;
        opacity: 0.9;
    }
    
    /* Pulse animation for critical states */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    /* Control buttons */
    .control-button {
        font-size: 20px !important;
        padding: 15px !important;
        margin: 5px !important;
    }
    
    /* Hide unnecessary elements */
    .stDeployButton, footer {
        display: none !important;
    }
    
    /* Metric containers */
    .metric-container {
        text-align: center;
        padding: 15px;
        border-radius: 10px;
        background: #f8f9fa;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-value {
        font-size: 48px;
        font-weight: bold;
        line-height: 1.2;
    }
    
    .metric-label {
        font-size: 16px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

class OperatorInterface:
    """Simple operator interface - International Version"""
    
    def __init__(self):
        self.config = industrial_config
        self.data_manager = data_manager
        self.ai_model = ai_model
        self.simulator = sensor_simulator
        self.alert_system = alert_system
        self.init_session()
    
    def init_session(self):
        if "running" not in st.session_state:
            st.session_state.running = False
            st.session_state.status = SystemStatus.STANDBY
            st.session_state.cycle = 0
            st.session_state.last_update = datetime.now()
    
    def run(self):
        """Main operator screen"""
        
        # Top bar with clock and status
        col_time, col_status, col_control = st.columns([1, 2, 1])
        
        with col_time:
            current_time = datetime.now().strftime("%H:%M:%S")
            st.markdown(f"### 🕐 {current_time} UTC")
        
        with col_status:
            status = st.session_state.status.value
            if st.session_state.status == SystemStatus.CRITICAL:
                st.markdown(f'<div class="status-box status-critical">🚨 {status}</div>', 
                           unsafe_allow_html=True)
            elif st.session_state.status == SystemStatus.WARNING:
                st.markdown(f'<div class="status-box status-warning">⚠️ {status}</div>', 
                           unsafe_allow_html=True)
            elif st.session_state.status == SystemStatus.NORMAL:
                st.markdown(f'<div class="status-box status-normal">✅ {status}</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="status-box status-standby">⏸️ {status}</div>', 
                           unsafe_allow_html=True)
        
        with col_control:
            if not st.session_state.running:
                if st.button("🚀 START", type="primary", use_container_width=True):
                    self.start_system()
            else:
                if st.button("🛑 STOP", type="secondary", use_container_width=True):
                    self.stop_system()
        
        st.markdown("---")
        
        if st.session_state.running:
            self.show_monitoring_dashboard()
        else:
            self.show_ready_screen()
    
    def start_system(self):
        """Start monitoring system"""
        st.session_state.running = True
        st.session_state.status = SystemStatus.NORMAL
        st.session_state.start_time = datetime.now()
        self.data_manager.reset()
        st.rerun()
    
    def stop_system(self):
        """Stop monitoring system"""
        st.session_state.running = False
        st.session_state.status = SystemStatus.STANDBY
        st.rerun()
    
    def show_ready_screen(self):
        """Ready screen"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="text-align: center; padding: 50px;">
                <h1>✅ SYSTEM READY</h1>
                <p style="font-size: 20px;">Press START to begin monitoring</p>
            </div>
            """, unsafe_allow_html=True)
    
    def show_monitoring_dashboard(self):
        """Main monitoring dashboard - ALL ON ONE SCREEN"""
        
        # Generate data
        if st.session_state.cycle < settings.SIMULATION_CYCLES:
            vibration, temperature, noise = self.simulator.generate_data(st.session_state.cycle)
            
            if vibration:
                # Calculate risk
                risk = self.calculate_risk(vibration, temperature, noise)
                
                # Update status
                if risk > 80:
                    st.session_state.status = SystemStatus.CRITICAL
                elif risk > 50:
                    st.session_state.status = SystemStatus.WARNING
                
                # Damper force
                damper_force = self.get_damper_force(risk)
                
                # Save data
                self.data_manager.add_reading(
                    st.session_state.cycle, vibration, temperature, noise,
                    {d: damper_force for d in self.config.MR_DAMPERS.keys()},
                    risk, {}
                )
                
                st.session_state.cycle += 1
        
        # === MAIN DASHBOARD - EVERYTHING VISIBLE WITHOUT SCROLLING ===
        
        # Top row - KEY METRICS
        col_rul, col_risk, col_alerts = st.columns(3)
        
        with col_risk:
            risk = self.data_manager.risk_history[-1] if self.data_manager.risk_history else 0
            risk_color = "#ff4444" if risk > 80 else "#ffaa00" if risk > 50 else "#00C851"
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">🎯 RISK INDEX</div>
                <div class="metric-value" style="color: {risk_color};">{risk}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_rul:
            rul = max(0, 100 - risk)
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">⏳ REMAINING LIFE</div>
                <div class="metric-value">{rul}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_alerts:
            active_alerts = len([a for a in self.alert_system.alerts if not a.resolved])
            alert_color = "#ff4444" if active_alerts > 0 else "#00C851"
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">⚠️ ACTIVE ALARMS</div>
                <div class="metric-value" style="color: {alert_color};">{active_alerts}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Middle row - ALL SENSORS (2 rows of 4)
        col_v1, col_v2, col_v3, col_v4 = st.columns(4)
        
        # Vibration sensors
        if self.data_manager.vibration_data is not None and len(self.data_manager.vibration_data) > 0:
            vib_data = self.data_manager.vibration_data.iloc[-1].to_dict()
            
            with col_v1:
                val = vib_data.get('VIB_MOTOR_DRIVE', 0)
                color = "#ff4444" if val > 4 else "#ffaa00" if val > 2 else "#00C851"
                st.markdown(f"""
                <div class="sensor-card">
                    <div style="font-size: 14px; color: #666;">MOTOR DRIVE</div>
                    <div style="font-size: 32px; font-weight: bold; color: {color};">{val:.1f}</div>
                    <div style="font-size: 12px; color: #666;">mm/s</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_v2:
                val = vib_data.get('VIB_MOTOR_NONDRIVE', 0)
                color = "#ff4444" if val > 4 else "#ffaa00" if val > 2 else "#00C851"
                st.markdown(f"""
                <div class="sensor-card">
                    <div style="font-size: 14px; color: #666;">MOTOR NON-DRIVE</div>
                    <div style="font-size: 32px; font-weight: bold; color: {color};">{val:.1f}</div>
                    <div style="font-size: 12px; color: #666;">mm/s</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_v3:
                val = vib_data.get('VIB_PUMP_INLET', 0)
                color = "#ff4444" if val > 4 else "#ffaa00" if val > 2 else "#00C851"
                st.markdown(f"""
                <div class="sensor-card">
                    <div style="font-size: 14px; color: #666;">PUMP INLET</div>
                    <div style="font-size: 32px; font-weight: bold; color: {color};">{val:.1f}</div>
                    <div style="font-size: 12px; color: #666;">mm/s</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_v4:
                val = vib_data.get('VIB_PUMP_OUTLET', 0)
                color = "#ff4444" if val > 4 else "#ffaa00" if val > 2 else "#00C851"
                st.markdown(f"""
                <div class="sensor-card">
                    <div style="font-size: 14px; color: #666;">PUMP OUTLET</div>
                    <div style="font-size: 32px; font-weight: bold; color: {color};">{val:.1f}</div>
                    <div style="font-size: 12px; color: #666;">mm/s</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Temperature sensors
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        
        if self.data_manager.temperature_data is not None and len(self.data_manager.temperature_data) > 0:
            temp_data = self.data_manager.temperature_data.iloc[-1].to_dict()
            
            with col_t1:
                val = temp_data.get('TEMP_MOTOR_WINDING', 0)
                color = "#ff4444" if val > 85 else "#ffaa00" if val > 70 else "#00C851"
                st.markdown(f"""
                <div class="sensor-card">
                    <div style="font-size: 14px; color: #666;">MOTOR WINDING</div>
                    <div style="font-size: 32px; font-weight: bold; color: {color};">{val:.0f}</div>
                    <div style="font-size: 12px; color: #666;">°C</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_t2:
                val = temp_data.get('TEMP_MOTOR_BEARING', 0)
                color = "#ff4444" if val > 85 else "#ffaa00" if val > 70 else "#00C851"
                st.markdown(f"""
                <div class="sensor-card">
                    <div style="font-size: 14px; color: #666;">MOTOR BEARING</div>
                    <div style="font-size: 32px; font-weight: bold; color: {color};">{val:.0f}</div>
                    <div style="font-size: 12px; color: #666;">°C</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_t3:
                val = temp_data.get('TEMP_PUMP_BEARING', 0)
                color = "#ff4444" if val > 85 else "#ffaa00" if val > 70 else "#00C851"
                st.markdown(f"""
                <div class="sensor-card">
                    <div style="font-size: 14px; color: #666;">PUMP BEARING</div>
                    <div style="font-size: 32px; font-weight: bold; color: {color};">{val:.0f}</div>
                    <div style="font-size: 12px; color: #666;">°C</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_t4:
                val = temp_data.get('TEMP_PUMP_CASING', 0)
                color = "#ff4444" if val > 85 else "#ffaa00" if val > 70 else "#00C851"
                st.markdown(f"""
                <div class="sensor-card">
                    <div style="font-size: 14px; color: #666;">PUMP CASING</div>
                    <div style="font-size: 32px; font-weight: bold; color: {color};">{val:.0f}</div>
                    <div style="font-size: 12px; color: #666;">°C</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Bottom row - NOISE and DAMPERS
        col_noise, col_dampers = st.columns(2)
        
        with col_noise:
            noise_val = self.data_manager.noise_data.iloc[-1].iloc[0] if not self.data_manager.noise_data.empty else 0
            noise_color = "#ff4444" if noise_val > 85 else "#ffaa00" if noise_val > 70 else "#00C851"
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 10px 0;">
                <div style="font-size: 18px; color: #666; margin-bottom: 10px;">🔊 ACOUSTIC NOISE</div>
                <div style="font-size: 48px; font-weight: bold; color: {noise_color};">{noise_val:.1f} dB</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_dampers:
            st.markdown("""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 10px 0;">
                <div style="font-size: 18px; color: #666; margin-bottom: 10px;">🔄 MR DAMPERS</div>
            </div>
            """, unsafe_allow_html=True)
            
            d1, d2, d3, d4 = st.columns(4)
            force = self.data_manager.damper_forces.get('DAMPER_FL', 0)
            force_color = "#ff4444" if force > 4000 else "#ffaa00" if force > 1000 else "#00C851"
            
            with d1:
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: {force_color};">{force}</div>
                    <div style="font-size: 14px; color: #666;">FL</div>
                </div>
                """, unsafe_allow_html=True)
            with d2:
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: {force_color};">{force}</div>
                    <div style="font-size: 14px; color: #666;">FR</div>
                </div>
                """, unsafe_allow_html=True)
            with d3:
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: {force_color};">{force}</div>
                    <div style="font-size: 14px; color: #666;">RL</div>
                </div>
                """, unsafe_allow_html=True)
            with d4:
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: {force_color};">{force}</div>
                    <div style="font-size: 14px; color: #666;">RR</div>
                </div>
                """, unsafe_allow_html=True)
    
    def calculate_risk(self, vibration, temperature, noise):
        """Simplified risk calculation"""
        vib_avg = sum(vibration.values()) / len(vibration)
        temp_avg = sum(temperature.values()) / len(temperature)
        
        vib_risk = min(vib_avg / 6.0, 1.0) * 40
        temp_risk = min((temp_avg - 20) / 80, 1.0) * 40
        noise_risk = min((noise - 30) / 70, 1.0) * 20
        
        return int(min(100, vib_risk + temp_risk + noise_risk))
    
    def get_damper_force(self, risk):
        """Damper force based on risk"""
        if risk > 80:
            return self.config.DAMPER_FORCES['critical']
        elif risk > 50:
            return self.config.DAMPER_FORCES['warning']
        elif risk > 20:
            return self.config.DAMPER_FORCES['normal']
        return self.config.DAMPER_FORCES['standby']

# Run application
if __name__ == "__main__":
    interface = OperatorInterface()
    interface.run()
