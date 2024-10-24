import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
    MONGO_URI = os.getenv("MONGO_URI")
    WEATHER_COLLECTION = "weather_data"
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS_METHODS = os.getenv("CORS_METHODS", "GET,POST,PUT,DELETE").split(",")
    CORS_HEADERS = os.getenv("CORS_HEADERS", "*").split(",")

config = Config()
