# Deployment Guide - Safety Dashboard

## GitHub Repository Update Instructions

### 1. Initialize Git (if not already done)
```bash
git init
git remote add origin https://github.com/shawnatwsu/HazardApp.git
```

### 2. Stage All Changes
```bash
git add .
git status  # Review what will be committed
```

### 3. Commit Latest Changes
```bash
git commit -m "feat: Major Safety Dashboard v2.0 update

- Enhanced mobile UI with next-level optimizations
- Fixed map navigation by removing blocking panels  
- Added NASA FIRMS fire detection (109 active fires)
- Integrated NWS weather alerts (48+ active alerts)
- Implemented PostgreSQL database for fire caching
- Added pull-to-refresh with haptic feedback
- Updated branding and proper data attribution
- Improved touch controls and animations"
```

### 4. Push to GitHub
```bash
git push -u origin main
```

If you encounter permission issues, you may need to:
```bash
git push --force-with-lease origin main
```

## Environment Setup for Deployment

### Required Environment Variables
```bash
# API Keys (required)
OPENWEATHERMAP_API_KEY=your_openweather_api_key
NASA_FIRMS_API_KEY=your_nasa_firms_key  
GOOGLE_MAPS_API_KEY=your_google_maps_key

# Database Configuration
DATABASE_URL=postgresql://username:password@hostname:port/database
PGHOST=your_db_host
PGPORT=5432
PGUSER=your_db_user
PGPASSWORD=your_db_password
PGDATABASE=hazardapp
```

### Production Deployment Options

#### Option 1: Replit Deployment
1. Connect GitHub repository to Replit
2. Set environment variables in Replit secrets
3. Run `python server.py`
4. Access via provided Replit URL

#### Option 2: Heroku Deployment  
1. Install Heroku CLI
2. Create new Heroku app: `heroku create your-app-name`
3. Add PostgreSQL addon: `heroku addons:create heroku-postgresql:hobby-dev`
4. Set environment variables: `heroku config:set OPENWEATHERMAP_API_KEY=your_key`
5. Deploy: `git push heroku main`

#### Option 3: Vercel Deployment
1. Install Vercel CLI: `npm i -g vercel`
2. Configure `vercel.json` for Python runtime
3. Set environment variables in Vercel dashboard
4. Deploy: `vercel --prod`

#### Option 4: Railway Deployment
1. Connect GitHub repository to Railway
2. Configure environment variables
3. Auto-deploy on push to main branch

## Database Setup

### PostgreSQL Schema Migration
```bash
# Install dependencies first
npm install

# Push database schema
npm run db:push
```

### Manual Database Setup (if needed)
```sql
-- Create fires table
CREATE TABLE fires (
    id SERIAL PRIMARY KEY,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    brightness INTEGER,
    confidence VARCHAR(1),
    acq_date DATE,
    acq_time VARCHAR(4),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create fire cache table  
CREATE TABLE fire_cache (
    id SERIAL PRIMARY KEY,
    last_update TIMESTAMP NOT NULL,
    total_fires INTEGER,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Production Checklist

### Before Deployment
- [ ] All API keys configured in environment variables
- [ ] PostgreSQL database accessible
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database schema migrated
- [ ] Test fire data loading
- [ ] Test weather alert system
- [ ] Test mobile interface on multiple devices

### After Deployment
- [ ] Verify fire markers loading (should see 109+ fires)
- [ ] Test NWS alerts button (should show 48+ alerts)
- [ ] Check mobile responsiveness 
- [ ] Verify pull-to-refresh functionality
- [ ] Test location search with Google Maps
- [ ] Confirm data attribution displays correctly

## API Rate Limits & Monitoring

### Current API Usage
- **NASA FIRMS**: 5,000 requests per 10 minutes (we use ~1 per 6 hours)
- **OpenWeatherMap**: 1,000 calls per day (varies by usage)
- **Google Maps**: Monitor geocoding quota
- **NWS**: No official rate limit (we refresh every 5 minutes)

### Monitoring Commands
```bash
# Check application logs
tail -f logs/app.log

# Monitor database connections
psql $DATABASE_URL -c "SELECT COUNT(*) FROM fires;"

# Test API endpoints
curl https://your-domain.com/api/fires
curl https://your-domain.com/api/storms
```

## Troubleshooting

### Common Issues
1. **"No fires loading"**: Check NASA FIRMS API key and network connectivity
2. **"NWS alerts not showing"**: NWS API may be temporarily unavailable  
3. **"Database connection error"**: Verify DATABASE_URL and PostgreSQL service
4. **"Map not loading"**: Check if port 5000 is accessible and not firewalled

### Debug Mode
```bash
# Run with debug output
python server.py --debug

# Check individual API responses
curl "https://your-domain.com/api/weather?lat=45.8&lon=-122.7"
```

---

**Ready for production deployment with real-time fire detection and weather alerts.**