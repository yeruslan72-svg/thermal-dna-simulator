# core/alert_system.py
"""Alert management and notification system"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from threading import Lock, Timer
import json
import os
from enum import Enum
import streamlit as st

from config.constants import AlertLevel, IndustrialConfig
from config.settings import settings
from utils.logger import logger

class AlertChannel(Enum):
    """Available alert notification channels"""
    UI = "ui"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    LOG = "log"

class AlertRule:
    """Alert rule definition"""
    
    def __init__(self, 
                 name: str,
                 condition: Callable,
                 level: AlertLevel,
                 message_template: str,
                 channels: List[AlertChannel],
                 cooldown_seconds: int = 300):
        """
        Initialize alert rule
        
        Args:
            name: Rule name
            condition: Function that returns True when alert should trigger
            level: Alert severity level
            message_template: Template for alert message
            channels: List of notification channels
            cooldown_seconds: Minimum time between identical alerts
        """
        self.name = name
        self.condition = condition
        self.level = level
        self.message_template = message_template
        self.channels = channels
        self.cooldown_seconds = cooldown_seconds
        self.last_triggered = None

class Alert:
    """Alert data structure"""
    
    def __init__(self, 
                 rule_name: str,
                 level: AlertLevel,
                 message: str,
                 data: Dict = None):
        self.id = f"{rule_name}_{datetime.now().timestamp()}"
        self.rule_name = rule_name
        self.level = level
        self.message = message
        self.data = data or {}
        self.timestamp = datetime.now()
        self.acknowledged = False
        self.resolved = False
        self.resolved_at = None

class AlertSystem:
    """Comprehensive alert management system"""
    
    def __init__(self):
        self.lock = Lock()
        self.alerts: List[Alert] = []
        self.rules: List[AlertRule] = []
        self.channel_handlers = {}
        self.alert_callbacks = []
        self.max_alerts = 1000
        self.alert_history_file = "data/alert_history.json"
        
        # Initialize default channel handlers
        self._init_channel_handlers()
        
        # Initialize default rules
        self._init_default_rules()
        
        # Load alert history
        self._load_history()
        
        logger.info("Alert system initialized with {} rules".format(len(self.rules)))
    
    def _init_channel_handlers(self):
        """Initialize notification channel handlers"""
        self.channel_handlers = {
            AlertChannel.UI: self._send_ui_alert,
            AlertChannel.EMAIL: self._send_email_alert,
            AlertChannel.SMS: self._send_sms_alert,
            AlertChannel.WEBHOOK: self._send_webhook_alert,
            AlertChannel.LOG: self._send_log_alert
        }
    
    def _init_default_rules(self):
        """Initialize default alert rules"""
        
        # Critical vibration rule
        self.add_rule(AlertRule(
            name="critical_vibration",
            condition=lambda data: any(
                v > IndustrialConfig.VIBRATION_SENSORS[s][2].critical 
                for s, v in data.get('vibration', {}).items()
            ),
            level=AlertLevel.CRITICAL,
            message_template="Critical vibration detected: {sensor} = {value:.1f} mm/s",
            channels=[AlertChannel.UI, AlertChannel.EMAIL, AlertChannel.LOG],
            cooldown_seconds=60
        ))
        
        # High temperature rule
        self.add_rule(AlertRule(
            name="high_temperature",
            condition=lambda data: any(
                t > IndustrialConfig.THERMAL_SENSORS[s][2].warning 
                for s, t in data.get('temperature', {}).items()
            ),
            level=AlertLevel.WARNING,
            message_template="High temperature detected: {sensor} = {value:.0f}°C",
            channels=[AlertChannel.UI, AlertChannel.LOG],
            cooldown_seconds=120
        ))
        
        # Critical temperature rule
        self.add_rule(AlertRule(
            name="critical_temperature",
            condition=lambda data: any(
                t > IndustrialConfig.THERMAL_SENSORS[s][2].critical 
                for s, t in data.get('temperature', {}).items()
            ),
            level=AlertLevel.CRITICAL,
            message_template="Critical temperature detected: {sensor} = {value:.0f}°C",
            channels=[AlertChannel.UI, AlertChannel.EMAIL, AlertChannel.LOG],
            cooldown_seconds=60
        ))
        
        # High noise rule
        self.add_rule(AlertRule(
            name="high_noise",
            condition=lambda data: data.get('noise', 0) > IndustrialConfig.ACOUSTIC_SENSOR[1].warning,
            level=AlertLevel.WARNING,
            message_template="High noise level: {noise:.1f} dB",
            channels=[AlertChannel.UI, AlertChannel.LOG],
            cooldown_seconds=120
        ))
        
        # Critical noise rule
        self.add_rule(AlertRule(
            name="critical_noise",
            condition=lambda data: data.get('noise', 0) > IndustrialConfig.ACOUSTIC_SENSOR[1].critical,
            level=AlertLevel.CRITICAL,
            message_template="Critical noise level: {noise:.1f} dB",
            channels=[AlertChannel.UI, AlertChannel.EMAIL, AlertChannel.LOG],
            cooldown_seconds=60
        ))
        
        # High risk rule
        self.add_rule(AlertRule(
            name="high_risk",
            condition=lambda data: data.get('risk_index', 0) > 80,
            level=AlertLevel.CRITICAL,
            message_template="Critical risk level: {risk_index}% - Immediate action required",
            channels=[AlertChannel.UI, AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.LOG],
            cooldown_seconds=30
        ))
        
        # Elevated risk rule
        self.add_rule(AlertRule(
            name="elevated_risk",
            condition=lambda data: data.get('risk_index', 0) > 50,
            level=AlertLevel.WARNING,
            message_template="Elevated risk level: {risk_index}% - Schedule maintenance",
            channels=[AlertChannel.UI, AlertChannel.LOG],
            cooldown_seconds=180
        ))
        
        # AI anomaly rule
        self.add_rule(AlertRule(
            name="ai_anomaly",
            condition=lambda data: data.get('ai_prediction', 1) == -1,
            level=AlertLevel.WARNING,
            message_template="AI detected anomalous pattern (confidence: {ai_confidence:.2f})",
            channels=[AlertChannel.UI, AlertChannel.LOG],
            cooldown_seconds=300
        ))
        
        # System error rule
        self.add_rule(AlertRule(
            name="system_error",
            condition=lambda data: data.get('error_count', 0) > 3,
            level=AlertLevel.ERROR,
            message_template="System errors detected: {error_count} errors in last minute",
            channels=[AlertChannel.UI, AlertChannel.EMAIL, AlertChannel.LOG],
            cooldown_seconds=60
        ))
        
        # Maintenance due rule
        self.add_rule(AlertRule(
            name="maintenance_due",
            condition=lambda data: data.get('rul_hours', 100) < 24,
            level=AlertLevel.WARNING,
            message_template="Maintenance required: {rul_hours} hours remaining",
            channels=[AlertChannel.UI, AlertChannel.EMAIL, AlertChannel.LOG],
            cooldown_seconds=3600  # 1 hour
        ))
    
    def add_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        with self.lock:
            self.rules.append(rule)
            logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """Remove an alert rule"""
        with self.lock:
            self.rules = [r for r in self.rules if r.name != rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
    
    def check_alerts(self, data: Dict) -> List[Alert]:
        """Check all rules against current data"""
        triggered_alerts = []
        
        with self.lock:
            for rule in self.rules:
                try:
                    # Check cooldown
                    if rule.last_triggered:
                        time_since = (datetime.now() - rule.last_triggered).total_seconds()
                        if time_since < rule.cooldown_seconds:
                            continue
                    
                    # Check condition
                    if rule.condition(data):
                        # Create alert
                        message = self._format_message(rule.message_template, data)
                        alert = Alert(rule.name, rule.level, message, data)
                        
                        # Send through channels
                        for channel in rule.channels:
                            if channel in self.channel_handlers:
                                self.channel_handlers[channel](alert)
                        
                        # Update rule
                        rule.last_triggered = datetime.now()
                        
                        # Add to alerts list
                        self.alerts.append(alert)
                        triggered_alerts.append(alert)
                        
                        # Trim alerts list
                        if len(self.alerts) > self.max_alerts:
                            self.alerts = self.alerts[-self.max_alerts:]
                        
                        # Call callbacks
                        for callback in self.alert_callbacks:
                            try:
                                callback(alert)
                            except Exception as e:
                                logger.error(f"Alert callback error: {e}")
                        
                        logger.warning(f"Alert triggered: {rule.name} - {message}")
                        
                except Exception as e:
                    logger.error(f"Error checking rule {rule.name}: {e}")
        
        # Save history
        if triggered_alerts:
            self._save_history()
        
        return triggered_alerts
    
    def _format_message(self, template: str, data: Dict) -> str:
        """Format alert message with data"""
        try:
            # Handle special cases
            if '{sensor}' in template:
                # Find which sensor triggered
                for sensor, value in data.get('vibration', {}).items():
                    if value > IndustrialConfig.VIBRATION_SENSORS[sensor][2].critical:
                        return template.format(
                            sensor=IndustrialConfig.VIBRATION_SENSORS[sensor][0],
                            value=value,
                            **data
                        )
                
                for sensor, value in data.get('temperature', {}).items():
                    if value > IndustrialConfig.THERMAL_SENSORS[sensor][2].critical:
                        return template.format(
                            sensor=IndustrialConfig.THERMAL_SENSORS[sensor][0],
                            value=value,
                            **data
                        )
            
            return template.format(**data)
            
        except Exception as e:
            logger.error(f"Message formatting error: {e}")
            return template
    
    def _send_ui_alert(self, alert: Alert):
        """Send alert to UI"""
        # Store in session state for Streamlit
        if "ui_alerts" not in st.session_state:
            st.session_state.ui_alerts = []
        
        st.session_state.ui_alerts.append({
            'level': alert.level.value,
            'message': alert.message,
            'time': alert.timestamp.strftime('%H:%M:%S')
        })
        
        # Keep last 10 alerts
        if len(st.session_state.ui_alerts) > 10:
            st.session_state.ui_alerts = st.session_state.ui_alerts[-10:]
    
    def _send_email_alert(self, alert: Alert):
        """Send email alert"""
        if not settings.ENABLE_EMAIL_ALERTS:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.ALERT_EMAIL
            msg['To'] = settings.ALERT_EMAIL  # Send to self
            msg['Subject'] = f"[{alert.level.value.upper()}] AVCS DNA Alert: {alert.rule_name}"
            
            body = f"""
            <h2>AVCS DNA Alert System</h2>
            <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Level:</strong> <span style="color: {'red' if alert.level == AlertLevel.CRITICAL else 'orange'};">{alert.level.value}</span></p>
            <p><strong>Rule:</strong> {alert.rule_name}</p>
            <p><strong>Message:</strong> {alert.message}</p>
            <hr>
            <h3>Sensor Data:</h3>
            <pre>{json.dumps(alert.data, indent=2, default=str)}</pre>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            server.starttls()
            # Add credentials if needed
            # server.login(user, password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent: {alert.rule_name}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def _send_sms_alert(self, alert: Alert):
        """Send SMS alert (placeholder)"""
        # Implement SMS gateway integration
        logger.info(f"SMS alert would be sent: {alert.message}")
    
    def _send_webhook_alert(self, alert: Alert):
        """Send webhook alert (placeholder)"""
        # Implement webhook integration (Slack, Teams, etc.)
        logger.info(f"Webhook alert would be sent: {alert.message}")
    
    def _send_log_alert(self, alert: Alert):
        """Send alert to log file"""
        log_level = {
            AlertLevel.INFO: logger.info,
            AlertLevel.SUCCESS: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical
        }.get(alert.level, logger.info)
        
        log_level(f"ALERT [{alert.rule_name}]: {alert.message}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unacknowledged) alerts"""
        with self.lock:
            return [a for a in self.alerts if not a.acknowledged and not a.resolved]
    
    def get_alerts_by_level(self, level: AlertLevel) -> List[Alert]:
        """Get alerts by level"""
        with self.lock:
            return [a for a in self.alerts if a.level == level]
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        with self.lock:
            for alert in self.alerts:
                if alert.id == alert_id:
                    alert.acknowledged = True
                    logger.info(f"Alert acknowledged: {alert_id}")
                    break
    
    def resolve_alert(self, alert_id: str):
        """Mark alert as resolved"""
        with self.lock:
            for alert in self.alerts:
                if alert.id == alert_id:
                    alert.resolved = True
                    alert.resolved_at = datetime.now()
                    logger.info(f"Alert resolved: {alert_id}")
                    break
    
    def resolve_all_by_rule(self, rule_name: str):
        """Resolve all alerts for a rule"""
        with self.lock:
            for alert in self.alerts:
                if alert.rule_name == rule_name and not alert.resolved:
                    alert.resolved = True
                    alert.resolved_at = datetime.now()
            logger.info(f"All alerts resolved for rule: {rule_name}")
    
    def register_callback(self, callback: Callable[[Alert], None]):
        """Register callback for new alerts"""
        self.alert_callbacks.append(callback)
    
    def _save_history(self):
        """Save alert history to file"""
        try:
            os.makedirs(os.path.dirname(self.alert_history_file), exist_ok=True)
            
            history = []
            for alert in self.alerts[-100:]:  # Save last 100
                history.append({
                    'id': alert.id,
                    'rule_name': alert.rule_name,
                    'level': alert.level.value,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat(),
                    'acknowledged': alert.acknowledged,
                    'resolved': alert.resolved,
                    'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
                })
            
            with open(self.alert_history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save alert history: {e}")
    
    def _load_history(self):
        """Load alert history from file"""
        try:
            if os.path.exists(self.alert_history_file):
                with open(self.alert_history_file, 'r') as f:
                    history = json.load(f)
                
                for item in history[-50:]:  # Load last 50
                    alert = Alert(
                        item['rule_name'],
                        AlertLevel(item['level']),
                        item['message'],
                        {}
                    )
                    alert.id = item['id']
                    alert.timestamp = datetime.fromisoformat(item['timestamp'])
                    alert.acknowledged = item['acknowledged']
                    alert.resolved = item['resolved']
                    if item['resolved_at']:
                        alert.resolved_at = datetime.fromisoformat(item['resolved_at'])
                    
                    self.alerts.append(alert)
                
                logger.info(f"Loaded {len(self.alerts)} alerts from history")
                
        except Exception as e:
            logger.error(f"Failed to load alert history: {e}")
    
    def get_statistics(self) -> Dict:
        """Get alert statistics"""
        with self.lock:
            total = len(self.alerts)
            active = len(self.get_active_alerts())
            
            by_level = {
                level: len([a for a in self.alerts if a.level == level])
                for level in AlertLevel
            }
            
            last_hour = datetime.now() - timedelta(hours=1)
            recent = len([a for a in self.alerts if a.timestamp > last_hour])
            
            return {
                'total_alerts': total,
                'active_alerts': active,
                'recent_alerts': recent,
                'by_level': by_level,
                'resolution_rate': (total - active) / total * 100 if total > 0 else 100
            }
    
    def clear_resolved(self, older_than_days: int = 7):
        """Clear resolved alerts older than specified days"""
        with self.lock:
            cutoff = datetime.now() - timedelta(days=older_than_days)
            self.alerts = [
                a for a in self.alerts 
                if not (a.resolved and a.resolved_at and a.resolved_at < cutoff)
            ]
            logger.info(f"Cleared resolved alerts older than {older_than_days} days")

# Create singleton instance
alert_system = AlertSystem()

# Streamlit UI component for displaying alerts
def render_alert_panel():
    """Render alert panel in Streamlit"""
    st.subheader("⚠️ Alert Panel")
    
    active_alerts = alert_system.get_active_alerts()
    
    if not active_alerts:
        st.success("✅ No active alerts")
        return
    
    for alert in active_alerts[-5:]:  # Show last 5 active alerts
        if alert.level == AlertLevel.CRITICAL:
            st.error(f"🔴 **CRITICAL**: {alert.message}")
        elif alert.level == AlertLevel.ERROR:
            st.error(f"❌ **ERROR**: {alert.message}")
        elif alert.level == AlertLevel.WARNING:
            st.warning(f"⚠️ **WARNING**: {alert.message}")
        elif alert.level == AlertLevel.INFO:
            st.info(f"ℹ️ **INFO**: {alert.message}")
        else:
            st.success(f"✅ **INFO**: {alert.message}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"Time: {alert.timestamp.strftime('%H:%M:%S')} | Rule: {alert.rule_name}")
        with col2:
            if st.button("Acknowledge", key=f"ack_{alert.id}"):
                alert_system.acknowledge_alert(alert.id)
                st.rerun()
        
        st.markdown("---")
    
    # Statistics
    stats = alert_system.get_statistics()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Alerts", stats['total_alerts'])
    with col2:
        st.metric("Active", stats['active_alerts'])
    with col3:
        st.metric("Resolution Rate", f"{stats['resolution_rate']:.1f}%")

# Example usage in main app
if __name__ == "__main__":
    # Test the alert system
    test_data = {
        'vibration': {'VIB_MOTOR_DRIVE': 7.0},
        'temperature': {'TEMP_MOTOR_WINDING': 95},
        'noise': 90,
        'risk_index': 85,
        'ai_prediction': -1,
        'ai_confidence': 0.7,
        'rul_hours': 10
    }
    
    alerts = alert_system.check_alerts(test_data)
    print(f"Triggered {len(alerts)} alerts")
    
    stats = alert_system.get_statistics()
    print(f"Statistics: {stats}")
