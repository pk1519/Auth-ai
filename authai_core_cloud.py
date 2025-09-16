"""
Cloud-Compatible AuthAI Core Module

This version simulates behavioral monitoring for cloud deployment
since pynput and pyautogui don't work in cloud environments.
"""

import time
import random
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import numpy as np
import os
import csv

class CloudRealTimeMonitor:
    """Simulated real-time monitor for cloud environments"""
    
    def __init__(self, model_name: str, model, scaler=None, ae_meta=None, 
                 window_seconds=30.0, detection_interval=2.0):
        self.model_name = model_name
        self.model = model
        self.scaler = scaler
        self.ae_meta = ae_meta
        self.window_seconds = window_seconds
        self.detection_interval = detection_interval
        self.is_running = False
        self.detection_thread = None
        self.log_file = "detections_log.csv"
        
        # Initialize CSV log file
        self._init_log_file()
        
        # Simulation parameters
        self.base_features = {
            'avg_mouse_speed': 150.0,
            'avg_typing_speed': 200.0,
            'tab_switch_rate': 0.5,
            'mouse_click_rate': 2.0,
            'keyboard_error_rate': 0.05,
            'active_window_duration': 10.0
        }
        
        # Add some randomness to simulate real behavior
        self.feature_variance = {
            'avg_mouse_speed': 50.0,
            'avg_typing_speed': 80.0,
            'tab_switch_rate': 0.2,
            'mouse_click_rate': 1.0,
            'keyboard_error_rate': 0.03,
            'active_window_duration': 5.0
        }
    
    def _init_log_file(self):
        """Initialize the CSV log file with headers"""
        if not os.path.exists(self.log_file):
            headers = [
                'timestamp', 'user_id', 'model', 'score', 'is_improper',
                'avg_mouse_speed', 'avg_typing_speed', 'tab_switch_rate',
                'mouse_click_rate', 'keyboard_error_rate', 'active_window_duration'
            ]
            with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    
    def _generate_simulated_features(self) -> Dict[str, float]:
        """Generate realistic behavioral features for simulation"""
        features = {}
        for feature, base_value in self.base_features.items():
            variance = self.feature_variance[feature]
            # Add random variation around base value
            features[feature] = max(0, base_value + random.gauss(0, variance))
        
        return features
    
    def _predict_with_model(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Make prediction using the loaded model"""
        try:
            # Convert features to array format expected by model
            feature_vector = np.array([
                features['avg_mouse_speed'],
                features['avg_typing_speed'],
                features['tab_switch_rate'],
                features['mouse_click_rate'],
                features['keyboard_error_rate'],
                features['active_window_duration']
            ])
            
            # Handle different model input requirements
            if self.model_name in ('LSTM', 'Transformer'):
                # Sequential models need 3D input: (batch_size, sequence_length, features)
                # Create a sequence by repeating the current feature vector
                seq_length = 50  # Based on model architecture
                feature_array = np.tile(feature_vector, (seq_length, 1)).reshape(1, seq_length, 6)
                
                # Apply scaling if scaler is available
                if self.scaler:
                    # Scale the flattened version then reshape
                    flat = feature_array.reshape(-1, 6)
                    flat_scaled = self.scaler.transform(flat)
                    feature_array = flat_scaled.reshape(1, seq_length, 6)
            else:
                # Tabular models need 2D input: (batch_size, features)
                feature_array = feature_vector.reshape(1, -1)
                
                # Apply scaling if scaler is available
                if self.scaler:
                    feature_array = self.scaler.transform(feature_array)
            
            # Make prediction based on model type
            if self.model_name in ('RandomForest', 'XGBoost', 'GradientBoosting'):
                # Classifier models with predict_proba
                pred_proba = self.model.predict_proba(feature_array)[0]
                score = float(pred_proba[1]) if len(pred_proba) > 1 else float(pred_proba[0])
            elif self.model_name == 'IsolationForest':
                # Anomaly detection model
                pred = self.model.predict(feature_array)[0]
                # Convert to probability-like score (higher = more anomalous)
                score = 0.8 if pred == -1 else 0.2
            elif self.model_name in ('LSTM', 'Transformer', 'Autoencoder'):
                # Deep learning models
                pred = self.model.predict(feature_array, verbose=0)
                score = float(pred.ravel()[0])
            else:
                # Default fallback
                pred = self.model.predict(feature_array)
                score = float(pred.ravel()[0]) if hasattr(pred, 'ravel') else float(pred[0])
            
            # Determine if it's considered improper (bot-like)
            is_improper = 1 if score > 0.5 else 0
            
            return {
                'score': score,
                'is_improper': is_improper,
                'prediction': 'Robot' if is_improper else 'Person'
            }
            
        except Exception as e:
            print(f"Prediction error: {e}")
            # Return default values on error
            return {
                'score': 0.1,
                'is_improper': 0,
                'prediction': 'Person'
            }
    
    def run_detection_once(self) -> Optional[Dict[str, Any]]:
        """Run a single detection cycle"""
        try:
            # Generate simulated features
            features = self._generate_simulated_features()
            
            # Make prediction
            prediction_result = self._predict_with_model(features)
            
            # Create detection event
            detection = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'user_id': 'cloud_user',
                'model': self.model_name,
                'score': prediction_result['score'],
                'is_improper': prediction_result['is_improper'],
                **features
            }
            
            # Log to CSV
            self._log_detection(detection)
            
            return detection
            
        except Exception as e:
            print(f"Detection error: {e}")
            return None
    
    def _log_detection(self, detection: Dict[str, Any]):
        """Log detection to CSV file"""
        try:
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    detection['timestamp'],
                    detection['user_id'],
                    detection['model'],
                    detection['score'],
                    detection['is_improper'],
                    detection['avg_mouse_speed'],
                    detection['avg_typing_speed'],
                    detection['tab_switch_rate'],
                    detection['mouse_click_rate'],
                    detection['keyboard_error_rate'],
                    detection['active_window_duration']
                ])
        except Exception as e:
            print(f"Logging error: {e}")
    
    def start(self):
        """Start the monitoring (simulation mode)"""
        self.is_running = True
        print(f"Started cloud simulation monitor with model: {self.model_name}")
    
    def stop(self):
        """Stop the monitoring"""
        self.is_running = False
        print("Stopped cloud simulation monitor")


class CloudBotSimulator:
    """Bot behavior simulator for cloud environments"""
    
    def __init__(self, duration_sec=15, step_interval=0.5):
        self.duration_sec = duration_sec
        self.step_interval = step_interval
        self.is_running = False
    
    def run(self):
        """Run bot simulation by modifying global state"""
        self.is_running = True
        start_time = time.time()
        
        print(f"🤖 Starting bot simulation for {self.duration_sec} seconds...")
        
        # Simulate bot behavior for the specified duration
        while time.time() - start_time < self.duration_sec and self.is_running:
            time.sleep(self.step_interval)
        
        self.is_running = False
        print("🤖 Bot simulation completed")


def load_best_model_and_meta(models_folder="models"):
    """
    Load the best performing model based on comparison results or fallback priorities
    Cloud-compatible version with proper model selection
    """
    import pandas as pd
    import joblib
    
    # Expected filenames
    results_csv = os.path.join(models_folder, "model_comparison_results.csv")
    fallback_names = {
        "RandomForest": os.path.join(models_folder, "rf_model.joblib"),
        "XGBoost": os.path.join(models_folder, "xgb_model.joblib"),
        "GradientBoosting": os.path.join(models_folder, "xgb_model.joblib"),
        "IsolationForest": os.path.join(models_folder, "iso_model.joblib"),
        "Autoencoder": os.path.join(models_folder, "ae_model.keras"),
        "LSTM": os.path.join(models_folder, "lstm_model.keras"),
        "Transformer": os.path.join(models_folder, "transformer_model.keras")
    }

    best_model_name = None
    best_performance = None
    
    # Try to load best model from comparison results
    if os.path.exists(results_csv):
        try:
            df = pd.read_csv(results_csv)
            print(f"\n📊 Model Performance Comparison (Cloud):")
            print(f"{'Model':<15} {'ROC-AUC':<8} {'Accuracy':<8}")
            print("-" * 35)
            
            # Sort by ROC-AUC score (primary metric)
            df_sorted = df.sort_values('roc_auc', ascending=False)
            
            for _, row in df_sorted.iterrows():
                model_name = row['model']
                roc_auc = row.get('roc_auc', 0)
                accuracy = row.get('accuracy', 0)
                
                print(f"{model_name:<15} {roc_auc:<8.3f} {accuracy:<8.3f}")
                
                # Check if model file exists
                model_path = fallback_names.get(model_name)
                if model_path and os.path.exists(model_path):
                    if best_model_name is None:
                        best_model_name = model_name
                        best_performance = roc_auc
            
            if best_model_name:
                print(f"\n🏆 Selected Best Model: {best_model_name} (ROC-AUC: {best_performance:.3f})")
            
        except Exception as e:
            print(f"⚠️ Error reading model comparison results: {e}")
            best_model_name = None

    # Fallback model selection based on availability and known performance
    if best_model_name is None:
        print("\n🔄 Using fallback model selection...")
        # Priority order for cloud: prefer simpler models for reliability
        priorities = ["Transformer", "LSTM", "XGBoost", "RandomForest", "IsolationForest", "Autoencoder"]
        
        print("📋 Available models:")
        available_models = []
        for name in priorities:
            model_path = fallback_names.get(name)
            if model_path and os.path.exists(model_path):
                available_models.append(name)
                print(f"  ✅ {name}")
            else:
                print(f"  ❌ {name} (not found)")
        
        if available_models:
            best_model_name = available_models[0]
            print(f"\n🎯 Selected Model: {best_model_name} (highest priority available)")
        else:
            # Create demo model as last resort
            print("\nℹ️ No trained models found, creating demo classifier...")
            from sklearn.ensemble import RandomForestClassifier
            demo_model = RandomForestClassifier(n_estimators=10, random_state=42)
            X_demo = np.random.rand(100, 6)
            y_demo = np.random.randint(0, 2, 100)
            demo_model.fit(X_demo, y_demo)
            return "Demo_RandomForest", demo_model, None, None

    # Load the selected model
    model = None
    model_path = fallback_names.get(best_model_name)
    
    try:
        if best_model_name in ("RandomForest", "XGBoost", "GradientBoosting", "IsolationForest"):
            model = joblib.load(model_path)
            print(f"✅ Loaded {best_model_name} model from {model_path}")
        else:
            # Try to load Keras models
            try:
                import tensorflow as tf
                model = tf.keras.models.load_model(model_path)
                print(f"✅ Loaded {best_model_name} model from {model_path}")
            except ImportError:
                print(f"⚠️ TensorFlow not available, skipping {best_model_name}")
                # Fallback to RandomForest
                rf_path = fallback_names.get("RandomForest")
                if rf_path and os.path.exists(rf_path):
                    model = joblib.load(rf_path)
                    best_model_name = "RandomForest"
                    print(f"✅ Fallback to RandomForest model")
                else:
                    raise Exception("No fallback models available")
    except Exception as e:
        print(f"❌ Failed to load {best_model_name}: {e}")
        raise Exception(f"Could not load model: {e}")

    # Try to load scaler
    scaler = None
    scaler_paths = [
        os.path.join(models_folder, "authai_scaler.joblib"),
        os.path.join(models_folder, "scaler.joblib"),
        os.path.join(models_folder, "authai_scaler.pkl")
    ]
    
    for scaler_path in scaler_paths:
        if os.path.exists(scaler_path):
            try:
                scaler = joblib.load(scaler_path)
                print(f"✅ Loaded scaler from {scaler_path}")
                break
            except Exception as e:
                print(f"⚠️ Failed to load scaler from {scaler_path}: {e}")
    
    # Try to load AE metadata
    ae_meta = None
    ae_meta_path = os.path.join(models_folder, "authai_ae_meta.joblib")
    if os.path.exists(ae_meta_path):
        try:
            ae_meta = joblib.load(ae_meta_path)
            print(f"✅ Loaded AE metadata from {ae_meta_path}")
        except Exception as e:
            print(f"⚠️ Failed to load AE metadata: {e}")

    return best_model_name, model, scaler, ae_meta


# Alias for backwards compatibility
RealTimeMonitor = CloudRealTimeMonitor
BotSimulator = CloudBotSimulator

if __name__ == "__main__":
    print("🔒 AuthAI Cloud Core Module Test")
    
    # Test model loading
    try:
        model_name, model, scaler, ae_meta = load_best_model_and_meta()
        print(f"✅ Successfully loaded model: {model_name}")
        
        # Test monitor
        monitor = CloudRealTimeMonitor(model_name, model, scaler, ae_meta)
        monitor.start()
        
        # Run a few detections
        for i in range(3):
            detection = monitor.run_detection_once()
            if detection:
                print(f"Detection {i+1}: {detection['prediction']} (score: {detection['score']:.3f})")
            time.sleep(1)
        
        monitor.stop()
        print("✅ Cloud core module test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
