# app.py - AVCS DNA Industrial Monitor v7.0 (Operator Interface)
"""Optimized for CCR Operator - Simple, Clear, No Stress"""

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
    initial_sidebar_state="collapsed"  # Скрываем sidebar по умолчанию
)

# Custom CSS для оператора
st.markdown("""
<style>
    /* Основной контейнер на весь экран */
    .main > div {
        padding: 0rem 1rem;
    }
    
    /* Крупные статусные индикаторы */
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
    
    /* Карточки сенсоров */
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
    
    /* Крупные метрики */
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
    
    /* Анимация для критических состояний */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    /* Кнопки управления */
    .control-button {
        font-size: 20px !important;
        padding: 15px !important;
        margin: 5px !important;
    }
    
    /* Скрываем лишние элементы */
    .stDeployButton, footer {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

class OperatorInterface:
    """Простой интерфейс для оператора"""
    
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
        """Главный экран оператора"""
        
        # Верхняя панель с часами и статусом
        col_time, col_status, col_control = st.columns([1, 2, 1])
        
        with col_time:
            current_time = datetime.now().strftime("%H:%M:%S")
            st.markdown(f"### 🕐 {current_time}")
        
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
                if st.button("🚀 ПУСК", type="primary", use_container_width=True):
                    self.start_system()
            else:
                if st.button("🛑 СТОП", type="secondary", use_container_width=True):
                    self.stop_system()
        
        st.markdown("---")
        
        if st.session_state.running:
            self.show_monitoring_dashboard()
        else:
            self.show_ready_screen()
    
    def start_system(self):
        """Запуск системы"""
        st.session_state.running = True
        st.session_state.status = SystemStatus.NORMAL
        st.session_state.start_time = datetime.now()
        self.data_manager.reset()
        st.rerun()
    
    def stop_system(self):
        """Остановка системы"""
        st.session_state.running = False
        st.session_state.status = SystemStatus.STANDBY
        st.rerun()
    
    def show_ready_screen(self):
        """Экран готовности"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="text-align: center; padding: 50px;">
                <h1>✅ СИСТЕМА ГОТОВА</h1>
                <p style="font-size: 20px;">Нажмите ПУСК для начала мониторинга</p>
            </div>
            """, unsafe_allow_html=True)
    
    def show_monitoring_dashboard(self):
        """Основная панель мониторинга - ВСЁ НА ОДНОМ ЭКРАНЕ"""
        
        # Генерируем данные
        if st.session_state.cycle < settings.SIMULATION_CYCLES:
            vibration, temperature, noise = self.simulator.generate_data(st.session_state.cycle)
            
            if vibration:
                # Расчет риска
                risk = self.calculate_risk(vibration, temperature, noise)
                
                # Обновляем статус
                if risk > 80:
                    st.session_state.status = SystemStatus.CRITICAL
                elif risk > 50:
                    st.session_state.status = SystemStatus.WARNING
                
                # Сила демпферов
                damper_force = self.get_damper_force(risk)
                
                # Сохраняем данные
                self.data_manager.add_reading(
                    st.session_state.cycle, vibration, temperature, noise,
                    {d: damper_force for d in self.config.MR_DAMPERS.keys()},
                    risk, {}
                )
                
                st.session_state.cycle += 1
        
        # === ОСНОВНАЯ ПАНЕЛЬ - ВСЁ ВИДНО БЕЗ ПРОКРУТКИ ===
        
        # Верхний ряд - КЛЮЧЕВЫЕ МЕТРИКИ
        col_rul, col_risk, col_alerts = st.columns(3)
        
        with col_risk:
            risk = self.data_manager.risk_history[-1] if self.data_manager.risk_history else 0
            risk_color = "red" if risk > 80 else "orange" if risk > 50 else "green"
            st.markdown(f"""
            <div style="text-align: center;">
                <span style="font-size: 16px;">🎯 РИСК</span>
                <div style="font-size: 48px; font-weight: bold; color: {risk_color};">{risk}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_rul:
            rul = max(0, 100 - risk)
            st.markdown(f"""
            <div style="text-align: center;">
                <span style="font-size: 16px;">⏳ РЕСУРС</span>
                <div style="font-size: 48px; font-weight: bold;">{rul}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_alerts:
            active_alerts = len([a for a in self.alert_system.alerts if not a.resolved])
            st.markdown(f"""
            <div style="text-align: center;">
                <span style="font-size: 16px;">⚠️ АВАРИИ</span>
                <div style="font-size: 48px; font-weight: bold; color: {'red' if active_alerts > 0 else 'green'};">
                    {active_alerts}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Средний ряд - ВСЕ СЕНСОРЫ (2 ряда по 4)
        col_v1, col_v2, col_v3, col_v4 = st.columns(4)
        
        # Вибрация (4 датчика)
        if self.data_manager.vibration_data is not None and len(self.data_manager.vibration_data) > 0:
            vib_data = self.data_manager.vibration_data.iloc[-1].to_dict()
            
            with col_v1:
                val = vib_data.get('VIB_MOTOR_DRIVE', 0)
                color = "red" if val > 4 else "orange" if val > 2 else "green"
                st.markdown(f"""
                <div class="sensor-card sensor-{color}">
                    <div style="font-size: 14px;">МОТОР DRIVE</div>
                    <div style="font-size: 28px; font-weight: bold;">{val:.1f}</div>
                    <div style="font-size: 12px;">mm/s</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_v2:
                val = vib_data.get('VIB_MOTOR_NONDRIVE', 0)
                color = "red" if val > 4 else "orange" if val > 2 else "green"
                st.markdown(f"""
                <div class="sensor-card sensor-{color}">
                    <div style="font-size: 14px;">МОТОР NON-DRIVE</div>
                    <div style="font-size: 28px; font-weight: bold;">{val:.1f}</div>
                    <div style="font-size: 12px;">mm/s</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_v3:
                val = vib_data.get('VIB_PUMP_INLET', 0)
                color = "red" if val > 4 else "orange" if val > 2 else "green"
                st.markdown(f"""
                <div class="sensor-card sensor-{color}">
                    <div style="font-size: 14px;">НАСОС ВХОД</div>
                    <div style="font-size: 28px; font-weight: bold;">{val:.1f}</div>
                    <div style="font-size: 12px;">mm/s</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_v4:
                val = vib_data.get('VIB_PUMP_OUTLET', 0)
                color = "red" if val > 4 else "orange" if val > 2 else "green"
                st.markdown(f"""
                <div class="sensor-card sensor-{color}">
                    <div style="font-size: 14px;">НАСОС ВЫХОД</div>
                    <div style="font-size: 28px; font-weight: bold;">{val:.1f}</div>
                    <div style="font-size: 12px;">mm/s</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Температура (4 датчика)
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        
        if self.data_manager.temperature_data is not None and len(self.data_manager.temperature_data) > 0:
            temp_data = self.data_manager.temperature_data.iloc[-1].to_dict()
            
            with col_t1:
                val = temp_data.get('TEMP_MOTOR_WINDING', 0)
                color = "red" if val > 85 else "orange" if val > 70 else "green"
                st.markdown(f"""
                <div class="sensor-card sensor-{color}">
                    <div style="font-size: 14px;">МОТОР ОБМОТКА</div>
                    <div style="font-size: 28px; font-weight: bold;">{val:.0f}</div>
                    <div style="font-size: 12px;">°C</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_t2:
                val = temp_data.get('TEMP_MOTOR_BEARING', 0)
                color = "red" if val > 85 else "orange" if val > 70 else "green"
                st.markdown(f"""
                <div class="sensor-card sensor-{color}">
                    <div style="font-size: 14px;">МОТОР ПОДШИП</div>
                    <div style="font-size: 28px; font-weight: bold;">{val:.0f}</div>
                    <div style="font-size: 12px;">°C</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_t3:
                val = temp_data.get('TEMP_PUMP_BEARING', 0)
                color = "red" if val > 85 else "orange" if val > 70 else "green"
                st.markdown(f"""
                <div class="sensor-card sensor-{color}">
                    <div style="font-size: 14px;">НАСОС ПОДШИП</div>
                    <div style="font-size: 28px; font-weight: bold;">{val:.0f}</div>
                    <div style="font-size: 12px;">°C</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_t4:
                val = temp_data.get('TEMP_PUMP_CASING', 0)
                color = "red" if val > 85 else "orange" if val > 70 else "green"
                st.markdown(f"""
                <div class="sensor-card sensor-{color}">
                    <div style="font-size: 14px;">НАСОС КОРПУС</div>
                    <div style="font-size: 28px; font-weight: bold;">{val:.0f}</div>
                    <div style="font-size: 12px;">°C</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Нижний ряд - ШУМ и ДЕМПФЕРЫ
        col_noise, col_dampers = st.columns(2)
        
        with col_noise:
            noise_val = self.data_manager.noise_data.iloc[-1].iloc[0] if not self.data_manager.noise_data.empty else 0
            noise_color = "red" if noise_val > 85 else "orange" if noise_val > 70 else "green"
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 10px 0;">
                <div style="font-size: 18px;">🔊 АКУСТИЧЕСКИЙ ШУМ</div>
                <div style="font-size: 48px; font-weight: bold; color: {noise_color};">{noise_val:.1f} dB</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_dampers:
            st.markdown("""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 10px 0;">
                <div style="font-size: 18px;">🔄 МАГНИТОРЕОЛОГИЧЕСКИЕ ДЕМПФЕРЫ</div>
            </div>
            """, unsafe_allow_html=True)
            
            d1, d2, d3, d4 = st.columns(4)
            force = self.data_manager.damper_forces.get('DAMPER_FL', 0)
            force_color = "red" if force > 4000 else "orange" if force > 1000 else "green"
            
            with d1:
                st.markdown(f"<div style='font-size: 24px; font-weight: bold; color: {force_color};'>{force} N</div><div>FL</div>", unsafe_allow_html=True)
            with d2:
                st.markdown(f"<div style='font-size: 24px; font-weight: bold; color: {force_color};'>{force} N</div><div>FR</div>", unsafe_allow_html=True)
            with d3:
                st.markdown(f"<div style='font-size: 24px; font-weight: bold; color: {force_color};'>{force} N</div><div>RL</div>", unsafe_allow_html=True)
            with d4:
                st.markdown(f"<div style='font-size: 24px; font-weight: bold; color: {force_color};'>{force} N</div><div>RR</div>", unsafe_allow_html=True)
    
    def calculate_risk(self, vibration, temperature, noise):
        """Упрощенный расчет риска"""
        vib_avg = sum(vibration.values()) / len(vibration)
        temp_avg = sum(temperature.values()) / len(temperature)
        
        vib_risk = min(vib_avg / 6.0, 1.0) * 40
        temp_risk = min((temp_avg - 20) / 80, 1.0) * 40
        noise_risk = min((noise - 30) / 70, 1.0) * 20
        
        return int(min(100, vib_risk + temp_risk + noise_risk))
    
    def get_damper_force(self, risk):
        """Сила демпферов по риску"""
        if risk > 80:
            return self.config.DAMPER_FORCES['critical']
        elif risk > 50:
            return self.config.DAMPER_FORCES['warning']
        elif risk > 20:
            return self.config.DAMPER_FORCES['normal']
        return self.config.DAMPER_FORCES['standby']

# Запуск
if __name__ == "__main__":
    interface = OperatorInterface()
    interface.run()
