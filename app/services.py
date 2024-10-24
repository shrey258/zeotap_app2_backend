import httpx
from app.config import config
from datetime import datetime, timedelta
from collections import Counter
from motor.motor_asyncio import AsyncIOMotorClient
from app.models import Notification, WeatherData
from bson import ObjectId
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

client = AsyncIOMotorClient(config.MONGO_URI)
db = client.weather_app
collection = db[config.WEATHER_COLLECTION]

async def fetch_weather_data(city: str) -> WeatherData:
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={config.OPENWEATHERMAP_API_KEY}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            weather_data = WeatherData(
                city=city,
                main=data['weather'][0]['main'],
                temp=data['main']['temp'] - 273.15,  # Convert Kelvin to Celsius
                feels_like=data['main']['feels_like'] - 273.15,
                timestamp=datetime.utcnow()
            )
            return weather_data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"City not found: {city}")
            else:
                raise HTTPException(status_code=500, detail="Error fetching weather data from external API")
        except KeyError as e:
            raise HTTPException(status_code=500, detail=f"Unexpected data format from external API: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

async def calculate_daily_summary():
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    
    cities = ["Delhi", "Mumbai", "Chennai", "Bangalore", "Kolkata", "Hyderabad"]
    
    for city in cities:
        # Fetch the latest weather data for the city
        weather_doc = await collection.find_one({"city": city})
        
        if not weather_doc:
            logger.info(f"No weather data available for {city}")
            continue
        
        # Check if the data is from yesterday
        if weather_doc['timestamp'].date() != yesterday:
            logger.info(f"No weather data available for {city} on {yesterday}")
            continue
        
        summary = {
            "date": yesterday.strftime("%Y-%m-%d"),
            "city": city,
            "avg_temp": weather_doc['temp'],
            "max_temp": weather_doc['temp'],
            "min_temp": weather_doc['temp'],
            "dominant_condition": weather_doc['main'],
            "total_entries": 1
        }
        
        # Store the summary in a separate collection for daily summaries
        summary_collection = db["daily_summaries"]
        await summary_collection.update_one(
            {"date": summary["date"], "city": city},
            {"$set": summary},
            upsert=True
        )
        
        logger.info(f"Daily summary for {city} on {yesterday} calculated and stored.")

async def create_notification(notification_data: dict) -> Notification:
    try:
        # Convert WeatherData to dict if it's not already
        if isinstance(notification_data['weather_data'], WeatherData):
            notification_data['weather_data'] = notification_data['weather_data'].dict()
        
        notification = Notification(**notification_data)
        result = await db["notifications"].insert_one(notification.dict(exclude={'id'}))
        notification.id = str(result.inserted_id)
        return notification
    except KeyError as e:
        logger.error(f"Missing key in notification data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid notification data: missing {str(e)}")
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error creating notification")
