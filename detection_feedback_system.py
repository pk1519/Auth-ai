"""
Enhanced Detection Feedback System for AuthAI

Features:
- Improved visual and audio alerts for bot detection
- Comprehensive logging and analytics
- Performance metrics and reporting
- Real-time statistics tracking
- Clear labeling of simulation vs real behavior
- Integration with behavior simulators
"""

import json
import csv
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import deque, defaultdict
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np

@dataclass
class DetectionEvent:
    """Single detection event data"""
    timestamp: datetime
    user_id: str
    session_id: str
    is_bot_detected: bool
    confidence_score: float
    model_used: str
    features: Dict[str, float]
    source_type: str  # 'real_user', 'simulation', 'dataset_replay'
    simulation_profile: Optional[str] = None
    simulation_mode: Optional[str] = None

@dataclass
class DetectionStats:
    """Detection statistics for analysis"""
    total_events: int = 0
    bot_detections: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    avg_confidence: float = 0.0
    detection_rate: float = 0.0
    last_detection: Optional[datetime] = None

class AlertSystem:
    """Enhanced alert system for bot detection"""
    
    def __init__(self):
        self.alert_callbacks = []
        self.alert_history = deque(maxlen=1000)
        self.sound_enabled = True
        self.visual_enabled = True
        
    def register_alert_callback(self, callback: Callable[[DetectionEvent], None]):
        """Register callback for alert notifications"""
        self.alert_callbacks.append(callback)
    
    def trigger_alert(self, detection_event: DetectionEvent):
        """Trigger all alert mechanisms"""
        alert_data = {
            'timestamp': detection_event.timestamp.isoformat(),
            'user_id': detection_event.user_id,
            'session_id': detection_event.session_id,
            'confidence_score': detection_event.confidence_score,
            'model_used': detection_event.model_used,
            'source_type': detection_event.source_type,
            'simulation_profile': detection_event.simulation_profile,
            'simulation_mode': detection_event.simulation_mode
        }
        
        # Add to history
        self.alert_history.append(alert_data)
        
        # Call all registered callbacks
        for callback in self.alert_callbacks:
            try:
                callback(detection_event)
            except Exception as e:
                print(f"⚠️ Alert callback error: {e}")
        
        # Console output
        source_info = ""
        if detection_event.source_type == 'simulation':
            source_info = f" [SIMULATION: {detection_event.simulation_profile}/{detection_event.simulation_mode}]"
        elif detection_event.source_type == 'dataset_replay':
            source_info = " [DATASET REPLAY]"
        
        print(f"🚨 BOT DETECTED{source_info}: User {detection_event.user_id} "
              f"(Score: {detection_event.confidence_score:.3f}, Model: {detection_event.model_used})")
    
    def get_recent_alerts(self, minutes: int = 10) -> List[Dict]:
        """Get recent alerts within specified time window"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_alerts = []
        
        for alert in self.alert_history:
            alert_time = datetime.fromisoformat(alert['timestamp'])
            if alert_time >= cutoff_time:
                recent_alerts.append(alert)
        
        return recent_alerts

class DetectionLogger:
    """Comprehensive logging system for detection events"""
    
    def __init__(self, log_file: str = 'enhanced_detections_log.csv'):
        self.log_file = log_file
        self.ensure_log_file()
        
    def ensure_log_file(self):
        """Ensure log file exists with proper headers"""
        if not os.path.exists(self.log_file):
            headers = [
                'timestamp', 'user_id', 'session_id', 'is_bot_detected', 
                'confidence_score', 'model_used', 'source_type',
                'simulation_profile', 'simulation_mode', 'avg_mouse_speed',
                'avg_typing_speed', 'tab_switch_rate', 'mouse_click_rate',
                'keyboard_error_rate', 'active_window_duration'
            ]
            
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    
    def log_detection(self, detection_event: DetectionEvent):
        """Log detection event to CSV file"""
        try:
            with open(self.log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                row = [
                    detection_event.timestamp.isoformat(),
                    detection_event.user_id,
                    detection_event.session_id,
                    detection_event.is_bot_detected,
                    detection_event.confidence_score,
                    detection_event.model_used,
                    detection_event.source_type,
                    detection_event.simulation_profile or '',
                    detection_event.simulation_mode or '',
                    detection_event.features.get('avg_mouse_speed', 0),
                    detection_event.features.get('avg_typing_speed', 0),
                    detection_event.features.get('tab_switch_rate', 0),
                    detection_event.features.get('mouse_click_rate', 0),
                    detection_event.features.get('keyboard_error_rate', 0),
                    detection_event.features.get('active_window_duration', 0)
                ]
                writer.writerow(row)
        except Exception as e:
            print(f"⚠️ Logging error: {e}")
    
    def get_detection_history(self, days: int = 7) -> pd.DataFrame:
        """Get detection history as DataFrame"""
        try:
            df = pd.read_csv(self.log_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_df = df[df['timestamp'] >= cutoff_date]
            
            return recent_df
        except Exception as e:
            print(f"⚠️ Error loading detection history: {e}")
            return pd.DataFrame()

class PerformanceAnalyzer:
    """Analyze detection system performance"""
    
    def __init__(self, logger: DetectionLogger):
        self.logger = logger
    
    def calculate_model_performance(self, days: int = 7) -> Dict[str, Dict]:
        """Calculate performance metrics by model"""
        df = self.logger.get_detection_history(days)
        
        if df.empty:
            return {}
        
        performance = {}
        
        for model in df['model_used'].unique():
            model_df = df[df['model_used'] == model]
            
            # Calculate metrics
            total = len(model_df)
            detections = len(model_df[model_df['is_bot_detected'] == True])
            
            # Separate real vs simulation performance
            real_df = model_df[model_df['source_type'] == 'real_user']
            sim_df = model_df[model_df['source_type'].isin(['simulation', 'dataset_replay'])]
            
            performance[model] = {
                'total_events': total,
                'bot_detections': detections,
                'detection_rate': detections / max(1, total) * 100,
                'avg_confidence': model_df['confidence_score'].mean(),
                'real_user_events': len(real_df),
                'simulation_events': len(sim_df),
                'real_user_detections': len(real_df[real_df['is_bot_detected'] == True]),
                'simulation_detections': len(sim_df[sim_df['is_bot_detected'] == True])
            }
        
        return performance
    
    def calculate_profile_performance(self, days: int = 7) -> Dict[str, Dict]:
        """Calculate performance metrics by simulation profile"""
        df = self.logger.get_detection_history(days)
        
        if df.empty:
            return {}
        
        # Filter to only simulation data
        sim_df = df[df['source_type'].isin(['simulation', 'dataset_replay'])]
        sim_df = sim_df[sim_df['simulation_profile'].notna()]
        
        performance = {}
        
        for profile in sim_df['simulation_profile'].unique():
            profile_df = sim_df[sim_df['simulation_profile'] == profile]
            
            total = len(profile_df)
            detections = len(profile_df[profile_df['is_bot_detected'] == True])
            
            performance[profile] = {
                'total_events': total,
                'bot_detections': detections,
                'detection_rate': detections / max(1, total) * 100,
                'avg_confidence': profile_df['confidence_score'].mean(),
                'modes_tested': profile_df['simulation_mode'].unique().tolist()
            }
        
        return performance
    
    def generate_summary_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive performance summary"""
        df = self.logger.get_detection_history(days)
        
        if df.empty:
            return {'error': 'No data available'}
        
        # Overall stats
        total_events = len(df)
        bot_detections = len(df[df['is_bot_detected'] == True])
        
        # By source type
        real_events = len(df[df['source_type'] == 'real_user'])
        sim_events = len(df[df['source_type'] == 'simulation'])
        replay_events = len(df[df['source_type'] == 'dataset_replay'])
        
        # Detection rates by source
        real_detections = len(df[(df['source_type'] == 'real_user') & (df['is_bot_detected'] == True)])
        sim_detections = len(df[(df['source_type'] == 'simulation') & (df['is_bot_detected'] == True)])
        replay_detections = len(df[(df['source_type'] == 'dataset_replay') & (df['is_bot_detected'] == True)])
        
        report = {
            'period': f'Last {days} days',
            'total_events': total_events,
            'bot_detections': bot_detections,
            'overall_detection_rate': bot_detections / max(1, total_events) * 100,
            'avg_confidence': df['confidence_score'].mean(),
            
            'by_source': {
                'real_user': {
                    'events': real_events,
                    'detections': real_detections,
                    'detection_rate': real_detections / max(1, real_events) * 100
                },
                'simulation': {
                    'events': sim_events,
                    'detections': sim_detections,
                    'detection_rate': sim_detections / max(1, sim_events) * 100
                },
                'dataset_replay': {
                    'events': replay_events,
                    'detections': replay_detections,
                    'detection_rate': replay_detections / max(1, replay_events) * 100
                }
            },
            
            'model_performance': self.calculate_model_performance(days),
            'profile_performance': self.calculate_profile_performance(days),
            
            'recommendations': self._generate_recommendations(df)
        }
        
        return report
    
    def _generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate recommendations based on performance analysis"""
        recommendations = []
        
        # Check overall detection rate
        total_events = len(df)
        bot_detections = len(df[df['is_bot_detected'] == True])
        overall_rate = bot_detections / max(1, total_events) * 100
        
        if overall_rate > 80:
            recommendations.append("High detection rate (>80%) - system may be too sensitive")
        elif overall_rate < 10:
            recommendations.append("Low detection rate (<10%) - system may need tuning")
        
        # Check simulation vs real user detection rates
        real_df = df[df['source_type'] == 'real_user']
        sim_df = df[df['source_type'] == 'simulation']
        
        if not real_df.empty and not sim_df.empty:
            real_rate = len(real_df[real_df['is_bot_detected'] == True]) / len(real_df) * 100
            sim_rate = len(sim_df[sim_df['is_bot_detected'] == True]) / len(sim_df) * 100
            
            if real_rate > 20:
                recommendations.append(f"High false positive rate on real users ({real_rate:.1f}%)")
            
            if sim_rate < 60:
                recommendations.append(f"Low detection rate on simulations ({sim_rate:.1f}%) - simulator may be too realistic")
        
        # Check model consistency
        models = df['model_used'].unique()
        if len(models) > 1:
            model_rates = {}
            for model in models:
                model_df = df[df['model_used'] == model]
                rate = len(model_df[model_df['is_bot_detected'] == True]) / len(model_df) * 100
                model_rates[model] = rate
            
            max_rate = max(model_rates.values())
            min_rate = min(model_rates.values())
            
            if max_rate - min_rate > 30:
                recommendations.append("Large variance in detection rates between models - consider ensemble approach")
        
        return recommendations

class EnhancedDetectionFeedback:
    """Main enhanced detection feedback system"""
    
    def __init__(self, log_file: str = 'enhanced_detections_log.csv'):
        self.alert_system = AlertSystem()
        self.logger = DetectionLogger(log_file)
        self.analyzer = PerformanceAnalyzer(self.logger)
        
        # Statistics tracking
        self.session_stats = defaultdict(DetectionStats)
        self.global_stats = DetectionStats()
        
        # Real-time monitoring
        self.detection_queue = deque(maxlen=100)
        self.monitoring_callbacks = []
        
    def register_monitoring_callback(self, callback: Callable[[Dict], None]):
        """Register callback for real-time monitoring updates"""
        self.monitoring_callbacks.append(callback)
    
    def process_detection(self, detection_data: Dict, source_type: str = 'real_user',
                         simulation_profile: str = None, simulation_mode: str = None):
        """Process a detection event and trigger appropriate responses"""
        
        # Create detection event
        detection_event = DetectionEvent(
            timestamp=datetime.now(),
            user_id=detection_data.get('user_id', 'unknown'),
            session_id=detection_data.get('session_id', f"session_{int(time.time())}"),
            is_bot_detected=detection_data.get('is_improper', 0) == 1,
            confidence_score=detection_data.get('score', 0.0),
            model_used=detection_data.get('model', 'unknown'),
            features={
                'avg_mouse_speed': detection_data.get('avg_mouse_speed', 0),
                'avg_typing_speed': detection_data.get('avg_typing_speed', 0),
                'tab_switch_rate': detection_data.get('tab_switch_rate', 0),
                'mouse_click_rate': detection_data.get('mouse_click_rate', 0),
                'keyboard_error_rate': detection_data.get('keyboard_error_rate', 0),
                'active_window_duration': detection_data.get('active_window_duration', 0)
            },
            source_type=source_type,
            simulation_profile=simulation_profile,
            simulation_mode=simulation_mode
        )
        
        # Add to queue for real-time monitoring
        self.detection_queue.append(asdict(detection_event))
        
        # Log the event
        self.logger.log_detection(detection_event)
        
        # Update statistics
        self._update_statistics(detection_event)
        
        # Trigger alerts if bot detected
        if detection_event.is_bot_detected:
            self.alert_system.trigger_alert(detection_event)
        
        # Call monitoring callbacks
        for callback in self.monitoring_callbacks:
            try:
                callback(asdict(detection_event))
            except Exception as e:
                print(f"⚠️ Monitoring callback error: {e}")
        
        return detection_event
    
    def _update_statistics(self, detection_event: DetectionEvent):
        """Update internal statistics"""
        # Update global stats
        self.global_stats.total_events += 1
        if detection_event.is_bot_detected:
            self.global_stats.bot_detections += 1
        
        self.global_stats.detection_rate = (
            self.global_stats.bot_detections / self.global_stats.total_events * 100
        )
        self.global_stats.last_detection = detection_event.timestamp
        
        # Calculate running average confidence
        if self.global_stats.total_events == 1:
            self.global_stats.avg_confidence = detection_event.confidence_score
        else:
            # Exponential moving average
            alpha = 0.1
            self.global_stats.avg_confidence = (
                alpha * detection_event.confidence_score + 
                (1 - alpha) * self.global_stats.avg_confidence
            )
        
        # Update session-specific stats
        session_id = detection_event.session_id
        session_stats = self.session_stats[session_id]
        session_stats.total_events += 1
        
        if detection_event.is_bot_detected:
            session_stats.bot_detections += 1
        
        session_stats.detection_rate = (
            session_stats.bot_detections / session_stats.total_events * 100
        )
        session_stats.last_detection = detection_event.timestamp
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time statistics for dashboard"""
        recent_events = list(self.detection_queue)[-20:]  # Last 20 events
        
        if not recent_events:
            return {
                'recent_detection_rate': 0,
                'recent_avg_confidence': 0,
                'total_events': self.global_stats.total_events,
                'total_detections': self.global_stats.bot_detections,
                'overall_detection_rate': self.global_stats.detection_rate,
                'last_detection': None
            }
        
        recent_detections = sum(1 for event in recent_events if event['is_bot_detected'])
        recent_confidences = [event['confidence_score'] for event in recent_events]
        
        return {
            'recent_detection_rate': recent_detections / len(recent_events) * 100,
            'recent_avg_confidence': np.mean(recent_confidences),
            'total_events': self.global_stats.total_events,
            'total_detections': self.global_stats.bot_detections,
            'overall_detection_rate': self.global_stats.detection_rate,
            'last_detection': self.global_stats.last_detection.isoformat() if self.global_stats.last_detection else None,
            'recent_events': recent_events
        }
    
    def generate_performance_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive dashboard data"""
        # Get analysis reports
        summary_report = self.analyzer.generate_summary_report(days=7)
        real_time_stats = self.get_real_time_stats()
        recent_alerts = self.alert_system.get_recent_alerts(minutes=30)
        
        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'real_time_stats': real_time_stats,
            'weekly_summary': summary_report,
            'recent_alerts': recent_alerts,
            'system_health': self._assess_system_health(summary_report, real_time_stats)
        }
        
        return dashboard
    
    def _assess_system_health(self, summary: Dict, real_time: Dict) -> Dict[str, Any]:
        """Assess overall system health"""
        health_score = 100  # Start with perfect score
        issues = []
        warnings = []
        
        # Check detection rates
        overall_rate = real_time.get('overall_detection_rate', 0)
        recent_rate = real_time.get('recent_detection_rate', 0)
        
        if overall_rate > 90:
            health_score -= 20
            issues.append("Very high detection rate - possible oversensitivity")
        elif overall_rate < 5:
            health_score -= 15
            issues.append("Very low detection rate - possible undersensitivity")
        
        # Check rate consistency
        if abs(overall_rate - recent_rate) > 30:
            health_score -= 10
            warnings.append("Detection rate variance - system behavior may be inconsistent")
        
        # Check confidence levels
        avg_confidence = real_time.get('recent_avg_confidence', 0)
        if avg_confidence < 0.3:
            health_score -= 10
            warnings.append("Low confidence scores - model may need retraining")
        
        # Check data availability
        total_events = real_time.get('total_events', 0)
        if total_events < 10:
            health_score -= 5
            warnings.append("Limited data available - more testing recommended")
        
        # Determine overall health status
        if health_score >= 85:
            status = "Excellent"
        elif health_score >= 70:
            status = "Good"
        elif health_score >= 50:
            status = "Fair"
        else:
            status = "Needs Attention"
        
        return {
            'score': max(0, health_score),
            'status': status,
            'issues': issues,
            'warnings': warnings
        }
    
    def export_analysis_report(self, filename: str = None) -> str:
        """Export comprehensive analysis report"""
        if filename is None:
            filename = f"detection_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        dashboard_data = self.generate_performance_dashboard()
        
        # Add additional analysis
        extended_report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'Enhanced Detection System Analysis',
                'version': '2.0.0'
            },
            'dashboard_data': dashboard_data,
            'detailed_analysis': {
                'model_performance': self.analyzer.calculate_model_performance(30),
                'profile_performance': self.analyzer.calculate_profile_performance(30)
            }
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(extended_report, f, indent=2, default=str)
            
            print(f"📊 Analysis report exported to {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error exporting report: {e}")
            return ""

# Factory function for easy initialization
def create_detection_feedback_system(log_file: str = 'enhanced_detections_log.csv') -> EnhancedDetectionFeedback:
    """Factory function to create detection feedback system"""
    return EnhancedDetectionFeedback(log_file)

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Enhanced Detection Feedback System")
    print("="*60)
    
    # Initialize system
    feedback_system = create_detection_feedback_system('test_detections.csv')
    
    # Register test alert callback
    def test_alert_callback(detection_event: DetectionEvent):
        print(f"🔔 ALERT TRIGGERED: {detection_event.user_id} - {detection_event.confidence_score:.3f}")
    
    feedback_system.alert_system.register_alert_callback(test_alert_callback)
    
    # Simulate some detection events
    test_events = [
        {
            'user_id': 'test_user_1',
            'session_id': 'session_001',
            'is_improper': 0,
            'score': 0.2,
            'model': 'RandomForest',
            'avg_mouse_speed': 250,
            'avg_typing_speed': 300,
            'tab_switch_rate': 1.2,
            'mouse_click_rate': 15,
            'keyboard_error_rate': 0.03,
            'active_window_duration': 45
        },
        {
            'user_id': 'sim_bot_1',
            'session_id': 'session_002', 
            'is_improper': 1,
            'score': 0.85,
            'model': 'Transformer',
            'avg_mouse_speed': 800,
            'avg_typing_speed': 1200,
            'tab_switch_rate': 5.0,
            'mouse_click_rate': 60,
            'keyboard_error_rate': 0.0,
            'active_window_duration': 120
        }
    ]
    
    print("\n🔬 Processing test detection events...")
    for i, event in enumerate(test_events):
        source = 'real_user' if i == 0 else 'simulation'
        profile = None if i == 0 else 'casual_user'
        mode = None if i == 0 else 'basic_variability'
        
        feedback_system.process_detection(event, source, profile, mode)
        time.sleep(1)
    
    # Get real-time stats
    print("\n📊 Real-time statistics:")
    stats = feedback_system.get_real_time_stats()
    for key, value in stats.items():
        if key != 'recent_events':
            print(f"  {key}: {value}")
    
    # Generate performance report
    print("\n📋 Generating performance dashboard...")
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
    report_file = feedback_system.export_analysis_report('test_analysis_report.json')
    if report_file:
        print(f"📄 Full report saved to: {report_file}")
    
    print("\n✅ Enhanced detection feedback system testing completed!")
