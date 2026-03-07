# utils/helpers.py
"""Helper utility functions for AVCS DNA Industrial Monitor"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Union, Optional, Tuple
import hashlib
import json
import re
from math import isclose

def format_number(value: float, decimals: int = 2, use_commas: bool = False) -> str:
    """
    Format number with specified decimals
    
    Args:
        value: Number to format
        decimals: Number of decimal places
        use_commas: Use commas for thousands
    
    Returns:
        Formatted number string
    """
    if value is None:
        return "N/A"
    
    try:
        if use_commas:
            return f"{value:,.{decimals}f}"
        return f"{value:.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)

def calculate_trend(values: List[float]) -> float:
    """
    Calculate trend percentage from list of values
    
    Args:
        values: List of values
    
    Returns:
        Trend percentage (positive = increasing, negative = decreasing)
    """
    if not values or len(values) < 2:
        return 0.0
    
    first = values[0]
    last = values[-1]
    
    if first == 0:
        return 0.0
    
    return ((last - first) / abs(first)) * 100

def safe_division(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safe division with default value
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if denominator is zero
    
    Returns:
        Division result or default
    """
    if denominator == 0 or denominator is None:
        return default
    
    try:
        return numerator / denominator
    except (ZeroDivisionError, TypeError):
        return default

def moving_average(data: List[float], window: int = 5) -> List[float]:
    """
    Calculate moving average
    
    Args:
        data: Input data list
        window: Window size for averaging
    
    Returns:
        List of moving averages
    """
    if not data or window <= 0:
        return data
    
    if len(data) < window:
        return data
    
    weights = np.ones(window) / window
    return list(np.convolve(data, weights, mode='valid'))

def detect_outliers(data: List[float], method: str = 'iqr', threshold: float = 1.5) -> List[bool]:
    """
    Detect outliers in data
    
    Args:
        data: Input data list
        method: Detection method ('iqr' or 'zscore')
        threshold: Threshold for outlier detection
    
    Returns:
        List of booleans (True = outlier)
    """
    if not data or len(data) < 4:
        return [False] * len(data)
    
    if method == 'iqr':
        # IQR method
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        return [(x < lower_bound or x > upper_bound) for x in data]
    
    elif method == 'zscore':
        # Z-score method
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return [False] * len(data)
        
        z_scores = [(x - mean) / std for x in data]
        return [abs(z) > threshold for z in z_scores]
    
    else:
        return [False] * len(data)

def time_ago(timestamp: datetime) -> str:
    """
    Convert datetime to human readable time ago
    
    Args:
        timestamp: Datetime to convert
    
    Returns:
        Human readable time string
    """
    if not timestamp:
        return "Unknown"
    
    now = datetime.now()
    diff = now - timestamp
    
    seconds = diff.total_seconds()
    
    if seconds < 0:
        return "in the future"
    
    if seconds < 60:
        return f"{int(seconds)} second{'s' if int(seconds) != 1 else ''} ago"
    
    minutes = seconds / 60
    if minutes < 60:
        return f"{int(minutes)} minute{'s' if int(minutes) != 1 else ''} ago"
    
    hours = minutes / 60
    if hours < 24:
        return f"{int(hours)} hour{'s' if int(hours) != 1 else ''} ago"
    
    days = hours / 24
    if days < 30:
        return f"{int(days)} day{'s' if int(days) != 1 else ''} ago"
    
    months = days / 30
    if months < 12:
        return f"{int(months)} month{'s' if int(months) != 1 else ''} ago"
    
    years = days / 365
    return f"{int(years)} year{'s' if int(years) != 1 else ''} ago"

def generate_id(prefix: str = "", length: int = 8) -> str:
    """
    Generate unique ID
    
    Args:
        prefix: Optional prefix for the ID
        length: Length of random part
    
    Returns:
        Unique ID string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    hash_obj = hashlib.md5(timestamp.encode())
    unique_id = hash_obj.hexdigest()[:length]
    
    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks
    
    Args:
        lst: List to split
        chunk_size: Size of each chunk
    
    Returns:
        List of chunks
    """
    if not lst or chunk_size <= 0:
        return [lst]
    
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def dict_to_json(data: Dict, pretty: bool = True, ensure_ascii: bool = False) -> str:
    """
    Convert dictionary to JSON string
    
    Args:
        data: Dictionary to convert
        pretty: Pretty print JSON
        ensure_ascii: Ensure ASCII characters
    
    Returns:
        JSON string
    """
    if pretty:
        return json.dumps(data, indent=2, default=str, ensure_ascii=ensure_ascii)
    return json.dumps(data, default=str, ensure_ascii=ensure_ascii)

def json_to_dict(json_str: str) -> Dict:
    """
    Convert JSON string to dictionary
    
    Args:
        json_str: JSON string
    
    Returns:
        Dictionary
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return {}

def safe_get(data: Dict, keys: List[str], default: Any = None) -> Any:
    """
    Safely get nested dictionary value
    
    Args:
        data: Dictionary to search
        keys: List of keys to traverse
        default: Default value if key not found
    
    Returns:
        Value or default
    """
    current = data
    
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
            if current is None:
                return default
        else:
            return default
    
    return current

def round_to_significant(value: float, significant: int = 3) -> float:
    """
    Round to significant figures
    
    Args:
        value: Value to round
        significant: Number of significant figures
    
    Returns:
        Rounded value
    """
    if value == 0 or not np.isfinite(value):
        return 0
    
    try:
        return round(value, significant - int(np.floor(np.log10(abs(value)))) - 1)
    except (ValueError, OverflowError):
        return value

def format_bytes(bytes_num: int) -> str:
    """
    Format bytes to human readable
    
    Args:
        bytes_num: Number of bytes
    
    Returns:
        Human readable string
    """
    if bytes_num < 0:
        return "N/A"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1024.0
    
    return f"{bytes_num:.1f} PB"

def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email to validate
    
    Returns:
        True if valid
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
    
    Returns:
        Truncated string
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse timestamp string to datetime
    
    Args:
        timestamp_str: Timestamp string
    
    Returns:
        Datetime object or None
    """
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%d/%m/%Y %H:%M:%S',
        '%m/%d/%Y %H:%M:%S'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except (ValueError, TypeError):
            continue
    
    return None

def calculate_percentage(value: float, total: float, default: float = 0.0) -> float:
    """
    Calculate percentage
    
    Args:
        value: Current value
        total: Total value
        default: Default value if total is zero
    
    Returns:
        Percentage
    """
    if total == 0:
        return default
    
    return (value / total) * 100

def normalize_value(value: float, min_val: float, max_val: float) -> float:
    """
    Normalize value to [0, 1] range
    
    Args:
        value: Value to normalize
        min_val: Minimum value
        max_val: Maximum value
    
    Returns:
        Normalized value
    """
    if max_val - min_val == 0:
        return 0.5
    
    return (value - min_val) / (max_val - min_val)

def denormalize_value(normalized: float, min_val: float, max_val: float) -> float:
    """
    Denormalize value from [0, 1] range
    
    Args:
        normalized: Normalized value
        min_val: Minimum value
        max_val: Maximum value
    
    Returns:
        Denormalized value
    """
    return min_val + normalized * (max_val - min_val)

def calculate_statistics(data: List[float]) -> Dict[str, float]:
    """
    Calculate statistics for data
    
    Args:
        data: List of values
    
    Returns:
        Dictionary with statistics
    """
    if not data:
        return {
            'mean': 0,
            'median': 0,
            'std': 0,
            'min': 0,
            'max': 0,
            'q1': 0,
            'q3': 0,
            'range': 0
        }
    
    data_array = np.array(data)
    
    return {
        'mean': float(np.mean(data_array)),
        'median': float(np.median(data_array)),
        'std': float(np.std(data_array)),
        'min': float(np.min(data_array)),
        'max': float(np.max(data_array)),
        'q1': float(np.percentile(data_array, 25)),
        'q3': float(np.percentile(data_array, 75)),
        'range': float(np.max(data_array) - np.min(data_array))
    }

def remove_outliers(data: List[float], method: str = 'iqr', threshold: float = 1.5) -> List[float]:
    """
    Remove outliers from data
    
    Args:
        data: Input data
        method: Detection method
        threshold: Threshold
    
    Returns:
        Data without outliers
    """
    outliers = detect_outliers(data, method, threshold)
    return [x for x, is_outlier in zip(data, outliers) if not is_outlier]

def smooth_data(data: List[float], window: int = 3, method: str = 'moving_average') -> List[float]:
    """
    Smooth data using various methods
    
    Args:
        data: Input data
        window: Smoothing window
        method: Smoothing method ('moving_average', 'exponential', 'gaussian')
    
    Returns:
        Smoothed data
    """
    if not data or len(data) < window:
        return data
    
    if method == 'moving_average':
        return moving_average(data, window)
    
    elif method == 'exponential':
        # Exponential smoothing
        alpha = 2 / (window + 1)
        result = [data[0]]
        for i in range(1, len(data)):
            result.append(alpha * data[i] + (1 - alpha) * result[-1])
        return result
    
    elif method == 'gaussian':
        # Gaussian smoothing
        from scipy.ndimage import gaussian_filter1d
        try:
            return list(gaussian_filter1d(data, sigma=window/3))
        except ImportError:
            return moving_average(data, window)
    
    return data

def find_peaks(data: List[float], threshold: float = 0) -> List[int]:
    """
    Find peaks in data
    
    Args:
        data: Input data
        threshold: Minimum peak height
    
    Returns:
        List of peak indices
    """
    if len(data) < 3:
        return []
    
    peaks = []
    for i in range(1, len(data) - 1):
        if data[i] > data[i-1] and data[i] > data[i+1] and data[i] > threshold:
            peaks.append(i)
    
    return peaks

def calculate_correlation(data1: List[float], data2: List[float]) -> float:
    """
    Calculate correlation between two datasets
    
    Args:
        data1: First dataset
        data2: Second dataset
    
    Returns:
        Correlation coefficient
    """
    if len(data1) != len(data2) or len(data1) < 2:
        return 0.0
    
    try:
        return float(np.corrcoef(data1, data2)[0, 1])
    except (ValueError, IndexError):
        return 0.0

def create_time_windows(data: List[Any], window_size: int, step: int = 1) -> List[List[Any]]:
    """
    Create sliding windows from data
    
    Args:
        data: Input data
        window_size: Size of each window
        step: Step size between windows
    
    Returns:
        List of windows
    """
    if len(data) < window_size:
        return [data]
    
    windows = []
    for i in range(0, len(data) - window_size + 1, step):
        windows.append(data[i:i + window_size])
    
    return windows

def is_number(value: Any) -> bool:
    """
    Check if value is a number
    
    Args:
        value: Value to check
    
    Returns:
        True if value is number
    """
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False

def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp value between min and max
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
    
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))

def lerp(a: float, b: float, t: float) -> float:
    """
    Linear interpolation
    
    Args:
        a: Start value
        b: End value
        t: Interpolation factor [0, 1]
    
    Returns:
        Interpolated value
    """
    return a + (b - a) * clamp(t, 0, 1)

def map_range(value: float, from_min: float, from_max: float, 
              to_min: float, to_max: float) -> float:
    """
    Map value from one range to another
    
    Args:
        value: Value to map
        from_min: Source range minimum
        from_max: Source range maximum
        to_min: Target range minimum
        to_max: Target range maximum
    
    Returns:
        Mapped value
    """
    normalized = (value - from_min) / (from_max - from_min)
    return to_min + normalized * (to_max - to_min)

# Decorator for caching function results
def memoize(func):
    """Decorator to cache function results"""
    cache = {}
    
    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    
    return wrapper

# Context manager for timing code execution
class Timer:
    """Context manager for timing code execution"""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        print(f"{self.name} took {duration:.3f} seconds")
    
    @property
    def duration(self) -> float:
        """Get duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
