# modules/alert_system.py
"""Alert management and notification system for AVCS DNA Industrial Monitor"""
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from threading import Lock, Timer
import json
from pathlib import Path

from modules.config import AlertLevel, settings, industrial_config
from utils.logger import logger

class AlertRule:
    """Alert rule definition"""
    
    def __init__(self, 
                 name: str,
                 condition: Callable,
                 level: AlertLevel,
                 message_template: str,
                 channels: List[str],
                 cooldown_seconds: int = 300):
        """
        Initialize alert rule
        
        Args:
            name: Rule name
            condition: Function that returns (triggered, data) tuple
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
        self.trigger_count = 0

class Alert:
    """Alert data structure"""
    
    def __init__(self, 
                 rule_name: str,
                 level: AlertLevel,
                 message: str,
                 data: Dict = None):
        self.id = f"alert_{datetime.now().timestamp()}_{rule_name}"
        self.rule_name = rule_name
        self.level = level
        self.message = message
        self.data = data or {}
        self.timestamp = datetime.now()
        self.acknowledged = False
        self.acknowledged_by = None
        self.acknowledged_at = None
        self.resolved = False
        self.resolved_at = None
        self.resolved_by = None
        self.escalated = False
        self.escalation_count = 0

class AlertSystem:
    """Comprehensive alert management system"""
    
    def __init__(self):
        self.lock = Lock()
        self.alerts: List[Alert] = []
        self.rules: List[AlertRule] = []
        self.channel_handlers = {}
        self.alert_history_file = settings.DATA_DIR / "alert_history.json"
        self.max_alerts = 1000
        self.escalation_timers = {}
        
        # Initialize channel handlers
        self._init_channel_handlers()
        
        # Initialize default rules
        self._init_default_rules()
        
        # Load alert history
        self._load_history()
        
        logger.info(f"Alert system initialized with {len(self.rules)} rules")
    
    def _init_channel_handlers(self):
        """Initialize notification channel handlers"""
        self.channel_handlers = {
            'ui': self._send_ui_alert,
            'email': self._send_email_alert,
            'log': self._send_log_alert,
            'console': self._send_console_alert
        }
    
    def _init_default_rules(self):
        """Initialize default alert rules"""
        
        # Critical vibration rule
        self.add_rule(AlertRule(
            name="critical_vibration",
            condition=self._check_critical_vibration,
            level=AlertLevel.CRITICAL,
            message_template="Critical vibration: {sensor} = {value:.1f} mm/s",
            channels=['ui', 'email', 'log'],
            cooldown_seconds=60
        ))
        
        # High temperature rule
        self.add_rule(AlertRule(
            name="high_temperature",
            condition=self._check_high_temperature,
            level=AlertLevel.WARNING,
            message_template="High temperature: {sensor} = {value:.0f}°C",
            channels=['ui', 'log'],
            cooldown_seconds=120
        ))
        
        # Critical temperature rule
        self.add_rule(AlertRule(
            name="critical_temperature",
            condition=self._check_critical_temperature,
            level=AlertLevel.CRITICAL,
            message_template="Critical temperature: {sensor} = {value:.0f}°C",
            channels=['ui', 'email', 'log'],
            cooldown_seconds=60
        ))
        
        # High noise rule
        self.add_rule(AlertRule(
            name="high_noise",
            condition=self._check_high_noise,
            level=AlertLevel.WARNING,
            message_template="High noise: {value:.1f} dB",
            channels=['ui', 'log'],
            cooldown_seconds=120
        ))
        
        # Critical noise rule
        self.add_rule(AlertRule(
            name="critical_noise",
            condition=self._check_critical_noise,
            level=AlertLevel.CRITICAL,
            message_template="Critical noise: {value:.1f} dB",
            channels=['ui', 'email', 'log'],
            cooldown_seconds=60
        ))
        
        # High risk rule
        self.add_rule(AlertRule(
            name="high_risk",
            condition=lambda data: data.get('risk_index', 0) > 80,
            level=AlertLevel.CRITICAL,
            message_template="Critical risk: {risk_index}% - Immediate action required",
            channels=['ui', 'email', 'log'],
            cooldown_seconds=30
        ))
        
        # Elevated risk rule
        self.add_rule(AlertRule(
            name="elevated_risk",
            condition=lambda data: data.get('risk_index', 0) > 50,
            level=AlertLevel.WARNING,
            message_template="Elevated risk: {risk_index}% - Schedule maintenance",
            channels=['ui', 'log'],
            cooldown_seconds=180
        ))
        
        # AI anomaly rule
        self.add_rule(AlertRule(
            name="ai_anomaly",
            condition=lambda data: data.get('ai_prediction', 1) == -1,
            level=AlertLevel.WARNING,
            message_template="AI anomaly detected (confidence: {ai_confidence:.2f})",
            channels=['ui', 'log'],
            cooldown_seconds=300
        ))
        
        # Sensor failure rule
        self.add_rule(AlertRule(
            name="sensor_failure",
            condition=self._check_sensor_failure,
            level=AlertLevel.ERROR,
            message_template="Sensor failure: {sensor}",
            channels=['ui', 'email', 'log'],
            cooldown_seconds=60
        ))
        
        # RUL warning rule
        self.add_rule(AlertRule(
            name="rul_warning",
            condition=lambda data: data.get('rul_hours', 100) < 24,
            level=AlertLevel.WARNING,
            message_template="Maintenance required: {rul_hours} hours remaining",
            channels=['ui', 'email', 'log'],
            cooldown_seconds=3600  # 1 hour
        ))
    
    def _check_critical_vibration(self, data: Dict) -> tuple:
        """Check for critical vibration"""
        for sensor, value in data.get('vibration', {}).items():
            limit = industrial_config.VIBRATION_SENSORS[sensor][1].critical
            if value > limit:
                return True, {
                    'sensor': industrial_config.VIBRATION_SENSORS[sensor][0],
                    'value': value,
                    'limit': limit
                }
        return False, {}
    
    def _check_high_temperature(self, data: Dict) -> tuple:
        """Check for high temperature"""
        for sensor, value in data.get('temperature', {}).items():
            limit = industrial_config.THERMAL_SENSORS[sensor][1].warning
            if value > limit:
                return True, {
                    'sensor': industrial_config.THERMAL_SENSORS[sensor][0],
                    'value': value,
                    'limit': limit
                }
        return False, {}
    
    def _check_critical_temperature(self, data: Dict) -> tuple:
        """Check for critical temperature"""
        for sensor, value in data.get('temperature', {}).items():
            limit = industrial_config.THERMAL_SENSORS[sensor][1].critical
            if value > limit:
                return True, {
                    'sensor': industrial_config.THERMAL_SENSORS[sensor][0],
                    'value': value,
                    'limit': limit
                }
        return False, {}
    
    def _check_high_noise(self, data: Dict) -> tuple:
        """Check for high noise"""
        value = data.get('noise', 0)
        limit = industrial_config.ACOUSTIC_SENSOR[1].warning
        if value > limit:
            return True, {'value': value, 'limit': limit}
        return False, {}
    
    def _check_critical_noise(self, data: Dict) -> tuple:
        """Check for critical noise"""
        value = data.get('noise', 0)
        limit = industrial_config.ACOUSTIC_SENSOR[1].critical
        if value > limit:
            return True, {'value': value, 'limit': limit}
        return False, {}
    
    def _check_sensor_failure(self, data: Dict) -> tuple:
        """Check for sensor failure"""
        for sensor, value in data.get('vibration', {}).items():
            if value == 0 or value is None:
                return True, {'sensor': industrial_config.VIBRATION_SENSORS[sensor][0]}
        
        for sensor, value in data.get('temperature', {}).items():
            if value == 0 or value is None:
                return True, {'sensor': industrial_config.THERMAL_SENSORS[sensor][0]}
        
        return False, {}
    
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
                    triggered, alert_data = rule.condition(data)
                    
                    if triggered:
                        # Format message
                        message = rule.message_template.format(**{**data, **alert_data})
                        
                        # Create alert
                        alert = Alert(rule.name, rule.level, message, {**data, **alert_data})
                        
                        # Send through channels
                        for channel in rule.channels:
                            if channel in self.channel_handlers:
                                self.channel_handlers[channel](alert)
                        
                        # Update rule
                        rule.last_triggered = datetime.now()
                        rule.trigger_count += 1
                        
                        # Add to alerts list
                        self.alerts.append(alert)
                        triggered_alerts.append(alert)
                        
                        # Trim alerts list
                        if len(self.alerts) > self.max_alerts:
                            self.alerts = self.alerts[-self.max_alerts:]
                        
                        logger.warning(f"Alert triggered: {rule.name} - {message}")
                        
                        # Schedule escalation if not acknowledged
                        self._schedule_escalation(alert)
                        
                except Exception as e:
                    logger.error(f"Error checking rule {rule.name}: {e}")
        
        # Save history
        if triggered_alerts:
            self._save_history()
        
        return triggered_alerts
    
    def _schedule_escalation(self, alert: Alert, delay: int = 300):
        """Schedule alert escalation"""
        def escalate():
            with self.lock:
                if not alert.acknowledged and not alert.resolved:
                    alert.escalated = True
                    alert.escalation_count += 1
                    
                    # Send escalation notification
                    escalation_msg = f"ESCALATION ({alert.escalation_count}): {alert.message}"
                    self._send_email_alert(Alert(
                        alert.rule_name,
                        AlertLevel.CRITICAL,
                        escalation_msg,
                        alert.data
                    ))
                    
                    logger.warning(f"Alert escalated: {alert.id}")
        
        timer = Timer(delay, escalate)
        timer.daemon = True
        timer.start()
        self.escalation_timers[alert.id] = timer
    
    def _send_ui_alert(self, alert: Alert):
        """Send alert to UI"""
        if "ui_alerts" not in st.session_state:
            st.session_state.ui_alerts = []
        
        st.session_state.ui_alerts.append({
            'id': alert.id,
            'level': alert.level.value,
            'message': alert.message,
            'time': alert.timestamp.strftime('%H:%M:%S'),
            'acknowledged': False
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
            msg['To'] = settings.ALERT_EMAIL
            msg['Subject'] = f"[{alert.level.value.upper()}] AVCS Alert: {alert.rule_name}"
            
            body = f"""
            <h2>AVCS DNA Alert System</h2>
            <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Level:</strong> <span style="color: {alert.level.color};">{alert.level.value}</span></p>
            <p><strong>Rule:</strong> {alert.rule_name}</p>
            <p><strong>Message:</strong> {alert.message}</p>
            <hr>
            <h3>Alert Data:</h3>
            <pre>{json.dumps(alert.data, indent=2, default=str)}</pre>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # In production, configure SMTP properly
            # server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            # server.starttls()
            # server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            # server.send_message(msg)
            # server.quit()
            
            logger.info(f"Email alert would be sent: {alert.rule_name}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def _send_log_alert(self, alert: Alert):
        """Send alert to log file"""
        log_message = f"ALERT [{alert.rule_name}] [{alert.level.value}]: {alert.message}"
        
        if alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
            logger.error(log_message)
        elif alert.level == AlertLevel.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _send_console_alert(self, alert: Alert):
        """Send alert to console"""
        print(f"\n!!! ALERT: {alert.message} !!!\n")
    
    def acknowledge_alert(self, alert_id: str, user: str = "system"):
        """Acknowledge an alert"""
        with self.lock:
            for alert in self.alerts:
                if alert.id == alert_id:
                    alert.acknowledged = True
                    alert.acknowledged_by = user
                    alert.acknowledged_at = datetime.now()
                    
                    # Cancel escalation timer
                    if alert_id in self.escalation_timers:
                        self.escalation_timers[alert_id].cancel()
                        del self.escalation_timers[alert_id]
                    
                    logger.info(f"Alert {alert_id} acknowledged by {user}")
                    break
    
    def resolve_alert(self, alert_id: str, user: str = "system"):
        """Resolve an alert"""
        with self.lock:
            for alert in self.alerts:
                if alert.id == alert_id:
                    alert.resolved = True
                    alert.resolved_by = user
                    alert.resolved_at = datetime.now()
                    
                    logger.info(f"Alert {alert_id} resolved by {user}")
                    break
    
    def get_active_alerts(self) -> List[Alert]:
        """Get active alerts"""
        with self.lock:
            return [a for a in self.alerts 
                   if not a.resolved and not a.acknowledged]
    
    def get_alerts_by_level(self, level: AlertLevel) -> List[Alert]:
        """Get alerts by level"""
        with self.lock:
            return [a for a in self.alerts if a.level == level]
    
    def get_statistics(self) -> Dict:
        """Get alert statistics"""
        with self.lock:
            total = len(self.alerts)
            active = len([a for a in self.alerts if not a.resolved])
            acknowledged = len([a for a in self.alerts if a.acknowledged])
            
            by_level = {}
            for level in AlertLevel:
                count = len([a for a in self.alerts if a.level == level])
                if count > 0:
                    by_level[level.value] = count
            
            last_hour = datetime.now() - timedelta(hours=1)
            recent = len([a for a in self.alerts if a.timestamp > last_hour])
            
            return {
                'total': total,
                'active': active,
                'acknowledged': acknowledged,
                'resolved': total - active,
                'by_level': by_level,
                'recent': recent,
                'resolution_rate': (total - active) / total * 100 if total > 0 else 100
            }
    
    def _save_history(self):
        """Save alert history to file"""
        try:
            history = []
            for alert in self.alerts[-100:]:  # Save last 100
                history.append({
                    'id': alert.id,
                    'rule_name': alert.rule_name,
                    'level': alert.level.value,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat(),
                    'acknowledged': alert.acknowledged,
                    'resolved': alert.resolved
                })
            
            with open(self.alert_history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save alert history: {e}")
    
    def _load_history(self):
        """Load alert history from file"""
        try:
            if self.alert_history_file.exists():
                with open(self.alert_history_file, 'r') as f:
                    history = json.load(f)
                
                for item in history[-50:]:  # Load last 50
                    alert = Alert(
                        item['rule_name'],
                        AlertLevel(item['level']),
                        item['message']
                    )
                    alert.id = item['id']
                    alert.timestamp = datetime.fromisoformat(item['timestamp'])
                    alert.acknowledged = item['acknowledged']
                    alert.resolved = item['resolved']
                    
                    self.alerts.append(alert)
                
                logger.info(f"Loaded {len(self.alerts)} alerts from history")
                
        except Exception as e:
            logger.error(f"Failed to load alert history: {e}")
    
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

def render_alert_panel():
    """Render alert panel in Streamlit"""
    st.subheader("⚠️ Active Alerts")
    
    active_alerts = alert_system.get_active_alerts()
    
    if not active_alerts:
        st.success("✅ No active alerts")
        return
    
    for alert in active_alerts[-5:]:  # Show last 5
        if alert.level == AlertLevel.CRITICAL:
            st.error(f"🔴 **CRITICAL**: {alert.message}")
        elif alert.level == AlertLevel.ERROR:
            st.error(f"❌ **ERROR**: {alert.message}")
        elif alert.level == AlertLevel.WARNING:
            st.warning(f"⚠️ **WARNING**: {alert.message}")
        else:
            st.info(f"ℹ️ **INFO**: {alert.message}")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.caption(f"🕐 {alert.timestamp.strftime('%H:%M:%S')}")
        with col2:
            if st.button("✓ Acknowledge", key=f"ack_{alert.id}"):
                alert_system.acknowledge_alert(alert.id)
                st.rerun()
        with col3:
            if st.button("✗ Resolve", key=f"res_{alert.id}"):
                alert_system.resolve_alert(alert.id)
                st.rerun()
        
        st.markdown("---")
    
    # Statistics
    stats = alert_system.get_statistics()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", stats['total'])
    with col2:
        st.metric("Active", stats['active'])
    with col3:
        st.metric("Rate", f"{stats['resolution_rate']:.0f}%")
