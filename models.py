import os
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime

DB_URL = os.getenv("DB_URL")
engine = create_engine(DB_URL)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

class MoodEntry(Base):
    __tablename__ = "mood_entries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    ts = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    mood = Column(Integer, nullable=False)
    note = Column(Text)

class Anomaly(Base):
    __tablename__ = "anomalies"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    ts = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    anomaly_type = Column(String, nullable=False)
    score = Column(Float)
    details = Column(JSON)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    ts = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    severity = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    sent = Column(Boolean, default=False)
    meta = Column(JSON)

def get_session():
    return SessionLocal()
