"""AI Model management module"""
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from typing import Tuple, Optional
import os
from utils.logger import logger

class AIModelManager:
    """Manages AI model lifecycle and predictions"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.is_trained = False
        self.model_path = model_path
        self.feature_names = [
            'vib_motor_drive', 'vib_motor_nondrive', 'vib_pump_inlet', 'vib_pump_outlet',
            'temp_motor_winding', 'temp_motor_bearing', 'temp_pump_bearing', 'temp_pump_casing',
            'noise'
        ]
        self.initialize_model()
    
    def initialize_model(self):
        """Initialize the Isolation Forest model"""
        try:
            # Try to load existing model
            if self.model_path and os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                logger.info(f"Model loaded from {self.model_path}")
            else:
                # Train new model
                self._train_new_model()
                
        except Exception as e:
            logger.error(f"Failed to initialize AI model: {e}")
            self.is_trained = False
    
    def _train_new_model(self):
        """Train a new Isolation Forest model"""
        # Generate synthetic training data
        np.random.seed(42)
        
        # Normal operation data
        normal_vibration = np.random.normal(1.0, 0.3, (1000, 4))
        normal_temperature = np.random.normal(65, 5, (1000, 4))
        normal_noise = np.random.normal(65, 3, (1000, 1))
        
        # Anomaly data
        anomaly_vibration = np.random.normal(5.0, 1.0, (200, 4))
        anomaly_temperature = np.random.normal(95, 10, (200, 4))
        anomaly_noise = np.random.normal(95, 8, (200, 1))
        
        # Combine data
        normal_data = np.column_stack([normal_vibration, normal_temperature, normal_noise])
        anomaly_data = np.column_stack([anomaly_vibration, anomaly_temperature, anomaly_noise])
        training_data = np.vstack([normal_data, anomaly_data])
        
        # Train model
        self.model = IsolationForest(
            contamination=0.15,
            random_state=42,
            n_estimators=200,
            max_samples='auto',
            bootstrap=False
        )
        self.model.fit(training_data)
        self.is_trained = True
        
        # Save model if path provided
        if self.model_path:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)
            logger.info(f"Model saved to {self.model_path}")
    
    def predict(self, features) -> Tuple[int, float]:
        """Make prediction with confidence score"""
        if not self.is_trained or self.model is None:
            return 1, 0.0
        
        try:
            # Reshape features if needed
            if isinstance(features, list):
                features = np.array(features).reshape(1, -1)
            
            prediction = self.model.predict(features)[0]
            confidence = self.model.decision_function(features)[0]
            
            return prediction, confidence
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return 1, 0.0
    
    def get_feature_importance(self) -> dict:
        """Get feature importance (approximated)"""
        # For Isolation Forest, we can use the feature weights
        if self.model and hasattr(self.model, 'feature_importances_'):
            return dict(zip(self.feature_names, self.model.feature_importances_))
        return {}
    
    def retrain(self, new_data: np.ndarray):
        """Retrain model with new data"""
        if self.model:
            self.model.fit(new_data)
            self.is_trained = True
            logger.info("Model retrained with new data")
