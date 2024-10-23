from fastapi import APIRouter, HTTPException, Depends, Query
from app.services import fetch_weather_data, create_notification
from app.config import config
from app.models import WeatherData, AlertThreshold, WeatherAlert, Notification, PaginationParams, DateRange
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List
from bson import ObjectId
from app.tasks import calculate_daily_summary
from datetime import datetime, timedelta
from app.logger import api_logger as logger

client = AsyncIOMotorClient(config.MONGO_URI)
db = client.weather_app  # Explicitly specify the database name
collection = db[config.WEATHER_COLLECTION]

router = APIRouter()

@router.get("/weather/{city}", response_model=WeatherData)
async def get_weather(city: str):
    try:
        return await fetch_weather_data(city)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error fetching weather data for {city}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.get("/summaries/{city}/")
async def get_daily_summary(city: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    query = {"city": city}

    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        if "date" in query:
            query["date"]["$lte"] = end_date
        else:
            query["date"] = {"$lte": end_date}

    if not start_date and not end_date:
        # If no date range is specified, use the last 30 days
        today = datetime.utcnow().date()
        thirty_days_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        query["date"] = {"$gte": thirty_days_ago}

    cursor = db["daily_summaries"].find(query).sort("date", -1)
    summaries = []
    async for summary in cursor:
        summary['_id'] = str(summary['_id'])
        summaries.append(summary)

    if not summaries:
        raise HTTPException(status_code=404, detail="No summaries found for the given criteria.")
    
    return {"summaries": summaries}

@router.post("/trigger-summary-calculation")
async def trigger_summary_calculation():
    cities = ["Delhi", "Mumbai", "Chennai", "Bangalore", "Kolkata", "Hyderabad"]
    for city in cities:
        try:
            await calculate_daily_summary(city)
            logger.info(f"Daily summary calculation triggered for {city}")
        except Exception as e:
            logger.error(f"Error calculating daily summary for {city}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error calculating daily summary for {city}")
    return {"message": "Daily summary calculation triggered for all cities"}

@router.get("/all-summaries")
async def get_all_summaries():
    cursor = db["daily_summaries"].find()
    summaries = []
    async for summary in cursor:
        summary['_id'] = str(summary['_id'])
        summaries.append(summary)
    return {"summaries": summaries}

@router.post("/set-alert-threshold")
async def set_alert_threshold(threshold: AlertThreshold):
    try:
        result = await db["alert_thresholds"].update_one(
            {"city": threshold.city},
            {"$set": threshold.dict(exclude_unset=True)},
            upsert=True
        )
        logger.info(f"Alert threshold set for {threshold.city}")
        return {"message": "Alert threshold set successfully"}
    except Exception as e:
        logger.error(f"Error setting alert threshold: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error setting alert threshold")

@router.get("/alert-threshold/{city}")
async def get_alert_threshold(city: str):
    threshold = await db["alert_thresholds"].find_one({"city": city})
    if threshold:
        return AlertThreshold(**threshold)
    raise HTTPException(status_code=404, detail=f"No alert threshold found for {city}")

@router.get("/weather-alerts/{city}")
async def get_weather_alerts(city: str, limit: int = 10):
    cursor = db["weather_alerts"].find({"city": city}).sort("timestamp", -1).limit(limit)
    alerts = []
    async for alert in cursor:
        alerts.append(WeatherAlert(**alert))
    return alerts

@router.get("/notifications", response_model=List[Notification])
async def get_notifications(params: PaginationParams = Depends()):
    try:
        cursor = db["notifications"].find().sort("timestamp", -1).skip(params.offset).limit(params.limit)
        return [Notification(**doc) for doc in await cursor.to_list(length=params.limit)]
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching notifications")

@router.get("/notifications/{city}")
async def get_city_notifications(city: str, limit: int = 10, offset: int = 0):
    cursor = db["notifications"].find({"city": city}).sort("timestamp", -1).skip(offset).limit(limit)
    notifications = []
    async for doc in cursor:
        doc['id'] = str(doc.pop('_id'))
        notifications.append(Notification(**doc))
    return {"notifications": notifications}

@router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(notification_id: str):
    result = await db["notifications"].update_one(
        {"_id": ObjectId(notification_id)},
        {"$set": {"is_read": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}

@router.get("/weather-history/{city}", response_model=List[WeatherData])
async def get_weather_history(
    city: str, 
    start_date: datetime = Query(default=None),
    end_date: datetime = Query(default=None)
):
    try:
        date_range = DateRange(start_date=start_date, end_date=end_date)
        query = {"city": city}
        if date_range.start_date:
            query["timestamp"] = {"$gte": date_range.start_date}
        if date_range.end_date:
            query["timestamp"] = query.get("timestamp", {}) | {"$lte": date_range.end_date}

        cursor = db[config.WEATHER_COLLECTION].find(query).sort("timestamp", -1)
        return [WeatherData(**doc) for doc in await cursor.to_list(length=None)]
    except Exception as e:
        logger.error(f"Error fetching weather history for {city}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching weather history")
