"""Reusable UI components"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from typing import Dict
from config.constants import AlertLevel, SensorLimits

class UIComponents:
    """Factory for creating reusable UI components"""
    
    @staticmethod
    def metric_card(title: str, value: str, delta: str = None, 
                   help_text: str = None):
        """Create a metric card"""
        with st.container():
            st.metric(title, value, delta, help=help_text)
    
    @staticmethod
    def status_badge(status: str, color: str):
        """Create a status badge"""
        st.markdown(
            f"<span style='background-color: {color}; padding: 5px 10px; "
            f"border-radius: 10px; color: white;'>{status}</span>",
            unsafe_allow_html=True
        )
    
    @staticmethod
    def sensor_status_section(sensors: Dict, values: Dict, title: str):
        """Create a sensor status section"""
        st.markdown(f"**{title}**")
        cols = st.columns(2)
        
        for i, (sensor_id, (sensor_name, limits)) in enumerate(sensors.items()):
            with cols[i % 2]:
                value = values.get(sensor_id, 0)
                level = limits.get_level(value)
                
                icon = {
                    AlertLevel.SUCCESS: "✅",
                    AlertLevel.INFO: "ℹ️",
                    AlertLevel.WARNING: "⚠️",
                    AlertLevel.ERROR: "🔴"
                }.get(level, "ℹ️")
                
                st.markdown(f"{icon} **{sensor_name}:** {value:.1f}")
    
    @staticmethod
    def create_gauge(value: float, title: str, min_val: float = 0, 
                    max_val: float = 100):
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
        fig.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=50, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': "darkblue", 'family': "Arial"}
        )
        return fig
    
    @staticmethod
    def create_trend_chart(data: pd.DataFrame, title: str, height: int = 200):
        """Create a trend line chart"""
        if data.empty:
            return None
        
        fig = go.Figure()
        
        for column in data.columns:
            fig.add_trace(go.Scatter(
                y=data[column],
                name=column,
                mode='lines',
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title=title,
            height=height,
            showlegend=True,
            hovermode='x unified',
            margin=dict(l=10, r=10, t=30, b=10)
        )
        
        return fig
