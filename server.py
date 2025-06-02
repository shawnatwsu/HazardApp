#!/usr/bin/env python3
import os
import json
import urllib.request
import urllib.parse
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Rate limiting variables
last_request_time = 0
min_request_interval = 1.5  # Minimum 1.5 seconds between requests

class WeatherAPIHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/weather':
            self.handle_weather_api(parsed_path)
        elif parsed_path.path.startswith('/api/weather-tiles/'):
            self.handle_weather_tiles(parsed_path)
        elif parsed_path.path == '/api/geocode':
            self.handle_geocode_api(parsed_path)
        else:
            # Serve static files
            super().do_GET()
    
    def handle_weather_api(self, parsed_path):
        global last_request_time
        
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - last_request_time
            if time_since_last < min_request_interval:
                sleep_time = min_request_interval - time_since_last
                print(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            
            last_request_time = time.time()
            
            query_params = parse_qs(parsed_path.query)
            lat = query_params.get('lat', [None])[0]
            lon = query_params.get('lon', [None])[0]
            
            if not lat or not lon:
                self.send_error(400, "Missing lat or lon parameters")
                return
                
            print(f"Fetching weather data for coordinates: {lat}, {lon}")
            
            # Use free Open-Meteo APIs (no API key required)
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=relativehumidity_2m,uv_index,windspeed_10m,visibility&timezone=auto"
            aq_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=pm2_5&timezone=auto"
            
            # Fetch all data
            weather_data = self.fetch_json(weather_url)
            aq_data = self.fetch_json(aq_url)
            
            # Process and combine the data
            result = self.process_openmeteo_data(weather_data, aq_data)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            print(f"Error in weather API: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def fetch_json(self, url, max_retries=2):
        for attempt in range(max_retries + 1):
            try:
                print(f"API call attempt {attempt + 1}: {url}")
                with urllib.request.urlopen(url, timeout=10) as response:
                    if response.status == 200:
                        return json.loads(response.read().decode())
                    else:
                        print(f"API returned status {response.status}")
            except urllib.error.HTTPError as e:
                print(f"HTTP Error {e.code}: {e.reason}")
                if e.code == 401:
                    raise Exception("Invalid API key or unauthorized access")
                elif e.code == 429:
                    if attempt < max_retries:
                        wait_time = (attempt + 1) * 2
                        print(f"Rate limited, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception("Rate limit exceeded, try again later")
                else:
                    raise e
            except Exception as e:
                if attempt < max_retries:
                    print(f"Request failed, retrying... ({e})")
                    time.sleep(1)
                else:
                    raise e
        raise Exception("All retry attempts failed")
    
    def process_openmeteo_data(self, weather_data, aq_data):
        # Extract current weather data
        current = weather_data['current_weather']
        temp_c = current['temperature']  # Celsius
        temp_f = temp_c * 9/5 + 32  # Convert to Fahrenheit
        wind_speed_kmh = current['windspeed']  # km/h
        wind_speed_mph = wind_speed_kmh * 0.621371  # Convert to mph
        
        # Get current time for hourly data lookup
        current_time = current['time']
        hourly = weather_data['hourly']
        times = hourly['time']
        
        # Find index for current time
        try:
            time_index = times.index(current_time)
        except ValueError:
            time_index = 0  # Use first available if exact match not found
        
        # Extract hourly data
        humidity = hourly['relativehumidity_2m'][time_index]
        uv_index = hourly['uv_index'][time_index] if hourly['uv_index'][time_index] is not None else 0
        visibility_m = hourly['visibility'][time_index] if hourly['visibility'][time_index] is not None else 10000
        visibility_miles = visibility_m * 0.000621371
        
        # Get air quality data
        pm25 = aq_data['current']['pm2_5'] if 'current' in aq_data and aq_data['current']['pm2_5'] is not None else 10
        
        # Calculate heat index
        heat_index = self.compute_heat_index(temp_f, humidity)
        
        return {
            'temperature': round(temp_f, 1),
            'humidity': humidity,
            'heat_index': heat_index,
            'uv_index': uv_index,
            'pm25': pm25,
            'wind_speed': round(wind_speed_mph, 1),
            'wind_gusts': round(weather_data.get('current', {}).get('wind_gusts_10m', 0) * 2.237, 1),
            'visibility': round(visibility_miles, 1),
            'precipitation': weather_data.get('current', {}).get('precipitation', 0),
            'cloud_cover': weather_data.get('current', {}).get('cloud_cover', 0),
            'pressure': weather_data.get('current', {}).get('surface_pressure', 1013),
            'snow_depth': weather_data.get('current', {}).get('snow_depth', 0),
            'ozone': aq_data.get('current', {}).get('ozone', 0) if aq_data else 0,
            'no2': aq_data.get('current', {}).get('nitrogen_dioxide', 0) if aq_data else 0,
            'fire_risk': self.calculate_fire_risk(temp_f, humidity, wind_speed_mph),
            'soil_moisture': weather_data.get('current', {}).get('soil_moisture_0_to_1cm', 0)
        }
    
    def handle_weather_tiles(self, parsed_path):
        """Proxy weather tile requests to OpenWeatherMap"""
        api_key = os.getenv('OPENWEATHERMAP_API_KEY')
        if not api_key:
            self.send_error(500, "OpenWeatherMap API key required for weather tiles")
            return
            
        # Extract tile parameters from path: /api/weather-tiles/{layer}/{z}/{x}/{y}.png
        path_parts = parsed_path.path.split('/')
        if len(path_parts) >= 6:
            layer = path_parts[3]
            z = path_parts[4]
            x = path_parts[5]
            y = path_parts[6].replace('.png', '')
            
            # Build OpenWeatherMap tile URL
            tile_url = f"https://tile.openweathermap.org/map/{layer}/{z}/{x}/{y}.png?appid={api_key}"
            
            try:
                # Fetch tile from OpenWeatherMap
                import urllib.request
                response = urllib.request.urlopen(tile_url)
                tile_data = response.read()
                
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Content-Length', str(len(tile_data)))
                self.end_headers()
                self.wfile.write(tile_data)
                
            except Exception as e:
                print(f"Error fetching weather tile: {e}")
                self.send_error(500, "Failed to fetch weather tile")
        else:
            self.send_error(400, "Invalid tile request format")
    

    
    def compute_heat_index(self, temp_f, humidity):
        """Compute heat index using NOAA formula"""
        if temp_f < 80 or humidity < 40:
            return temp_f
        
        T, R = temp_f, humidity
        HI = (-42.379 + 2.04901523 * T + 10.14333127 * R - 
              0.22475541 * T * R - 6.83783e-3 * T * T - 
              5.481717e-2 * R * R + 1.22874e-3 * T * T * R + 
              8.5282e-4 * T * R * R - 1.99e-6 * T * T * R * R)
        return round(HI, 1)
    
    def calculate_fire_risk(self, temp_f, humidity, wind_speed):
        """Calculate fire weather index based on temperature, humidity, and wind"""
        risk_score = 0
        
        # Temperature factor (higher is worse)
        if temp_f > 85:
            risk_score += 3
        elif temp_f > 75:
            risk_score += 2
        elif temp_f > 65:
            risk_score += 1
            
        # Humidity factor (lower is worse)
        if humidity < 20:
            risk_score += 4
        elif humidity < 35:
            risk_score += 3
        elif humidity < 50:
            risk_score += 2
        elif humidity < 65:
            risk_score += 1
            
        # Wind factor (higher is worse)
        if wind_speed > 25:
            risk_score += 3
        elif wind_speed > 15:
            risk_score += 2
        elif wind_speed > 10:
            risk_score += 1
            
        return min(risk_score, 10)
    
    def handle_geocode_api(self, parsed_path):
        """Handle Google Maps geocoding requests"""
        try:
            # Get query parameter
            query_params = parse_qs(parsed_path.query)
            address = query_params.get('address', [''])[0]
            
            if not address:
                self.send_error(400, "Missing address parameter")
                return
                
            # Use Google Maps API key
            api_key = os.getenv('GOOGLE_MAPS_API_KEY')
            if not api_key:
                self.send_error(500, "Google Maps API key not configured")
                return
                
            # Build Google Geocoding API URL
            geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&components=country:US&key={api_key}"
            
            # Fetch from Google Geocoding API
            response = urllib.request.urlopen(geocode_url)
            data = json.loads(response.read().decode())
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
            
        except Exception as e:
            print(f"Error in geocoding API: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")

if __name__ == '__main__':
    port = 5000
    server = HTTPServer(('0.0.0.0', port), WeatherAPIHandler)
    print(f"Server running on port {port}")
    server.serve_forever()