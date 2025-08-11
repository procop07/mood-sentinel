"""
Feature Extraction Module

Extracts features from social media posts for analysis.
Includes sentiment analysis, keyword detection, and engagement metrics.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None

from etl import SocialMediaPost


@dataclass
class PostFeatures:
    """Features extracted from a social media post."""
    post_id: str
    sentiment_score: float  # -1 to 1
    sentiment_label: str   # positive, negative, neutral
    emotion_scores: Dict[str, float]
    keywords: List[str]
    engagement_score: float
    author_activity: Dict[str, Any]
    temporal_features: Dict[str, Any]
    text_features: Dict[str, Any]


class FeatureExtractor:
    """Extracts features from social media posts."""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load configuration
        processing_config = config.get('processing', {})
        self.sentiment_threshold = processing_config.get('sentiment_analysis', {}).get('threshold', 0.7)
        self.negative_keywords = processing_config.get('keywords', {}).get('negative', [])
        self.positive_keywords = processing_config.get('keywords', {}).get('positive', [])
    
    def process(self, posts: List[SocialMediaPost]) -> List[PostFeatures]:
        """Extract features from list of posts."""
        features = []
        
        for post in posts:
            try:
                feature = self.extract_features(post)
                features.append(feature)
            except Exception as e:
                self.logger.error(f"Error extracting features from post {post.id}: {e}")
        
        self.logger.info(f"Extracted features from {len(features)} posts")
        return features
    
    def extract_features(self, post: SocialMediaPost) -> PostFeatures:
        """Extract all features from a single post."""
        # Sentiment analysis
        sentiment_score, sentiment_label = self.analyze_sentiment(post.content)
        
        # Emotion detection
        emotion_scores = self.detect_emotions(post.content)
        
        # Keyword extraction
        keywords = self.extract_keywords(post.content)
        
        # Engagement metrics
        engagement_score = self.calculate_engagement_score(post)
        
        # Author activity features
        author_features = self.extract_author_features(post)
        
        # Temporal features
        temporal_features = self.extract_temporal_features(post)
        
        # Text features
        text_features = self.extract_text_features(post.content)
        
        return PostFeatures(
            post_id=post.id,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            emotion_scores=emotion_scores,
            keywords=keywords,
            engagement_score=engagement_score,
            author_activity=author_features,
            temporal_features=temporal_features,
            text_features=text_features
        )
    
    def analyze_sentiment(self, text: str) -> tuple[float, str]:
        """Analyze sentiment of text."""
        if TextBlob:
            try:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity  # -1 to 1
                
                if polarity > 0.1:
                    label = 'positive'
                elif polarity < -0.1:
                    label = 'negative'
                else:
                    label = 'neutral'
                    
                return polarity, label
            except Exception as e:
                self.logger.warning(f"TextBlob sentiment analysis failed: {e}")
        
        # Fallback keyword-based sentiment
        return self._keyword_sentiment(text)
    
    def _keyword_sentiment(self, text: str) -> tuple[float, str]:
        """Simple keyword-based sentiment analysis."""
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.positive_keywords if word in text_lower)
        negative_count = sum(1 for word in self.negative_keywords if word in text_lower)
        
        if positive_count > negative_count:
            return 0.5, 'positive'
        elif negative_count > positive_count:
            return -0.5, 'negative'
        else:
            return 0.0, 'neutral'
    
    def detect_emotions(self, text: str) -> Dict[str, float]:
        """Detect emotions in text."""
        # Simple emotion detection based on keywords
        emotions = {
            'anger': 0.0,
            'fear': 0.0,
            'joy': 0.0,
            'sadness': 0.0,
            'surprise': 0.0
        }
        
        emotion_keywords = {
            'anger': ['angry', 'furious', 'mad', 'rage', 'hate', 'annoyed'],
            'fear': ['scared', 'afraid', 'terrified', 'worried', 'anxious'],
            'joy': ['happy', 'joyful', 'excited', 'glad', 'cheerful'],
            'sadness': ['sad', 'depressed', 'upset', 'disappointed', 'hurt'],
            'surprise': ['surprised', 'amazed', 'shocked', 'astonished']
        }
        
        text_lower = text.lower()
        
        for emotion, keywords in emotion_keywords.items():
            count = sum(1 for word in keywords if word in text_lower)
            emotions[emotion] = min(count / len(keywords), 1.0)
        
        return emotions
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text."""
        # Simple keyword extraction - remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'cant', 'wont', 'dont', 'doesnt', 'didnt', 'havent', 'hasnt', 'hadnt', 'wouldnt', 'couldnt', 'shouldnt', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        # Clean and split text
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # Return unique keywords
        return list(set(keywords))
    
    def calculate_engagement_score(self, post: SocialMediaPost) -> float:
        """Calculate engagement score based on likes, shares, replies."""
        # Weighted engagement score
        weights = {'likes': 1.0, 'shares': 2.0, 'replies': 1.5}
        
        score = (
            post.likes * weights['likes'] +
            post.shares * weights['shares'] +
            post.replies * weights['replies']
        )
        
        # Normalize by time (newer posts have advantage)
        hours_old = (datetime.now() - post.timestamp).total_seconds() / 3600
        time_factor = max(0.1, 1.0 / (1.0 + hours_old * 0.1))  # Decay over time
        
        return score * time_factor
    
    def extract_author_features(self, post: SocialMediaPost) -> Dict[str, Any]:
        """Extract author-related features."""
        return {
            'author': post.author,
            'platform': post.platform,
            'has_mentions': len(post.mentions) > 0,
            'mention_count': len(post.mentions),
            'hashtag_count': len(post.hashtags)
        }
    
    def extract_temporal_features(self, post: SocialMediaPost) -> Dict[str, Any]:
        """Extract time-related features."""
        timestamp = post.timestamp
        
        return {
            'hour_of_day': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'is_weekend': timestamp.weekday() >= 5,
            'month': timestamp.month,
            'time_since_post': (datetime.now() - timestamp).total_seconds() / 3600  # hours
        }
    
    def extract_text_features(self, text: str) -> Dict[str, Any]:
        """Extract text-related features."""
        return {
            'character_count': len(text),
            'word_count': len(text.split()),
            'sentence_count': len(re.split(r'[.!?]+', text)),
            'exclamation_count': text.count('!'),
            'question_count': text.count('?'),
            'uppercase_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0,
            'has_url': bool(re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)),
            'emoji_count': len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', text))
        }
    
    def get_feature_summary(self, features_list: List[PostFeatures]) -> Dict[str, Any]:
        """Generate summary statistics from extracted features."""
        if not features_list:
            return {}
        
        # Calculate averages and distributions
        sentiment_scores = [f.sentiment_score for f in features_list]
        engagement_scores = [f.engagement_score for f in features_list]
        
        # Count sentiment labels
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        for f in features_list:
            sentiment_counts[f.sentiment_label] += 1
        
        # Most common keywords
        all_keywords = []
        for f in features_list:
            all_keywords.extend(f.keywords)
        
        keyword_freq = {}
        for keyword in all_keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_posts': len(features_list),
            'avg_sentiment': sum(sentiment_scores) / len(sentiment_scores),
            'sentiment_distribution': sentiment_counts,
            'avg_engagement': sum(engagement_scores) / len(engagement_scores),
            'top_keywords': top_keywords,
            'negative_post_ratio': sentiment_counts['negative'] / len(features_list),
            'high_engagement_threshold': sorted(engagement_scores, reverse=True)[:int(len(engagement_scores)*0.1)]
        }
