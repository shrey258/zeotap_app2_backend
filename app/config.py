import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
    MONGO_URI = os.getenv("MONGO_URI")
    WEATHER_COLLECTION = "weather_data"

config = Config()
