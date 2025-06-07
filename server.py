#!/usr/bin/env python3
import os
import json
import urllib.request
import urllib.parse
import urllib.error
import time
import psycopg2
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from fire_service import FireDataService

# Database-backed fire data service
# Fire data is now stored in PostgreSQL with 6-hour update cycles
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
        elif parsed_path.path == '/api/fires':
            self.handle_fires_api(parsed_path)
        elif parsed_path.path == '/api/storms':
            self.handle_storms_api(parsed_path)
        else:
            # Serve static files with no-cache headers for HTML
            if self.path == '/' or self.path.endswith('.html'):
                try:
                    with open('index.html', 'r') as f:
                        content = f.read()
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                    self.send_header('Pragma', 'no-cache')
                    self.send_header('Expires', '0')
                    self.end_headers()
                    self.wfile.write(content.encode('utf-8'))
                except Exception as e:
                    self.send_error(500, f"Error serving HTML: {str(e)}")
            else:
                # Serve other static files normally
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
                self.send_error(400, "Missing latitude or longitude")
                return
                
            print(f"Fetching weather data for coordinates: {lat}, {lon}")
            
            # Use OpenWeatherMap API for accurate current conditions
            api_key = os.getenv('OPENWEATHERMAP_API_KEY')
            if not api_key:
                self.send_error(500, "OpenWeatherMap API key required")
                return
            
            # Get current weather
            current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
            current_data = self.fetch_json(current_url)
            
            # Get 5-day forecast
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
            forecast_data = self.fetch_json(forecast_url)
            
            # Get UV index
            uv_url = f"https://api.openweathermap.org/data/2.5/uvi?lat={lat}&lon={lon}&appid={api_key}"
            uv_data = self.fetch_json(uv_url)
            
            # Get air quality
            air_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
            air_data = self.fetch_json(air_url)
            
            # Fire data is now handled by separate API endpoint /api/fires
            
            # Process and combine the data
            result = self.process_openweathermap_data(current_data, forecast_data, uv_data, air_data)
            
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
                        print(f"HTTP Error {response.status}: {response.reason}")
            except urllib.error.HTTPError as e:
                print(f"HTTP Error {e.code}: {e.reason}")
            except Exception as e:
                print(f"Request error: {e}")
            
            if attempt < max_retries:
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None

    def process_openweathermap_data(self, current_data, forecast_data, uv_data, air_data):
        """Process OpenWeatherMap API responses into unified format"""
        try:
            # Extract current weather
            main = current_data['main']
            wind = current_data['wind']
            
            temp_f = main['temp']
            humidity = main['humidity']
            pressure = main['pressure']
            visibility_m = current_data.get('visibility', 10000)
            visibility_miles = visibility_m * 0.000621371
            
            # Wind data
            wind_speed_ms = wind.get('speed', 0)
            wind_speed_mph = wind_speed_ms * 2.237  # Convert m/s to mph
            wind_gusts_ms = wind.get('gust', 0)
            wind_gusts_mph = wind_gusts_ms * 2.237
            
            # UV index
            uv_index = uv_data.get('value', 0) if uv_data else 0
            
            # Air quality
            pm25 = 10  # Default
            components = {}
            if air_data and 'list' in air_data and air_data['list']:
                components = air_data['list'][0].get('components', {})
                pm25 = components.get('pm2_5', 10)
            
            # Calculate heat index using NOAA formula
            heat_index = self.compute_heat_index(temp_f, humidity)
            
            # Get daily min/max from forecast
            temp_max = temp_f
            temp_min = temp_f
            if forecast_data and 'list' in forecast_data:
                temps = [item['main']['temp'] for item in forecast_data['list'][:8]]  # Next 24 hours
                temp_max = max(temps) if temps else temp_f
                temp_min = min(temps) if temps else temp_f
            
            return {
                'temperature': round(temp_f, 1),
                'temp_max': round(temp_max, 1),
                'temp_min': round(temp_min, 1),
                'humidity': humidity,
                'heat_index': round(heat_index, 3),
                'uv_index': uv_index,
                'pm25': pm25,
                'wind_speed': round(wind_speed_mph, 1),
                'wind_gusts': round(wind_gusts_mph, 1),
                'visibility': round(visibility_miles, 1),
                'precipitation': current_data.get('rain', {}).get('1h', 0),
                'cloud_cover': current_data.get('clouds', {}).get('all', 0),
                'pressure': pressure,
                'snow_depth': current_data.get('snow', {}).get('1h', 0),
                'ozone': 0,  # Not available in OpenWeatherMap
                'no2': components.get('no2', 0),
                'fire_risk': self.calculate_fire_risk(temp_f, humidity, wind_speed_mph),
                'soil_moisture': 0  # Not available in OpenWeatherMap
            }
        except Exception as e:
            print(f"Error processing OpenWeatherMap data: {e}")
            raise Exception(f"Failed to process weather data: {e}")



    def fetch_csv_data(self, url, max_retries=3):
        """Fetch CSV data from FIRMS fire API"""
        for attempt in range(max_retries + 1):
            try:
                print(f"FIRMS API call attempt {attempt + 1}: {url}")
                
                # Create request with proper headers
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Environmental-Monitoring-App/1.0')
                
                with urllib.request.urlopen(req, timeout=20) as response:
                    if response.status == 200:
                        csv_content = response.read().decode('utf-8')
                        parsed_data = self.parse_csv(csv_content)
                        if parsed_data:
                            print(f"Successfully fetched {len(parsed_data)} fire records")
                            return parsed_data
                        else:
                            print("No fire data in response")
                            return []
                    else:
                        print(f"FIRMS HTTP Error {response.status}: {response.reason}")
            except urllib.error.HTTPError as e:
                print(f"FIRMS HTTP Error {e.code}: {e.reason}")
                if e.code == 500:
                    print("NASA FIRMS API experiencing server issues")
            except Exception as e:
                print(f"FIRMS request error: {e}")
            
            if attempt < max_retries:
                wait_time = (attempt + 1) * 2  # Progressive backoff
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        print("All FIRMS API attempts failed")
        return None

    def parse_csv(self, csv_content):
        """Parse CSV fire data into list of dictionaries"""
        lines = csv_content.strip().split('\n')
        if len(lines) < 2:
            return []
        
        headers = lines[0].split(',')
        fires = []
        
        for line in lines[1:]:
            values = line.split(',')
            if len(values) == len(headers):
                fire_dict = dict(zip(headers, values))
                fires.append(fire_dict)
        
        return fires

    def compute_heat_index(self, temp_f, humidity):
        """Compute heat index using NOAA formula"""
        if temp_f < 80:
            return temp_f
        
        T = temp_f
        R = humidity
        
        # Rothfusz regression
        HI = (-42.379 + 2.04901523*T + 10.14333127*R - 0.22475541*T*R - 
              6.83783e-3*T*T - 5.481717e-2*R*R + 1.22874e-3*T*T*R + 
              8.5282e-4*T*R*R - 1.99e-6*T*T*R*R)
        
        # Adjustments
        if R < 13 and 80 <= T <= 112:
            HI = HI - ((13-R)/4)*((17-abs(T-95))/17)**0.5
        elif R > 85 and 80 <= T <= 87:
            HI = HI + ((R-85)/10)*((87-T)/5)
        
        return HI

    def calculate_fire_risk(self, temp_f, humidity, wind_speed):
        """Calculate fire weather index based on temperature, humidity, and wind"""
        # Base fire risk calculation
        fire_risk_level = 0
        
        # Temperature factor (higher temp = higher risk)
        if temp_f >= 90:
            fire_risk_level += 3
        elif temp_f >= 80:
            fire_risk_level += 2
        elif temp_f >= 70:
            fire_risk_level += 1
        
        # Humidity factor (lower humidity = higher risk)
        if humidity <= 20:
            fire_risk_level += 4
        elif humidity <= 30:
            fire_risk_level += 3
        elif humidity <= 40:
            fire_risk_level += 2
        elif humidity <= 50:
            fire_risk_level += 1
        
        # Wind factor (higher wind = higher risk)
        if wind_speed >= 25:
            fire_risk_level += 3
        elif wind_speed >= 15:
            fire_risk_level += 2
        elif wind_speed >= 10:
            fire_risk_level += 1
        
        # Cap at maximum risk level
        return min(fire_risk_level, 10)

    def handle_fires_api(self, parsed_path):
        """Serve fire data directly from NASA FIRMS API"""
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Get NASA FIRMS API key
            api_key = os.environ.get('NASA_FIRMS_API_KEY', '5c34e7394c85b3e51634e51ac0eebf73')
            
            # Try direct NASA FIRMS API call for current US fires
            url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{api_key}/VIIRS_SNPP_NRT/-130,20,-60,50/7"
            
            try:
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Environmental-Monitoring-App/1.0')
                
                with urllib.request.urlopen(req, timeout=15) as response:
                    if response.status == 200:
                        csv_content = response.read().decode('utf-8')
                        fires = self.parse_nasa_fires_csv(csv_content)
                        
                        if fires:
                            # Filter for lower 48 US states with high confidence fires only
                            us_fires = [fire for fire in fires if 
                                       25.0 <= fire['latitude'] <= 49.0 and 
                                       -125.0 <= fire['longitude'] <= -66.0 and
                                       fire['confidence'] == 'H']
                            
                            response_data = {
                                'fires': us_fires,
                                'count': len(us_fires),
                                'source': 'NASA FIRMS API Direct',
                                'last_updated': int(time.time())
                            }
                            
                            self.wfile.write(json.dumps(response_data).encode())
                            return
            except Exception as api_error:
                print(f"NASA FIRMS API error: {api_error}")
            
            # Fallback response
            response = {
                'fires': [],
                'count': 0,
                'message': 'Fire data temporarily unavailable',
                'source': 'NASA FIRMS API'
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"Error in fires API: {e}")
            self.send_error(500, f"Fire data error: {str(e)}")
    
    def parse_nasa_fires_csv(self, csv_content):
        """Parse NASA FIRMS CSV data into fire records"""
        lines = csv_content.strip().split('\n')
        if len(lines) < 2:
            return []
        
        headers = [h.strip() for h in lines[0].split(',')]
        fires = []
        
        for line in lines[1:]:
            values = [v.strip() for v in line.split(',')]
            if len(values) >= len(headers):
                fire_dict = dict(zip(headers, values))
                
                try:
                    lat = float(fire_dict.get('latitude', 0))
                    lon = float(fire_dict.get('longitude', 0))
                    confidence = fire_dict.get('confidence', '').upper()
                    
                    if lat != 0 and lon != 0 and confidence in ['L', 'N', 'H']:
                        fires.append({
                            'latitude': lat,
                            'longitude': lon,
                            'confidence': confidence,
                            'brightness': float(fire_dict.get('bright_ti4', 0)) if fire_dict.get('bright_ti4') else None,
                            'acq_date': fire_dict.get('acq_date', ''),
                            'acq_time': fire_dict.get('acq_time', '')
                        })
                except (ValueError, TypeError):
                    continue
        
        return fires

    def handle_weather_tiles(self, parsed_path):
        """Proxy weather tile requests to OpenWeatherMap"""
        api_key = os.getenv('OPENWEATHERMAP_API_KEY')
        if not api_key:
            self.send_error(500, "OpenWeatherMap API key required for weather tiles")
            return
        
        # Extract tile parameters from path
        path_parts = parsed_path.path.split('/')
        if len(path_parts) >= 6:
            layer = path_parts[3]
            z = path_parts[4]
            x = path_parts[5]
            y = path_parts[6].split('.')[0]  # Remove .png extension
            
            # Construct OpenWeatherMap tile URL
            tile_url = f"https://tile.openweathermap.org/map/{layer}/{z}/{x}/{y}.png?appid={api_key}"
            
            try:
                with urllib.request.urlopen(tile_url, timeout=10) as response:
                    if response.status == 200:
                        self.send_response(200)
                        self.send_header('Content-Type', 'image/png')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(response.read())
                    else:
                        self.send_error(response.status, f"Tile request failed: {response.reason}")
            except Exception as e:
                self.send_error(500, f"Tile proxy error: {str(e)}")
        else:
            self.send_error(400, "Invalid tile request format")

    def handle_geocode_api(self, parsed_path):
        """Handle Google Maps geocoding requests"""
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not api_key:
            self.send_error(500, "Google Maps API key required")
            return
        
        query_params = parse_qs(parsed_path.query)
        address = query_params.get('address', [None])[0]
        
        if not address:
            self.send_error(400, "Missing address parameter")
            return
        
        try:
            # Use Google Geocoding API
            geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={api_key}"
            
            with urllib.request.urlopen(geocode_url, timeout=10) as response:
                if response.status == 200:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(response.read())
                else:
                    self.send_error(response.status, f"Geocoding failed: {response.reason}")
        except Exception as e:
            self.send_error(500, f"Geocoding error: {str(e)}")

    def handle_storms_api(self, parsed_path):
        """Handle National Weather Service alerts and warnings"""
        try:
            print("Fetching National Weather Service alerts...")
            
            # NWS API endpoint for active alerts in the continental US
            nws_url = "https://api.weather.gov/alerts/active?status=actual&message_type=alert"
            
            # Create request with proper headers
            req = urllib.request.Request(
                nws_url,
                headers={
                    'User-Agent': '(EnvironmentalSafetyDashboard, admin@example.com)',
                    'Accept': 'application/geo+json'
                }
            )
            
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    data = json.loads(response.read())
                    
                    all_warnings = []
                    
                    if 'features' in data:
                        for alert in data['features']:
                            properties = alert.get('properties', {})
                            geometry = alert.get('geometry')
                            
                            # Extract alert details
                            event = properties.get('event', '')
                            severity = properties.get('severity', 'Unknown')
                            urgency = properties.get('urgency', 'Unknown')
                            certainty = properties.get('certainty', 'Unknown')
                            headline = properties.get('headline', '')
                            description = properties.get('description', '')
                            instruction = properties.get('instruction', '')
                            areas = properties.get('areaDesc', '')
                            
                            # Skip test alerts
                            if any(test_word in event.lower() for test_word in ['test', 'practice', 'exercise']):
                                continue
                            
                            # Process alerts with or without coordinates
                            include_alert = False
                            display_geometry = geometry
                            
                            if geometry and 'coordinates' in geometry:
                                coords = geometry['coordinates']
                                if coords and len(coords) > 0:
                                    # Get representative coordinate
                                    if isinstance(coords[0], list) and isinstance(coords[0][0], list):
                                        # Polygon geometry
                                        sample_coord = coords[0][0]
                                    elif isinstance(coords[0], list):
                                        # LineString or simple polygon
                                        sample_coord = coords[0]
                                    else:
                                        # Point geometry
                                        sample_coord = coords
                                    
                                    if len(sample_coord) >= 2:
                                        lng, lat = sample_coord[0], sample_coord[1]
                                        
                                        # Expanded continental US bounds to include all lower 48 states
                                        if 20.0 <= lat <= 50.0 and -130.0 <= lng <= -60.0:
                                            include_alert = True
                            else:
                                # Handle alerts without coordinates by checking area descriptions
                                # Include if areas mention US states (but exclude Alaska, Hawaii, territories)
                                if areas:
                                    lower_areas = areas.lower()
                                    # List of continental US state indicators
                                    us_states = ['washington', 'oregon', 'california', 'nevada', 'arizona', 'utah', 'idaho',
                                               'montana', 'wyoming', 'colorado', 'new mexico', 'north dakota', 'south dakota',
                                               'nebraska', 'kansas', 'oklahoma', 'texas', 'minnesota', 'iowa', 'missouri',
                                               'arkansas', 'louisiana', 'wisconsin', 'illinois', 'mississippi', 'alabama',
                                               'tennessee', 'kentucky', 'indiana', 'michigan', 'ohio', 'west virginia',
                                               'virginia', 'north carolina', 'south carolina', 'georgia', 'florida',
                                               'maine', 'new hampshire', 'vermont', 'massachusetts', 'rhode island',
                                               'connecticut', 'new york', 'pennsylvania', 'new jersey', 'delaware',
                                               'maryland', 'columbia']
                                    
                                    # Exclude Alaska, Hawaii, and territories
                                    excluded = ['alaska', 'hawaii', 'puerto rico', 'virgin islands', 'guam', 'samoa']
                                    
                                    if any(state in lower_areas for state in us_states) and not any(excl in lower_areas for excl in excluded):
                                        include_alert = True
                                        # Create approximate coordinates based on area descriptions
                                        approx_coords = None
                                        
                                        # More specific location matching for heat advisories
                                        if any(term in lower_areas for term in ['columbia river', 'portland', 'willamette', 'tualatin', 'vancouver metro', 'clackamas']):
                                            approx_coords = [-122.68, 45.52]  # Portland area
                                        elif any(term in lower_areas for term in ['seattle', 'puget sound', 'king county']):
                                            approx_coords = [-122.33, 47.61]  # Seattle area
                                        elif any(term in lower_areas for term in ['spokane', 'coeur d\'alene', 'northern panhandle']):
                                            approx_coords = [-117.43, 47.66]  # Spokane area
                                        elif any(term in lower_areas for term in ['yakima', 'kittitas', 'wenatchee', 'chelan']):
                                            approx_coords = [-120.51, 46.60]  # Central Washington
                                        elif any(term in lower_areas for term in ['el paso', 'hudspeth']):
                                            approx_coords = [-106.49, 31.76]  # El Paso area
                                        elif any(term in lower_areas for term in ['brewster', 'terrell', 'chisos']):
                                            approx_coords = [-103.25, 30.25]  # West Texas
                                        elif 'texas' in lower_areas:
                                            approx_coords = [-99.25, 31.25]  # Central Texas
                                        elif 'washington' in lower_areas or 'okanogan' in lower_areas:
                                            approx_coords = [-120.84, 47.04]  # Central Washington
                                        elif 'oregon' in lower_areas or 'blue mountains' in lower_areas:
                                            approx_coords = [-123.03, 44.93]  # Central Oregon
                                        elif 'idaho' in lower_areas or 'lewiston' in lower_areas:
                                            approx_coords = [-114.74, 44.07]  # Central Idaho
                                        
                                        # If we have approximate coordinates, create geometry
                                        if approx_coords:
                                            display_geometry = {
                                                'type': 'Point',
                                                'coordinates': approx_coords
                                            }
                                        else:
                                            # Still include the alert even without coordinates for debugging
                                            display_geometry = {
                                                'type': 'Point',
                                                'coordinates': [-120.0, 45.0]  # Default US location
                                            }
                            
                            if include_alert:
                                warning = {
                                    'properties': {
                                        'event': event,
                                        'severity': severity,
                                        'urgency': urgency,
                                        'certainty': certainty,
                                        'headline': headline,
                                        'description': description,
                                        'instruction': instruction,
                                        'areas': areas,
                                        'effective': properties.get('effective'),
                                        'expires': properties.get('expires')
                                    },
                                    'geometry': display_geometry
                                }
                                all_warnings.append(warning)
                    
                    response_data = {
                        'warnings': all_warnings,
                        'total_alerts': len(data.get('features', [])),
                        'filtered_count': len(all_warnings),
                        'timestamp': int(time.time()),
                        'source': 'National Weather Service'
                    }
                    
                    # Debug: Count alert types and check for heat advisories
                    event_counts = {}
                    heat_advisories = []
                    excluded_heat_advisories = []
                    
                    for alert in data.get('features', []):
                        properties = alert.get('properties', {})
                        geometry = alert.get('geometry')
                        event = properties.get('event', 'Unknown')
                        areas = properties.get('areaDesc', '')
                        
                        event_counts[event] = event_counts.get(event, 0) + 1
                        
                        # Track heat advisories specifically
                        if 'heat' in event.lower():
                            coords_info = "No coords"
                            included = False
                            
                            if geometry and 'coordinates' in geometry:
                                coords = geometry['coordinates']
                                if coords and len(coords) > 0:
                                    # Get representative coordinate
                                    if isinstance(coords[0], list) and isinstance(coords[0][0], list):
                                        sample_coord = coords[0][0]
                                    elif isinstance(coords[0], list):
                                        sample_coord = coords[0]
                                    else:
                                        sample_coord = coords
                                    
                                    if len(sample_coord) >= 2:
                                        lng, lat = sample_coord[0], sample_coord[1]
                                        coords_info = f"({lat:.2f}, {lng:.2f})"
                                        
                                        # Check if within bounds
                                        if 20.0 <= lat <= 50.0 and -130.0 <= lng <= -60.0:
                                            included = True
                                            heat_advisories.append(f"{event} - {areas} {coords_info}")
                                        else:
                                            excluded_heat_advisories.append(f"{event} - {areas} {coords_info} [OUT OF BOUNDS]")
                            
                            if not included and coords_info == "No coords":
                                # Check if this is a heat advisory that should be included based on area
                                lower_areas = areas.lower()
                                us_states = ['washington', 'oregon', 'california', 'nevada', 'arizona', 'utah', 'idaho',
                                           'montana', 'wyoming', 'colorado', 'new mexico', 'north dakota', 'south dakota',
                                           'nebraska', 'kansas', 'oklahoma', 'texas', 'minnesota', 'iowa', 'missouri',
                                           'arkansas', 'louisiana', 'wisconsin', 'illinois', 'mississippi', 'alabama',
                                           'tennessee', 'kentucky', 'indiana', 'michigan', 'ohio', 'west virginia',
                                           'virginia', 'north carolina', 'south carolina', 'georgia', 'florida',
                                           'maine', 'new hampshire', 'vermont', 'massachusetts', 'rhode island',
                                           'connecticut', 'new york', 'pennsylvania', 'new jersey', 'delaware',
                                           'maryland', 'columbia']
                                
                                excluded = ['alaska', 'hawaii', 'puerto rico', 'virgin islands', 'guam', 'samoa']
                                
                                if any(state in lower_areas for state in us_states) and not any(excl in lower_areas for excl in excluded):
                                    heat_advisories.append(f"{event} - {areas} [INCLUDED WITHOUT COORDS]")
                                else:
                                    excluded_heat_advisories.append(f"{event} - {areas} [NO COORDINATES]")
                    
                    print(f"Retrieved {len(all_warnings)} NWS alerts from {len(data.get('features', []))} total alerts")
                    print("Alert types in original data:", dict(list(event_counts.items())[:15]))
                    
                    if heat_advisories:
                        print(f"INCLUDED Heat advisories ({len(heat_advisories)}):", heat_advisories)
                    if excluded_heat_advisories:
                        print(f"EXCLUDED Heat advisories ({len(excluded_heat_advisories)}):", excluded_heat_advisories)
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode())
                    
                else:
                    print(f"NWS API returned status {response.status}")
                    self.send_error(response.status, f"NWS API error: {response.reason}")
                    
        except urllib.error.HTTPError as e:
            print(f"HTTP error accessing NWS API: {e.code} {e.reason}")
            # Fallback to empty response rather than error for better UX
            fallback_response = {
                'warnings': [],
                'total_alerts': 0,
                'filtered_count': 0,
                'timestamp': int(time.time()),
                'source': 'National Weather Service (Unavailable)',
                'error': f"NWS API temporarily unavailable: {e.reason}"
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(fallback_response).encode())
            
        except Exception as e:
            print(f"Error fetching NWS alerts: {str(e)}")
            # Fallback response
            fallback_response = {
                'warnings': [],
                'total_alerts': 0,
                'filtered_count': 0,
                'timestamp': int(time.time()),
                'source': 'National Weather Service (Error)',
                'error': f"Unable to fetch alerts: {str(e)}"
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(fallback_response).encode())

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Create and start the server
    server = HTTPServer(('0.0.0.0', port), WeatherAPIHandler)
    print(f"Server running on port {port}")
    server.serve_forever()
