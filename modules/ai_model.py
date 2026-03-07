# modules/ai_model.py
"""AI Model management for AVCS DNA Industrial Monitor"""
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from typing import Tuple, Optional, Dict, List
import os
from datetime import datetime

from modules.config import settings
from utils.logger import logger

class AIModelManager:
    """Manages AI model lifecycle and predictions"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.is_trained = False
        self.model_path = model_path or settings.MODEL_PATH
        self.training_date = None
        self.training_samples = 0
        self.feature_importance = {}
        
        # Feature names for reference
        self.feature_names = [
            'vib_motor_drive', 'vib_motor_nondrive', 'vib_pump_inlet', 'vib_pump_outlet',
            'temp_motor_winding', 'temp_motor_bearing', 'temp_pump_bearing', 'temp_pump_casing',
            'noise'
        ]
        
        # Model parameters
        self.model_params = {
            'contamination': 0.15,
            'random_state': 42,
            'n_estimators': 200,
            'max_samples': 'auto',
            'bootstrap': False,
            'n_jobs': -1
        }
        
        self.initialize_model()
    
    def initialize_model(self):
        """Initialize the Isolation Forest model"""
        try:
            # Try to load existing model
            if os.path.exists(self.model_path):
                self.load_model()
                logger.info(f"Model loaded from {self.model_path}")
            else:
                # Train new model
                self.train_new_model()
                
        except Exception as e:
            logger.error(f"Failed to initialize AI model: {e}")
            self.is_trained = False
    
    def train_new_model(self):
        """Train a new Isolation Forest model"""
        try:
            logger.info("Training new Isolation Forest model...")
            
            # Generate synthetic training data
            np.random.seed(42)
            
            # Normal operation data (70%)
            n_normal = 700
            normal_vibration = np.random.normal(1.0, 0.3, (n_normal, 4))
            normal_temperature = np.random.normal(65, 5, (n_normal, 4))
            normal_noise = np.random.normal(65, 3, (n_normal, 1))
            
            # Anomaly data (30%)
            n_anomaly = 300
            anomaly_vibration = np.random.normal(5.0, 1.5, (n_anomaly, 4))
            anomaly_temperature = np.random.normal(95, 10, (n_anomaly, 4))
            anomaly_noise = np.random.normal(95, 8, (n_anomaly, 1))
            
            # Combine data
            normal_data = np.column_stack([normal_vibration, normal_temperature, normal_noise])
            anomaly_data = np.column_stack([anomaly_vibration, anomaly_temperature, anomaly_noise])
            training_data = np.vstack([normal_data, anomaly_data])
            
            # Shuffle data
            np.random.shuffle(training_data)
            
            # Train model
            self.model = IsolationForest(**self.model_params)
            self.model.fit(training_data)
            
            self.is_trained = True
            self.training_date = datetime.now()
            self.training_samples = len(training_data)
            
            # Calculate feature importance (approximated)
            self._calculate_feature_importance()
            
            # Save model
            self.save_model()
            
            logger.info(f"Model trained successfully with {self.training_samples} samples")
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            self.is_trained = False
    
    def _calculate_feature_importance(self):
        """Calculate approximate feature importance"""
        try:
            # For Isolation Forest, we can use the average path length
            if self.model and hasattr(self.model, 'estimators_'):
                importance = []
                for estimator in self.model.estimators_[:10]:  # Use first 10 trees
                    if hasattr(estimator, 'feature_importances_'):
                        importance.append(estimator.feature_importances_)
                
                if importance:
                    avg_importance = np.mean(importance, axis=0)
                    self.feature_importance = dict(zip(self.feature_names, avg_importance))
        except Exception as e:
            logger.error(f"Error calculating feature importance: {e}")
    
    def predict(self, features: List[float]) -> Tuple[int, float]:
        """Make prediction with confidence score"""
        if not self.is_trained or self.model is None:
            return 1, 0.0
        
        try:
            # Reshape features if needed
            if isinstance(features, list):
                features = np.array(features).reshape(1, -1)
            
            # Make prediction
            prediction = self.model.predict(features)[0]
            
            # Get confidence score (decision function)
            confidence = self.model.decision_function(features)[0]
            
            # Normalize confidence to [0, 1] range
            normalized_confidence = 1 / (1 + np.exp(-confidence))
            
            return prediction, float(normalized_confidence)
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return 1, 0.0
    
    def predict_batch(self, features_batch: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Make predictions for multiple samples"""
        if not self.is_trained or self.model is None:
            return np.ones(len(features_batch)), np.zeros(len(features_batch))
        
        try:
            predictions = self.model.predict(features_batch)
            confidences = self.model.decision_function(features_batch)
            
            # Normalize confidences
            confidences = 1 / (1 + np.exp(-confidences))
            
            return predictions, confidences
            
        except Exception as e:
            logger.error(f"Batch prediction error: {e}")
            return np.ones(len(features_batch)), np.zeros(len(features_batch))
    
    def save_model(self):
        """Save model to disk"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Save model
            joblib.dump(self.model, self.model_path)
            
            # Save metadata
            metadata = {
                'training_date': self.training_date.isoformat() if self.training_date else None,
                'training_samples': self.training_samples,
                'feature_names': self.feature_names,
                'model_params': self.model_params,
                'feature_importance': self.feature_importance
            }
            
            metadata_path = self.model_path.replace('.pkl', '_metadata.json')
            with open(metadata_path, 'w') as f:
                import json
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Model saved to {self.model_path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def load_model(self):
        """Load model from disk"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                
                # Load metadata
                metadata_path = self.model_path.replace('.pkl', '_metadata.json')
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        import json
                        metadata = json.load(f)
                        
                        self.training_date = datetime.fromisoformat(metadata['training_date']) if metadata.get('training_date') else None
                        self.training_samples = metadata.get('training_samples', 0)
                        self.feature_importance = metadata.get('feature_importance', {})
                
                logger.info(f"Model loaded from {self.model_path}")
            else:
                logger.warning(f"Model file not found: {self.model_path}")
                
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.is_trained = False
    
    def retrain(self, new_data: np.ndarray, labels: Optional[np.ndarray] = None):
        """Retrain model with new data"""
        try:
            logger.info(f"Retraining model with {len(new_data)} new samples")
            
            if labels is not None:
                # Adjust contamination based on new labels
                contamination = sum(labels == -1) / len(labels)
                self.model_params['contamination'] = max(0.05, min(0.3, contamination))
            
            # Create new model with updated parameters
            self.model = IsolationForest(**self.model_params)
            self.model.fit(new_data)
            
            self.is_trained = True
            self.training_date = datetime.now()
            self.training_samples = len(new_data)
            
            # Save updated model
            self.save_model()
            
            logger.info("Model retrained successfully")
            
        except Exception as e:
            logger.error(f"Error retraining model: {e}")
    
    def get_model_info(self) -> Dict:
        """Get model information"""
        return {
            'is_trained': self.is_trained,
            'training_date': self.training_date.isoformat() if self.training_date else None,
            'training_samples': self.training_samples,
            'model_path': self.model_path,
            'feature_names': self.feature_names,
            'model_params': self.model_params,
            'feature_importance': self.feature_importance
        }
    
    def validate_features(self, features: List[float]) -> bool:
        """Validate feature vector"""
        if len(features) != len(self.feature_names):
            logger.error(f"Invalid feature count: expected {len(self.feature_names)}, got {len(features)}")
            return False
        
        # Check for NaN or inf
        if not np.all(np.isfinite(features)):
            logger.error("Features contain NaN or inf values")
            return False
        
        return True

# Create singleton instance
ai_model = AIModelManager()
