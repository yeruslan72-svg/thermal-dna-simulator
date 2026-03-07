# utils/__init__.py
"""Utilities package for AVCS DNA Industrial Monitor"""

from .logger import logger, setup_logger
from .helpers import (
    format_number,
    calculate_trend,
    safe_division,
    moving_average,
    detect_outliers,
    time_ago,
    generate_id,
    chunk_list,
    dict_to_json,
    json_to_dict,
    safe_get,
    round_to_significant,
    format_bytes,
    validate_email,
    truncate_string,
    parse_timestamp,
    calculate_percentage,
    normalize_value,
    denormalize_value,
    calculate_statistics,
    remove_outliers,
    smooth_data,
    find_peaks,
    calculate_correlation,
    create_time_windows
)

__all__ = [
    # Logger
    'logger',
    'setup_logger',
    
    # Helpers
    'format_number',
    'calculate_trend',
    'safe_division',
    'moving_average',
    'detect_outliers',
    'time_ago',
    'generate_id',
    'chunk_list',
    'dict_to_json',
    'json_to_dict',
    'safe_get',
    'round_to_significant',
    'format_bytes',
    'validate_email',
    'truncate_string',
    'parse_timestamp',
    'calculate_percentage',
    'normalize_value',
    'denormalize_value',
    'calculate_statistics',
    'remove_outliers',
    'smooth_data',
    'find_peaks',
    'calculate_correlation',
    'create_time_windows'
]
