"""
ETL Module - Extract, Transform, Load
Handles data extraction from various social media sources,
data transformation, and storage operations.
"""
import logging
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import requests
import pandas as pd
import os

# Optional tweepy import - Twitter integration is optional
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    tweepy = None

@dataclass
class SocialMediaPost:
    """Data structure for social media posts."""
    id: str
    platform: str
    author: str
    content: str
    timestamp: datetime
    likes: int = 0
    shares: int = 0
    replies: int = 0
    hashtags: List[str] = None
    mentions: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.hashtags is None:
            self.hashtags = []
        if self.mentions is None:
            self.mentions = []
        if self.metadata is None:
            self.metadata = {}

class DataSource(ABC):
    """Abstract base class for data sources."""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def extract(self, limit: int = 100) -> List[SocialMediaPost]:
        """Extract data from the source."""
        pass

class TwitterDataSource(DataSource):
    """Twitter data extraction using Twitter API v2."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        twitter_config = config.get('sources', {}).get('social_media', {}).get('twitter', {})
        
        if not twitter_config.get('enabled', False):
            self.logger.warning("Twitter source is disabled")
            self.enabled = False
            return
            
        if not TWEEPY_AVAILABLE:
            self.logger.warning("tweepy library not available - Twitter source disabled")
            self.enabled = False
            return
            
        self.enabled = True
        # Initialize Twitter API client
        # Note: In production, use proper API credentials
        self.bearer_token = twitter_config.get('bearer_token', '')
        
    def extract(self, limit: int = 100) -> List[SocialMediaPost]:
        """Extract tweets using Twitter API."""
        if not self.enabled:
            return []
            
        posts = []
        try:
            # Simulated tweet extraction (replace with actual API calls)
            sample_tweets = self._get_sample_tweets(limit)
            
            for tweet in sample_tweets:
                post = SocialMediaPost(
                    id=tweet['id'],
                    platform='twitter',
                    author=tweet['author'],
                    content=tweet['text'],
                    timestamp=datetime.fromisoformat(tweet['created_at']),
                    likes=tweet.get('public_metrics', {}).get('like_count', 0),
                    shares=tweet.get('public_metrics', {}).get('retweet_count', 0),
                    replies=tweet.get('public_metrics', {}).get('reply_count', 0),
                    hashtags=self._extract_hashtags(tweet['text']),
                    mentions=self._extract_mentions(tweet['text']),
                    metadata=tweet
                )
                posts.append(post)
                
            self.logger.info(f"Extracted {len(posts)} tweets")
            
        except Exception as e:
            self.logger.error(f"Error extracting Twitter data: {e}")
            
        return posts
    
    def _get_sample_tweets(self, limit: int) -> List[dict]:
        """Generate sample tweets for demonstration."""
        # In production, this would make actual API calls
        import random
        sample_texts = [
            "Great day today! Feeling optimistic about the future #positive",
            "Really frustrated with the current situation #angry #upset",
            "Love spending time with family #family #love",
            "Traffic is terrible again... #frustrated #commute",
            "Excited about the new project launch! #excited #work",
            "Hate when people don't listen #annoyed #communication"
        ]
        
        tweets = []
        for i in range(min(limit, len(sample_texts))):
            tweets.append({
                'id': f"tweet_{i}_{int(datetime.now().timestamp())}",
                'author': f"user_{i}",
                'text': sample_texts[i],
                'created_at': (datetime.now() - timedelta(minutes=random.randint(1, 1440))).isoformat(),
                'public_metrics': {
                    'like_count': random.randint(0, 100),
                    'retweet_count': random.randint(0, 50),
                    'reply_count': random.randint(0, 20)
                }
            })
        
        return tweets
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text."""
        import re
        return re.findall(r'#\w+', text)
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract mentions from text."""
        import re
        return re.findall(r'@\w+', text)

class TelegramDataSource(DataSource):
    """Telegram data extraction."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        telegram_config = config.get('sources', {}).get('social_media', {}).get('telegram', {})
        self.enabled = telegram_config.get('enabled', False)
        
    def extract(self, limit: int = 100) -> List[SocialMediaPost]:
        """Extract Telegram messages."""
        if not self.enabled:
            return []
            
        # Placeholder for Telegram extraction
        self.logger.info("Telegram extraction not implemented yet")
        return []

class DatabaseManager:
    """Handles database operations for storing extracted data."""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        db_config = config.get('database', {})
        self.db_path = db_config.get('path', 'mood_data.db')
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS social_posts (
                    id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    author TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    likes INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    replies INTEGER DEFAULT 0,
                    hashtags TEXT,
                    mentions TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_platform_timestamp 
                ON social_posts(platform, timestamp)
            ''')
    
    def store_posts(self, posts: List[SocialMediaPost]) -> int:
        """Store posts in database."""
        stored_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            for post in posts:
                try:
                    conn.execute('''
                        INSERT OR REPLACE INTO social_posts 
                        (id, platform, author, content, timestamp, likes, shares, replies, 
                         hashtags, mentions, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        post.id,
                        post.platform,
                        post.author,
                        post.content,
                        post.timestamp.isoformat(),
                        post.likes,
                        post.shares,
                        post.replies,
                        json.dumps(post.hashtags),
                        json.dumps(post.mentions),
                        json.dumps(post.metadata)
                    ))
                    stored_count += 1
                except sqlite3.Error as e:
                    self.logger.error(f"Error storing post {post.id}: {e}")
        
        self.logger.info(f"Stored {stored_count} posts to database")
        return stored_count
    
    def get_recent_posts(self, hours: int = 24, platform: Optional[str] = None) -> List[SocialMediaPost]:
        """Retrieve recent posts from database."""
        since = datetime.now() - timedelta(hours=hours)
        
        query = '''
            SELECT id, platform, author, content, timestamp, likes, shares, replies,
                   hashtags, mentions, metadata
            FROM social_posts 
            WHERE timestamp >= ?
        '''
        params = [since.isoformat()]
        
        if platform:
            query += ' AND platform = ?'
            params.append(platform)
            
        query += ' ORDER BY timestamp DESC'
        
        posts = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            
            for row in cursor.fetchall():
                post = SocialMediaPost(
                    id=row[0],
                    platform=row[1],
                    author=row[2],
                    content=row[3],
                    timestamp=datetime.fromisoformat(row[4]),
                    likes=row[5],
                    shares=row[6],
                    replies=row[7],
                    hashtags=json.loads(row[8]),
                    mentions=json.loads(row[9]),
                    metadata=json.loads(row[10])
                )
                posts.append(post)
        
        return posts

class DataExtractor:
    """Main ETL coordinator class."""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize data sources
        self.sources = []
        self.sources.append(TwitterDataSource(config))
        self.sources.append(TelegramDataSource(config))
        
        # Initialize database manager
        self.db_manager = DatabaseManager(config)
    
    def add_source(self, source: DataSource):
        """Adds a data source to the extractor."""
        self.sources.append(source)

    def extract_all(self) -> List[SocialMediaPost]:
        """Extract data from all enabled sources."""
        all_posts = []
        batch_size = self.config.get('monitoring', {}).get('batch_size', 100)
        
        for source in self.sources:
            try:
                posts = source.extract(limit=batch_size)
                all_posts.extend(posts)
                self.logger.info(f"Extracted {len(posts)} posts from {source.__class__.__name__}")
            except Exception as e:
                self.logger.error(f"Error extracting from {source.__class__.__name__}: {e}")
        
        # Store extracted posts
        if all_posts:
            self.db_manager.store_posts(all_posts)
        
        return all_posts
    
    def get_stored_data(self, hours: int = 24) -> List[SocialMediaPost]:
        """Get stored data from database."""
        return self.db_manager.get_recent_posts(hours)


class CsvDataSource(DataSource):
    """Data source for reading health data from CSV files."""

    def __init__(self, config: dict, csv_dir: str):
        """
        Initializes the CsvDataSource.
        Args:
            config: The application configuration dictionary.
            csv_dir: The directory containing the CSV files.
        """
        super().__init__(config)
        self.csv_dir = csv_dir
        self.enabled = os.path.isdir(csv_dir)
        if not self.enabled:
            self.logger.warning(f"CSV directory not found or not a directory: {csv_dir}")

    def extract(self, limit: int = 10000) -> List[SocialMediaPost]:
        """Extracts data from all CSV files in the directory."""
        if not self.enabled:
            return []

        all_posts = []
        for filename in os.listdir(self.csv_dir):
            if filename.endswith(".csv"):
                file_path = os.path.join(self.csv_dir, filename)
                try:
                    df = pd.read_csv(file_path)
                    filename_without_ext = os.path.splitext(filename)[0]

                    for index, row in df.iterrows():
                        if len(all_posts) >= limit:
                            break

                        row_dict = row.to_dict()
                        timestamp_str = row_dict.get('timestamp')
                        if not timestamp_str:
                            self.logger.warning(f"Skipping row {index} in {filename} due to missing timestamp.")
                            continue

                        try:
                            timestamp = datetime.fromisoformat(timestamp_str)
                        except ValueError:
                            self.logger.warning(f"Skipping row {index} in {filename} due to invalid timestamp format: {timestamp_str}")
                            continue

                        post = SocialMediaPost(
                            id=f"csv_{filename_without_ext}_{index}",
                            platform="csv_import",
                            author="user_1",
                            content=f"{filename_without_ext} data point at {timestamp_str}",
                            timestamp=timestamp,
                            metadata=row_dict
                        )
                        all_posts.append(post)

                except Exception as e:
                    self.logger.error(f"Error processing CSV file {filename}: {e}")

            if len(all_posts) >= limit:
                break

        self.logger.info(f"Extracted {len(all_posts)} records from CSV files in {self.csv_dir}")
        return all_posts
