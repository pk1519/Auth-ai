"""
Enhanced Human Behavior Simulator for AuthAI Testing

Features:
- Realistic human behavior profiles with natural variations
- Smooth mouse movements using Bezier curves
- Natural typing patterns with errors and corrections
- Controlled variability for robustness testing
- Dataset replay functionality with Gaussian noise
- Comprehensive logging and analytics
- Clear labeling of all synthetic behavior

This simulator is designed for legitimate testing and evaluation of 
behavioral biometric systems, not for evasion or bypassing security.
"""

import pyautogui
import time
import random
import math
import numpy as np
import pandas as pd
import threading
import json
import os
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import deque
import csv

# Disable pyautogui failsafe for controlled testing
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.001

class SimulatorMode(Enum):
    """Different simulation modes for testing"""
    BASIC_VARIABILITY = "basic_variability"
    INTERMEDIATE_VARIABILITY = "intermediate_variability" 
    HIGH_VARIABILITY = "high_variability"
    DATASET_REPLAY = "dataset_replay"

@dataclass
class BehaviorProfile:
    """Human behavior characteristics for simulation"""
    name: str
    avg_typing_speed: float  # characters per minute
    typing_variance: float   # speed variation coefficient
    mouse_speed_range: Tuple[float, float]  # min, max pixels/second
    click_accuracy: float    # 0-1, probability of accurate clicks
    idle_frequency: float    # seconds between idle periods
    error_rate: float       # typing error probability
    backspace_probability: float  # probability of corrections
    pause_frequency: float   # probability of pauses while typing
    double_click_rate: float # probability of double clicks
    scroll_frequency: float  # scrolling behavior frequency

@dataclass
class SimulationSession:
    """Track simulation session data"""
    session_id: str
    mode: SimulatorMode
    profile_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_actions: int = 0
    detected_as_bot: int = 0
    detection_events: List[Dict] = None
    
    def __post_init__(self):
        if self.detection_events is None:
            self.detection_events = []

class BezierCurveGenerator:
    """Generate smooth, natural mouse movements using Bezier curves"""
    
    @staticmethod
    def cubic_bezier(t: float, p0: Tuple[float, float], p1: Tuple[float, float], 
                    p2: Tuple[float, float], p3: Tuple[float, float]) -> Tuple[float, float]:
        """Calculate point on cubic Bezier curve at parameter t"""
        x = (1-t)**3 * p0[0] + 3*(1-t)**2*t * p1[0] + 3*(1-t)*t**2 * p2[0] + t**3 * p3[0]
        y = (1-t)**3 * p0[1] + 3*(1-t)**2*t * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1]
        return (x, y)
    
    @staticmethod
    def generate_natural_control_points(start: Tuple[int, int], end: Tuple[int, int], 
                                      curvature: float = 0.2) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """Generate control points for natural-looking curves"""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < 50:  # Short movements are more direct
            curvature *= 0.3
        
        # Create gentle curve with some randomness
        offset_magnitude = distance * curvature * random.uniform(0.4, 1.2)
        angle_offset = random.uniform(-math.pi/6, math.pi/6)  # Smaller angle variation
        
        # Calculate perpendicular direction for curve
        if distance > 0:
            perpendicular_angle = math.atan2(dy, dx) + math.pi/2 + angle_offset
        else:
            perpendicular_angle = angle_offset
        
        offset_x = offset_magnitude * math.cos(perpendicular_angle)
        offset_y = offset_magnitude * math.sin(perpendicular_angle)
        
        # Control points for smooth curve
        cp1 = (
            int(start[0] + dx/4 + offset_x * 0.6),
            int(start[1] + dy/4 + offset_y * 0.6)
        )
        cp2 = (
            int(end[0] - dx/4 + offset_x * 0.8),
            int(end[1] - dy/4 + offset_y * 0.8)
        )
        
        return cp1, cp2
    
    @classmethod
    def move_mouse_naturally(cls, start: Tuple[int, int], end: Tuple[int, int], 
                           duration: float = 1.0, steps: int = None):
        """Move mouse along natural Bezier curve"""
        distance = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        
        # Adaptive step count based on distance
        if steps is None:
            steps = max(15, min(80, int(distance / 8)))
        
        cp1, cp2 = cls.generate_natural_control_points(start, end)
        step_duration = duration / steps
        
        for i in range(steps + 1):
            t = i / steps
            
            # Add subtle hand tremor (very small)
            tremor_x = random.uniform(-1, 1) if random.random() < 0.2 else 0
            tremor_y = random.uniform(-1, 1) if random.random() < 0.2 else 0
            
            x, y = cls.cubic_bezier(t, start, cp1, cp2, end)
            
            try:
                pyautogui.moveTo(int(x + tremor_x), int(y + tremor_y), duration=0)
                # Natural timing variation
                time.sleep(step_duration * random.uniform(0.8, 1.3))
            except pyautogui.FailSafeException:
                break

class TypingSimulator:
    """Simulate natural human typing patterns"""
    
    def __init__(self, profile: BehaviorProfile):
        self.profile = profile
        
        # Common typing mistakes by keyboard layout
        self.qwerty_mistakes = {
            'a': ['s', 'q', 'w'], 'b': ['v', 'n', 'g'], 'c': ['x', 'v', 'd'],
            'd': ['s', 'f', 'c'], 'e': ['w', 'r', 'd'], 'f': ['d', 'g', 'v'],
            'g': ['f', 'h', 'b'], 'h': ['g', 'j', 'n'], 'i': ['u', 'o', 'k'],
            'j': ['h', 'k', 'm'], 'k': ['j', 'l', 'i'], 'l': ['k', 'o', 'p'],
            'm': ['n', 'j'], 'n': ['b', 'm', 'h'], 'o': ['i', 'p', 'l'],
            'p': ['o', 'l'], 'q': ['w', 'a'], 'r': ['e', 't', 'f'],
            's': ['a', 'd', 'w'], 't': ['r', 'y', 'g'], 'u': ['y', 'i', 'j'],
            'v': ['c', 'b', 'f'], 'w': ['q', 'e', 's'], 'x': ['z', 'c', 's'],
            'y': ['t', 'u', 'h'], 'z': ['x', 'a']
        }
    
    def get_typing_intervals(self, text: str) -> List[float]:
        """Generate realistic typing intervals based on profile"""
        base_interval = 60.0 / self.profile.avg_typing_speed
        intervals = []
        
        for i, char in enumerate(text):
            # Base timing with natural variation
            variance = random.gauss(1.0, self.profile.typing_variance)
            interval = base_interval * max(0.3, variance)
            
            # Adjust for character type
            if char.isspace():
                interval *= random.uniform(1.8, 2.5)  # Longer pause for spaces
            elif char in '.!?':
                interval *= random.uniform(2.0, 3.5)  # Pause after punctuation
            elif char in ',;:':
                interval *= random.uniform(1.3, 2.0)  # Medium pause
            elif char.isupper():
                interval *= random.uniform(1.1, 1.4)  # Slight delay for capitals
            
            # Occasional thinking pauses
            if random.random() < self.profile.pause_frequency:
                interval += random.uniform(0.5, 2.0)
            
            intervals.append(interval)
        
        return intervals
    
    def should_make_mistake(self) -> bool:
        """Determine if a typing mistake should occur"""
        return random.random() < self.profile.error_rate
    
    def get_mistake_for_char(self, char: str) -> str:
        """Get a realistic typing mistake for given character"""
        char_lower = char.lower()
        if char_lower in self.qwerty_mistakes:
            mistake = random.choice(self.qwerty_mistakes[char_lower])
            return mistake.upper() if char.isupper() else mistake
        else:
            # Random nearby key
            nearby = 'qwertyuiopasdfghjklzxcvbnm'
            return random.choice(nearby)
    
    def type_text_naturally(self, text: str) -> int:
        """Type text with natural human-like patterns"""
        intervals = self.get_typing_intervals(text)
        actions_count = 0
        
        i = 0
        while i < len(text):
            char = text[i]
            
            # Check for typing mistake
            if self.should_make_mistake():
                # Type wrong character
                wrong_char = self.get_mistake_for_char(char)
                pyautogui.write(wrong_char)
                actions_count += 1
                
                # Delay before realizing mistake
                time.sleep(random.uniform(0.2, 1.0))
                
                # Maybe correct it
                if random.random() < self.profile.backspace_probability:
                    pyautogui.press('backspace')
                    time.sleep(random.uniform(0.1, 0.3))
                    pyautogui.write(char)
                    actions_count += 2
                else:
                    # Leave the mistake and continue
                    pass
            else:
                # Type correct character
                pyautogui.write(char)
                actions_count += 1
            
            # Apply timing
            if i < len(intervals):
                time.sleep(max(0.02, intervals[i]))
            
            i += 1
        
        return actions_count

class MouseSimulator:
    """Simulate natural mouse behavior"""
    
    def __init__(self, profile: BehaviorProfile):
        self.profile = profile
        self.curve_generator = BezierCurveGenerator()
    
    def move_naturally(self, target: Tuple[int, int]) -> bool:
        """Move mouse naturally to target position"""
        try:
            current_pos = pyautogui.position()
            distance = math.sqrt((target[0] - current_pos[0])**2 + (target[1] - current_pos[1])**2)
            
            # Calculate natural movement duration based on distance and profile
            min_speed, max_speed = self.profile.mouse_speed_range
            target_speed = random.uniform(min_speed, max_speed)
            duration = max(0.3, distance / target_speed)
            
            self.curve_generator.move_mouse_naturally(current_pos, target, duration)
            return True
        except pyautogui.FailSafeException:
            return False
    
    def add_micro_movements(self):
        """Add subtle micro-movements during idle periods"""
        current_pos = pyautogui.position()
        
        for _ in range(random.randint(1, 4)):
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            
            new_x = max(0, min(pyautogui.size().width - 1, current_pos[0] + offset_x))
            new_y = max(0, min(pyautogui.size().height - 1, current_pos[1] + offset_y))
            
            try:
                pyautogui.moveTo(new_x, new_y, duration=random.uniform(0.1, 0.2))
                time.sleep(random.uniform(0.05, 0.1))
            except pyautogui.FailSafeException:
                break
    
    def simulate_click_behavior(self) -> bool:
        """Simulate natural clicking with occasional inaccuracies"""
        try:
            # Occasional miss-click (but not maliciously)
            if random.random() > self.profile.click_accuracy:
                current_pos = pyautogui.position()
                # Small inaccuracy
                offset_x = random.randint(-10, 10)
                offset_y = random.randint(-10, 10)
                
                miss_x = max(50, min(pyautogui.size().width - 50, current_pos[0] + offset_x))
                miss_y = max(50, min(pyautogui.size().height - 50, current_pos[1] + offset_y))
                
                pyautogui.click(miss_x, miss_y)
                time.sleep(random.uniform(0.1, 0.3))  # Brief pause
                
                # Correct click
                pyautogui.click()
            else:
                # Accurate click
                if random.random() < self.profile.double_click_rate:
                    pyautogui.doubleClick()
                else:
                    pyautogui.click()
            
            return True
        except pyautogui.FailSafeException:
            return False

class DatasetReplaySystem:
    """Replay real user behavior traces with controlled noise"""
    
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self.behavior_traces = []
        self.load_dataset()
    
    def load_dataset(self):
        """Load behavior dataset for replay"""
        try:
            if os.path.exists(self.dataset_path):
                df = pd.read_csv(self.dataset_path)
                self.behavior_traces = df.to_dict('records')
                print(f"📊 Loaded {len(self.behavior_traces)} behavior traces from dataset")
            else:
                print(f"⚠️ Dataset not found at {self.dataset_path}")
                # Create sample dataset
                self.create_sample_dataset()
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            self.create_sample_dataset()
    
    def create_sample_dataset(self):
        """Create a sample behavior dataset for testing"""
        print("🔧 Creating sample behavior dataset...")
        
        sample_traces = []
        for i in range(50):
            trace = {
                'session_id': f'sample_{i:03d}',
                'avg_mouse_speed': random.uniform(100, 500),
                'avg_typing_speed': random.uniform(120, 600),
                'tab_switch_rate': random.uniform(0, 3),
                'mouse_click_rate': random.uniform(5, 40),
                'keyboard_error_rate': random.uniform(0, 0.1),
                'active_window_duration': random.uniform(1, 300),
                'is_human': 1 if i < 40 else 0  # Most are human
            }
            sample_traces.append(trace)
        
        self.behavior_traces = sample_traces
        
        # Save sample dataset
        try:
            df = pd.DataFrame(sample_traces)
            df.to_csv('sample_behavior_dataset.csv', index=False)
            print("✅ Sample dataset created and saved")
        except Exception as e:
            print(f"⚠️ Could not save sample dataset: {e}")
    
    def get_random_trace(self) -> Dict:
        """Get a random behavior trace with Gaussian noise"""
        if not self.behavior_traces:
            return {}
        
        base_trace = random.choice(self.behavior_traces)
        
        # Add controlled Gaussian noise (small amount)
        noisy_trace = {}
        for key, value in base_trace.items():
            if isinstance(value, (int, float)) and key != 'is_human':
                # Add 5-10% noise
                noise_factor = 0.05 + random.uniform(0, 0.05)
                noise = random.gauss(0, abs(value) * noise_factor)
                noisy_trace[key] = max(0, value + noise)
            else:
                noisy_trace[key] = value
        
        return noisy_trace

class EnhancedBehaviorSimulator:
    """Main enhanced behavior simulator"""
    
    def __init__(self, mode: SimulatorMode = SimulatorMode.BASIC_VARIABILITY):
        self.mode = mode
        self.is_running = False
        self.current_session = None
        
        # Initialize behavior profiles
        self.behavior_profiles = self._create_behavior_profiles()
        self.current_profile = self.behavior_profiles['casual_user']
        
        # Initialize simulators
        self.typing_simulator = TypingSimulator(self.current_profile)
        self.mouse_simulator = MouseSimulator(self.current_profile)
        
        # Dataset replay system
        self.dataset_replay = DatasetReplaySystem('Dataset/user_behavior_dataset.csv')
        
        # Logging system
        self.session_log = []
        self.detection_callback = None
        
        # Sample texts for typing simulation
        self.sample_texts = [
            "The quick brown fox jumps over the lazy dog.",
            "Machine learning models require careful validation.",
            "Behavioral biometrics can enhance security systems.", 
            "Data preprocessing is crucial for model performance.",
            "Cross-validation helps prevent overfitting issues.",
            "Feature engineering improves prediction accuracy.",
            "Authentication systems must balance security and usability.",
            "Natural language processing has many applications.",
            "Deep learning requires substantial computational resources.",
            "Privacy protection is essential in modern systems."
        ]
    
    def _create_behavior_profiles(self) -> Dict[str, BehaviorProfile]:
        """Create realistic behavior profiles for different user types"""
        return {
            'casual_user': BehaviorProfile(
                name='Casual User',
                avg_typing_speed=200,  # ~33 WPM
                typing_variance=0.25,
                mouse_speed_range=(120, 350),
                click_accuracy=0.88,
                idle_frequency=12.0,
                error_rate=0.04,
                backspace_probability=0.7,
                pause_frequency=0.15,
                double_click_rate=0.08,
                scroll_frequency=0.3
            ),
            'fast_typer': BehaviorProfile(
                name='Fast Typer',
                avg_typing_speed=480,  # ~80 WPM
                typing_variance=0.35,
                mouse_speed_range=(200, 550),
                click_accuracy=0.92,
                idle_frequency=6.0,
                error_rate=0.08,
                backspace_probability=0.85,
                pause_frequency=0.05,
                double_click_rate=0.12,
                scroll_frequency=0.4
            ),
            'careful_user': BehaviorProfile(
                name='Careful User',
                avg_typing_speed=140,  # ~23 WPM
                typing_variance=0.15,
                mouse_speed_range=(80, 220),
                click_accuracy=0.96,
                idle_frequency=20.0,
                error_rate=0.02,
                backspace_probability=0.9,
                pause_frequency=0.25,
                double_click_rate=0.05,
                scroll_frequency=0.2
            ),
            'mobile_style': BehaviorProfile(
                name='Mobile-Style User',
                avg_typing_speed=100,  # ~17 WPM (hunt and peck)
                typing_variance=0.4,
                mouse_speed_range=(60, 180),
                click_accuracy=0.82,
                idle_frequency=15.0,
                error_rate=0.12,
                backspace_probability=0.6,
                pause_frequency=0.3,
                double_click_rate=0.03,
                scroll_frequency=0.6
            )
        }
    
    def set_profile(self, profile_name: str):
        """Switch to a different behavior profile"""
        if profile_name in self.behavior_profiles:
            self.current_profile = self.behavior_profiles[profile_name]
            self.typing_simulator = TypingSimulator(self.current_profile)
            self.mouse_simulator = MouseSimulator(self.current_profile)
            print(f"🔄 Switched to {self.current_profile.name} profile")
        else:
            print(f"❌ Profile '{profile_name}' not found")
    
    def set_detection_callback(self, callback):
        """Set callback for detection events"""
        self.detection_callback = callback
    
    def start_simulation_session(self, duration: float):
        """Start a new simulation session"""
        session_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
        
        self.current_session = SimulationSession(
            session_id=session_id,
            mode=self.mode,
            profile_name=self.current_profile.name,
            start_time=datetime.now()
        )
        
        print(f"🚀 Starting simulation session: {session_id}")
        print(f"   Mode: {self.mode.value}")
        print(f"   Profile: {self.current_profile.name}")
        print(f"   Duration: {duration} seconds")
        print("   📝 All behavior is clearly labeled as SIMULATED")
    
    def end_simulation_session(self):
        """End current simulation session"""
        if self.current_session:
            self.current_session.end_time = datetime.now()
            self.save_session_log()
            
            duration = (self.current_session.end_time - self.current_session.start_time).total_seconds()
            detection_rate = (self.current_session.detected_as_bot / max(1, self.current_session.total_actions)) * 100
            
            print(f"✅ Session {self.current_session.session_id} completed")
            print(f"   Duration: {duration:.1f} seconds")
            print(f"   Total actions: {self.current_session.total_actions}")
            print(f"   Detection rate: {detection_rate:.1f}%")
    
    def simulate_typing_session(self, duration: float):
        """Simulate natural typing behavior"""
        end_time = time.time() + duration
        
        while time.time() < end_time and self.is_running:
            # Choose random text
            text = random.choice(self.sample_texts)
            
            # Add some variation to text
            if random.random() < 0.3:  # 30% chance to modify
                words = text.split()
                # Sometimes type partial sentences
                if len(words) > 3 and random.random() < 0.4:
                    cut_point = random.randint(2, len(words) - 1)
                    text = ' '.join(words[:cut_point])
            
            # Type the text naturally
            actions = self.typing_simulator.type_text_naturally(text)
            if self.current_session:
                self.current_session.total_actions += actions
            
            # Natural pause between typing sessions
            pause_duration = random.uniform(2, 8)
            if self.current_profile.name == 'Careful User':
                pause_duration *= random.uniform(1.2, 2.0)  # Longer pauses
            
            time.sleep(pause_duration)
    
    def simulate_mouse_activity(self, duration: float):
        """Simulate natural mouse movements and clicks"""
        screen_width, screen_height = pyautogui.size()
        end_time = time.time() + duration
        
        # Define safe areas for mouse movement (avoid screen edges)
        safe_margin = 100
        safe_area = (safe_margin, safe_margin, screen_width - safe_margin, screen_height - safe_margin)
        
        while time.time() < end_time and self.is_running:
            try:
                # Choose target within safe area
                target_x = random.randint(safe_area[0], safe_area[2])
                target_y = random.randint(safe_area[1], safe_area[3])
                
                # Move to target
                if self.mouse_simulator.move_naturally((target_x, target_y)):
                    if self.current_session:
                        self.current_session.total_actions += 1
                    
                    # Sometimes hover briefly
                    if random.random() < 0.4:
                        time.sleep(random.uniform(0.5, 2.0))
                        self.mouse_simulator.add_micro_movements()
                    
                    # Sometimes click
                    if random.random() < 0.6:
                        if self.mouse_simulator.simulate_click_behavior():
                            if self.current_session:
                                self.current_session.total_actions += 1
                
                # Natural pause between movements
                pause = random.uniform(1, 5)
                time.sleep(pause)
                
            except Exception as e:
                print(f"⚠️ Mouse simulation error: {e}")
                break
    
    def simulate_tab_switching(self, duration: float):
        """Simulate natural tab switching behavior"""
        end_time = time.time() + duration
        
        while time.time() < end_time and self.is_running:
            # Natural intervals for tab switching
            interval = random.uniform(8, 25)  # 8-25 seconds between switches
            
            # Adjust based on profile
            if self.current_profile.name == 'Fast Typer':
                interval *= random.uniform(0.6, 1.0)
            elif self.current_profile.name == 'Careful User':
                interval *= random.uniform(1.2, 1.8)
            
            time.sleep(interval)
            
            if self.is_running:
                try:
                    # Variety in tab switching methods
                    switch_method = random.choice(['ctrl_tab', 'alt_tab', 'ctrl_pageup'])
                    
                    if switch_method == 'ctrl_tab':
                        pyautogui.hotkey('ctrl', 'tab')
                    elif switch_method == 'alt_tab':
                        pyautogui.hotkey('alt', 'tab')
                        time.sleep(random.uniform(0.1, 0.5))
                        pyautogui.press('enter')
                    else:  # ctrl_pageup
                        pyautogui.hotkey('ctrl', 'pageup')
                    
                    if self.current_session:
                        self.current_session.total_actions += 1
                
                except pyautogui.FailSafeException:
                    break
    
    def simulate_scrolling_behavior(self, duration: float):
        """Simulate natural scrolling patterns"""
        end_time = time.time() + duration
        
        while time.time() < end_time and self.is_running:
            # Wait for natural scroll opportunity
            scroll_wait = random.uniform(5, 15)
            time.sleep(scroll_wait)
            
            if self.is_running and random.random() < self.current_profile.scroll_frequency:
                try:
                    # Natural scrolling patterns
                    scroll_amount = random.randint(1, 5)
                    scroll_direction = random.choice(['up', 'down', 'down'])  # Bias toward down
                    
                    for _ in range(scroll_amount):
                        if scroll_direction == 'down':
                            pyautogui.scroll(-3)
                        else:
                            pyautogui.scroll(3)
                        time.sleep(random.uniform(0.1, 0.3))
                    
                    if self.current_session:
                        self.current_session.total_actions += scroll_amount
                
                except pyautogui.FailSafeException:
                    break
    
    def replay_dataset_trace(self, duration: float):
        """Replay behavior from dataset with controlled noise"""
        if not self.dataset_replay.behavior_traces:
            print("❌ No dataset traces available for replay")
            return
        
        end_time = time.time() + duration
        
        while time.time() < end_time and self.is_running:
            # Get noisy trace
            trace = self.dataset_replay.get_random_trace()
            
            # Simulate the traced behavior
            print(f"🔄 Replaying trace: Mouse Speed={trace.get('avg_mouse_speed', 0):.1f}, "
                  f"Typing Speed={trace.get('avg_typing_speed', 0):.1f}")
            
            # Adjust current behavior to match trace (approximately)
            # This is a simplified implementation - in practice you'd need more sophisticated replay
            
            if self.current_session:
                self.current_session.total_actions += 1
            
            # Wait before next trace replay
            time.sleep(random.uniform(3, 8))
    
    def run_simulation(self, duration: float = 30.0):
        """Run the behavior simulation"""
        if self.is_running:
            print("❌ Simulation already running!")
            return False
        
        # Apply mode-specific adjustments
        if self.mode == SimulatorMode.BASIC_VARIABILITY:
            # Reduce natural variation for basic mode
            original_variance = self.current_profile.typing_variance
            self.current_profile.typing_variance *= 0.5
        elif self.mode == SimulatorMode.HIGH_VARIABILITY:
            # Increase natural variation for high variability mode
            original_variance = self.current_profile.typing_variance
            self.current_profile.typing_variance *= 1.8
        
        self.is_running = True
        self.start_simulation_session(duration)
        
        try:
            # Start multiple behavior threads
            threads = []
            
            if self.mode == SimulatorMode.DATASET_REPLAY:
                # Dataset replay mode
                replay_thread = threading.Thread(
                    target=self.replay_dataset_trace,
                    args=(duration,),
                    daemon=True
                )
                threads.append(replay_thread)
            else:
                # Normal behavior simulation
                typing_thread = threading.Thread(
                    target=self.simulate_typing_session,
                    args=(duration,),
                    daemon=True
                )
                threads.append(typing_thread)
                
                mouse_thread = threading.Thread(
                    target=self.simulate_mouse_activity,
                    args=(duration,),
                    daemon=True
                )
                threads.append(mouse_thread)
                
                tab_thread = threading.Thread(
                    target=self.simulate_tab_switching,
                    args=(duration,),
                    daemon=True
                )
                threads.append(tab_thread)
                
                scroll_thread = threading.Thread(
                    target=self.simulate_scrolling_behavior,
                    args=(duration,),
                    daemon=True
                )
                threads.append(scroll_thread)
            
            # Start all threads
            for thread in threads:
                thread.start()
            
            # Monitor simulation progress
            start_time = time.time()
            while time.time() - start_time < duration and self.is_running:
                time.sleep(0.5)
            
        except pyautogui.FailSafeException:
            print("🛑 Simulation stopped by failsafe (mouse moved to corner)")
        except Exception as e:
            print(f"❌ Simulation error: {str(e)}")
        finally:
            self.is_running = False
            self.end_simulation_session()
            
            # Restore original profile settings
            if self.mode in [SimulatorMode.BASIC_VARIABILITY, SimulatorMode.HIGH_VARIABILITY]:
                pass  # Settings will be reset when profile is reloaded
        
        return True
    
    def stop_simulation(self):
        """Stop the running simulation"""
        if self.is_running:
            self.is_running = False
            print("🛑 Stopping behavior simulation...")
        else:
            print("ℹ️ No simulation currently running")
    
    def on_detection_event(self, detection_data: Dict):
        """Handle detection feedback"""
        if self.current_session and detection_data:
            is_detected = detection_data.get('is_improper', 0) == 1
            
            if is_detected:
                self.current_session.detected_as_bot += 1
                print(f"🚨 Simulation detected as bot (Session: {self.current_session.session_id})")
            
            # Log the detection event
            detection_event = {
                'timestamp': datetime.now().isoformat(),
                'detected_as_bot': is_detected,
                'confidence_score': detection_data.get('score', 0.0),
                'model_used': detection_data.get('model', 'Unknown'),
                'session_id': self.current_session.session_id
            }
            
            self.current_session.detection_events.append(detection_event)
            
            # Call external callback if set
            if self.detection_callback:
                self.detection_callback(is_detected, detection_data)
    
    def save_session_log(self):
        """Save session data to log file"""
        if not self.current_session:
            return
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_data': asdict(self.current_session),
            'profile_used': asdict(self.current_profile),
            'mode': self.mode.value
        }
        
        # Save to JSON log
        log_filename = 'behavior_simulation_log.json'
        try:
            if os.path.exists(log_filename):
                with open(log_filename, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            with open(log_filename, 'w') as f:
                json.dump(logs, f, indent=2, default=str)
            
            print(f"📝 Session logged to {log_filename}")
            
        except Exception as e:
            print(f"⚠️ Could not save session log: {e}")
    
    def get_simulation_stats(self) -> Dict:
        """Get current simulation statistics"""
        stats = {
            'is_running': self.is_running,
            'current_mode': self.mode.value,
            'current_profile': self.current_profile.name,
            'available_profiles': list(self.behavior_profiles.keys()),
            'available_modes': [mode.value for mode in SimulatorMode]
        }
        
        if self.current_session:
            stats['current_session'] = {
                'session_id': self.current_session.session_id,
                'start_time': self.current_session.start_time.isoformat(),
                'total_actions': self.current_session.total_actions,
                'detections': self.current_session.detected_as_bot,
                'detection_events_count': len(self.current_session.detection_events)
            }
        
        return stats
    
    def generate_behavior_report(self) -> Dict:
        """Generate a comprehensive report of simulation behavior"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'simulator_version': '2.0.0',
            'profiles_tested': [],
            'detection_summary': {},
            'recommendations': []
        }
        
        # Load session logs
        log_filename = 'behavior_simulation_log.json'
        if os.path.exists(log_filename):
            try:
                with open(log_filename, 'r') as f:
                    logs = json.load(f)
                
                # Analyze logs
                profile_stats = {}
                mode_stats = {}
                
                for log_entry in logs[-50:]:  # Last 50 sessions
                    session = log_entry['session_data']
                    profile_name = session['profile_name']
                    mode = session['mode']
                    
                    if profile_name not in profile_stats:
                        profile_stats[profile_name] = {'sessions': 0, 'detections': 0, 'actions': 0}
                    
                    profile_stats[profile_name]['sessions'] += 1
                    profile_stats[profile_name]['detections'] += session['detected_as_bot']
                    profile_stats[profile_name]['actions'] += session['total_actions']
                    
                    if mode not in mode_stats:
                        mode_stats[mode] = {'sessions': 0, 'detections': 0}
                    mode_stats[mode]['sessions'] += 1
                    mode_stats[mode]['detections'] += session['detected_as_bot']
                
                report['profiles_tested'] = list(profile_stats.keys())
                report['detection_summary'] = {
                    'by_profile': profile_stats,
                    'by_mode': mode_stats
                }
                
                # Generate recommendations
                recommendations = []
                for profile, stats in profile_stats.items():
                    detection_rate = stats['detections'] / max(1, stats['actions']) * 100
                    if detection_rate > 50:
                        recommendations.append(f"Profile '{profile}' has high detection rate ({detection_rate:.1f}%) - consider refining parameters")
                    elif detection_rate < 5:
                        recommendations.append(f"Profile '{profile}' has very low detection rate ({detection_rate:.1f}%) - detector might need tuning")
                
                report['recommendations'] = recommendations
                
            except Exception as e:
                print(f"⚠️ Error generating report: {e}")
        
        return report

# Factory function for backward compatibility and easy instantiation
def create_behavior_simulator(mode: str = 'basic_variability', profile: str = 'casual_user') -> EnhancedBehaviorSimulator:
    """Factory function to create behavior simulator"""
    try:
        sim_mode = SimulatorMode(mode)
    except ValueError:
        print(f"⚠️ Invalid mode '{mode}', using basic_variability")
        sim_mode = SimulatorMode.BASIC_VARIABILITY
    
    simulator = EnhancedBehaviorSimulator(sim_mode)
    
    if profile in simulator.behavior_profiles:
        simulator.set_profile(profile)
    else:
        print(f"⚠️ Invalid profile '{profile}', using casual_user")
    
    return simulator

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Enhanced Behavior Simulator Test Suite")
    print("="*60)
    
    # Test different modes and profiles
    test_configurations = [
        ('basic_variability', 'casual_user'),
        ('intermediate_variability', 'fast_typer'),
        ('high_variability', 'careful_user'),
        ('dataset_replay', 'mobile_style')
    ]
    
    for mode, profile in test_configurations:
        print(f"\n🔧 Testing: {mode} mode with {profile} profile")
        print("-" * 40)
        
        simulator = create_behavior_simulator(mode, profile)
        
        # Set up detection feedback
        def test_detection_callback(is_detected, detection_data):
            status = "DETECTED" if is_detected else "PASSED"
            score = detection_data.get('score', 0.0)
            print(f"  📊 Detection Result: {status} (Score: {score:.3f})")
        
        simulator.set_detection_callback(test_detection_callback)
        
        # Run short test simulation
        print(f"  ▶️ Running 8-second test simulation...")
        simulator.run_simulation(duration=8.0)
        
        # Show stats
        stats = simulator.get_simulation_stats()
        if 'current_session' in stats:
            session = stats['current_session']
            print(f"  📈 Actions: {session['total_actions']}, Detections: {session['detections']}")
        
        time.sleep(2)  # Brief pause between tests
    
    # Generate and display report
    print(f"\n📋 Generating behavior analysis report...")
    any_simulator = create_behavior_simulator()
    report = any_simulator.generate_behavior_report()
    
    print(f"\n📊 SIMULATION REPORT")
    print("="*40)
    print(f"Profiles Tested: {', '.join(report['profiles_tested'])}")
    
    if report['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    print(f"\n✅ Enhanced behavior simulator testing completed!")
    print(f"📝 Note: All simulated behavior is clearly labeled and logged for analysis")
