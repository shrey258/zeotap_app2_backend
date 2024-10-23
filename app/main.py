from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routes import router
from dotenv import load_dotenv
from app.tasks import start_weather_monitoring
from app.logger import main_logger as logger
import asyncio

load_dotenv()  # This line loads the variables from .env

app = FastAPI()
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up")
    asyncio.create_task(start_weather_monitoring())

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred. Please try again later."}
    )

# Start the server with: uvicorn app.main:app --reload
