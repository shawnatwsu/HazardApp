# Deployment Guide

## GitHub Setup

1. **Initialize Git Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Environmental Monitoring Dashboard"
   ```

2. **Create GitHub Repository**
   - Go to GitHub and create a new repository
   - Don't initialize with README (we already have one)

3. **Push to GitHub**
   ```bash
   git remote add origin https://github.com/yourusername/environmental-monitoring.git
   git branch -M main
   git push -u origin main
   ```

## Security Notes

- API keys are stored in environment variables
- `.env` file is excluded from Git via `.gitignore`
- Use `.env.example` as template for new deployments
- Never commit actual API keys to the repository

## Environment Variables for Production

Set these in your deployment platform:

```
GOOGLE_MAPS_API_KEY=your_production_google_maps_key
OPENWEATHERMAP_API_KEY=your_production_openweather_key
```

## Platform Deployment Options

### Replit Deployments
- Environment variables managed in Replit Secrets
- Automatic deployment from GitHub repository
- Built-in HTTPS and custom domains

### Heroku
```bash
heroku create your-app-name
heroku config:set GOOGLE_MAPS_API_KEY=your_key
heroku config:set OPENWEATHERMAP_API_KEY=your_key
git push heroku main
```

### Railway
- Connect GitHub repository
- Set environment variables in Railway dashboard
- Automatic deployments on push

### Vercel/Netlify
- Suitable for static hosting with serverless functions
- Configure environment variables in platform settings