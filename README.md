# Environmental Monitoring Dashboard

A real-time environmental monitoring system that provides heat index, air quality, UV index, and wind speed data for locations across the United States.

## Features

- **Real-time Environmental Data**: Live weather and air quality monitoring using Open-Meteo APIs
- **Interactive Map**: Click anywhere on the US map to get environmental conditions
- **Smart Location Search**: Autocomplete search with Google Maps integration
- **Professional Dashboard**: Clean, modern interface with safety status indicators
- **US Territory Focus**: Optimized for Continental US, Alaska, Hawaii, and Puerto Rico

## Setup

1. Clone this repository
2. Copy `.env.example` to `.env`
3. Add your API keys to the `.env` file:
   ```
   GOOGLE_MAPS_API_KEY=your_actual_google_maps_key
   OPENWEATHERMAP_API_KEY=your_actual_openweather_key
   ```

## API Keys Required

### Google Maps API Key
- Used for address autocomplete and geocoding
- Get from: [Google Cloud Console](https://console.cloud.google.com/)
- Enable: Geocoding API and Places API

### OpenWeatherMap API Key (Optional)
- Used for weather overlay visualizations
- Get from: [OpenWeatherMap](https://openweathermap.org/api)

## Running Locally

```bash
python server.py
```

Visit `http://localhost:5000` to access the dashboard.

## Deployment

This application can be deployed to any platform that supports Python web applications:

- Set environment variables for your API keys
- Run `python server.py` 
- Ensure port 5000 is accessible

## Technologies

- **Backend**: Python HTTP server with weather API integration
- **Frontend**: Leaflet.js mapping with OpenStreetMap tiles
- **APIs**: Open-Meteo (weather data), Google Maps (geocoding)
- **Design**: Modern glassmorphism UI with Inter font

## Environmental Data Sources

- **Weather Data**: Open-Meteo API (temperature, humidity, wind, visibility)
- **Air Quality**: Open-Meteo Air Quality API (PM2.5 measurements)
- **Calculations**: Heat index computed using NOAA formula
- **Coverage**: United States territory only

## License

This project uses authentic environmental data sources and requires proper API credentials for full functionality.