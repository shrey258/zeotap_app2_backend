import asyncio
from app.services import fetch_weather_data, create_notification
from app.config import config
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from app.models import AlertThreshold, WeatherAlert, WeatherData, Notification
import logging

# List of metro cities in India
cities = ["Delhi", "Mumbai", "Chennai", "Bangalore", "Kolkata", "Hyderabad"]

client = AsyncIOMotorClient(config.MONGO_URI)
db = client.weather_app
collection = db[config.WEATHER_COLLECTION]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def calculate_daily_summary(city: str):
    today = datetime.utcnow().date()
    weather_entries = collection.find({
        "city": city,
        "timestamp": {
            "$gte": datetime.combine(today, datetime.min.time()),
            "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time())
        }
    })

    temps = []
    conditions = {}
    async for entry in weather_entries:
        temps.append(entry['temp'])
        condition = entry['main']
        conditions[condition] = conditions.get(condition, 0) + 1

    if temps:
        summary_data = {
            "date": today.strftime("%Y-%m-%d"),
            "city": city,
            "avg_temp": sum(temps) / len(temps),
            "max_temp": max(temps),
            "min_temp": min(temps),
            "dominant_condition": max(conditions, key=conditions.get),
            "total_entries": len(temps)
        }

        # Store the summary in a separate collection for daily summaries
        summary_collection = db["daily_summaries"]
        await summary_collection.update_one(
            {"date": summary_data["date"], "city": city},
            {"$set": summary_data},
            upsert=True
        )

        logger.info(f"Daily summary for {city} on {today} calculated and stored.")
    else:
        logger.info(f"No weather data available for {city} on {today}")

async def check_alert_thresholds(weather_data: WeatherData):
    try:
        threshold = await db["alert_thresholds"].find_one({"city": weather_data.city})
        
        if not threshold:
            logger.info(f"No alert thresholds set for {weather_data.city}")
            return

        alert_threshold = AlertThreshold(**threshold)
        alerts = []

        if alert_threshold.max_temp and weather_data.temp > alert_threshold.max_temp:
            alerts.append(f"High temperature alert: {weather_data.temp:.1f}°C exceeds threshold of {alert_threshold.max_temp}°C")
        
        if alert_threshold.min_temp and weather_data.temp < alert_threshold.min_temp:
            alerts.append(f"Low temperature alert: {weather_data.temp:.1f}°C is below threshold of {alert_threshold.min_temp}°C")

        if alert_threshold.weather_condition and weather_data.main == alert_threshold.weather_condition:
            alerts.append(f"Weather condition alert: {weather_data.main} matches alert condition")

        if alerts:
            alert_message = f"ALERT for {weather_data.city}: {', '.join(alerts)}"
            logger.warning(alert_message)
            
            notification = Notification(
                city=weather_data.city,
                message=alert_message,
                timestamp=datetime.utcnow(),
                weather_data=weather_data
            )
            await create_notification(notification.dict())
        else:
            logger.info(f"No alerts triggered for {weather_data.city}. Current temp: {weather_data.temp:.1f}°C, Condition: {weather_data.main}")
    
    except Exception as e:
        logger.error(f"Error checking alert thresholds for {weather_data.city}: {str(e)}", exc_info=True)

async def start_weather_monitoring():
    while True:
        for city in ["Delhi", "Mumbai", "Chennai", "Bangalore", "Kolkata", "Hyderabad"]:
            try:
                weather_data = await fetch_weather_data(city)
                collection = db[config.WEATHER_COLLECTION]
                
                # Convert WeatherData to dictionary
                weather_dict = weather_data.dict()
                
                # Update the document for this city, or insert if it doesn't exist
                result = await collection.update_one(
                    {"city": city},
                    {"$set": weather_dict},
                    upsert=True
                )

                if result.modified_count > 0:
                    logger.info(f"Updated weather data for {city}")
                elif result.upserted_id:
                    logger.info(f"Inserted new weather data for {city}")
                else:
                    logger.info(f"No changes to weather data for {city}")

                # Check alert thresholds
                await check_alert_thresholds(weather_data)
                
                # Calculate daily summary
                await calculate_daily_summary(city)
                
            except Exception as e:
                logger.error(f"Error processing weather data for {city}: {str(e)}", exc_info=True)
        
        # Wait for 5 minutes before the next round of data fetching
        await asyncio.sleep(300)
