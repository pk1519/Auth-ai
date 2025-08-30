"""
Test Script for Enhanced Behavior Simulator System

This script demonstrates the enhanced behavior simulation system with:
- Realistic human-like behavior profiles
- Smooth mouse movements using Bezier curves
- Natural typing patterns with errors and corrections
- Controlled variability testing
- Dataset replay functionality
- Comprehensive logging and analytics

All behavior is clearly labeled as simulated for testing purposes.
"""

import time
import random
from datetime import datetime
from enhanced_behavior_simulator import (
    EnhancedBehaviorSimulator, SimulatorMode, create_behavior_simulator
)
from detection_feedback_system import create_detection_feedback_system

def demo_basic_functionality():
    """Demonstrate basic enhanced simulator functionality"""
    print("\n" + "="*60)
    print("🧪 ENHANCED BEHAVIOR SIMULATOR DEMONSTRATION")
    print("="*60)
    
    # Test different simulation modes
    test_modes = [
        (SimulatorMode.BASIC_VARIABILITY, "casual_user"),
        (SimulatorMode.INTERMEDIATE_VARIABILITY, "fast_typer"),
        (SimulatorMode.HIGH_VARIABILITY, "careful_user"),
        (SimulatorMode.DATASET_REPLAY, "mobile_style")
    ]
    
    feedback_system = create_detection_feedback_system('test_enhanced_log.csv')
    
    for mode, profile in test_modes:
        print(f"\n🔧 Testing: {mode.value} mode with {profile} profile")
        print("-" * 50)
        
        # Create simulator
        simulator = create_behavior_simulator(mode.value, profile)
        
        # Set up detection callback
        def test_detection_callback(is_detected, detection_data):
            # Process through feedback system
            feedback_system.process_detection(
                detection_data,
                source_type='simulation',
                simulation_profile=profile,
                simulation_mode=mode.value
            )
            
            # Console output
            status = "🚨 DETECTED" if is_detected else "✅ PASSED"
            score = detection_data.get('score', 0.0) if detection_data else 0.0
            print(f"  📊 Detection Result: {status} (Score: {score:.3f})")
        
        simulator.set_detection_callback(test_detection_callback)
        
        # Run short simulation
        print(f"  ▶️ Running 10-second simulation...")
        
        # Simulate detection data (since we're not running full AuthAI monitor)
        def simulate_detection():
            # Mock detection data based on profile characteristics
            mock_data = {
                'user_id': f'test_user_{profile}',
                'session_id': f'test_session_{int(time.time())}',
                'score': random.uniform(0.1, 0.9),
                'is_improper': 1 if random.random() < 0.3 else 0,  # 30% chance of detection
                'model': 'TestModel',
                'avg_mouse_speed': random.uniform(100, 600),
                'avg_typing_speed': random.uniform(120, 800),
                'tab_switch_rate': random.uniform(0, 4),
                'mouse_click_rate': random.uniform(5, 50),
                'keyboard_error_rate': random.uniform(0, 0.15),
                'active_window_duration': random.uniform(10, 120)
            }
            
            test_detection_callback(mock_data['is_improper'] == 1, mock_data)
        
        # Simulate detection every 2 seconds during simulation
        import threading
        def detection_thread():
            for _ in range(5):  # 5 detections over 10 seconds
                time.sleep(2)
                simulate_detection()
        
        detection_t = threading.Thread(target=detection_thread, daemon=True)
        detection_t.start()
        
        # Run actual simulator (but very briefly for demo)
        simulator.run_simulation(duration=10.0)
        
        # Show stats
        stats = simulator.get_simulation_stats()
        if 'current_session' in stats:
            session = stats['current_session']
            print(f"  📈 Session Stats: {session['total_actions']} actions, {session['detections']} detections")
        
        time.sleep(1)  # Brief pause between tests

def demo_analytics_system():
    """Demonstrate the analytics and feedback system"""
    print(f"\n📊 ANALYTICS SYSTEM DEMONSTRATION")
    print("-" * 50)
    
    feedback_system = create_detection_feedback_system('test_enhanced_log.csv')
    
    # Generate sample detection events
    sample_events = [
        # Real user events (mostly human)
        {
            'user_id': 'real_user_1',
            'session_id': 'real_session_001',
            'is_improper': 0,
            'score': 0.15,
            'model': 'RandomForest',
            'avg_mouse_speed': 280,
            'avg_typing_speed': 320,
            'tab_switch_rate': 1.8,
            'mouse_click_rate': 18,
            'keyboard_error_rate': 0.04,
            'active_window_duration': 65
        },
        {
            'user_id': 'real_user_2',
            'session_id': 'real_session_002',
            'is_improper': 0,
            'score': 0.25,
            'model': 'Transformer',
            'avg_mouse_speed': 150,
            'avg_typing_speed': 180,
            'tab_switch_rate': 0.8,
            'mouse_click_rate': 12,
            'keyboard_error_rate': 0.02,
            'active_window_duration': 90
        },
        # Simulation events (higher detection rate)
        {
            'user_id': 'sim_casual_1',
            'session_id': 'sim_session_001',
            'is_improper': 1,
            'score': 0.72,
            'model': 'Transformer',
            'avg_mouse_speed': 450,
            'avg_typing_speed': 680,
            'tab_switch_rate': 3.2,
            'mouse_click_rate': 35,
            'keyboard_error_rate': 0.08,
            'active_window_duration': 45
        },
        {
            'user_id': 'sim_fast_1',
            'session_id': 'sim_session_002',
            'is_improper': 1,
            'score': 0.89,
            'model': 'XGBoost',
            'avg_mouse_speed': 620,
            'avg_typing_speed': 950,
            'tab_switch_rate': 4.5,
            'mouse_click_rate': 55,
            'keyboard_error_rate': 0.12,
            'active_window_duration': 30
        }
    ]
    
    print("📝 Processing sample detection events...")
    for i, event in enumerate(sample_events):
        if i < 2:
            # Real user events
            feedback_system.process_detection(event, source_type='real_user')
        else:
            # Simulation events
            profile = 'casual_user' if i == 2 else 'fast_typer'
            mode = 'intermediate_variability'
            feedback_system.process_detection(
                event, 
                source_type='simulation',
                simulation_profile=profile,
                simulation_mode=mode
            )
        time.sleep(0.5)
    
    # Get real-time stats
    print("\n📊 Real-time Statistics:")
    stats = feedback_system.get_real_time_stats()
    for key, value in stats.items():
        if key != 'recent_events':
            print(f"  {key}: {value}")
    
    # Generate dashboard
    print("\n📋 Generating Performance Dashboard...")
    dashboard = feedback_system.generate_performance_dashboard()
    
    print(f"System Health: {dashboard['system_health']['status']} "
          f"(Score: {dashboard['system_health']['score']}/100)")
    
    if dashboard['system_health']['issues']:
        print("🚨 Issues:")
        for issue in dashboard['system_health']['issues']:
            print(f"  • {issue}")
    
    if dashboard['system_health']['warnings']:
        print("⚠️ Warnings:")
        for warning in dashboard['system_health']['warnings']:
            print(f"  • {warning}")
    
    # Export report
    print("\n📄 Exporting analysis report...")
    report_file = feedback_system.export_analysis_report('demo_analysis_report.json')
    if report_file:
        print(f"Report saved to: {report_file}")

def demo_profile_comparison():
    """Demonstrate different behavior profile characteristics"""
    print(f"\n👥 BEHAVIOR PROFILE COMPARISON")
    print("-" * 50)
    
    profiles = ['casual_user', 'fast_typer', 'careful_user', 'mobile_style']
    
    for profile in profiles:
        print(f"\n🔍 Profile: {profile.replace('_', ' ').title()}")
        
        simulator = create_behavior_simulator('basic_variability', profile)
        
        # Get profile characteristics
        behavior_profile = simulator.current_profile
        print(f"  • Typing Speed: {behavior_profile.avg_typing_speed:.0f} chars/min")
        print(f"  • Mouse Speed Range: {behavior_profile.mouse_speed_range[0]:.0f}-{behavior_profile.mouse_speed_range[1]:.0f} px/s")
        print(f"  • Click Accuracy: {behavior_profile.click_accuracy:.1%}")
        print(f"  • Error Rate: {behavior_profile.error_rate:.1%}")
        print(f"  • Backspace Probability: {behavior_profile.backspace_probability:.1%}")
        
        # Generate sample timing
        sample_text = "The quick brown fox jumps over the lazy dog"
        intervals = simulator.typing_simulator.get_typing_intervals(sample_text)
        avg_interval = sum(intervals) / len(intervals)
        print(f"  • Average Keystroke Interval: {avg_interval:.3f}s")

def demo_integration_flow():
    """Demonstrate the full integration flow"""
    print(f"\n🔄 FULL SYSTEM INTEGRATION DEMONSTRATION")
    print("-" * 50)
    
    print("1. 🚀 Initializing Enhanced Behavior Simulator...")
    simulator = create_behavior_simulator('high_variability', 'casual_user')
    
    print("2. 📊 Initializing Detection Feedback System...")
    feedback_system = create_detection_feedback_system('integration_test_log.csv')
    
    print("3. 🔗 Connecting simulator to feedback system...")
    def integrated_detection_callback(is_detected, detection_data):
        # This would normally come from the AuthAI monitor
        feedback_system.process_detection(
            detection_data,
            source_type='simulation',
            simulation_profile='casual_user',
            simulation_mode='high_variability'
        )
        
        status = "🚨 DETECTED" if is_detected else "✅ HUMAN-LIKE"
        print(f"  📡 Detection: {status}")
    
    simulator.set_detection_callback(integrated_detection_callback)
    
    print("4. ⚡ Running integrated simulation...")
    
    # Simulate periodic detection checks
    def mock_detection_loop():
        for i in range(6):  # 6 detections over 12 seconds
            time.sleep(2)
            mock_detection = {
                'user_id': 'integrated_test_user',
                'session_id': 'integration_session_001',
                'score': random.uniform(0.1, 0.8),
                'is_improper': 1 if random.random() < 0.4 else 0,  # 40% detection rate
                'model': 'IntegrationTestModel',
                'avg_mouse_speed': random.uniform(200, 400),
                'avg_typing_speed': random.uniform(250, 450),
                'tab_switch_rate': random.uniform(0.5, 2.5),
                'mouse_click_rate': random.uniform(10, 30),
                'keyboard_error_rate': random.uniform(0.02, 0.08),
                'active_window_duration': random.uniform(30, 90)
            }
            integrated_detection_callback(mock_detection['is_improper'] == 1, mock_detection)
    
    # Run both threads
    import threading
    detection_thread = threading.Thread(target=mock_detection_loop, daemon=True)
    detection_thread.start()
    
    simulator.run_simulation(duration=12.0)
    
    print("5. 📈 Generating final statistics...")
    stats = feedback_system.get_real_time_stats()
    print(f"   Total Events: {stats['total_events']}")
    print(f"   Bot Detections: {stats['total_detections']}")
    print(f"   Detection Rate: {stats['overall_detection_rate']:.1f}%")
    
    print("\n✅ Integration demonstration completed!")

def run_comprehensive_demo():
    """Run complete demonstration of the enhanced system"""
    print("🎬 ENHANCED AUTHAI BEHAVIOR SIMULATOR")
    print("🔒 Legitimate Testing & Evaluation System")
    print("="*60)
    print("📝 All simulated behavior is clearly labeled and logged")
    print("🎯 Designed for security system testing, not evasion")
    print("="*60)
    
    try:
        # Demo 1: Basic functionality
        demo_basic_functionality()
        
        time.sleep(2)
        
        # Demo 2: Analytics system
        demo_analytics_system()
        
        time.sleep(2)
        
        # Demo 3: Profile comparison
        demo_profile_comparison()
        
        time.sleep(2)
        
        # Demo 4: Integration flow
        demo_integration_flow()
        
        print(f"\n🎉 DEMONSTRATION COMPLETE!")
        print("="*60)
        print("📁 Log files created:")
        print("  • test_enhanced_log.csv - Detection events")
        print("  • integration_test_log.csv - Integration test data")
        print("  • behavior_simulation_log.json - Simulation sessions")
        print("  • demo_analysis_report.json - Analytics report")
        
        print(f"\n🔍 To view full analytics:")
        print("  1. Run the Streamlit app: streamlit run authai_streamlit_app.py")
        print("  2. Navigate to the Analytics tab")
        print("  3. Explore the comprehensive dashboards and reports")
        
        print(f"\n🧪 For testing with the enhanced simulator:")
        print("  1. Select 'Enhanced Behavior Simulator' in the web interface")
        print("  2. Choose simulation mode and behavior profile")
        print("  3. Run simulations and observe detection patterns")
        print("  4. Use analytics to evaluate system performance")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        print("Make sure all required modules are available")

if __name__ == "__main__":
    try:
        run_comprehensive_demo()
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Please ensure all dependencies are installed and modules are available")
