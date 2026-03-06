"""Configuration settings for the application"""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings"""
    
    # App settings
    APP_NAME = "AVCS DNA Industrial Monitor"
    APP_VERSION = "6.0.0"
    APP_ICON = "🏭"
    
    # Simulation settings
    SIMULATION_CYCLES = int(os.getenv("SIMULATION_CYCLES", 100))
    UPDATE_INTERVAL = float(os.getenv("UPDATE_INTERVAL", 0.5))
    MAX_HISTORY_POINTS = int(os.getenv("MAX_HISTORY_POINTS", 1000))
    
    # Database settings (optional)
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/readings.db")
    
    # Alert settings
    ENABLE_EMAIL_ALERTS = os.getenv("ENABLE_EMAIL_ALERTS", "False").lower() == "true"
    ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

settings = Settings()
