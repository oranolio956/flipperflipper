#!/usr/bin/env python3
"""
Machine Learning Proxy Quality Predictor
Uses TensorFlow for real-time quality prediction
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass
import json
import pickle

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import joblib

logger = logging.getLogger(__name__)


@dataclass
class ProxyFeatures:
    """Features used for ML prediction"""
    # Network features
    response_time_ms: float
    download_speed_mbps: float
    upload_speed_mbps: float
    latency_ms: float
    jitter_ms: float
    packet_loss: float
    
    # Protocol & Location
    protocol: str  # http, https, socks4, socks5
    country_code: str
    city: str
    asn: str
    is_residential: bool
    is_mobile: bool
    is_datacenter: bool
    
    # Historical performance
    success_rate_7d: float
    avg_uptime_hours: float
    failure_count_24h: int
    test_count_total: int
    
    # Security features
    ssl_fingerprint_changes: int
    dns_leak_detected: bool
    ip_leak_detected: bool
    fraud_score: float
    
    # Time-based features
    hour_of_day: int
    day_of_week: int
    is_weekend: bool
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array for model input"""
        return np.array([
            self.response_time_ms,
            self.download_speed_mbps,
            self.upload_speed_mbps,
            self.latency_ms,
            self.jitter_ms,
            self.packet_loss,
            float(self.is_residential),
            float(self.is_mobile),
            float(self.is_datacenter),
            self.success_rate_7d,
            self.avg_uptime_hours,
            float(self.failure_count_24h),
            float(self.test_count_total),
            float(self.ssl_fingerprint_changes),
            float(self.dns_leak_detected),
            float(self.ip_leak_detected),
            self.fraud_score,
            float(self.hour_of_day),
            float(self.day_of_week),
            float(self.is_weekend)
        ])


class ProxyQualityPredictor:
    """
    ML model for predicting proxy quality and lifetime
    Uses deep learning with attention mechanisms
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model: Optional[Model] = None
        self.scaler: Optional[StandardScaler] = None
        self.label_encoders = {}
        self.feature_names = []
        self.model_path = model_path or "models/proxy_quality_model.h5"
        self.scaler_path = model_path.replace('.h5', '_scaler.pkl') if model_path else "models/proxy_quality_scaler.pkl"
        
        # Model hyperparameters
        self.sequence_length = 24  # Hours of history
        self.n_features = 20
        self.embedding_dims = {
            'protocol': 8,
            'country': 16,
            'asn': 32
        }
        
        # Load existing model if available
        if model_path:
            self.load_model()
    
    def build_model(self) -> Model:
        """
        Build advanced neural network with attention mechanism
        """
        # Input layers
        numeric_input = layers.Input(shape=(self.n_features,), name='numeric_features')
        protocol_input = layers.Input(shape=(1,), name='protocol')
        country_input = layers.Input(shape=(1,), name='country')
        asn_input = layers.Input(shape=(1,), name='asn')
        
        # Embeddings for categorical features
        protocol_embed = layers.Embedding(
            input_dim=5,  # http, https, socks4, socks5, unknown
            output_dim=self.embedding_dims['protocol']
        )(protocol_input)
        protocol_embed = layers.Flatten()(protocol_embed)
        
        country_embed = layers.Embedding(
            input_dim=250,  # ~250 countries
            output_dim=self.embedding_dims['country']
        )(country_input)
        country_embed = layers.Flatten()(country_embed)
        
        asn_embed = layers.Embedding(
            input_dim=10000,  # Common ASNs
            output_dim=self.embedding_dims['asn']
        )(asn_input)
        asn_embed = layers.Flatten()(asn_embed)
        
        # Combine all features
        combined = layers.concatenate([
            numeric_input,
            protocol_embed,
            country_embed,
            asn_embed
        ])
        
        # Deep network with batch normalization and dropout
        x = layers.Dense(256, activation='relu')(combined)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        x = layers.Dense(128, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        # Attention mechanism
        attention = layers.Dense(128, activation='tanh')(x)
        attention = layers.Dense(1, activation='softmax')(attention)
        attended = layers.multiply([x, attention])
        
        x = layers.Dense(64, activation='relu')(attended)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        # Multi-task outputs
        quality_output = layers.Dense(1, activation='sigmoid', name='quality')(x)
        lifetime_output = layers.Dense(1, activation='linear', name='lifetime_hours')(x)
        failure_risk = layers.Dense(1, activation='sigmoid', name='failure_risk')(x)
        
        # Build model
        model = Model(
            inputs=[numeric_input, protocol_input, country_input, asn_input],
            outputs=[quality_output, lifetime_output, failure_risk]
        )
        
        # Custom loss weights for multi-task learning
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss={
                'quality': 'binary_crossentropy',
                'lifetime_hours': 'huber',
                'failure_risk': 'binary_crossentropy'
            },
            loss_weights={
                'quality': 1.0,
                'lifetime_hours': 0.5,
                'failure_risk': 0.8
            },
            metrics={
                'quality': ['accuracy', tf.keras.metrics.AUC()],
                'lifetime_hours': ['mae'],
                'failure_risk': ['accuracy']
            }
        )
        
        return model
    
    async def train(self, training_data: pd.DataFrame) -> Dict[str, float]:
        """
        Train the model on historical proxy data
        """
        logger.info(f"Training on {len(training_data)} samples")
        
        # Prepare features
        X_numeric, X_protocol, X_country, X_asn, y = self._prepare_training_data(training_data)
        
        # Split data
        split_data = train_test_split(
            X_numeric, X_protocol, X_country, X_asn,
            y['quality'], y['lifetime'], y['failure_risk'],
            test_size=0.2, random_state=42
        )
        
        X_train = [split_data[0], split_data[1], split_data[2], split_data[3]]
        X_val = [split_data[4], split_data[5], split_data[6], split_data[7]]
        y_train = {
            'quality': split_data[8],
            'lifetime_hours': split_data[9],
            'failure_risk': split_data[10]
        }
        y_val = {
            'quality': split_data[11],
            'lifetime_hours': split_data[12],
            'failure_risk': split_data[13]
        }
        
        # Build and train model
        self.model = self.build_model()
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-6
            ),
            keras.callbacks.ModelCheckpoint(
                self.model_path,
                monitor='val_loss',
                save_best_only=True
            )
        ]
        
        # Train
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=100,
            batch_size=64,
            callbacks=callbacks,
            verbose=1
        )
        
        # Save scaler and encoders
        self._save_preprocessors()
        
        # Return final metrics
        final_metrics = {
            'quality_accuracy': history.history['quality_accuracy'][-1],
            'quality_auc': history.history['quality_auc'][-1],
            'lifetime_mae': history.history['lifetime_hours_mae'][-1],
            'failure_accuracy': history.history['failure_risk_accuracy'][-1],
            'val_loss': history.history['val_loss'][-1]
        }
        
        logger.info(f"Training completed: {final_metrics}")
        return final_metrics
    
    async def predict(self, features: ProxyFeatures) -> Dict[str, float]:
        """
        Predict proxy quality, lifetime, and failure risk
        """
        if not self.model:
            raise ValueError("Model not loaded. Train or load a model first.")
        
        # Prepare input
        X_numeric = self.scaler.transform([features.to_array()])
        X_protocol = self.label_encoders['protocol'].transform([features.protocol])
        X_country = self.label_encoders['country'].transform([features.country_code])
        X_asn = self._encode_asn(features.asn)
        
        # Predict
        predictions = self.model.predict(
            [X_numeric, X_protocol, X_country, X_asn],
            verbose=0
        )
        
        return {
            'quality_score': float(predictions[0][0]),
            'expected_lifetime_hours': float(predictions[1][0]),
            'failure_risk_24h': float(predictions[2][0]),
            'recommendation': self._get_recommendation(predictions)
        }
    
    async def batch_predict(self, features_list: List[ProxyFeatures]) -> List[Dict[str, float]]:
        """
        Batch prediction for efficiency
        """
        if not features_list:
            return []
        
        # Prepare batch inputs
        X_numeric = self.scaler.transform([f.to_array() for f in features_list])
        X_protocol = self.label_encoders['protocol'].transform([f.protocol for f in features_list])
        X_country = self.label_encoders['country'].transform([f.country_code for f in features_list])
        X_asn = np.array([self._encode_asn(f.asn) for f in features_list])
        
        # Batch predict
        predictions = self.model.predict(
            [X_numeric, X_protocol, X_country, X_asn],
            batch_size=32,
            verbose=0
        )
        
        # Format results
        results = []
        for i in range(len(features_list)):
            results.append({
                'quality_score': float(predictions[0][i]),
                'expected_lifetime_hours': float(predictions[1][i]),
                'failure_risk_24h': float(predictions[2][i]),
                'recommendation': self._get_recommendation([
                    predictions[0][i],
                    predictions[1][i],
                    predictions[2][i]
                ])
            })
        
        return results
    
    def _prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, ...]:
        """
        Prepare training data with feature engineering
        """
        # Initialize encoders
        self.label_encoders['protocol'] = LabelEncoder()
        self.label_encoders['country'] = LabelEncoder()
        
        # Encode categorical variables
        df['protocol_encoded'] = self.label_encoders['protocol'].fit_transform(df['protocol'])
        df['country_encoded'] = self.label_encoders['country'].fit_transform(df['country_code'])
        
        # Feature engineering
        df['response_time_log'] = np.log1p(df['response_time_ms'])
        df['speed_ratio'] = df['download_speed_mbps'] / (df['upload_speed_mbps'] + 1)
        df['reliability_score'] = df['success_rate_7d'] * (1 - df['packet_loss'])
        
        # Numeric features
        numeric_features = [
            'response_time_log', 'download_speed_mbps', 'upload_speed_mbps',
            'latency_ms', 'jitter_ms', 'packet_loss', 'is_residential',
            'is_mobile', 'is_datacenter', 'success_rate_7d', 'avg_uptime_hours',
            'failure_count_24h', 'test_count_total', 'ssl_fingerprint_changes',
            'dns_leak_detected', 'ip_leak_detected', 'fraud_score',
            'hour_of_day', 'day_of_week', 'is_weekend'
        ]
        
        # Scale numeric features
        self.scaler = StandardScaler()
        X_numeric = self.scaler.fit_transform(df[numeric_features])
        
        # Prepare targets
        y = {
            'quality': (df['quality_label'] == 'high').astype(int),
            'lifetime': df['actual_lifetime_hours'],
            'failure_risk': (df['failed_within_24h'] == True).astype(int)
        }
        
        return (
            X_numeric,
            df['protocol_encoded'].values,
            df['country_encoded'].values,
            df['asn'].apply(self._encode_asn).values,
            y
        )
    
    def _encode_asn(self, asn: str) -> int:
        """
        Encode ASN to numeric ID
        """
        try:
            # Extract numeric part from ASN
            if asn.startswith('AS'):
                return min(int(asn[2:]), 9999)
            return 0
        except:
            return 0
    
    def _get_recommendation(self, predictions: List[np.ndarray]) -> str:
        """
        Generate recommendation based on predictions
        """
        quality = predictions[0][0] if len(predictions[0].shape) > 0 else predictions[0]
        lifetime = predictions[1][0] if len(predictions[1].shape) > 0 else predictions[1]
        risk = predictions[2][0] if len(predictions[2].shape) > 0 else predictions[2]
        
        if quality > 0.8 and lifetime > 24 and risk < 0.2:
            return "EXCELLENT - Use for critical tasks"
        elif quality > 0.6 and lifetime > 12 and risk < 0.4:
            return "GOOD - Suitable for general use"
        elif quality > 0.4 and risk < 0.6:
            return "FAIR - Use with caution"
        else:
            return "POOR - Not recommended"
    
    def save_model(self):
        """Save model and preprocessors"""
        if self.model:
            self.model.save(self.model_path)
            self._save_preprocessors()
            logger.info(f"Model saved to {self.model_path}")
    
    def load_model(self):
        """Load model and preprocessors"""
        try:
            self.model = keras.models.load_model(self.model_path)
            self._load_preprocessors()
            logger.info(f"Model loaded from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
    
    def _save_preprocessors(self):
        """Save scaler and encoders"""
        preprocessors = {
            'scaler': self.scaler,
            'label_encoders': self.label_encoders
        }
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(preprocessors, f)
    
    def _load_preprocessors(self):
        """Load scaler and encoders"""
        try:
            with open(self.scaler_path, 'rb') as f:
                preprocessors = pickle.load(f)
                self.scaler = preprocessors['scaler']
                self.label_encoders = preprocessors['label_encoders']
        except Exception as e:
            logger.error(f"Failed to load preprocessors: {e}")
    
    async def update_model(self, new_data: pd.DataFrame):
        """
        Update model with new data (online learning)
        """
        if not self.model:
            raise ValueError("Model not loaded")
        
        # Prepare new data
        X_numeric, X_protocol, X_country, X_asn, y = self._prepare_training_data(new_data)
        
        # Fine-tune on new data with lower learning rate
        self.model.optimizer.learning_rate = 0.0001
        
        history = self.model.fit(
            [X_numeric, X_protocol, X_country, X_asn],
            y,
            epochs=5,
            batch_size=32,
            verbose=0
        )
        
        logger.info(f"Model updated with {len(new_data)} new samples")
        return history.history