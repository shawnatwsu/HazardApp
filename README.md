# 🛡️ Safety Dashboard

**Real-time environmental hazards monitor for the continental United States.**

A single-page web app that visualizes active wildfires, severe weather alerts, and local weather conditions on an interactive map — powered entirely by free, public APIs with zero backend required.

**[▶ Live Demo](https://shawnatwsu.github.io/HazardApp/)**

---

## What It Does

Click anywhere on the map (or search a city) and instantly see:

- 🔥 **Active wildfires** — NASA satellite detections rendered in real time
- ⚠️ **NWS weather alerts** — Tornado, thunderstorm, heat, flood, and fire warnings
- 🌡️ **Local conditions** — Temperature, heat index, humidity, wind, UV, air quality (PM2.5)
- 🏃 **Activity recommendations** — Whether it's safe to walk, run, or be outdoors
- 🫁 **Health risk flags** — Warnings for sensitive groups (elderly, children, asthma/lung conditions)

Everything runs client-side. No server, no database, no API keys to configure.

---

## Data Sources

| Layer | Source | Update Frequency |
|-------|--------|-----------------|
| Wildfires | [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/) — NOAA-20 & NOAA-21 VIIRS satellites | Near real-time via WMS |
| Weather alerts | [NOAA National Weather Service](https://www.weather.gov/) | Every 5 minutes |
| Current weather | [Open-Meteo](https://open-meteo.com/) | On click / 15-min auto-refresh |
| Air quality | [Open-Meteo Air Quality API](https://open-meteo.com/) | On click |
| Geocoding | [Nominatim](https://nominatim.openstreetmap.org/) (OpenStreetMap) | On search |
| Base map | [OpenStreetMap](https://www.openstreetmap.org/) | — |

All APIs are free and require no authentication.

---

## Features

### Fire Detection
NASA FIRMS VIIRS data is displayed as a WMS tile layer directly on the map, showing high-confidence fire detections across the lower 48 states. This is the same rendering method used on the official FIRMS website. Low-confidence detections (industrial lights, gas flares) are excluded.

### Weather Alerts
Live alerts from the NWS are filtered to the continental US and displayed as clickable markers color-coded by type — tornadoes (🌪️), thunderstorms (⛈️), floods (🌊), heat (🔥), wind (💨), fire weather (🔥), fog (🌫️), and more. Click any marker for full details and safety instructions.

### Safety Dashboard
The bottom-left panel shows a comprehensive breakdown of conditions at the selected location, including an overall safety status (Safe → Caution → Danger → Emergency), along with actionable guidance — what activities are safe, who is at risk, and what to do.

### Mobile-First Design
Touch-friendly 56px button targets, glassmorphism UI, pull-to-refresh with haptic feedback, and responsive layout that works on phones and tablets.

---

## Deployment

This is a static site — just one `index.html` file. No build step, no dependencies.

### GitHub Pages

1. Fork or clone this repo
2. Go to **Settings → Pages**
3. Set source to **Deploy from a branch** → `main` / `/ (root)`
4. Save — your site goes live at `https://<username>.github.io/HazardApp/`

### Any Static Host

Upload `index.html` to any static hosting provider (Netlify, Vercel, Cloudflare Pages, S3, etc.). That's it.

### Local Development

```bash
# No build tools needed — just open the file
open index.html

# Or use any local server
python -m http.server 8000
# → http://localhost:8000
```

---

## How It Works

The app is a single HTML file (~3,100 lines) containing all markup, styles, and JavaScript. On load, it:

1. Initializes a [Leaflet.js](https://leafletjs.com/) map centered on the continental US
2. Loads NASA FIRMS fire data as WMS tile layers (NOAA-20 + NOAA-21 VIIRS)
3. On map click or location search, fetches weather from Open-Meteo and air quality data
4. Computes heat index (NOAA Rothfusz regression), fire risk score, and safety status
5. NWS alerts are fetched on demand and filtered to the lower 48 states

All API calls happen directly from the browser. No proxy, no backend, no CORS workarounds needed.

---

## Geographic Scope

Continental United States only (lower 48 states + DC). Alaska, Hawaii, and US territories are excluded. The map is bounded to prevent panning outside this region.

---

## Technical Details

- **Frontend:** HTML5, CSS3, vanilla JavaScript (ES6+)
- **Mapping:** Leaflet.js 1.9.4 with Turf.js and TopoJSON
- **Weather:** Open-Meteo forecast + air quality APIs
- **Fires:** NASA FIRMS WMS tile service
- **Alerts:** NWS API (api.weather.gov)
- **Search:** Nominatim geocoding (OpenStreetMap)
- **Heat Index:** NOAA Rothfusz regression with low-humidity and high-humidity adjustments
- **Fire Risk:** Composite score based on temperature, humidity, and wind speed (0–10 scale)

---

## API Rate Limits

Since everything is client-side, rate limits apply per user:

| API | Limit | Notes |
|-----|-------|-------|
| Open-Meteo | 10,000 req/day | Very generous for personal use |
| NWS | No official limit | Requests a User-Agent header |
| NASA FIRMS WMS | No practical limit | Standard map tile requests |
| Nominatim | 1 req/second | Only triggers on search |

---

## License

MIT

---

## Attribution

This application displays data from multiple authoritative public sources:

- **NASA FIRMS** — Public domain fire detection data
- **NOAA National Weather Service** — Public domain weather alerts
- **Open-Meteo** — Open-source weather API ([CC BY 4.0](https://open-meteo.com/en/terms))
- **OpenStreetMap** — Map tiles and geocoding ([ODbL](https://www.openstreetmap.org/copyright))
