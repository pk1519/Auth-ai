"""
Real-Time AuthAI Streamlit GUI

Features:
- Real-time behavioral biometrics monitoring
- Live feature display and predictions
- Bot simulation with button trigger
- Time-series plotting of predictions
- Model information display
- Confidence scoring
"""

import streamlit as st
import time
import threading
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from collections import deque
import queue
import os

# Import authentication modules
try:
    from user_auth import (
        init_session_state, is_authenticated, get_current_user, 
        logout_user_session, require_authentication
    )
    from auth_pages import show_auth_page
except ImportError:
    st.error("Could not import authentication modules. Make sure user_auth.py and auth_pages.py are in the same directory.")
    st.stop()

# Import our custom modules
try:
    from authai_core import load_best_model_and_meta, RealTimeMonitor, BotSimulator
except ImportError:
    st.error("Could not import authai_core module. Make sure authai_core.py is in the same directory.")
    st.stop()

# Import enhanced behavior simulator
try:
    from enhanced_behavior_simulator import (
        EnhancedBehaviorSimulator, SimulatorMode, BehaviorProfile, create_behavior_simulator
    )
    from detection_feedback_system import (
        EnhancedDetectionFeedback, create_detection_feedback_system
    )
except ImportError:
    st.error("Could not import enhanced simulator modules. Make sure enhanced_behavior_simulator.py and detection_feedback_system.py are available.")
    EnhancedBehaviorSimulator = None
    SimulatorMode = None

# Configure Streamlit page
st.set_page_config(
    page_title="AuthAI Real-Time Monitor",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'monitor' not in st.session_state:
    st.session_state.monitor = None
if 'monitor_running' not in st.session_state:
    st.session_state.monitor_running = False
if 'bot_simulator' not in st.session_state:
    st.session_state.bot_simulator = None
if 'bot_running' not in st.session_state:
    st.session_state.bot_running = False

# Enhanced behavior simulator session state
if 'enhanced_simulator' not in st.session_state:
    st.session_state.enhanced_simulator = None
if 'enhanced_simulator_running' not in st.session_state:
    st.session_state.enhanced_simulator_running = False
if 'simulator_mode' not in st.session_state:
    st.session_state.simulator_mode = 'basic_variability'
if 'simulator_profile' not in st.session_state:
    st.session_state.simulator_profile = 'casual_user'
if 'detection_feedback_system' not in st.session_state:
    st.session_state.detection_feedback_system = None

if 'detection_history' not in st.session_state:
    st.session_state.detection_history = deque(maxlen=100)
if 'feature_history' not in st.session_state:
    st.session_state.feature_history = deque(maxlen=100)
if 'model_info' not in st.session_state:
    st.session_state.model_info = None
if 'last_detection' not in st.session_state:
    st.session_state.last_detection = None
if 'bot_detected' not in st.session_state:
    st.session_state.bot_detected = False
if 'bot_alert_count' not in st.session_state:
    st.session_state.bot_alert_count = 0
if 'last_bot_detection_time' not in st.session_state:
    st.session_state.last_bot_detection_time = None

# Custom CSS for styling
st.markdown("""
<style>
.metric-container {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 5px solid #1f77b4;
    margin-bottom: 1rem;
}
.alert-container {
    background-color: #ffebee;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 5px solid #f44336;
    margin-bottom: 1rem;
}
.success-container {
    background-color: #e8f5e8;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 5px solid #4caf50;
    margin-bottom: 1rem;
}
.feature-box {
    background-color: #fafafa;
    padding: 0.8rem;
    border-radius: 0.3rem;
    border: 1px solid #e0e0e0;
    text-align: center;
}
.bot-alert {
    background-color: #f8d7da;
    color: #721c24;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 2px solid #f5c6cb;
    text-align: center;
    animation: pulse 1s infinite;
    font-size: 1.2rem;
    font-weight: bold;
    margin: 1rem 0;
}
.robot-icon {
    font-size: 3rem;
    animation: bounce 1s infinite;
    text-align: center;
    margin: 0.5rem 0;
}
.human-status {
    background-color: #d1edff;
    color: #0056b3;
    padding: 0.5rem;
    border-radius: 0.3rem;
    text-align: center;
    font-weight: bold;
}
@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}
@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}
</style>
""", unsafe_allow_html=True)

def initialize_monitor():
    """Initialize the AuthAI monitor"""
    try:
        if st.session_state.monitor is None:
            with st.spinner("Loading AuthAI model..."):
                best_model_name, model, scaler, ae_meta = load_best_model_and_meta()
                st.session_state.model_info = {
                    'name': best_model_name,
                    'scaler_available': scaler is not None,
                    'ae_meta_available': ae_meta is not None
                }
                # Create monitor with shorter intervals for GUI responsiveness
                monitor = RealTimeMonitor(
                    best_model_name, model, scaler, ae_meta,
                    window_seconds=30.0,
                    detection_interval=2.0  # Faster updates for GUI
                )
                st.session_state.monitor = monitor
                return True
    except Exception as e:
        st.error(f"Failed to initialize monitor: {str(e)}")
        return False
    return True

def start_monitor():
    """Start the real-time monitor"""
    if st.session_state.monitor and not st.session_state.monitor_running:
        try:
            st.session_state.monitor.start()
            st.session_state.monitor_running = True
            return True
        except Exception as e:
            st.error(f"Failed to start monitor: {str(e)}")
            return False
    return True

def stop_monitor():
    """Stop the real-time monitor"""
    if st.session_state.monitor and st.session_state.monitor_running:
        try:
            st.session_state.monitor.stop()
            st.session_state.monitor_running = False
            return True
        except Exception as e:
            st.error(f"Failed to stop monitor: {str(e)}")
            return False
    return True

def run_bot_simulation():
    """Run bot simulation in a separate thread"""
    def bot_thread():
        try:
            st.session_state.bot_running = True
            bot_simulator = BotSimulator(duration_sec=15, step_interval=0.02)
            bot_simulator.run()
        except Exception as e:
            st.error(f"Bot simulation error: {str(e)}")
        finally:
            st.session_state.bot_running = False
    
    if not st.session_state.bot_running:
        threading.Thread(target=bot_thread, daemon=True).start()
        return True
    return False

def show_bot_alert(detection):
    """Show bot detection alert with visual indicators"""
    # Update bot detection state
    st.session_state.bot_detected = True
    st.session_state.bot_alert_count += 1
    st.session_state.last_bot_detection_time = datetime.now()
    
    # Show animated robot icon
    st.markdown('<div class="robot-icon">🤖</div>', unsafe_allow_html=True)
    
    # Show alert message
    score = detection.get('score', 0.0)
    user_id = detection.get('user_id', 'Unknown')
    model = detection.get('model', 'Unknown')
    
    alert_message = f"""
    <div class="bot-alert">
        ⚠️ <strong>BOT DETECTED!</strong> ⚠️<br>
        User: {user_id} has been flagged as suspicious<br>
        Confidence Score: {float(score):.3f}<br>
        Model: {model}<br>
        Alert #{st.session_state.bot_alert_count}
    </div>
    """
    
    st.markdown(alert_message, unsafe_allow_html=True)
    
    # Show balloons for dramatic effect
    st.error("🚨 SECURITY ALERT: Automated behavior detected!")
    
    # Play a sound notification (if browser supports it)
    st.markdown("""
    <script>
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance('Bot detected! Security alert!');
        utterance.rate = 1.2;
        utterance.pitch = 1.5;
        speechSynthesis.speak(utterance);
    }
    </script>
    """, unsafe_allow_html=True)

def show_human_status():
    """Show human status indicator"""
    st.session_state.bot_detected = False
    
    st.markdown("""
    <div class="human-status">
        👤 Human Behavior Confirmed
    </div>
    """, unsafe_allow_html=True)

def get_latest_detection():
    """Get the latest detection from the monitor"""
    if st.session_state.monitor and st.session_state.monitor_running:
        try:
            # Run detection once and return result
            event = st.session_state.monitor.run_detection_once()
            if event:
                st.session_state.last_detection = event
                st.session_state.detection_history.append(event)
                
                # Store features separately for plotting
                features = {
                    'timestamp': datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')),
                    'avg_mouse_speed': event['avg_mouse_speed'],
                    'avg_typing_speed': event['avg_typing_speed'],
                    'tab_switch_rate': event['tab_switch_rate'],
                    'mouse_click_rate': event['mouse_click_rate'],
                    'keyboard_error_rate': event['keyboard_error_rate'],
                    'active_window_duration': event['active_window_duration']
                }
                st.session_state.feature_history.append(features)
                
            return event
        except Exception as e:
            st.error(f"Detection error: {str(e)}")
            return None
    return None

def create_prediction_chart():
    """Create time-series chart of predictions"""
    if not st.session_state.detection_history:
        return None
    
    # Convert detection history to DataFrame
    df_data = []
    for detection in list(st.session_state.detection_history):
        try:
            timestamp = datetime.fromisoformat(detection['timestamp'].replace('Z', '+00:00'))
            score = detection.get('score', 0.0)
            if score is not None:
                df_data.append({
                    'timestamp': timestamp,
                    'score': float(score),
                    'prediction': 'Robot' if detection.get('is_improper', 0) == 1 else 'Person',
                    'model': detection.get('model', 'Unknown')
                })
        except (ValueError, TypeError, KeyError):
            continue
    
    if not df_data:
        return None
    
    df = pd.DataFrame(df_data)
    
    # Create plotly chart
    fig = go.Figure()
    
    # Add score line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['score'],
        mode='lines+markers',
        name='Confidence Score',
        line=dict(color='#1f77b4', width=2),
        marker=dict(
            color=df['prediction'].map({'Person': '#2ecc71', 'Robot': '#e74c3c'}),
            size=8
        ),
        hovertemplate='<b>%{y:.3f}</b><br>%{x}<br>Prediction: %{marker.color}<extra></extra>'
    ))
    
    # Add threshold line
    fig.add_hline(y=0.5, line_dash="dash", line_color="red", 
                  annotation_text="Bot Threshold (0.5)")
    
    fig.update_layout(
        title="Real-Time Prediction Confidence Over Time",
        xaxis_title="Time",
        yaxis_title="Confidence Score",
        height=400,
        showlegend=True,
        hovermode='x unified'
    )
    
    return fig

def create_feature_charts():
    """Create charts for feature values over time"""
    if not st.session_state.feature_history:
        return []
    
    # Convert feature history to DataFrame
    df_data = []
    for features in list(st.session_state.feature_history):
        df_data.append(features)
    
    if not df_data:
        return []
    
    df = pd.DataFrame(df_data)
    
    charts = []
    feature_names = ['avg_mouse_speed', 'avg_typing_speed', 'tab_switch_rate', 
                    'mouse_click_rate', 'keyboard_error_rate', 'active_window_duration']
    
    for i, feature in enumerate(feature_names):
        if feature in df.columns:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df[feature],
                mode='lines+markers',
                name=feature.replace('_', ' ').title(),
                line=dict(width=2),
                marker=dict(size=6)
            ))
            
            fig.update_layout(
                title=feature.replace('_', ' ').title(),
                xaxis_title="Time",
                yaxis_title="Value",
                height=250,
                showlegend=False
            )
            charts.append(fig)
    
    return charts

def show_user_dashboard():
    """Show user dashboard with logout functionality"""
    # User info in header
    user = get_current_user()
    
    # Auto-initialize system on first load
    if st.session_state.monitor is None:
        with st.spinner("🚀 Auto-initializing AuthAI system with best model..."):
            if initialize_monitor():
                st.success(f"✅ System initialized with model: {st.session_state.model_info['name']}")
                # Auto-start monitoring
                time.sleep(1)
                if start_monitor():
                    st.success("▶️ Monitor started automatically!")
                    time.sleep(2)
                    st.rerun()
    
    # Header with user info and navigation
    header_col1, header_col2 = st.columns([2, 1])
    
    with header_col1:
        st.title("🔒 AuthAI Real-Time Monitor")
        st.markdown(f"**Welcome, {user['username']}!** | Behavioral Biometrics Authentication System")
    
    with header_col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        nav_col1, nav_col2, nav_col3 = st.columns(3)
        
        with nav_col1:
            if st.button("📈 Analytics", key="analytics_btn"):
                st.session_state.page = "analytics"
                st.rerun()
        
        with nav_col2:
            if st.button("👤 Profile", key="profile_btn"):
                st.session_state.page = "profile"
                st.rerun()
        
        with nav_col3:
            if st.button("🚺 Logout", key="logout_btn"):
                logout_user_session()
                st.success("✅ You have been logged out successfully!")
                st.session_state.page = "login"
                st.rerun()

def main():
    """Main Streamlit application"""
    
    # Initialize session state for authentication
    init_session_state()
    
    # Check authentication status
    if not is_authenticated():
        # Show authentication pages
        show_auth_page()
        return
    
    # Show different pages based on session state
    if st.session_state.get('page') == 'profile':
        from auth_pages import show_profile_page
        show_profile_page()
        
        # Back to dashboard button
        if st.button("← Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        return
    
    elif st.session_state.get('page') == 'analytics':
        try:
            from analytics_dashboard import show_analytics_page
            show_analytics_page()
        except ImportError:
            st.error("Analytics dashboard not available. Check analytics_dashboard.py")
        
        # Back to dashboard button
        if st.button("← Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        return
    
    # Show user dashboard
    show_user_dashboard()
    
    # Sidebar controls
    st.sidebar.title("Controls")
    
    # Initialize monitor
    if st.sidebar.button("🚀 Initialize System", key="init_btn"):
        if initialize_monitor():
            st.sidebar.success("System initialized successfully!")
    
    # Monitor controls
    if st.session_state.monitor:
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("▶️ Start Monitor", key="start_btn", disabled=st.session_state.monitor_running):
                if start_monitor():
                    st.sidebar.success("Monitor started!")
                    st.rerun()
        
        with col2:
            if st.button("⏹️ Stop Monitor", key="stop_btn", disabled=not st.session_state.monitor_running):
                if stop_monitor():
                    st.sidebar.success("Monitor stopped!")
                    st.rerun()
    
    # Bot simulation section
    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 Bot Testing")
    
    # Tab selection for bot types
    bot_tab = st.sidebar.radio(
        "Select Testing Mode:",
        ["Basic Bot", "Enhanced Behavior Simulator"],
        key="bot_type_tab"
    )
    
    if bot_tab == "Basic Bot":
        # Original basic bot
        if st.sidebar.button("🤖 Run Basic Bot", key="basic_bot_btn", disabled=st.session_state.bot_running):
            if st.session_state.monitor and st.session_state.monitor_running:
                if run_bot_simulation():
                    st.sidebar.warning("Basic bot running for 15 seconds...")
            else:
                st.sidebar.error("Start monitor first!")
        
        if st.session_state.bot_running:
            st.sidebar.warning("🤖 Basic bot simulation in progress...")
    
    else:  # Enhanced Behavior Simulator
        if EnhancedBehaviorSimulator and SimulatorMode:
            st.sidebar.info("🧪 Enhanced Behavior Simulator: Available")
            
            # Initialize detection feedback system
            if st.session_state.detection_feedback_system is None:
                st.session_state.detection_feedback_system = create_detection_feedback_system()
            
            # Simulation mode selection
            mode_options = {
                "🟢 Basic Variability": "basic_variability",
                "🟡 Intermediate Variability": "intermediate_variability", 
                "🔴 High Variability": "high_variability",
                "📊 Dataset Replay": "dataset_replay"
            }
            
            selected_mode = st.sidebar.selectbox(
                "Simulation Mode:",
                list(mode_options.keys()),
                key="simulation_mode_select"
            )
            
            mode_value = mode_options[selected_mode]
            
            # Behavior profile selection
            profile_options = {
                "👤 Casual User": "casual_user",
                "⚡ Fast Typer": "fast_typer",
                "🎯 Careful User": "careful_user",
                "📱 Mobile-Style User": "mobile_style"
            }
            
            selected_profile = st.sidebar.selectbox(
                "Behavior Profile:",
                list(profile_options.keys()),
                key="behavior_profile_select"
            )
            
            profile_value = profile_options[selected_profile]
            
            # Initialize enhanced simulator if needed
            if (st.session_state.enhanced_simulator is None or 
                st.session_state.simulator_mode != mode_value or
                st.session_state.simulator_profile != profile_value):
                
                st.sidebar.info(f"🔄 Initializing simulator ({mode_value} / {profile_value})...")
                
                st.session_state.enhanced_simulator = create_behavior_simulator(mode_value, profile_value)
                st.session_state.simulator_mode = mode_value
                st.session_state.simulator_profile = profile_value
                
                # Set up detection feedback integration
                def detection_feedback(is_detected, detection_data):
                    if st.session_state.detection_feedback_system:
                        st.session_state.detection_feedback_system.process_detection(
                            detection_data, 
                            source_type='simulation',
                            simulation_profile=profile_value,
                            simulation_mode=mode_value
                        )
                
                st.session_state.enhanced_simulator.set_detection_callback(detection_feedback)
                
                st.sidebar.success(f"✅ Simulator ready!")
            
            # Simulation duration setting
            duration = st.sidebar.slider(
                "Simulation Duration (seconds):",
                min_value=10,
                max_value=120,
                value=30,
                step=5,
                key="sim_duration"
            )
            
            # Simulation control buttons
            col1, col2 = st.sidebar.columns(2)
            
            with col1:
                if st.button(
                    "🚀 Run Simulation", 
                    key="enhanced_sim_run", 
                    disabled=st.session_state.enhanced_simulator_running
                ):
                    if st.session_state.monitor and st.session_state.monitor_running:
                        if st.session_state.enhanced_simulator:
                            def enhanced_sim_thread():
                                try:
                                    st.session_state.enhanced_simulator_running = True
                                    st.session_state.enhanced_simulator.run_simulation(duration=duration)
                                except Exception as e:
                                    st.error(f"Enhanced simulator error: {str(e)}")
                                finally:
                                    st.session_state.enhanced_simulator_running = False
                            
                            threading.Thread(target=enhanced_sim_thread, daemon=True).start()
                            st.sidebar.success(f"Running {selected_mode} simulation...")
                    else:
                        st.sidebar.error("Start monitor first!")
            
            with col2:
                if st.button(
                    "⏹️ Stop Simulation", 
                    key="enhanced_sim_stop", 
                    disabled=not st.session_state.enhanced_simulator_running
                ):
                    if st.session_state.enhanced_simulator:
                        st.session_state.enhanced_simulator.stop_simulation()
                        st.session_state.enhanced_simulator_running = False
                        st.sidebar.info("Simulation stopped")
            
            # Simulation status and statistics
            if st.session_state.enhanced_simulator_running:
                st.sidebar.warning(f"🤖 {selected_mode.replace('_', ' ').title()} simulation active...")
            
            # Show simulation statistics
            if st.session_state.enhanced_simulator:
                stats = st.session_state.enhanced_simulator.get_simulation_stats()
                
                st.sidebar.markdown("**Simulation Statistics:**")
                if 'current_session' in stats:
                    session = stats['current_session']
                    st.sidebar.metric("Total Actions", session['total_actions'])
                    st.sidebar.metric("Detections", session['detections'])
                    
                    if session['total_actions'] > 0:
                        detection_rate = (session['detections'] / session['total_actions']) * 100
                        st.sidebar.metric("Detection Rate", f"{detection_rate:.1f}%")
                
                st.sidebar.metric("Current Profile", stats['current_profile'])
                st.sidebar.metric("Current Mode", stats['current_mode'])
            
            # Show detection feedback system stats
            if st.session_state.detection_feedback_system:
                feedback_stats = st.session_state.detection_feedback_system.get_real_time_stats()
                
                st.sidebar.markdown("---")
                st.sidebar.markdown("**Detection System Stats:**")
                st.sidebar.metric("Total Events", feedback_stats['total_events'])
                st.sidebar.metric("Bot Detections", feedback_stats['total_detections'])
                
                if feedback_stats['total_events'] > 0:
                    overall_rate = feedback_stats['overall_detection_rate']
                    st.sidebar.metric("Overall Detection Rate", f"{overall_rate:.1f}%")
        
        else:
            st.sidebar.error("Enhanced behavior simulator not available. Check enhanced_behavior_simulator.py")
    
    # Model information
    if st.session_state.model_info:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Model Information")
        st.sidebar.info(f"**Model:** {st.session_state.model_info['name']}")
        st.sidebar.info(f"**Scaler:** {'✅' if st.session_state.model_info['scaler_available'] else '❌'}")
        st.sidebar.info(f"**AE Meta:** {'✅' if st.session_state.model_info['ae_meta_available'] else '❌'}")
    
    # Main content area
    if not st.session_state.monitor:
        st.info("👈 Click 'Initialize System' to start")
        return
    
    # Status display
    status_col1, status_col2 = st.columns(2)
    
    with status_col1:
        if st.session_state.monitor_running:
            st.markdown('<div class="success-container"><h4>🟢 System Status: ACTIVE</h4></div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-container"><h4>🔴 System Status: INACTIVE</h4></div>', 
                       unsafe_allow_html=True)
    
    with status_col2:
        if st.session_state.bot_running:
            st.markdown('<div class="alert-container"><h4>🤖 Basic Bot: RUNNING</h4></div>', 
                       unsafe_allow_html=True)
        elif st.session_state.enhanced_simulator_running:
            mode = getattr(st.session_state, 'simulator_mode', 'unknown').replace('_', ' ').title()
            profile = getattr(st.session_state, 'simulator_profile', 'unknown').replace('_', ' ').title()
            st.markdown(f'<div class="alert-container"><h4>🧪 SIMULATION ACTIVE</h4><p>{mode} - {profile}</p></div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-container"><h4>👤 Mode: USER MONITORING</h4></div>', 
                       unsafe_allow_html=True)
    
    # Real-time updates
    if st.session_state.monitor_running:
        
        # Auto-refresh placeholder
        placeholder = st.empty()
        
        with placeholder.container():
            # Get latest detection
            detection = get_latest_detection()
            
            if detection:
                # Check if bot detected and show alerts
                is_bot_detected = detection.get('is_improper', 0) == 1
                
                if is_bot_detected:
                    # Show bot alert with visual indicators
                    show_bot_alert(detection)
                    
                    # Show additional security measures
                    st.warning("🚫 **SECURITY ACTION REQUIRED**: Please verify your identity or contact system administrator.")
                    
                    # Add security action buttons
                    sec_col1, sec_col2 = st.columns(2)
                    with sec_col1:
                        if st.button("🔒 Lock Account", key="lock_account"):
                            st.error("Account has been temporarily locked for security reasons.")
                    with sec_col2:
                        if st.button("📧 Report False Positive", key="report_fp"):
                            st.info("False positive report submitted for review.")
                else:
                    # Show normal human status
                    show_human_status()
                
                # Current prediction display
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    prediction = "🤖 ROBOT" if is_bot_detected else "👤 PERSON"
                    color = "red" if is_bot_detected else "green"
                    st.markdown(f"### Prediction: :{color}[{prediction}]")
                
                with col2:
                    score = detection.get('score', 0.0)
                    if score is not None:
                        st.metric("Confidence Score", f"{float(score):.3f}")
                
                with col3:
                    st.metric("Model Used", detection.get('model', 'Unknown'))
                
                with col4:
                    timestamp = detection.get('timestamp', datetime.now().isoformat())
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        st.metric("Last Update", dt.strftime("%H:%M:%S"))
                    except:
                        st.metric("Last Update", "Unknown")
                
                # Feature values display
                st.subheader("📊 Current Input Features")
                
                feat_col1, feat_col2, feat_col3 = st.columns(3)
                
                with feat_col1:
                    st.markdown('<div class="feature-box">', unsafe_allow_html=True)
                    st.metric("Mouse Speed", f"{detection.get('avg_mouse_speed', 0):.2f} px/s")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="feature-box">', unsafe_allow_html=True)
                    st.metric("Typing Speed", f"{detection.get('avg_typing_speed', 0):.2f} keys/min")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with feat_col2:
                    st.markdown('<div class="feature-box">', unsafe_allow_html=True)
                    st.metric("Tab Switch Rate", f"{detection.get('tab_switch_rate', 0):.2f} /min")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="feature-box">', unsafe_allow_html=True)
                    st.metric("Click Rate", f"{detection.get('mouse_click_rate', 0):.2f} /min")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with feat_col3:
                    st.markdown('<div class="feature-box">', unsafe_allow_html=True)
                    st.metric("Error Rate", f"{detection.get('keyboard_error_rate', 0):.2f}%")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="feature-box">', unsafe_allow_html=True)
                    st.metric("Window Duration", f"{detection.get('active_window_duration', 0):.2f} sec")
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Prediction timeline chart
            st.subheader("📈 Prediction Timeline")
            pred_chart = create_prediction_chart()
            if pred_chart:
                st.plotly_chart(pred_chart, use_container_width=True)
            else:
                st.info("Waiting for prediction data...")
            
            # Feature timeline charts
            st.subheader("📊 Feature Values Over Time")
            feature_charts = create_feature_charts()
            if feature_charts:
                # Display charts in a 2x3 grid
                for i in range(0, len(feature_charts), 2):
                    cols = st.columns(2)
                    for j, col in enumerate(cols):
                        if i + j < len(feature_charts):
                            with col:
                                st.plotly_chart(feature_charts[i + j], use_container_width=True)
            else:
                st.info("Waiting for feature data...")
        
        # Auto-refresh the page every 2 seconds
        time.sleep(2)
        st.rerun()
    
    else:
        st.info("👈 Start the monitor to see real-time data")
        
        # Show detection log if available
        if os.path.exists('detections_log.csv'):
            st.subheader("📋 Detection History")
            try:
                df = pd.read_csv('detections_log.csv')
                if not df.empty:
                    # Show last 10 records
                    st.dataframe(df.tail(10), use_container_width=True)
                else:
                    st.info("No detection history available yet.")
            except Exception as e:
                st.error(f"Could not load detection history: {str(e)}")

if __name__ == "__main__":
    main()
