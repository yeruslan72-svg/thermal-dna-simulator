# utils/helpers.py
"""Helper utility functions"""
import numpy as np
from typing import List, Union, Optional
from datetime import datetime, timedelta
import hashlib
import json

def format_number(value: float, decimals: int = 2) -> str:
    """Format number with specified decimals"""
    return f"{value:.{decimals}f}"

def calculate_trend(values: List[float]) -> float:
    """Calculate trend percentage from list of values"""
    if len(values) < 2:
        return 0.0
    
    first = values[0]
    last = values[-1]
    
    if first == 0:
        return 0.0
    
    return ((last - first) / first) * 100

def safe_division(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default value"""
    if denominator == 0:
        return default
    return numerator / denominator

def moving_average(data: List[float], window: int = 5) -> List[float]:
    """Calculate moving average"""
    if len(data) < window:
        return data
    
    weights = np.ones(window) / window
    return list(np.convolve(data, weights, mode='valid'))

def detect_outliers_iqr(data: List[float], multiplier: float = 1.5) -> List[bool]:
    """Detect outliers using IQR method"""
    if len(data) < 4:
        return [False] * len(data)
    
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    
    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr
    
    return [(x < lower_bound or x > upper_bound) for x in data]

def time_ago(timestamp: datetime) -> str:
    """Convert datetime to human readable time ago"""
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return f"{diff.seconds} second{'s' if diff.seconds > 1 else ''} ago"

def generate_id(prefix: str = "") -> str:
    """Generate unique ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    hash_obj = hashlib.md5(timestamp.encode())
    unique_id = hash_obj.hexdigest()[:8]
    
    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def dict_to_json(dict_data: dict, pretty: bool = True) -> str:
    """Convert dictionary to JSON string"""
    if pretty:
        return json.dumps(dict_data, indent=2, default=str)
    return json.dumps(dict_data, default=str)

def json_to_dict(json_str: str) -> dict:
    """Convert JSON string to dictionary"""
    try:
        return json.loads(json_str)
    except:
        return {}

def safe_get(data: dict, keys: List[str], default=None):
    """Safely get nested dictionary value"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
            if data is None:
                return default
        else:
            return default
    return data

def round_to_significant(value: float, significant: int = 3) -> float:
    """Round to significant figures"""
    if value == 0:
        return 0
    return round(value, significant - int(np.floor(np.log10(abs(value)))) - 1)

def format_bytes(bytes_num: int) -> str:
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} PB"
