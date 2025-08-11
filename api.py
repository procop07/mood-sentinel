from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Any

app = FastAPI(title="Mood Sentinel API", version="1.0.0")

# Путь к файлам данных
DATA_DIR = "data"
REPORTS_FILE = os.path.join(DATA_DIR, "reports.json")
FLAGS_FILE = os.path.join(DATA_DIR, "flags.json")

def load_json_data(file_path: str) -> Dict[str, Any]:
    """Загрузка данных из JSON файла"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        return {}

def get_date_range_data(days: int) -> List[Dict[str, Any]]:
    """Получение данных за указанное количество дней"""
    reports = load_json_data(REPORTS_FILE)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    filtered_data = []
    for report in reports.get('reports', []):
        report_date = datetime.fromisoformat(report.get('timestamp', '').replace('Z', '+00:00'))
        if start_date <= report_date <= end_date:
            filtered_data.append(report)
    
    return filtered_data

@app.get("/health")
async def health_check():
    """Проверка состояния API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/today")
async def get_today_data():
    """Получение данных за сегодня"""
    try:
        data = get_date_range_data(1)
        return {
            "date": datetime.now().date().isoformat(),
            "reports_count": len(data),
            "reports": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных за сегодня: {str(e)}")

@app.get("/week")
async def get_week_data():
    """Получение данных за неделю"""
    try:
        data = get_date_range_data(7)
        return {
            "period": "week",
            "start_date": (datetime.now() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.now().date().isoformat(),
            "reports_count": len(data),
            "reports": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных за неделю: {str(e)}")

@app.get("/flags")
async def get_flags():
    """Получение флагов и настроек системы"""
    try:
        flags_data = load_json_data(FLAGS_FILE)
        return {
            "flags": flags_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении флагов: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
