# Safety Dashboard – Real-time Environmental Hazards Monitor

A comprehensive “Waze for hazards + weather” environmental monitoring system providing real-time safety insights across US territories through advanced geospatial visualization and multi-source hazard tracking.

---

## Overview

The Safety Dashboard is a professional-grade environmental monitoring application that displays real-time safety data on an interactive Leaflet map, restricted to the lower 48 US states. The system integrates multiple authentic data sources to provide users with critical safety information for informed decision-making.

---

## Key Features

### 🗺️ Interactive Mapping
- Leaflet.js-powered map with smooth navigation and mobile optimization  
- US-focused bounds (excludes Alaska, Hawaii, and territories)  
- Real-time data layers with 15-minute auto-refresh intervals  
- Advanced mobile UI with pull-to-refresh and haptic feedback  

### 🔥 Fire Detection & Monitoring
- NASA FIRMS satellite integration (VIIRS/MODIS)  
- High-confidence fire markers with detailed popups  
- 110+ active fires tracked across lower 48 states  
- 6-hour update intervals respecting NASA API rate limits  

### 🌪️ Weather Alert System
- National Weather Service (NWS) integration for live warnings & alerts  
- 48+ active alerts including severe thunderstorms, heat advisories, flood warnings  
- Clickable alert markers with detailed descriptions & safety instructions  
- Smart coordinate detection for alerts without GPS data  

### 🌡️ Comprehensive Weather Data
- OpenWeatherMap API for current conditions and 5-day forecasts  
- Multi-metric monitoring: Temperature, humidity, wind speed, UV index, air quality (PM2.5)  
- Heat index calculations with safety recommendations  
- Emergency condition detection (heat stroke risk, hazardous air quality)  

### 📱 Mobile-First Design
- Modern iOS/Android-style UI with glass-morphism and backdrop blur  
- Touch-friendly controls (56 px button targets) and smooth animations  
- Pull-to-refresh with haptic feedback simulation  

---

## Technical Architecture

### Frontend
- HTML 5 / CSS 3 / JavaScript (ES6+)  
- Leaflet.js 1.9.4 for mapping  
- Responsive, mobile-first design  
- Advanced CSS animations with cubic-bezier transitions  

### Backend
- Python 3.11 with async processing  
- Real-time API aggregation from multiple sources  
- PostgreSQL for fire data caching & persistence  
- Built-in rate-limiting and exponential backoff  

---

## Data Sources & Attribution

- **NASA FIRMS** – Fire Information for Resource Management System  
- **OpenWeatherMap** – Weather data & forecasts  
- **NOAA NWS** – Weather alerts & warnings  
- **Google Maps** – Geocoding & location services  
- **OpenStreetMap** – Base map tiles  

---

## Installation & Setup

### Prerequisites
- Python 3.11+  
- Node.js 20+  
- PostgreSQL database  

### Environment Variables
# Required API Keys
OPENWEATHERMAP_API_KEY=your_openweather_key  
NASA_FIRMS_API_KEY=your_nasa_firms_key  
GOOGLE_MAPS_API_KEY=your_google_maps_key  

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/hazardapp  
PGHOST=localhost  
PGPORT=5432  
PGUSER=your_db_user  
PGPASSWORD=your_db_password  
PGDATABASE=hazardapp  

### Quickstart
# Clone repository
git clone https://github.com/shawnatwsu/HazardApp.git
cd HazardApp

# Install dependencies
pip install -r requirements.txt
npm install

# Database setup
npm run db:push

# Start server
python server.py

# Open in browser
http://localhost:5000

API Endpoints
GET /api/weather?lat={lat}&lon={lon} – Current weather conditions

GET /api/fires – Active fire locations

GET /api/storms – NWS weather alerts

GET /api/geocode?address={address} – Location geocoding

Data Update Intervals
Weather data: real-time on location click

Fire data: every 6 hours (NASA rate limits)

NWS alerts: every 5 minutes

Auto-refresh: every 15 minutes

Database Schema
Fire Data Storage
fires: id, latitude, longitude, brightness, confidence, acq_date, acq_time

fire_cache: id, last_update, total_fires, status, created_at

Performance & Optimization
Data Management
Intelligent caching (6-hour fire data)

Rate-limit compliance & exponential backoff

Batch processing for efficiency

Robust error handling

Mobile Performance
Touch-optimized 60 fps animations

Lazy loading of data & tiles

Offline resilience with graceful degradation

Efficient marker cleanup & memory management

Current Data Coverage
Active Monitoring (as of latest update)
109 active fires across lower 48 states

48 active NWS alerts (severe weather warnings)

Heat advisories in PNW, Idaho, and Texas

Real-time thunderstorm & tornado tracking

Geographic Scope
Continental US only (48 states + DC)

Excludes Alaska, Hawaii, and territories

Focus areas: fire-prone regions, Tornado Alley, hurricane zones

Contributing
Development Guidelines
Use real data—no placeholders

Maintain mobile-first responsive design

Respect API rate limits & terms of service

Include proper data source attribution

Test on multiple devices & browsers

Code Style
JavaScript: ES6+ with async/await

CSS: custom properties & advanced selectors

Python: 3.11+ with type hints & async support

RESTful API design principles

License
MIT License – see LICENSE for details

Data Attribution
This application displays data from multiple authoritative sources:

NASA FIRMS – Public domain fire data

OpenWeatherMap – API license required

NOAA NWS – Public domain alerts

Google Maps – API license required

OpenStreetMap – ODbL license
