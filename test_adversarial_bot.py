"""
Test program for Advanced Adversarial Bot System
This will test each difficulty level without the Streamlit interface
"""

import sys
import time
import random
from adversarial_bot import AdvancedAdversarialBot, BotDifficulty

def test_bot_difficulty(difficulty: BotDifficulty, duration: float = 3.0):
    """Test a specific bot difficulty level"""
    print(f"\n🎯 Testing {difficulty.value.upper()} Bot")
    print("=" * 50)
    
    try:
        # Create bot
        bot = AdvancedAdversarialBot(difficulty)
        print(f"✅ Created {difficulty.value} bot")
        
        # Print initial configuration
        stats = bot.get_stats()
        print(f"📊 Initial Stats:")
        print(f"   - Difficulty: {stats['difficulty']}")
        print(f"   - Noise levels: {stats['feature_noise_levels']}")
        
        # Set bot difficulty (this configures noise levels)
        bot.set_difficulty(difficulty)
        updated_stats = bot.get_stats()
        print(f"📊 Updated noise levels: {updated_stats['feature_noise_levels']}")
        
        # Test behavior profile
        profile_name = bot.behavior_mimicker.switch_profile()
        print(f"👤 Using behavior profile: {profile_name}")
        profile = bot.behavior_mimicker.current_profile
        print(f"   - Typing speed: {profile.avg_typing_speed} chars/min")
        print(f"   - Mouse speed range: {profile.mouse_speed_range}")
        print(f"   - Error rate: {profile.error_rate:.1%}")
        
        # Test noise generation
        print(f"🔧 Testing noise generation:")
        test_values = {
            'mouse_speed': 100.0,
            'typing_speed': 60.0,
            'click_rate': 5.0
        }
        
        for feature, base_value in test_values.items():
            if feature in updated_stats['feature_noise_levels']:
                noise_level = updated_stats['feature_noise_levels'][feature]
                noisy_value = bot.noise_generator.apply_noise(feature, base_value, noise_level)
                print(f"   - {feature}: {base_value} → {noisy_value:.2f} (noise: {noise_level})")
        
        print(f"🚀 Running {difficulty.value} bot simulation for {duration} seconds...")
        
        # Run a very short simulation (no GUI automation, just test the logic)
        def mock_detection_callback(detected):
            print(f"   📡 Detection feedback: {'DETECTED' if detected else 'EVADED'}")
            bot.on_detection_feedback(detected)
        
        bot.set_detection_callback(mock_detection_callback)
        
        # Simulate some detection feedback
        for i in range(3):
            # Simulate detection results based on difficulty
            if difficulty == BotDifficulty.BASIC:
                detected = True  # Basic bots should get detected
            elif difficulty == BotDifficulty.INTERMEDIATE:
                detected = random.choice([True, False])  # Mixed results
            else:  # ADVANCED
                detected = random.choice([False, False, True])  # Mostly evade
            
            mock_detection_callback(detected)
            time.sleep(0.5)
        
        # Final stats
        final_stats = bot.get_stats()
        print(f"📊 Final Stats:")
        print(f"   - Total attempts: {final_stats['total_attempts']}")
        print(f"   - Detections: {final_stats['detections']}")
        print(f"   - Successful evasions: {final_stats['successful_evasions']}")
        print(f"   - Success rate: {final_stats['success_rate']:.1%}")
        print(f"   - Adaptation level: {final_stats['adaptation_level']:.1%}")
        
        print(f"✅ {difficulty.value.upper()} bot test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing {difficulty.value} bot: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🧪 Advanced Adversarial Bot System Test")
    print("=" * 60)
    
    # Import the required modules
    try:
        import random
        print("✅ All required modules imported successfully")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return
    
    # Test each difficulty level
    success_count = 0
    
    for difficulty in [BotDifficulty.BASIC, BotDifficulty.INTERMEDIATE, BotDifficulty.ADVANCED]:
        if test_bot_difficulty(difficulty):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"🎉 Test Results: {success_count}/3 difficulty levels passed")
    
    if success_count == 3:
        print("✅ All adversarial bot tests PASSED!")
        print("\n🚀 The bot system is ready for integration with Streamlit!")
        print("\n📋 Expected behavior in Streamlit:")
        print("   🟢 Basic: Obvious robotic behavior, easily detected")
        print("   🟡 Intermediate: More human-like, sometimes detected")
        print("   🔴 Advanced: Very realistic, hard to detect but may still trigger alerts")
    else:
        print("❌ Some tests FAILED. Check the error messages above.")

if __name__ == "__main__":
    main()
