from fastapi import FastAPI, HTTPException
from fastapi import Query, Body
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
from sqlalchemy.orm import Session
from models import MoodEntry, Anomaly, get_db_session
from sqlalchemy import and_

app = FastAPI(
    title="Mood Sentinel API", 
    version="1.0.0"
)

# Pydantic models for request/response
class MoodCreate(BaseModel):
    mood: int = Field(..., ge=1, le=10, description="Mood value from 1 to 10")
    note: Optional[str] = Field(None, description="Optional note")

class MoodResponse(BaseModel):
    id: int
    user_id: int
    ts: datetime
    mood: int
    note: Optional[str]

class AnomalyResponse(BaseModel):
    id: int
    user_id: int
    ts: datetime
    anomaly_type: str
    score: float
    details: Optional[str]

@app.post("/api/v1/mood", response_model=dict)
def create_mood_entry(mood_data: MoodCreate):
    """Create new mood entry"""
    try:
        session = get_db_session()
        
        # Create new mood entry
        mood_entry = MoodEntry(
            user_id=1,  # Single-tenant default
            ts=datetime.utcnow(),
            mood=mood_data.mood,
            note=mood_data.note
        )
        
        session.add(mood_entry)
        session.commit()
        session.refresh(mood_entry)
        
        return {
            "id": mood_entry.id,
            "user_id": mood_entry.user_id,
            "ts": mood_entry.ts.isoformat(),
            "mood": mood_entry.mood,
            "note": mood_entry.note,
            "status": "created"
        }
    except Exception as e:
        session.rollback() if 'session' in locals() else None
        raise HTTPException(status_code=422, detail=f"Error creating mood entry: {str(e)}")
    finally:
        if 'session' in locals():
            session.close()

@app.get("/api/v1/mood/history", response_model=List[MoodResponse])
def get_mood_history(
    from_ts: Optional[datetime] = Query(None, description="Start datetime filter"),
    to_ts: Optional[datetime] = Query(None, description="End datetime filter"),
    user_id: int = Query(1, description="User ID filter"),
    limit: int = Query(100, ge=1, le=1000, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset")
):
    """Get mood history with filters"""
    try:
        session = get_db_session()
        
        # Default to last 30 days if no date range specified
        if not from_ts and not to_ts:
            to_ts = datetime.utcnow()
            from_ts = to_ts - timedelta(days=30)
        
        query = session.query(MoodEntry)
        query = query.filter(MoodEntry.user_id == user_id)
        
        if from_ts:
            query = query.filter(MoodEntry.ts >= from_ts)
        if to_ts:
            query = query.filter(MoodEntry.ts <= to_ts)
            
        query = query.order_by(MoodEntry.ts.desc()).limit(limit).offset(offset)
        
        results = query.all()
        
        return [
            MoodResponse(
                id=entry.id,
                user_id=entry.user_id,
                ts=entry.ts,
                mood=entry.mood,
                note=entry.note
            ) for entry in results
        ]
        
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error retrieving mood history: {str(e)}")
    finally:
        if 'session' in locals():
            session.close()

@app.get("/api/v1/anomalies", response_model=List[AnomalyResponse])
def get_anomalies(
    from_ts: Optional[datetime] = Query(None, description="Start datetime filter"),
    to_ts: Optional[datetime] = Query(None, description="End datetime filter"),
    user_id: int = Query(1, description="User ID filter"),
    type: Optional[str] = Query(None, description="Anomaly type filter"),
    limit: int = Query(100, ge=1, le=1000, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset")
):
    """Get anomalies with filters"""
    try:
        session = get_db_session()
        
        # Default to last 30 days if no date range specified
        if not from_ts and not to_ts:
            to_ts = datetime.utcnow()
            from_ts = to_ts - timedelta(days=30)
        
        query = session.query(Anomaly)
        query = query.filter(Anomaly.user_id == user_id)
        
        if from_ts:
            query = query.filter(Anomaly.ts >= from_ts)
        if to_ts:
            query = query.filter(Anomaly.ts <= to_ts)
        if type:
            query = query.filter(Anomaly.anomaly_type == type)
            
        query = query.order_by(Anomaly.ts.desc()).limit(limit).offset(offset)
        
        results = query.all()
        
        return [
            AnomalyResponse(
                id=anomaly.id,
                user_id=anomaly.user_id,
                ts=anomaly.ts,
                anomaly_type=anomaly.anomaly_type,
                score=anomaly.score,
                details=anomaly.details
            ) for anomaly in results
        ]
        
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error retrieving anomalies: {str(e)}")
    finally:
        if 'session' in locals():
            session.close()

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Root endpoint
@app.get("/")
def root():
    return {"message": "Mood Sentinel API", "version": "1.0.0"}
