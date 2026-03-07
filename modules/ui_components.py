# modules/ui_components.py
"""Reusable UI components for AVCS DNA Industrial Monitor"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from modules.config import AlertLevel, SensorLimits, industrial_config

class UIComponents:
    """Factory for creating reusable UI components"""
    
    @staticmethod
    def metric_card(title: str, value: str, delta: str = None, 
                   help_text: str = None, color: str = None):
        """Create a metric card"""
        with st.container():
            if color:
                st.markdown(f"""
                <div style="background: {color}; padding: 10px; border-radius: 10px;">
                    <h3 style="color: white; margin: 0;">{value}</h3>
                    <p style="color: white; margin: 0;">{title}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.metric(title, value, delta, help=help_text)
    
    @staticmethod
    def status_badge(status: str, color: str, size: str = "medium"):
        """Create a status badge"""
        font_sizes = {"small": "12px", "medium": "16px", "large": "20px"}
        font_size = font_sizes.get(size, "16px")
        
        st.markdown(
            f"""
            <div style="
                background-color: {color}; 
                color: white; 
                padding: 5px 15px; 
                border-radius: 20px; 
                display: inline-block;
                font-size: {font_size};
                font-weight: bold;
                text-align: center;
            ">
                {status}
            </div>
            """,
            unsafe_allow_html=True
        )
    
    @staticmethod
    def sensor_status_section(sensors: Dict, values: Dict, title: str):
        """Create a sensor status section"""
        if title:
            st.markdown(f"**{title}**")
        
        # Create grid layout
        cols = st.columns(2)
        
        for i, (sensor_id, (sensor_name, limits)) in enumerate(sensors.items()):
            with cols[i % 2]:
                value = values.get(sensor_id, 0)
                level = limits.get_level(value)
                percentage = limits.get_percentage(value)
                
                # Choose icon and color
                if level == AlertLevel.SUCCESS:
                    icon = "✅"
                    color = "green"
                elif level == AlertLevel.INFO:
                    icon = "ℹ️"
                    color = "blue"
                elif level == AlertLevel.WARNING:
                    icon = "⚠️"
                    color = "orange"
                else:
                    icon = "🔴"
                    color = "red"
                
                # Create sensor card
                st.markdown(f"""
                <div style="
                    background: #f0f2f6; 
                    padding: 10px; 
                    border-radius: 5px; 
                    margin: 5px 0;
                    border-left: 5px solid {color};
                ">
                    <div style="display: flex; justify-content: space-between;">
                        <span>{icon} <strong>{sensor_name}</strong></span>
                        <span style="color: {color}; font-weight: bold;">{value:.1f}</span>
                    </div>
                    <div style="
                        background: #ddd; 
                        height: 5px; 
                        border-radius: 5px; 
                        margin-top: 5px;
                    ">
                        <div style="
                            background: {color}; 
                            width: {percentage}%; 
                            height: 5px; 
                            border-radius: 5px;
                        "></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    @staticmethod
    def create_gauge(value: float, title: str, min_val: float = 0, 
                    max_val: float = 100, height: int = 200):
        """Create a gauge chart"""
        # Determine color based on value
        if value > 80:
            color = "red"
        elif value > 50:
            color = "orange"
        else:
            color = "green"
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            title={'text': title, 'font': {'size': 14}},
            number={'font': {'size': 24, 'color': color}},
            gauge={
                'axis': {
                    'range': [min_val, max_val],
                    'tickwidth': 1,
                    'tickcolor': "darkblue"
                },
                'bar': {'color': color, 'thickness': 0.3},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [min_val, 50], 'color': '#90EE90'},
                    {'range': [50, 80], 'color': '#FFD700'},
                    {'range': [80, max_val], 'color': '#FF6B6B'}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': value
                }
            }
        ))
        
        fig.update_layout(
            height=height,
            margin=dict(l=10, r=10, t=50, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': "darkblue", 'family': "Arial"}
        )
        
        return fig
    
    @staticmethod
    def create_trend_chart(data: pd.DataFrame, title: str = None, 
                          height: int = 200, show_legend: bool = True):
        """Create a trend line chart"""
        if data.empty:
            return None
        
        fig = go.Figure()
        
        for column in data.columns:
            fig.add_trace(go.Scatter(
                y=data[column],
                name=column,
                mode='lines',
                line=dict(width=2),
                hovertemplate=f'{column}: %{{y:.1f}}<br>Point: %{{x}}<extra></extra>'
            ))
        
        fig.update_layout(
            title=title,
            height=height,
            showlegend=show_legend,
            hovermode='x unified',
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                title="Time"
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='lightgray'
            )
        )
        
        return fig
    
    @staticmethod
    def create_bar_chart(data: Dict, title: str = None, height: int = 200):
        """Create a bar chart"""
        fig = go.Figure(data=[
            go.Bar(
                x=list(data.keys()),
                y=list(data.values()),
                marker_color=['green' if v < 50 else 'orange' if v < 80 else 'red' 
                            for v in data.values()]
            )
        ])
        
        fig.update_layout(
            title=title,
            height=height,
            showlegend=False,
            margin=dict(l=10, r=10, t=30, b=10)
        )
        
        return fig
    
    @staticmethod
    def create_heatmap(data: pd.DataFrame, title: str = None, height: int = 400):
        """Create a heatmap"""
        if data.empty:
            return None
        
        fig = go.Figure(data=go.Heatmap(
            z=data.values,
            x=data.columns,
            y=data.index,
            colorscale='RdBu',
            zmid=0,
            text=np.round(data.values, 2),
            texttemplate='%{text}',
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title=title,
            height=height,
            margin=dict(l=10, r=10, t=30, b=10)
        )
        
        return fig
    
    @staticmethod
    def create_pie_chart(data: Dict, title: str = None, height: int = 300):
        """Create a pie chart"""
        fig = go.Figure(data=[go.Pie(
            labels=list(data.keys()),
            values=list(data.values()),
            hole=0.3,
            marker=dict(colors=px.colors.qualitative.Set3)
        )])
        
        fig.update_layout(
            title=title,
            height=height,
            margin=dict(l=10, r=10, t=30, b=10)
        )
        
        return fig
    
    @staticmethod
    def info_box(message: str, level: str = "info"):
        """Create an info box"""
        colors = {
            "info": {"bg": "#e7f3ff", "border": "#2196F3", "icon": "ℹ️"},
            "success": {"bg": "#d4edda", "border": "#28a745", "icon": "✅"},
            "warning": {"bg": "#fff3cd", "border": "#ffc107", "icon": "⚠️"},
            "error": {"bg": "#f8d7da", "border": "#dc3545", "icon": "❌"}
        }
        
        color = colors.get(level, colors["info"])
        
        st.markdown(f"""
        <div style="
            background-color: {color['bg']};
            border-left: 5px solid {color['border']};
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        ">
            <strong>{color['icon']} {message}</strong>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def create_progress_card(title: str, value: float, max_value: float, 
                            color: str = None):
        """Create a progress card"""
        percentage = (value / max_value) * 100
        
        if not color:
            if percentage > 80:
                color = "red"
            elif percentage > 50:
                color = "orange"
            else:
                color = "green"
        
        st.markdown(f"""
        <div style="
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 10px 0;
        ">
            <div style="display: flex; justify-content: space-between;">
                <span>{title}</span>
                <span style="font-weight: bold;">{value:.1f}/{max_value:.1f}</span>
            </div>
            <div style="
                background: #ddd;
                height: 10px;
                border-radius: 5px;
                margin-top: 10px;
            ">
                <div style="
                    background: {color};
                    width: {percentage}%;
                    height: 10px;
                    border-radius: 5px;
                "></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def create_timestamp():
        """Create a timestamp display"""
        now = datetime.now()
        st.markdown(f"""
        <div style="
            text-align: right;
            color: #666;
            font-size: 12px;
            padding: 5px;
        ">
            Last updated: {now.strftime('%Y-%m-%d %H:%M:%S')}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def create_button_grid(buttons: List[Dict], cols: int = 3):
        """Create a grid of buttons"""
        for i in range(0, len(buttons), cols):
            row_buttons = buttons[i:i+cols]
            cols_ui = st.columns(len(row_buttons))
            
            for col, button in zip(cols_ui, row_buttons):
                with col:
                    if st.button(
                        button.get('label', 'Button'),
                        key=button.get('key', f"btn_{i}"),
                        type=button.get('type', 'secondary'),
                        use_container_width=True
                    ):
                        if 'callback' in button:
                            button['callback']()

# Create singleton instance
ui_components = UIComponents()
