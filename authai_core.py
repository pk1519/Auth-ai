"""
AuthAI Core Module

Real-time AuthAI detector that:
- collects behavioral features automatically
- loads saved models from ./models/
- flags users/bots in real-time and logs events
- includes a bot simulator that performs abnormal activity (will be flagged)
"""

import time
import math
import random
import threading
import subprocess
import platform
from collections import deque, defaultdict
from datetime import datetime
import numpy as np
import pandas as pd
import joblib
import os

# Optional imports (wrapped in try/except)
try:
    from pynput import mouse, keyboard
except Exception:
    mouse = None
    keyboard = None

try:
    import pyautogui
except Exception:
    pyautogui = None

try:
    import tensorflow as tf
    from tensorflow import keras
except Exception:
    tf = None
    keras = None

# Import advanced adversarial bot if available
try:
    from adversarial_bot import AdvancedAdversarialBot, BotDifficulty
except ImportError:
    print("Warning: Adversarial bot module not found. Using basic bot simulator.")
    AdvancedAdversarialBot = None
    BotDifficulty = None

# ----------------------------
# CONFIG
MODE = "real"    # "real" (capture real events) or "simulate" (stream dataset rows for testing)
DATASET_PATH = "user_behavior_dataset.csv"  # used in simulate mode
MODELS_FOLDER = "models"
DETECTION_INTERVAL = 5.0   # seconds between feature computation & model call
WINDOW_SECONDS = 30.0      # sliding window length for statistics (seconds)
SEQ_DEQUE_MAX = 200        # maximum slots for sequence history (we'll trim to model need)

CLASSIFIER_THRESHOLD = 0.5   # probability threshold for classifier -> improper if > threshold
ISO_PERCENTILE = 85          # percentile threshold for IsolationForest scores (if used)
AE_PERCENTILE = 90           # threshold percentile for autoencoder recon error where applicable

LOG_PATH = "detections_log.csv"

# ----------------------------
# UTIL: active window title (cross-platform)
def get_active_window_title():
    system = platform.system()
    try:
        if system == "Windows":
            try:
                import win32gui
                hwnd = win32gui.GetForegroundWindow()
                return win32gui.GetWindowText(hwnd)
            except Exception:
                # fallback to pygetwindow if available
                try:
                    import pygetwindow as gw
                    w = gw.getActiveWindow()
                    return w.title if w else None
                except Exception:
                    return None
        elif system == "Linux":
            # requires xdotool on system
            try:
                out = subprocess.check_output(["xdotool", "getactivewindow", "getwindowname"], stderr=subprocess.DEVNULL)
                return out.decode().strip()
            except Exception:
                return None
        elif system == "Darwin":  # macOS
            try:
                script = 'tell application "System Events" to get name of (processes where frontmost is true)'
                out = subprocess.check_output(["osascript", "-e", script])
                return out.decode().strip()
            except Exception:
                return None
        else:
            return None
    except Exception:
        return None

# ----------------------------
# Load the best model (auto-detect from results file)
def load_best_model_and_meta(models_folder=MODELS_FOLDER):
    """Load the best performing model based on comparison results or fallback priorities"""
    # Expected filenames (from your notebook)
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
            print(f"\n📊 Model Performance Comparison:")
            print(f"{'Model':<15} {'ROC-AUC':<8} {'Accuracy':<8} {'F1-Score':<8}")
            print("-" * 45)
            
            # Sort by ROC-AUC score (primary metric)
            df_sorted = df.sort_values('roc_auc', ascending=False)
            
            for _, row in df_sorted.iterrows():
                model_name = row['model']
                roc_auc = row.get('roc_auc', 0)
                accuracy = row.get('accuracy', 0)
                f1_score = row.get('f1_score', 0)
                
                print(f"{model_name:<15} {roc_auc:<8.3f} {accuracy:<8.3f} {f1_score:<8.3f}")
                
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
        # Priority order: Transformer -> LSTM -> XGB -> RF -> ISO -> AE
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
            raise FileNotFoundError("No trained models found in the models directory!")

    # load model
    model = None
    model_path = fallback_names.get(best_model_name)
    if model_path and os.path.exists(model_path):
        if best_model_name in ("RandomForest", "XGBoost", "GradientBoosting", "IsolationForest"):
            model = joblib.load(model_path)
        else:
            if tf is None:
                raise RuntimeError("Keras/TensorFlow not available but a sequential model is selected. Install tensorflow.")
            model = tf.keras.models.load_model(model_path)
    else:
        raise FileNotFoundError(f"Couldn't find saved model for best model ({best_model_name}). Looked at {model_path}")

    # load scaler if present
    scaler = None
    scaler_path = os.path.join(models_folder, "authai_scaler.joblib")
    if not os.path.exists(scaler_path):
        scaler_path = os.path.join(models_folder, "authai_scaler.pkl")
    if os.path.exists(scaler_path):
        scaler = joblib.load(scaler_path)
    else:
        # try generic scaler saved earlier named 'scaler' in workspace (common when building)
        try:
            scaler = joblib.load(os.path.join(models_folder, "scaler.joblib"))
        except Exception:
            scaler = None

    # load AE threshold meta if exists
    ae_meta = None
    ae_meta_path = os.path.join(models_folder, "authai_ae_meta.joblib")
    if os.path.exists(ae_meta_path):
        try:
            ae_meta = joblib.load(ae_meta_path)
        except Exception:
            ae_meta = None

    return best_model_name, model, scaler, ae_meta

# ----------------------------
# RealTimeMonitor: captures events and computes features periodically
class RealTimeMonitor:
    def __init__(self, best_model_name, model, scaler=None, ae_meta=None,
                 window_seconds=WINDOW_SECONDS, detection_interval=DETECTION_INTERVAL, seq_deque_max=SEQ_DEQUE_MAX):
        self.best_model_name = best_model_name
        self.model = model
        self.scaler = scaler
        self.ae_meta = ae_meta
        self.window_seconds = window_seconds
        self.detection_interval = detection_interval

        # raw event buffers (timestamped)
        self.mouse_positions = deque()   # entries: (t, x, y)
        self.mouse_clicks = deque()      # timestamps
        self.key_presses = deque()       # timestamps
        self.backspace_presses = deque() # timestamps (to approximate keyboard errors)
        self.active_window_history = deque()  # entries: (t, title)

        # sequence history of computed feature vectors
        self.feature_seq = deque(maxlen=seq_deque_max)  # each: numpy array of shape (n_features,)

        # for listeners
        self._mouse_listener = None
        self._kb_listener = None

        # state
        self.running = False
        self.user_id = os.getenv("USER") or os.getenv("USERNAME") or "LOCAL_USER"

    # --- event handlers
    def _on_move(self, x, y):
        self.mouse_positions.append((time.time(), float(x), float(y)))
        # trim old
        self._trim_old()

    def _on_click(self, x, y, button, pressed):
        if pressed:
            self.mouse_clicks.append(time.time())
            self._trim_old()

    def _on_key(self, key):
        ts = time.time()
        self.key_presses.append(ts)
        # approximate an "error" as backspace or delete press
        try:
            if key == keyboard.Key.backspace or key == keyboard.Key.delete:
                self.backspace_presses.append(ts)
        except Exception:
            # some Key code objects
            kstr = str(key).lower()
            if "backspace" in kstr or "delete" in kstr:
                self.backspace_presses.append(ts)
        self._trim_old()

    # trim all buffers older than window_seconds
    def _trim_old(self):
        cutoff = time.time() - self.window_seconds
        while self.mouse_positions and self.mouse_positions[0][0] < cutoff:
            self.mouse_positions.popleft()
        while self.mouse_clicks and self.mouse_clicks[0] < cutoff:
            self.mouse_clicks.popleft()
        while self.key_presses and self.key_presses[0] < cutoff:
            self.key_presses.popleft()
        while self.backspace_presses and self.backspace_presses[0] < cutoff:
            self.backspace_presses.popleft()
        while self.active_window_history and self.active_window_history[0][0] < cutoff:
            self.active_window_history.popleft()

    # poll active window periodically (separate thread)
    def _poll_active_window(self):
        last_title = None
        last_change = time.time()
        while self.running:
            title = get_active_window_title()
            ts = time.time()
            if title is None:
                # still record something (None is fine)
                if not self.active_window_history or self.active_window_history[-1][1] != "UNKNOWN":
                    self.active_window_history.append((ts, "UNKNOWN"))
            else:
                if last_title != title:
                    # focus changed
                    self.active_window_history.append((ts, title))
                    last_title = title
            self._trim_old()
            time.sleep(0.5)

    # compute aggregated features from the current buffers
    def compute_features(self):
        self._trim_old()
        now = time.time()
        cutoff = now - self.window_seconds

        # mouse speed: compute total distance / total time
        positions = list(self.mouse_positions)
        total_dist = 0.0
        total_time = 0.0
        for i in range(1, len(positions)):
            t0, x0, y0 = positions[i-1]
            t1, x1, y1 = positions[i]
            dt = max(1e-6, t1 - t0)
            total_dist += math.hypot(x1 - x0, y1 - y0)
            total_time += dt
        avg_mouse_speed = (total_dist / total_time) if total_time > 0 else 0.0  # pixels per sec

        # keyboard typing speed (keystrokes per minute)
        key_count = len(self.key_presses)
        avg_typing_speed = (key_count / self.window_seconds) * 60.0

        # tab_switch rate (switches per minute) -> count of unique active window title changes
        switch_count = 0
        titles = [t for (ts, t) in self.active_window_history]
        if len(titles) > 1:
            # count changes between consecutive titles
            for i in range(1, len(titles)):
                if titles[i] != titles[i-1]:
                    switch_count += 1
        tab_switch_rate = (switch_count / self.window_seconds) * 60.0

        # mouse click rate (clicks per minute)
        mouse_click_rate = (len(self.mouse_clicks) / self.window_seconds) * 60.0

        # keyboard error rate (% errors) approximated by backspace / total keystrokes * 100
        keyboard_error_rate = (len(self.backspace_presses) / key_count * 100.0) if key_count > 0 else 0.0

        # active window duration: average time per active window in seconds (approx)
        durations = []
        hist = list(self.active_window_history)
        if len(hist) >= 2:
            for i in range(1, len(hist)):
                durations.append(hist[i][0] - hist[i-1][0])
        # include time since last change
        if hist:
            durations.append(now - hist[-1][0])
        active_window_duration = (sum(durations) / len(durations)) if durations else self.window_seconds

        features = {
            "user_id": self.user_id,
            "avg_mouse_speed": float(avg_mouse_speed),
            "avg_typing_speed": float(avg_typing_speed),
            "tab_switch_rate": float(tab_switch_rate),
            "mouse_click_rate": float(mouse_click_rate),
            "keyboard_error_rate": float(keyboard_error_rate),
            "active_window_duration": float(active_window_duration)
        }
        return features

    # push features into sequence deque (for seq models)
    def push_features_seq(self, features):
        vec = np.array([
            features["avg_mouse_speed"],
            features["avg_typing_speed"],
            features["tab_switch_rate"],
            features["mouse_click_rate"],
            features["keyboard_error_rate"],
            features["active_window_duration"]
        ], dtype=float)
        self.feature_seq.append(vec)

    # prepare model input (tabular or sequence) based on model type
    def prepare_input_for_model(self):
        n_features = 6
        if self.best_model_name in ("LSTM", "Transformer"):
            # determine required seq length from model input shape if available
            seq_len_needed = None
            try:
                shape = self.model.input_shape  # (None, seq_len, n_features) or similar
                if isinstance(shape, tuple) or isinstance(shape, list):
                    seq_len_needed = int(shape[1])
            except Exception:
                seq_len_needed = None
            if seq_len_needed is None:
                seq_len_needed = min(len(self.feature_seq), 50) if len(self.feature_seq) > 0 else 50

            # Build a sequence array with most recent seq_len_needed vectors
            seq_list = list(self.feature_seq)[-seq_len_needed:]
            if len(seq_list) < seq_len_needed:
                # pad by repeating first element or zeros
                if seq_list:
                    pad = [seq_list[0]] * (seq_len_needed - len(seq_list))
                else:
                    pad = [np.zeros(n_features)] * (seq_len_needed - len(seq_list))
                seq_array = np.vstack(pad + seq_list)
            else:
                seq_array = np.vstack(seq_list)

            # scale if scaler exists (we assume scaler is for individual feature scaling)
            if self.scaler is not None:
                flat = seq_array.reshape(-1, n_features)
                flat_s = self.scaler.transform(flat)
                seq_array = flat_s.reshape(1, seq_len_needed, n_features)
            else:
                seq_array = seq_array.reshape(1, seq_len_needed, n_features)
            return seq_array

        else:
            # tabular single vector
            if not self.feature_seq:
                # fallback zero vector
                arr = np.zeros((1, n_features))
            else:
                arr = np.array(self.feature_seq[-1]).reshape(1, n_features)
            if self.scaler is not None:
                arr_s = self.scaler.transform(arr)
                return arr_s
            return arr

    # run detection once
    def run_detection_once(self):
        features = self.compute_features()
        self.push_features_seq(features)

        model_input = self.prepare_input_for_model()

        score = None
        is_improper = False
        reason = None

        # model-specific scoring
        try:
            if self.best_model_name in ("RandomForest", "XGBoost", "GradientBoosting"):
                # classifier: probability of class 1 = improper
                proba = float(self.model.predict_proba(model_input)[:,1][0])
                score = proba
                is_improper = proba >= CLASSIFIER_THRESHOLD
                reason = f"classifier_proba={proba:.3f}"
            elif self.best_model_name == "IsolationForest":
                pred = int(self.model.predict(model_input)[0])
                # model returns 1 for normal, -1 for anomaly
                is_improper = (pred == -1)
                score = float(-self.model.decision_function(model_input)[0])  # higher more anomalous
                reason = f"isof_score={score:.4f}"
            elif self.best_model_name == "Autoencoder":
                if tf is None:
                    raise RuntimeError("Autoencoder selected but tensorflow not installed")
                recon = self.model.predict(model_input)
                mse = float(np.mean(np.square(recon - model_input)))
                score = mse
                # use loaded threshold from ae_meta if present
                thresh = self.ae_meta.get("ae_thresh") if (self.ae_meta and "ae_thresh" in self.ae_meta) else None
                if thresh is None:
                    # fallback to percentile on current mse distribution (conservative)
                    thresh = np.percentile([mse], AE_PERCENTILE)
                is_improper = mse >= thresh
                reason = f"ae_mse={mse:.6f},thr={thresh:.6f}"
            elif self.best_model_name in ("LSTM", "Transformer"):
                if tf is None:
                    raise RuntimeError("Sequential model selected but tensorflow not installed")
                proba = float(self.model.predict(model_input).ravel()[0])
                score = proba
                is_improper = proba >= CLASSIFIER_THRESHOLD
                reason = f"seq_proba={proba:.3f}"
            else:
                # default fallback: use model.predict
                try:
                    out = self.model.predict(model_input)
                    proba = float(np.ravel(out)[0])
                    score = proba
                    is_improper = proba >= CLASSIFIER_THRESHOLD
                    reason = f"fallback_proba={proba:.3f}"
                except Exception as e:
                    score = None
                    is_improper = False
                    reason = f"error:{e}"
        except Exception as e:
            # model execution error should not crash monitoring loop
            score = None
            is_improper = False
            reason = f"model_error:{e}"

        # log event
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": features["user_id"],
            "avg_mouse_speed": features["avg_mouse_speed"],
            "avg_typing_speed": features["avg_typing_speed"],
            "tab_switch_rate": features["tab_switch_rate"],
            "mouse_click_rate": features["mouse_click_rate"],
            "keyboard_error_rate": features["keyboard_error_rate"],
            "active_window_duration": features["active_window_duration"],
            "model": self.best_model_name,
            "score": score,
            "is_improper": int(is_improper),
            "reason": reason
        }
        self._append_log(event)

        # immediate action when improper
        if is_improper:
            print(f"[ALERT] {event['timestamp']} - USER {event['user_id']} FLAGGED -> {reason} (score={score})")
            # placeholder for actions: block session, notify, etc.
        else:
            print(f"[OK] {event['timestamp']} - USER {event['user_id']} OK -> {reason} (score={score})")
        return event

    # append to logfile
    def _append_log(self, event):
        cols = ["timestamp","user_id","avg_mouse_speed","avg_typing_speed","tab_switch_rate",
                "mouse_click_rate","keyboard_error_rate","active_window_duration",
                "model","score","is_improper","reason"]
        df = pd.DataFrame([event])
        header = not os.path.exists(LOG_PATH)
        df.to_csv(LOG_PATH, mode='a', index=False, header=header)

    # main loop: compute and detect periodically
    def _detection_loop(self):
        while self.running:
            try:
                self.run_detection_once()
            except Exception as e:
                print("Detection error:", e)
            time.sleep(self.detection_interval)

    # start listeners and threads
    def start(self):
        if self.running:
            return
        self.running = True

        # start polling active window thread
        self._poll_thread = threading.Thread(target=self._poll_active_window, daemon=True)
        self._poll_thread.start()

        # start listeners for mouse/keyboard if available
        if mouse:
            self._mouse_listener = mouse.Listener(on_move=self._on_move, on_click=self._on_click)
            self._mouse_listener.start()
        else:
            print("pynput.mouse not available; mouse events not captured.")

        if keyboard:
            self._kb_listener = keyboard.Listener(on_press=self._on_key)
            self._kb_listener.start()
        else:
            print("pynput.keyboard not available; keyboard events not captured.")

        # start detection loop
        self._detect_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self._detect_thread.start()
        print("RealTimeMonitor started.")

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._kb_listener:
            self._kb_listener.stop()
        print("RealTimeMonitor stopped.")


# ----------------------------
# BotSimulator: performs automated abnormal activity (will be flagged)
class BotSimulator:
    def __init__(self, duration_sec=20, step_interval=0.02):
        self.duration = duration_sec
        self.step_interval = step_interval

    def run(self):
        if pyautogui is None:
            raise RuntimeError("pyautogui not installed. Install it to run the bot simulator.")
        print("Starting bot simulator (will move mouse, click, and type) — move mouse to top-left to abort.")
        end = time.time() + self.duration
        try:
            while time.time() < end:
                # fast mouse motion
                dx = random.randint(-300, 300)
                dy = random.randint(-300, 300)
                pyautogui.moveRel(dx, dy, duration=self.step_interval)
                # click occasionally
                if random.random() < 0.2:
                    pyautogui.click()
                # type very fast occasionally
                if random.random() < 0.05:
                    s = "botspam" * random.randint(5, 20)
                    pyautogui.typewrite(s, interval=0.01)
                time.sleep(0.02)
        except pyautogui.FailSafeException:
            print("Bot simulator aborted by moving mouse to a corner (pyautogui failsafe).")
        print("Bot simulator finished.")


# ----------------------------
# Simulation mode: stream rows from a CSV dataset (useful if you cannot capture live events)
def run_simulation_stream(monitor, dataset_path=DATASET_PATH, interval=1.0, loop=False):
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"{dataset_path} not found for simulation mode.")
    df = pd.read_csv(dataset_path)
    # ensure columns exist
    required = ["user_id","avg_mouse_speed","avg_typing_speed","tab_switch_rate",
                "mouse_click_rate","keyboard_error_rate","active_window_duration"]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"Dataset missing column: {c}")
    print("Starting simulation stream from dataset...")
    try:
        while True:
            for _, row in df.iterrows():
                # feed into monitor buffers directly
                # For simplicity we set the monitor's feature_seq to the row value and run detection
                features = {
                    "user_id": row["user_id"],
                    "avg_mouse_speed": float(row["avg_mouse_speed"]),
                    "avg_typing_speed": float(row["avg_typing_speed"]),
                    "tab_switch_rate": float(row["tab_switch_rate"]),
                    "mouse_click_rate": float(row["mouse_click_rate"]),
                    "keyboard_error_rate": float(row["keyboard_error_rate"]),
                    "active_window_duration": float(row["active_window_duration"])
                }
                monitor.push_features_seq(features)
                # run detection using the latest seq/window
                event = monitor.run_detection_once()
                time.sleep(interval)
            if not loop:
                break
    except KeyboardInterrupt:
        print("Simulation stream interrupted by user.")
