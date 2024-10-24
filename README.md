# Weather Monitoring and Alert System

This project is a FastAPI-based backend application for monitoring weather conditions in major Indian cities, providing daily summaries, and sending alerts based on user-defined thresholds.

## Features

- Real-time weather data fetching for major Indian cities (Delhi, Mumbai, Chennai, Bangalore, Kolkata, Hyderabad)
- Daily weather summaries
- Historical weather data retrieval
- CORS support for frontend integration

## Prerequisites

- Python 3.11+
- MongoDB Atlas account

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/zeotap_app2_backend.git
   cd zeotap_app2_backend
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory and add the following:
   ```
   OPENWEATHERMAP_API_KEY=your_api_key_here
   MONGO_URI=your_mongodb_atlas_connection_string
   CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
   CORS_METHODS=GET,POST,PUT,DELETE
   CORS_HEADERS=Content-Type,Authorization
   ```

## Running the Application

To start the server, run:

```
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Endpoints

- `/weather/{city}`: Get current weather for a city
- `/summaries/{city}/`: Get daily weather summaries for a city
- `/weather-history/{city}`: Get historical weather data for a city

## Project Structure

- `app/main.py`: Main application file with FastAPI app configuration
- `app/routes.py`: API route definitions
- `app/services.py`: Core business logic for fetching weather data
- `app/tasks.py`: Background task for continuous weather monitoring
- `app/models.py`: Pydantic models for data validation
- `app/config.py`: Configuration management using environment variables
- `app/logger.py`: Custom logging setup

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
