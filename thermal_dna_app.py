# thermal_dna_app.py - AVCS DNA Industrial Monitor v5.2
import streamlit as st
import numpy as np
import pandas as pd
import time
from sklearn.ensemble import IsolationForest
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="AVCS DNA Industrial Monitor", layout="wide")

# --- SYSTEM CONFIG ---
class IndustrialConfig:
    VIBRATION_SENSORS = {
        'VIB_MOTOR_DRIVE': 'Motor Drive End',
        'VIB_MOTOR_NONDRIVE': 'Motor Non-Drive End',
        'VIB_PUMP_INLET': 'Pump Inlet Bearing',
        'VIB_PUMP_OUTLET': 'Pump Outlet Bearing'
    }

    THERMAL_SENSORS = {
        'TEMP_MOTOR_WINDING': 'Motor Winding',
        'TEMP_MOTOR_BEARING': 'Motor Bearing',
        'TEMP_PUMP_BEARING': 'Pump Bearing',
        'TEMP_PUMP_CASING': 'Pump Casing'
    }

    MR_DAMPERS = {
        'DAMPER_FL': 'Front-Left (LORD RD-8040)',
        'DAMPER_FR': 'Front-Right (LORD RD-8040)',
        'DAMPER_RL': 'Rear-Left (LORD RD-8040)',
        'DAMPER_RR': 'Rear-Right (LORD RD-8040)'
    }

    ACOUSTIC_SENSOR = "Pump Acoustic Noise (dB)"

    VIBRATION_LIMITS = {'normal': 2.0, 'warning': 4.0, 'critical': 6.0}
    TEMPERATURE_LIMITS = {'normal': 70, 'warning': 85, 'critical': 100}
    NOISE_LIMITS = {'normal': 70, 'warning': 85, 'critical': 100}
    DAMPER_FORCES = {'standby': 500, 'normal': 1000, 'warning': 4000, 'critical': 8000}


# --- HEADER ---
st.title("🏭 AVCS DNA - Industrial Monitoring System v5.2")
st.markdown("**Active Vibration Control System with AI-Powered Predictive Maintenance**")

# --- STATE INIT ---
if "system_running" not in st.session_state:
    st.session_state.system_running = False
if "vibration_data" not in st.session_state:
    st.session_state.vibration_data = pd.DataFrame(columns=list(IndustrialConfig.VIBRATION_SENSORS.keys()))
if "temperature_data" not in st.session_state:
    st.session_state.temperature_data = pd.DataFrame(columns=list(IndustrialConfig.THERMAL_SENSORS.keys()))
if "noise_data" not in st.session_state:
    st.session_state.noise_data = pd.DataFrame(columns=[IndustrialConfig.ACOUSTIC_SENSOR])
if "damper_forces" not in st.session_state:
    st.session_state.damper_forces = {damper: 0 for damper in IndustrialConfig.MR_DAMPERS.keys()}
if "damper_history" not in st.session_state:
    st.session_state.damper_history = pd.DataFrame(columns=list(IndustrialConfig.MR_DAMPERS.keys()))
if "risk_history" not in st.session_state:
    st.session_state.risk_history = []
if "ai_model" not in st.session_state:
    normal_vibration = np.random.normal(1.0, 0.3, (500, 4))
    normal_temperature = np.random.normal(65, 5, (500, 4))
    normal_noise = np.random.normal(65, 3, (500, 1))
    normal_data = np.column_stack([normal_vibration, normal_temperature, normal_noise])
    st.session_state.ai_model = IsolationForest(contamination=0.08, random_state=42, n_estimators=150)
    st.session_state.ai_model.fit(normal_data)

# --- SIDEBAR CONTROL ---
st.sidebar.header("🎛️ AVCS DNA Control Panel")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("⚡ Start System", type="primary", use_container_width=True):
        st.session_state.system_running = True
        st.session_state.vibration_data = pd.DataFrame(columns=list(IndustrialConfig.VIBRATION_SENSORS.keys()))
        st.session_state.temperature_data = pd.DataFrame(columns=list(IndustrialConfig.THERMAL_SENSORS.keys()))
        st.session_state.noise_data = pd.DataFrame(columns=[IndustrialConfig.ACOUSTIC_SENSOR])
        st.session_state.damper_forces = {damper: IndustrialConfig.DAMPER_FORCES['standby'] for damper in IndustrialConfig.MR_DAMPERS.keys()}
        st.session_state.damper_history = pd.DataFrame(columns=list(IndustrialConfig.MR_DAMPERS.keys()))
        st.session_state.risk_history = []
        st.rerun()
with col2:
    if st.button("🛑 Emergency Stop", use_container_width=True):
        st.session_state.system_running = False
        st.session_state.damper_forces = {damper: 0 for damper in IndustrialConfig.MR_DAMPERS.keys()}
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📊 System Status")
status_indicator = st.sidebar.empty()

# System Architecture
st.sidebar.markdown("---")
st.sidebar.subheader("🏭 System Architecture")
st.sidebar.write("• 4x Vibration Sensors (PCB 603C01)")
st.sidebar.write("• 4x Thermal Sensors (FLIR A500f)") 
st.sidebar.write("• 1x Acoustic Sensor (NI 9234)")
st.sidebar.write("• 4x MR Dampers (LORD RD-8040)")
st.sidebar.write("• AI: Isolation Forest + Fusion Logic")

# Business Case
st.sidebar.markdown("---")
st.sidebar.subheader("💰 Business Case")
st.sidebar.metric("System Cost", "$250,000")
st.sidebar.metric("Typical ROI", ">2000%")
st.sidebar.metric("Payback Period", "<3 months")

# --- MAIN DISPLAY AREA ---
if not st.session_state.system_running:
    st.info("🚀 System is ready. Click 'Start System' to begin monitoring.")
else:
    # --- DASHBOARD LAYOUT ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Vibration Monitoring")
        vib_chart = st.empty()
        vib_status = st.empty()

        st.subheader("🌡️ Thermal Monitoring")
        temp_chart = st.empty()
        temp_status = st.empty()

    with col2:
        st.subheader("🔊 Acoustic Monitoring")
        noise_chart = st.empty()
        noise_status = st.empty()

        st.subheader("🔄 MR Dampers Control")
        damper_chart = st.empty()
        damper_status_display = st.empty()

    st.markdown("---")
    
    # AI Fusion Analysis Section
    st.subheader("🤖 AI Fusion Analysis")
    fusion_col1, fusion_col2, fusion_col3, fusion_col4 = st.columns([2, 1, 1, 1])
    
    # Initialize placeholders for AI section
    fusion_chart_ph = fusion_col1.empty()
    gauge_ph = fusion_col2.empty()
    ai_conf_ph = fusion_col3.empty()
    rul_ph = fusion_col4.empty()

    # --- SIMULATION LOOP ---
    progress_bar = st.sidebar.progress(0)
    cycle_counter = st.sidebar.empty()
    
    max_cycles = 100
    current_cycle = 0
    
    while current_cycle < max_cycles and st.session_state.system_running:
        # --- DATA GENERATION ---
        if current_cycle < 30:
            # Normal operation
            vibration = {k: max(0.1, 1.0 + np.random.normal(0, 0.2)) for k in IndustrialConfig.VIBRATION_SENSORS.keys()}
            temperature = {k: max(20, 65 + np.random.normal(0, 3)) for k in IndustrialConfig.THERMAL_SENSORS.keys()}
            noise = max(30, 65 + np.random.normal(0, 2))
        elif current_cycle < 60:
            # Gradual degradation
            degradation = (current_cycle - 30) * 0.05
            vibration = {k: max(0.1, 1.0 + degradation + np.random.normal(0, 0.3)) for k in IndustrialConfig.VIBRATION_SENSORS.keys()}
            temperature = {k: max(20, 65 + degradation * 2 + np.random.normal(0, 4)) for k in IndustrialConfig.THERMAL_SENSORS.keys()}
            noise = max(30, 70 + degradation * 2 + np.random.normal(0, 3))
        else:
            # Critical condition
            vibration = {k: max(0.1, 5.0 + np.random.normal(0, 0.5)) for k in IndustrialConfig.VIBRATION_SENSORS.keys()}
            temperature = {k: max(20, 95 + np.random.normal(0, 5)) for k in IndustrialConfig.THERMAL_SENSORS.keys()}
            noise = max(30, 95 + np.random.normal(0, 5))

        # Save data
        st.session_state.vibration_data.loc[current_cycle] = vibration
        st.session_state.temperature_data.loc[current_cycle] = temperature
        st.session_state.noise_data.loc[current_cycle] = [noise]

        # AI Analysis
        features = list(vibration.values()) + list(temperature.values()) + [noise]
        ai_prediction = st.session_state.ai_model.predict([features])[0]
        ai_conf = st.session_state.ai_model.decision_function([features])[0]
        risk_index = min(100, max(0, int(abs(ai_conf) * 120)))

        # Remaining Useful Life (RUL)
        rul_hours = max(0, int(100 - risk_index * 0.9))

        # Save risk history for chart
        st.session_state.risk_history.append(risk_index)

        # Damper control logic
        if ai_prediction == -1 or risk_index > 80:
            damper_force = IndustrialConfig.DAMPER_FORCES['critical']
            system_status = "🚨 CRITICAL"
            status_color = "red"
        elif risk_index > 50:
            damper_force = IndustrialConfig.DAMPER_FORCES['warning']
            system_status = "⚠️ WARNING"
            status_color = "orange"
        elif risk_index > 20:
            damper_force = IndustrialConfig.DAMPER_FORCES['normal']
            system_status = "✅ NORMAL"
            status_color = "green"
        else:
            damper_force = IndustrialConfig.DAMPER_FORCES['standby']
            system_status = "🟢 STANDBY"
            status_color = "blue"

        st.session_state.damper_forces = {d: damper_force for d in IndustrialConfig.MR_DAMPERS.keys()}
        st.session_state.damper_history.loc[current_cycle] = st.session_state.damper_forces

        # --- UPDATE DISPLAYS ---
        
        # Vibration Monitoring
        vib_chart.line_chart(st.session_state.vibration_data, height=200)
        with vib_status.container():
            for k, v in vibration.items():
                color = "🟢" if v < 2 else "🟡" if v < 4 else "🔴"
                st.write(f"{color} {IndustrialConfig.VIBRATION_SENSORS[k]}: {v:.1f} mm/s")

        # Temperature Monitoring
        temp_chart.line_chart(st.session_state.temperature_data, height=200)
        with temp_status.container():
            for k, v in temperature.items():
                color = "🟢" if v < 70 else "🟡" if v < 85 else "🔴"
                st.write(f"{color} {IndustrialConfig.THERMAL_SENSORS[k]}: {v:.0f} °C")

        # Noise Monitoring
        noise_chart.line_chart(st.session_state.noise_data, height=200)
        with noise_status.container():
            color = "🟢" if noise < 70 else "🟡" if noise < 85 else "🔴"
            st.write(f"{color} Noise Level: {noise:.1f} dB")

        # Dampers Display
        damper_chart.line_chart(st.session_state.damper_history, height=200)
        with damper_status_display.container():
            cols = st.columns(4)
            for i, (d, loc) in enumerate(IndustrialConfig.MR_DAMPERS.items()):
                with cols[i]:
                    force = st.session_state.damper_forces[d]
                    if force >= 4000:
                        st.error(f"🔴 {loc}\n{force} N")
                    elif force >= 1000:
                        st.warning(f"🟡 {loc}\n{force} N")
                    else:
                        st.success(f"🟢 {loc}\n{force} N")

        # AI Fusion Analysis - UPDATED WITH PROPER PLACEHOLDERS
        with fusion_chart_ph.container():
            if len(st.session_state.risk_history) > 0:
                risk_df = pd.DataFrame({
                    'Risk Index': st.session_state.risk_history,
                    'Critical Threshold': [80] * len(st.session_state.risk_history),
                    'Warning Threshold': [50] * len(st.session_state.risk_history)
                })
                st.line_chart(risk_df, height=200)

        with gauge_ph.container():
            gauge_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=risk_index,
                title={'text': "Risk Index"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "green"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': risk_index
                    }
                }
            ))
            gauge_fig.update_layout(height=250)
            st.plotly_chart(gauge_fig, use_container_width=True, key=f"gauge_{current_cycle}")

        with ai_conf_ph.container():
            st.metric("🤖 AI Confidence", f"{abs(ai_conf):.2f}")

        with rul_ph.container():
            if rul_hours < 24:
                st.error(f"⏳ RUL\n{rul_hours} h")
            elif rul_hours < 72:
                st.warning(f"⏳ RUL\n{rul_hours} h")
            else:
                st.success(f"⏳ RUL\n{rul_hours} h")

        # Update status
        status_indicator.markdown(f"<h3 style='color: {status_color};'>{system_status}</h3>", unsafe_allow_html=True)

        # Update progress
        progress_bar.progress((current_cycle + 1) / max_cycles)
        cycle_counter.text(f"🔄 Cycle: {current_cycle+1}/{max_cycles}")

        current_cycle += 1
        time.sleep(0.5)

    # Simulation complete
    if current_cycle >= max_cycles:
        st.success("✅ Simulation completed successfully!")
        st.session_state.system_running = False

st.markdown("---")
st.caption("AVCS DNA Industrial Monitor v5.2 | Yeruslan Technologies | Predictive Maintenance System")
