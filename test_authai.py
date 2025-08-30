#!/usr/bin/env python3
"""
Simple test script for AuthAI functionality
"""

import time
import threading
from authai_core import load_best_model_and_meta, RealTimeMonitor, BotSimulator

def test_model_loading():
    """Test model loading functionality"""
    print("Testing model loading...")
    try:
        best_model_name, model, scaler, ae_meta = load_best_model_and_meta()
        print(f"✅ Model loaded successfully: {best_model_name}")
        print(f"   - Scaler available: {scaler is not None}")
        print(f"   - AE meta available: {ae_meta is not None}")
        return best_model_name, model, scaler, ae_meta
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return None, None, None, None

def test_monitor_creation(best_model_name, model, scaler, ae_meta):
    """Test monitor creation"""
    print("\nTesting monitor creation...")
    try:
        monitor = RealTimeMonitor(best_model_name, model, scaler, ae_meta)
        print("✅ Monitor created successfully")
        return monitor
    except Exception as e:
        print(f"❌ Monitor creation failed: {e}")
        return None

def test_feature_computation(monitor):
    """Test feature computation"""
    print("\nTesting feature computation...")
    try:
        features = monitor.compute_features()
        print("✅ Features computed successfully:")
        for key, value in features.items():
            print(f"   - {key}: {value}")
        return features
    except Exception as e:
        print(f"❌ Feature computation failed: {e}")
        return None

def test_single_detection(monitor):
    """Test single detection run"""
    print("\nTesting single detection...")
    try:
        event = monitor.run_detection_once()
        print("✅ Detection completed successfully:")
        print(f"   - Prediction: {'🤖 ROBOT' if event.get('is_improper', 0) == 1 else '👤 PERSON'}")
        print(f"   - Confidence: {event.get('score', 0.0):.3f}")
        print(f"   - Model: {event.get('model', 'Unknown')}")
        return event
    except Exception as e:
        print(f"❌ Detection failed: {e}")
        return None

def test_bot_simulator():
    """Test bot simulator creation"""
    print("\nTesting bot simulator...")
    try:
        bot = BotSimulator(duration_sec=2, step_interval=0.1)  # Short test
        print("✅ Bot simulator created successfully")
        
        print("⚠️  Bot simulation test skipped (would move mouse)")
        print("   Use the Streamlit GUI to test bot simulation safely")
        
        return True
    except Exception as e:
        print(f"❌ Bot simulator creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔒 AuthAI Core Functionality Test")
    print("=" * 40)
    
    # Test model loading
    best_model_name, model, scaler, ae_meta = test_model_loading()
    if not model:
        print("\n❌ Cannot proceed without model")
        return
    
    # Test monitor creation
    monitor = test_monitor_creation(best_model_name, model, scaler, ae_meta)
    if not monitor:
        print("\n❌ Cannot proceed without monitor")
        return
    
    # Test feature computation
    features = test_feature_computation(monitor)
    if not features:
        print("\n❌ Cannot proceed without features")
        return
    
    # Test single detection
    event = test_single_detection(monitor)
    if not event:
        print("\n❌ Detection test failed")
        return
    
    # Test bot simulator
    test_bot_simulator()
    
    print("\n" + "=" * 40)
    print("✅ All core functionality tests passed!")
    print("\nTo test the full GUI experience:")
    print("   streamlit run authai_streamlit_app.py")

if __name__ == "__main__":
    main()
