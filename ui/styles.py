# ui/styles.py
"""Custom CSS styles for the application"""
import streamlit as st

def apply_custom_styles():
    """Apply custom CSS styles"""
    st.markdown("""
    <style>
    /* Main container */
    .main {
        padding: 0rem 1rem;
    }
    
    /* Headers */
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Cards */
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Status badges */
    .status-badge {
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        text-align: center;
    }
    
    .status-critical {
        background: linear-gradient(90deg, #ff416c, #ff4b2b);
        color: white;
    }
    
    .status-warning {
        background: linear-gradient(90deg, #f7971e, #ffd200);
        color: white;
    }
    
    .status-normal {
        background: linear-gradient(90deg, #56ab2f, #a8e063);
        color: white;
    }
    
    .status-standby {
        background: linear-gradient(90deg, #4b6cb7, #182848);
        color: white;
    }
    
    /* Alerts */
    .alert-container {
        border-left: 4px solid;
        padding: 10px;
        margin: 10px 0;
        background: #f8f9fa;
    }
    
    .alert-critical {
        border-left-color: #dc3545;
    }
    
    .alert-warning {
        border-left-color: #ffc107;
    }
    
    .alert-info {
        border-left-color: #17a2b8;
    }
    
    /* Buttons */
    .stButton button {
        border-radius: 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Progress bars */
    .stProgress > div > div {
        background: linear-gradient(90deg, #4b6cb7, #182848);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        background-color: #f0f2f6;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #1e3c72, #2a5298);
        color: white;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: bold;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.9rem;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #f0f2f6;
        border-radius: 5px;
        font-weight: bold;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Dark theme adjustments */
    @media (prefers-color-scheme: dark) {
        .metric-card {
            background: #1e1e1e;
            color: white;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #2d2d2d;
            color: white;
        }
    }
    
    /* Animations */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    /* Tooltips */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 120px;
        background-color: black;
        color: white;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -60px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    </style>
    """, unsafe_allow_html=True)
