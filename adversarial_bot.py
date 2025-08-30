"""
Advanced Adversarial Bot Simulator for AuthAI Testing

Features:
- Multiple difficulty levels: Basic, Intermediate, Advanced
- Human-like typing with variable speeds and corrections
- Realistic mouse movements using Bezier curves
- Adaptive behavioral patterns and adversarial noise
- Reinforcement learning adaptation based on detection feedback
- Context-aware behavior mimicking real users
"""

import pyautogui
import time
import random
import math
import numpy as np
import threading
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import json
import os
from collections import deque

# Disable pyautogui failsafe for controlled testing
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.001  # Minimal pause for faster execution

class BotDifficulty(Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate" 
    ADVANCED = "advanced"

@dataclass
class UserBehaviorProfile:
    """Real user behavior patterns for mimicking"""
    avg_typing_speed: float  # chars per minute
    typing_variance: float   # speed variation
    mouse_speed_range: Tuple[float, float]  # min, max pixels/second
    click_accuracy: float    # 0-1, probability of accurate clicks
    idle_frequency: float    # seconds between idle periods
    error_rate: float       # typing error probability
    backspace_probability: float  # probability of corrections

@dataclass
class AdversarialStats:
    """Track bot performance and adaptation"""
    total_detections: int = 0
    successful_evasions: int = 0
    current_difficulty: BotDifficulty = BotDifficulty.BASIC
    adaptation_level: float = 0.0
    feature_noise_levels: Dict[str, float] = None
    
    def __post_init__(self):
        if self.feature_noise_levels is None:
            self.feature_noise_levels = {
                'mouse_speed': 0.1,
                'typing_speed': 0.1,
                'click_rate': 0.1,
                'tab_switch_rate': 0.1
            }

class HumanBehaviorMimicker:
    """Generates realistic human-like behavior patterns"""
    
    def __init__(self):
        # Realistic human behavior profiles
        self.behavior_profiles = {
            'casual_user': UserBehaviorProfile(
                avg_typing_speed=180,  # 30 WPM
                typing_variance=0.3,
                mouse_speed_range=(100, 400),
                click_accuracy=0.85,
                idle_frequency=15.0,
                error_rate=0.05,
                backspace_probability=0.3
            ),
            'fast_typer': UserBehaviorProfile(
                avg_typing_speed=420,  # 70 WPM
                typing_variance=0.4,
                mouse_speed_range=(200, 600),
                click_accuracy=0.92,
                idle_frequency=8.0,
                error_rate=0.08,
                backspace_probability=0.4
            ),
            'careful_user': UserBehaviorProfile(
                avg_typing_speed=120,  # 20 WPM
                typing_variance=0.2,
                mouse_speed_range=(50, 200),
                click_accuracy=0.95,
                idle_frequency=25.0,
                error_rate=0.02,
                backspace_probability=0.6
            )
        }
        
        self.current_profile = self.behavior_profiles['casual_user']
        
    def switch_profile(self, profile_name: str = None):
        """Switch to a different behavior profile"""
        if profile_name and profile_name in self.behavior_profiles:
            self.current_profile = self.behavior_profiles[profile_name]
        else:
            # Random profile selection
            profile_name = random.choice(list(self.behavior_profiles.keys()))
            self.current_profile = self.behavior_profiles[profile_name]
        
        return profile_name
    
    def generate_typing_timing(self, text: str) -> List[float]:
        """Generate realistic typing intervals"""
        profile = self.current_profile
        base_interval = 60.0 / profile.avg_typing_speed  # seconds per character
        
        intervals = []
        for i, char in enumerate(text):
            # Add variance based on profile
            variance = random.gauss(1.0, profile.typing_variance)
            interval = base_interval * max(0.1, variance)
            
            # Longer pauses for punctuation and spaces
            if char in [' ', '.', ',', '!', '?', '\n']:
                interval *= random.uniform(1.5, 3.0)
            
            intervals.append(interval)
        
        return intervals
    
    def should_make_typo(self) -> bool:
        """Determine if a typing error should occur"""
        return random.random() < self.current_profile.error_rate
    
    def should_backspace(self) -> bool:
        """Determine if user should correct a mistake"""
        return random.random() < self.current_profile.backspace_probability

class BezierMouseController:
    """Realistic mouse movement using Bezier curves"""
    
    @staticmethod
    def cubic_bezier(t: float, p0: Tuple[int, int], p1: Tuple[int, int], 
                    p2: Tuple[int, int], p3: Tuple[int, int]) -> Tuple[float, float]:
        """Calculate point on cubic Bezier curve"""
        x = (1-t)**3 * p0[0] + 3*(1-t)**2*t * p1[0] + 3*(1-t)*t**2 * p2[0] + t**3 * p3[0]
        y = (1-t)**3 * p0[1] + 3*(1-t)**2*t * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1]
        return (x, y)
    
    @staticmethod
    def generate_control_points(start: Tuple[int, int], end: Tuple[int, int], 
                              curvature: float = 0.3) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """Generate control points for natural curve"""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        # Add some randomness to control points
        offset_magnitude = distance * curvature * random.uniform(0.5, 1.5)
        angle_offset = random.uniform(-math.pi/3, math.pi/3)
        
        # Calculate perpendicular direction
        if distance > 0:
            perpendicular_angle = math.atan2(dy, dx) + math.pi/2 + angle_offset
        else:
            perpendicular_angle = angle_offset
        
        offset_x = offset_magnitude * math.cos(perpendicular_angle)
        offset_y = offset_magnitude * math.sin(perpendicular_angle)
        
        # Control points
        cp1 = (
            int(start[0] + dx/3 + offset_x * random.uniform(0.5, 1.0)),
            int(start[1] + dy/3 + offset_y * random.uniform(0.5, 1.0))
        )
        cp2 = (
            int(end[0] - dx/3 + offset_x * random.uniform(0.5, 1.0)),
            int(end[1] - dy/3 + offset_y * random.uniform(0.5, 1.0))
        )
        
        return cp1, cp2
    
    @classmethod
    def move_mouse_bezier(cls, start: Tuple[int, int], end: Tuple[int, int], 
                         duration: float = 1.0, steps: int = 50):
        """Move mouse along a Bezier curve"""
        cp1, cp2 = cls.generate_control_points(start, end)
        
        step_duration = duration / steps
        
        for i in range(steps + 1):
            t = i / steps
            
            # Add some jitter for realism
            jitter_x = random.uniform(-2, 2) if random.random() < 0.3 else 0
            jitter_y = random.uniform(-2, 2) if random.random() < 0.3 else 0
            
            x, y = cls.cubic_bezier(t, start, cp1, cp2, end)
            
            try:
                pyautogui.moveTo(int(x + jitter_x), int(y + jitter_y), duration=0)
                time.sleep(step_duration * random.uniform(0.8, 1.2))  # Vary timing
            except pyautogui.FailSafeException:
                break
    
    @staticmethod
    def add_idle_movement():
        """Add small random movements during idle periods"""
        current_x, current_y = pyautogui.position()
        
        # Small random movements
        for _ in range(random.randint(2, 8)):
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-10, 10)
            
            new_x = max(0, min(pyautogui.size().width, current_x + offset_x))
            new_y = max(0, min(pyautogui.size().height, current_y + offset_y))
            
            try:
                pyautogui.moveTo(new_x, new_y, duration=random.uniform(0.1, 0.3))
                time.sleep(random.uniform(0.05, 0.15))
            except pyautogui.FailSafeException:
                break

class AdversarialNoiseGenerator:
    """Generates adversarial noise to confuse ML models"""
    
    def __init__(self):
        self.noise_patterns = {
            'mouse_speed': self._mouse_speed_noise,
            'typing_speed': self._typing_speed_noise,
            'click_rate': self._click_rate_noise,
            'tab_switch_rate': self._tab_switch_noise
        }
        
    def _mouse_speed_noise(self, base_speed: float, noise_level: float) -> float:
        """Add adversarial noise to mouse speed"""
        # Create patterns that might confuse transformers
        periodic_noise = math.sin(time.time() * 0.5) * noise_level * base_speed
        random_noise = random.gauss(0, noise_level * base_speed * 0.3)
        return max(10, base_speed + periodic_noise + random_noise)
    
    def _typing_speed_noise(self, base_speed: float, noise_level: float) -> float:
        """Add adversarial noise to typing speed"""
        # Sudden bursts followed by pauses - confusing for sequence models
        if random.random() < 0.1:  # 10% chance of burst
            return base_speed * (2 + noise_level)
        elif random.random() < 0.15:  # 15% chance of pause
            return base_speed * (0.3 - noise_level * 0.2)
        return base_speed * (1 + random.gauss(0, noise_level))
    
    def _click_rate_noise(self, base_rate: float, noise_level: float) -> float:
        """Add adversarial noise to click patterns"""
        # Create irregular patterns
        burst_probability = 0.05 + noise_level * 0.1
        if random.random() < burst_probability:
            return base_rate * (3 + noise_level * 2)
        return base_rate * max(0.1, 1 + random.gauss(0, noise_level))
    
    def _tab_switch_noise(self, base_rate: float, noise_level: float) -> float:
        """Add adversarial noise to tab switching"""
        return max(0, base_rate + random.uniform(-noise_level, noise_level))
    
    def apply_noise(self, feature_name: str, base_value: float, noise_level: float) -> float:
        """Apply adversarial noise to a feature"""
        if feature_name in self.noise_patterns:
            return self.noise_patterns[feature_name](base_value, noise_level)
        return base_value

class ReinforcementLearningAdapter:
    """Simple RL system for adapting bot behavior"""
    
    def __init__(self):
        self.q_table = {}  # State-action values
        self.learning_rate = 0.1
        self.exploration_rate = 0.3
        self.adaptation_history = deque(maxlen=100)
        
    def get_state(self, detection_rate: float, current_difficulty: BotDifficulty) -> str:
        """Convert current situation to state representation"""
        detection_bucket = "high" if detection_rate > 0.7 else "medium" if detection_rate > 0.3 else "low"
        return f"{current_difficulty.value}_{detection_bucket}"
    
    def choose_action(self, state: str) -> Dict[str, float]:
        """Choose adaptation parameters based on current state"""
        if state not in self.q_table:
            self.q_table[state] = {
                'increase_human_mimicking': 0.0,
                'add_more_noise': 0.0,
                'change_timing_patterns': 0.0,
                'switch_behavior_profile': 0.0
            }
        
        # Epsilon-greedy action selection
        if random.random() < self.exploration_rate:
            # Random exploration
            return {action: random.uniform(0, 1) for action in self.q_table[state].keys()}
        else:
            # Exploit best known actions
            return self.q_table[state].copy()
    
    def update_q_values(self, state: str, actions: Dict[str, float], reward: float):
        """Update Q-values based on detection outcome"""
        if state not in self.q_table:
            return
        
        for action, strength in actions.items():
            if action in self.q_table[state]:
                current_q = self.q_table[state][action]
                self.q_table[state][action] = current_q + self.learning_rate * (reward - current_q)
    
    def get_reward(self, was_detected: bool, evasion_time: float) -> float:
        """Calculate reward based on detection outcome"""
        if was_detected:
            return -1.0  # Negative reward for being detected
        else:
            # Positive reward for evasion, bonus for longer evasion
            return 1.0 + min(2.0, evasion_time / 30.0)  # Max 3.0 reward

class AdvancedAdversarialBot:
    """Main adversarial bot with multiple difficulty levels"""
    
    def __init__(self, difficulty: BotDifficulty = BotDifficulty.BASIC):
        self.difficulty = difficulty
        self.stats = AdversarialStats(current_difficulty=difficulty)
        self.behavior_mimicker = HumanBehaviorMimicker()
        self.mouse_controller = BezierMouseController()
        self.noise_generator = AdversarialNoiseGenerator()
        self.rl_adapter = ReinforcementLearningAdapter()
        
        self.is_running = False
        self.detection_callback = None
        self.session_start_time = None
        self.last_adaptation_time = time.time()
        
        # Load previous learning if exists
        self.load_learning_data()
        
    def set_difficulty(self, difficulty: BotDifficulty):
        """Change bot difficulty level"""
        self.difficulty = difficulty
        self.stats.current_difficulty = difficulty
        
        # Adjust behavior based on difficulty
        if difficulty == BotDifficulty.BASIC:
            # Obvious bot behavior
            self.stats.feature_noise_levels = {k: 0.05 for k in self.stats.feature_noise_levels}
        elif difficulty == BotDifficulty.INTERMEDIATE:
            # Moderate human-like behavior
            self.stats.feature_noise_levels = {k: 0.15 for k in self.stats.feature_noise_levels}
            self.behavior_mimicker.switch_profile('casual_user')
        else:  # ADVANCED
            # Highly sophisticated behavior
            self.stats.feature_noise_levels = {k: 0.25 for k in self.stats.feature_noise_levels}
            self.behavior_mimicker.switch_profile(None)  # Random profile
    
    def set_detection_callback(self, callback):
        """Set callback function to be called when bot is detected"""
        self.detection_callback = callback
    
    def on_detection_feedback(self, was_detected: bool):
        """Process detection feedback for learning"""
        self.stats.total_detections += 1
        
        if was_detected:
            print(f"🚨 Bot detected! Adapting strategy... (Detection #{self.stats.total_detections})")
        else:
            self.stats.successful_evasions += 1
            print(f"✅ Evasion successful! ({self.stats.successful_evasions}/{self.stats.total_detections})")
        
        # Update RL system
        if self.session_start_time:
            evasion_time = time.time() - self.session_start_time
            state = self.rl_adapter.get_state(
                self.stats.total_detections / max(1, self.stats.total_detections + self.stats.successful_evasions),
                self.difficulty
            )
            
            # Get last actions (simplified for this implementation)
            last_actions = self.rl_adapter.choose_action(state)
            reward = self.rl_adapter.get_reward(was_detected, evasion_time)
            self.rl_adapter.update_q_values(state, last_actions, reward)
            
            # Apply adaptations if detected frequently
            if self.stats.total_detections % 3 == 0 and was_detected:
                self.adapt_behavior()
    
    def adapt_behavior(self):
        """Adapt bot behavior based on detection patterns"""
        print("🧠 Adapting behavior based on detection patterns...")
        
        # Get current state and choose adaptations
        detection_rate = self.stats.total_detections / max(1, self.stats.total_detections + self.stats.successful_evasions)
        state = self.rl_adapter.get_state(detection_rate, self.difficulty)
        adaptations = self.rl_adapter.choose_action(state)
        
        # Apply adaptations
        if adaptations['increase_human_mimicking'] > 0.5:
            self.behavior_mimicker.switch_profile()
            print("  → Switched to different behavior profile")
        
        if adaptations['add_more_noise'] > 0.5:
            for feature in self.stats.feature_noise_levels:
                self.stats.feature_noise_levels[feature] = min(0.5, 
                    self.stats.feature_noise_levels[feature] * 1.2)
            print("  → Increased adversarial noise levels")
        
        if adaptations['change_timing_patterns'] > 0.5:
            self.stats.adaptation_level = min(1.0, self.stats.adaptation_level + 0.2)
            print("  → Modified timing patterns")
        
        self.last_adaptation_time = time.time()
        self.save_learning_data()
    
    def simulate_human_typing(self, duration: float):
        """Simulate realistic human typing"""
        profile = self.behavior_mimicker.current_profile
        
        # Sample text to type
        sample_texts = [
            "The quick brown fox jumps over the lazy dog",
            "Hello world, this is a test message",
            "Lorem ipsum dolor sit amet consectetur",
            "Machine learning and artificial intelligence",
            "Python programming is very interesting"
        ]
        
        end_time = time.time() + duration
        
        while time.time() < end_time and self.is_running:
            text = random.choice(sample_texts)
            intervals = self.behavior_mimicker.generate_typing_timing(len(text))
            
            for i, char in enumerate(text):
                if not self.is_running or time.time() >= end_time:
                    break
                
                # Check for typos
                if self.behavior_mimicker.should_make_typo() and self.difficulty != BotDifficulty.BASIC:
                    # Type wrong character
                    wrong_char = random.choice('qwertyuiopasdfghjklzxcvbnm')
                    pyautogui.write(wrong_char)
                    time.sleep(intervals[i] * random.uniform(0.5, 1.5))
                    
                    # Maybe correct it
                    if self.behavior_mimicker.should_backspace():
                        time.sleep(random.uniform(0.1, 0.8))  # Realize mistake
                        pyautogui.press('backspace')
                        time.sleep(random.uniform(0.05, 0.2))
                        pyautogui.write(char)
                else:
                    pyautogui.write(char)
                
                # Apply adversarial timing noise
                if i < len(intervals):
                    noise_level = self.stats.feature_noise_levels.get('typing_speed', 0.1)
                    modified_interval = self.noise_generator.apply_noise(
                        'typing_speed', intervals[i], noise_level
                    )
                    time.sleep(max(0.01, modified_interval))
            
            # Random pause between texts
            time.sleep(random.uniform(1, 3))
    
    def simulate_realistic_mouse_movement(self, duration: float):
        """Simulate realistic mouse movements with Bezier curves"""
        screen_width, screen_height = pyautogui.size()
        end_time = time.time() + duration
        
        while time.time() < end_time and self.is_running:
            current_pos = pyautogui.position()
            
            # Choose movement type based on difficulty
            if self.difficulty == BotDifficulty.BASIC:
                # Simple linear movements
                target_x = random.randint(100, screen_width - 100)
                target_y = random.randint(100, screen_height - 100)
                pyautogui.moveTo(target_x, target_y, duration=random.uniform(0.5, 2.0))
                
            elif self.difficulty == BotDifficulty.INTERMEDIATE:
                # Slightly curved movements with some pauses
                target_x = random.randint(100, screen_width - 100)
                target_y = random.randint(100, screen_height - 100)
                
                self.mouse_controller.move_mouse_bezier(
                    current_pos, (target_x, target_y),
                    duration=random.uniform(0.8, 2.5),
                    steps=random.randint(20, 40)
                )
                
                # Occasional pause
                if random.random() < 0.3:
                    time.sleep(random.uniform(0.5, 2.0))
                    
            else:  # ADVANCED
                # Very realistic movements with hovering and corrections
                target_x = random.randint(50, screen_width - 50)
                target_y = random.randint(50, screen_height - 50)
                
                # Sometimes "overshoot" and correct
                if random.random() < 0.2:
                    overshoot_x = target_x + random.randint(-50, 50)
                    overshoot_y = target_y + random.randint(-50, 50)
                    
                    self.mouse_controller.move_mouse_bezier(
                        current_pos, (overshoot_x, overshoot_y),
                        duration=random.uniform(0.6, 1.5),
                        steps=random.randint(15, 30)
                    )
                    time.sleep(random.uniform(0.1, 0.4))
                    
                    # Correct to actual target
                    self.mouse_controller.move_mouse_bezier(
                        (overshoot_x, overshoot_y), (target_x, target_y),
                        duration=random.uniform(0.3, 0.8),
                        steps=random.randint(10, 20)
                    )
                else:
                    self.mouse_controller.move_mouse_bezier(
                        current_pos, (target_x, target_y),
                        duration=random.uniform(1.0, 3.0),
                        steps=random.randint(25, 60)
                    )
                
                # Add idle micro-movements
                if random.random() < 0.4:
                    self.mouse_controller.add_idle_movement()
                
                # Occasional longer pause (reading/thinking)
                if random.random() < 0.15:
                    time.sleep(random.uniform(2, 8))
            
            # Random pause between movements
            pause_duration = random.uniform(0.2, 1.5)
            if self.difficulty == BotDifficulty.ADVANCED:
                pause_duration *= random.uniform(0.5, 2.0)  # More varied pauses
                
            time.sleep(pause_duration)
    
    def simulate_clicking_behavior(self, duration: float):
        """Simulate clicking with adaptive patterns"""
        end_time = time.time() + duration
        
        while time.time() < end_time and self.is_running:
            # Determine click frequency based on difficulty and noise
            base_click_interval = {
                BotDifficulty.BASIC: 2.0,
                BotDifficulty.INTERMEDIATE: random.uniform(1.5, 4.0),
                BotDifficulty.ADVANCED: random.uniform(0.8, 8.0)
            }[self.difficulty]
            
            # Apply adversarial noise
            noise_level = self.stats.feature_noise_levels.get('click_rate', 0.1)
            click_interval = self.noise_generator.apply_noise(
                'click_rate', base_click_interval, noise_level
            )
            
            # Advanced bots sometimes miss-click
            if self.difficulty == BotDifficulty.ADVANCED and random.random() < 0.1:
                # Miss-click first
                screen_width, screen_height = pyautogui.size()
                miss_x = random.randint(100, screen_width - 100)
                miss_y = random.randint(100, screen_height - 100)
                pyautogui.click(miss_x, miss_y)
                time.sleep(random.uniform(0.2, 0.6))
            
            # Actual click
            try:
                pyautogui.click()
                time.sleep(max(0.1, click_interval))
            except pyautogui.FailSafeException:
                break
    
    def simulate_tab_switching(self, duration: float):
        """Simulate adaptive tab switching behavior"""
        end_time = time.time() + duration
        
        while time.time() < end_time and self.is_running:
            # Determine tab switch frequency
            if self.difficulty == BotDifficulty.BASIC:
                interval = random.uniform(3, 6)
            elif self.difficulty == BotDifficulty.INTERMEDIATE:
                interval = random.uniform(2, 10)
            else:  # ADVANCED
                interval = random.uniform(1, 15)  # Very irregular
            
            # Apply adversarial noise
            noise_level = self.stats.feature_noise_levels.get('tab_switch_rate', 0.1)
            interval = self.noise_generator.apply_noise('tab_switch_rate', interval, noise_level)
            
            time.sleep(max(0.5, interval))
            
            if self.is_running:
                # Sometimes use Ctrl+Tab, sometimes Alt+Tab
                if random.random() < 0.7:
                    pyautogui.hotkey('ctrl', 'tab')
                else:
                    pyautogui.hotkey('alt', 'tab')
                    time.sleep(random.uniform(0.1, 0.5))
                    pyautogui.press('enter')
    
    def run_simulation(self, duration: float = 30.0):
        """Run the adversarial bot simulation"""
        if self.is_running:
            print("❌ Bot simulation already running!")
            return False
        
        print(f"🤖 Starting {self.difficulty.value.title()} Adversarial Bot simulation...")
        print(f"📊 Stats: {self.stats.successful_evasions}/{self.stats.total_detections} successful evasions")
        
        self.is_running = True
        self.session_start_time = time.time()
        
        try:
            # Start multiple behavior threads
            threads = []
            
            # Typing simulation
            typing_thread = threading.Thread(
                target=self.simulate_human_typing,
                args=(duration,),
                daemon=True
            )
            threads.append(typing_thread)
            
            # Mouse movement simulation
            mouse_thread = threading.Thread(
                target=self.simulate_realistic_mouse_movement,
                args=(duration,),
                daemon=True
            )
            threads.append(mouse_thread)
            
            # Clicking simulation
            click_thread = threading.Thread(
                target=self.simulate_clicking_behavior,
                args=(duration,),
                daemon=True
            )
            threads.append(click_thread)
            
            # Tab switching simulation
            tab_thread = threading.Thread(
                target=self.simulate_tab_switching,
                args=(duration,),
                daemon=True
            )
            threads.append(tab_thread)
            
            # Start all threads
            for thread in threads:
                thread.start()
            
            # Wait for completion or early termination
            start_time = time.time()
            while time.time() - start_time < duration and self.is_running:
                time.sleep(0.1)
                
                # Check for adaptation triggers
                if time.time() - self.last_adaptation_time > 10:  # Adapt every 10 seconds if needed
                    if random.random() < 0.1:  # 10% chance
                        self.adapt_behavior()
            
        except pyautogui.FailSafeException:
            print("🛑 Bot simulation stopped by failsafe (mouse moved to corner)")
        except Exception as e:
            print(f"❌ Bot simulation error: {str(e)}")
        finally:
            self.is_running = False
            print(f"✅ {self.difficulty.value.title()} bot simulation completed!")
            self.save_learning_data()
    
    def stop_simulation(self):
        """Stop the running simulation"""
        self.is_running = False
        print("🛑 Stopping adversarial bot simulation...")
    
    def save_learning_data(self):
        """Save RL learning data to file"""
        try:
            data = {
                'q_table': self.rl_adapter.q_table,
                'stats': {
                    'total_detections': self.stats.total_detections,
                    'successful_evasions': self.stats.successful_evasions,
                    'adaptation_level': self.stats.adaptation_level,
                    'feature_noise_levels': self.stats.feature_noise_levels
                }
            }
            
            with open('adversarial_bot_learning.json', 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save learning data: {str(e)}")
    
    def load_learning_data(self):
        """Load previous RL learning data"""
        try:
            if os.path.exists('adversarial_bot_learning.json'):
                with open('adversarial_bot_learning.json', 'r') as f:
                    data = json.load(f)
                
                self.rl_adapter.q_table = data.get('q_table', {})
                stats_data = data.get('stats', {})
                
                self.stats.total_detections = stats_data.get('total_detections', 0)
                self.stats.successful_evasions = stats_data.get('successful_evasions', 0)
                self.stats.adaptation_level = stats_data.get('adaptation_level', 0.0)
                
                if 'feature_noise_levels' in stats_data:
                    self.stats.feature_noise_levels.update(stats_data['feature_noise_levels'])
                
                print(f"📚 Loaded learning data: {self.stats.successful_evasions}/{self.stats.total_detections} previous evasions")
                
        except Exception as e:
            print(f"Warning: Could not load learning data: {str(e)}")
    
    def get_stats(self) -> Dict:
        """Get current bot statistics"""
        total_attempts = self.stats.total_detections + self.stats.successful_evasions
        success_rate = self.stats.successful_evasions / max(1, total_attempts)
        
        return {
            'difficulty': self.difficulty.value,
            'total_attempts': total_attempts,
            'detections': self.stats.total_detections,
            'successful_evasions': self.stats.successful_evasions,
            'success_rate': success_rate,
            'adaptation_level': self.stats.adaptation_level,
            'feature_noise_levels': self.stats.feature_noise_levels.copy(),
            'is_running': self.is_running
        }

# Example usage and testing
if __name__ == "__main__":
    print("🤖 Testing Advanced Adversarial Bot System")
    
    # Test different difficulty levels
    for difficulty in BotDifficulty:
        print(f"\n{'='*50}")
        print(f"Testing {difficulty.value.upper()} difficulty")
        print(f"{'='*50}")
        
        bot = AdvancedAdversarialBot(difficulty)
        
        # Simulate detection feedback
        def mock_detection_callback(is_detected):
            bot.on_detection_feedback(is_detected)
        
        bot.set_detection_callback(mock_detection_callback)
        
        # Run short test
        bot.run_simulation(duration=5.0)
        
        # Print stats
        stats = bot.get_stats()
        print(f"📊 Final Stats: {stats}")
        
        time.sleep(2)  # Brief pause between tests
    
    print("\n✅ Adversarial bot system testing completed!")
