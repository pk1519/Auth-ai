#!/usr/bin/env python3
"""Test script to verify model selection and prediction"""

from authai_core_cloud import load_best_model_and_meta, RealTimeMonitor
import numpy as np

def test_model():
    """Test the model loading and prediction"""
    try:
        # Load the best model
        model_name, model, scaler, ae_meta = load_best_model_and_meta()
        print(f"✅ Model loaded: {model_name}")
        print(f"   Model type: {type(model)}")
        print(f"   Scaler available: {scaler is not None}")
        print(f"   AE meta available: {ae_meta is not None}")
        
        # Test prediction
        monitor = RealTimeMonitor(model_name, model, scaler, ae_meta)
        detection = monitor.run_detection_once()
        
        if detection:
            print("\n🎯 Test prediction successful:")
            print(f"   Score: {detection['score']:.3f}")
            print(f"   Is Improper: {'Robot' if detection['is_improper'] else 'Person'}")
            print(f"   Model Used: {detection['model']}")
            print(f"   Mouse Speed: {detection['avg_mouse_speed']:.1f} px/s")
            print(f"   Typing Speed: {detection['avg_typing_speed']:.1f} keys/min")
            return True
        else:
            print("❌ Detection failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_model()
    print(f"\n{'✅ Test PASSED' if success else '❌ Test FAILED'}")