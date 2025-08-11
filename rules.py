"""
Mood Sentinel - Rules Engine
This module contains the business rules for mood detection and alerting.
It evaluates mood scores and determines when to trigger notifications.
"""
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

class MoodRules:
    """
    Business rules engine for mood monitoring and alerting.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Load thresholds from config
        self.critical_threshold = config.get('critical_threshold', 0.2)
        self.warning_threshold = config.get('warning_threshold', 0.4)
        self.recovery_threshold = config.get('recovery_threshold', 0.6)
        
        # Alert frequency settings
        self.alert_cooldown = config.get('alert_cooldown_hours', 2)
        self.max_alerts_per_day = config.get('max_alerts_per_day', 5)
        
    def evaluate_mood_score(self, mood_score: float, user_id: str, timestamp: datetime = None) -> Dict[str, Any]:
        """
        Evaluate a mood score and determine if any actions should be taken.
        
        Args:
            mood_score: Mood score between 0 (very negative) and 1 (very positive)
            user_id: Identifier for the user
            timestamp: When the mood was detected
            
        Returns:
            Dict containing evaluation results and recommended actions
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        result = {
            'user_id': user_id,
            'mood_score': mood_score,
            'timestamp': timestamp,
            'alert_level': None,
            'action_required': False,
            'message': '',
            'recommendations': []
        }
        
        # Determine alert level
        if mood_score <= self.critical_threshold:
            result['alert_level'] = 'CRITICAL'
            result['action_required'] = True
            result['message'] = f'Critical mood detected (score: {mood_score:.2f})'
            result['recommendations'] = self._get_critical_recommendations()
            
        elif mood_score <= self.warning_threshold:
            result['alert_level'] = 'WARNING'
            result['action_required'] = True
            result['message'] = f'Low mood detected (score: {mood_score:.2f})'
            result['recommendations'] = self._get_warning_recommendations()
            
        elif mood_score >= self.recovery_threshold:
            result['alert_level'] = 'POSITIVE'
            result['message'] = f'Positive mood detected (score: {mood_score:.2f})'
            result['recommendations'] = self._get_positive_recommendations()
            
        else:
            result['alert_level'] = 'NEUTRAL'
            result['message'] = f'Neutral mood (score: {mood_score:.2f})'
            
        self.logger.info(f"Mood evaluation for {user_id}: {result['alert_level']} - {result['message']}")
        return result
        
    def should_send_alert(self, evaluation: Dict[str, Any], recent_alerts: List[Dict]) -> bool:
        """
        Determine if an alert should be sent based on evaluation and recent alert history.
        
        Args:
            evaluation: Result from evaluate_mood_score
            recent_alerts: List of recent alerts for this user
            
        Returns:
            Boolean indicating whether to send alert
        """
        if not evaluation['action_required']:
            return False
            
        user_id = evaluation['user_id']
        alert_level = evaluation['alert_level']
        current_time = evaluation['timestamp']
        
        # Always send critical alerts immediately
        if alert_level == 'CRITICAL':
            return True
            
        # Check cooldown period
        recent_similar_alerts = [
            alert for alert in recent_alerts
            if alert['user_id'] == user_id and 
               alert['alert_level'] == alert_level and
               current_time - alert['timestamp'] < timedelta(hours=self.alert_cooldown)
        ]
        
        if recent_similar_alerts:
            self.logger.info(f"Alert for {user_id} suppressed due to cooldown")
            return False
            
        # Check daily alert limit
        today_alerts = [
            alert for alert in recent_alerts
            if alert['user_id'] == user_id and 
               alert['timestamp'].date() == current_time.date()
        ]
        
        if len(today_alerts) >= self.max_alerts_per_day:
            self.logger.warning(f"Daily alert limit reached for {user_id}")
            return False
            
        return True
        
    def _get_critical_recommendations(self) -> List[str]:
        """
        Get recommendations for critical mood states.
        """
        return [
            "Consider reaching out to a mental health professional",
            "Contact a trusted friend or family member",
            "Use crisis helpline if feeling overwhelmed",
            "Practice grounding techniques (5-4-3-2-1 method)",
            "Ensure you're in a safe environment"
        ]
        
    def _get_warning_recommendations(self) -> List[str]:
        """
        Get recommendations for warning-level mood states.
        """
        return [
            "Take a short break from current activities",
            "Practice deep breathing or meditation",
            "Go for a brief walk or light exercise",
            "Listen to calming music",
            "Consider talking to someone you trust"
        ]
        
    def _get_positive_recommendations(self) -> List[str]:
        """
        Get recommendations for positive mood states.
        """
        return [
            "Great job maintaining positive mood!",
            "Consider sharing your positive energy with others",
            "Take note of what's contributing to your good mood",
            "This might be a good time for creative activities"
        ]
        
    def get_trend_analysis(self, mood_history: List[Dict]) -> Dict[str, Any]:
        """
        Analyze mood trends over time.
        
        Args:
            mood_history: List of mood evaluations over time
            
        Returns:
            Trend analysis results
        """
        if len(mood_history) < 2:
            return {'trend': 'INSUFFICIENT_DATA', 'message': 'Not enough data for trend analysis'}
            
        recent_scores = [entry['mood_score'] for entry in mood_history[-10:]]
        earlier_scores = [entry['mood_score'] for entry in mood_history[-20:-10]] if len(mood_history) >= 20 else []
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        
        trend_result = {
            'recent_average': recent_avg,
            'trend': 'STABLE',
            'message': f'Recent average mood: {recent_avg:.2f}'
        }
        
        if earlier_scores:
            earlier_avg = sum(earlier_scores) / len(earlier_scores)
            difference = recent_avg - earlier_avg
            
            if difference > 0.1:
                trend_result['trend'] = 'IMPROVING'
                trend_result['message'] = f'Mood trending upward (improvement: +{difference:.2f})'
            elif difference < -0.1:
                trend_result['trend'] = 'DECLINING'
                trend_result['message'] = f'Mood trending downward (decline: {difference:.2f})'
                
        return trend_result


class RuleEngine:
    """
    Rule engine that evaluates features and generates alerts.
    Used by main.py for mood monitoring and alerting.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.mood_rules = MoodRules(config)
        
        # Load alert thresholds
        self.sentiment_threshold = config.get('sentiment_threshold', -0.5)
        self.engagement_threshold = config.get('engagement_threshold', 0.2)
        self.volume_spike_threshold = config.get('volume_spike_threshold', 2.0)
        
    def evaluate(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate features and generate alerts if necessary.
        
        Args:
            features: Dictionary containing extracted features from social media data
            
        Returns:
            List of alert dictionaries with type, severity, timestamp, etc.
        """
        alerts = []
        
        # Check sentiment-based alerts
        avg_sentiment = features.get('avg_sentiment', 0.0)
        if avg_sentiment < self.sentiment_threshold:
            alerts.append({
                'type': 'NEGATIVE_SENTIMENT',
                'severity': 'HIGH' if avg_sentiment < -0.8 else 'MEDIUM',
                'timestamp': datetime.now().isoformat(),
                'summary': f'Negative sentiment detected: {avg_sentiment:.2f}',
                'actions': [
                    'Monitor user closely for signs of distress',
                    'Consider reaching out with support resources',
                    'Track sentiment trends over time'
                ]
            })
            
        # Check engagement anomalies
        engagement_score = features.get('engagement_score', 0.0)
        if engagement_score < self.engagement_threshold:
            alerts.append({
                'type': 'LOW_ENGAGEMENT',
                'severity': 'LOW',
                'timestamp': datetime.now().isoformat(),
                'summary': f'Low engagement detected: {engagement_score:.2f}',
                'actions': [
                    'Monitor for social withdrawal patterns',
                    'Check if user needs support or encouragement'
                ]
            })
            
        # Check for volume spikes (unusual activity)
        post_volume = features.get('post_volume', 0)
        avg_volume = features.get('avg_post_volume', 1)
        
        if post_volume > avg_volume * self.volume_spike_threshold:
            alerts.append({
                'type': 'ACTIVITY_SPIKE',
                'severity': 'MEDIUM',
                'timestamp': datetime.now().isoformat(),
                'summary': f'Unusual activity spike: {post_volume} posts (avg: {avg_volume})',
                'actions': [
                    'Review recent posts for concerning content',
                    'Check if spike indicates manic episode or crisis'
                ]
            })
            
        # Check for keyword alerts (crisis terms)
        crisis_keywords = features.get('crisis_keywords', [])
        if crisis_keywords:
            alerts.append({
                'type': 'CRISIS_KEYWORDS',
                'severity': 'CRITICAL',
                'timestamp': datetime.now().isoformat(),
                'summary': f'Crisis keywords detected: {", ".join(crisis_keywords)}',
                'actions': [
                    'IMMEDIATE attention required',
                    'Contact crisis intervention team',
                    'Reach out to user directly',
                    'Monitor continuously'
                ]
            })
            
        # Log results
        if alerts:
            self.logger.warning(f"Generated {len(alerts)} alerts from feature evaluation")
        else:
            self.logger.info("No alerts generated from current features")
            
        return alerts
