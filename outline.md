# BetterWeather Project Outline

## Overview
A weather radar app for Garmin watches (FR745) that displays animated Australian Bureau of Meteorology radar images. The system consists of a Python backend server and a MonkeyC Garmin watch application.

## Architecture

### Data Flow
```
BOM FTP Server (ftp.bom.gov.au)
    ↓ (downloads IDR714 radar images every 60s)
Python Server (ftpscraper.py)
    ↓ (crops/resizes to 240x240, maintains rolling buffer)
Static Images (0.png - 6.png)
    ↓ (HTTP download every 5 minutes)
Garmin Watch App
    ↓ (animated display at 500ms per frame)
Watch Display
```

## Components

### 1. Python Backend Server
**Location**: `webscraping/`

**Main File**: `ftpscraper.py`
- Connects to Bureau of Meteorology FTP server
- Downloads latest radar images (IDR714 format) every 60 seconds
- Calculates filename based on UTC time minus 6 minutes
- Crops images (removes 70+16px borders)
- Resizes to 240x240 pixels for watch display
- Maintains rolling buffer of 7 most recent images (0.png - 6.png)
- Creates composite radar.png (3x3 grid of 7 images)
- Calls updateDNS.sh script after each update

**Dependencies**: Pillow, NumPy, ftplib

**Output**: `images/` directory with 0.png through 6.png plus radar.png

### 2. Garmin Watch Application
**Location**: `source/`

**Language**: MonkeyC (Garmin Connect IQ)

**Target Device**: Garmin FR745 (specified in manifest.xml)

**Files**:

- **BetterWeatherApp.mc** (Main Application)
  - Downloads 7 radar images from server
  - URL: `http://betterweather.nickhespe.com/images/$1$.png`
  - Downloads sequentially (6 down to 0) on startup
  - Refreshes every 5 minutes via timer
  - Stores images in device storage using Storage API
  - Handles download failures with retry logic
  - Image format: YUV packed, no dithering

- **BetterWeatherView.mc** (UI Display)
  - Main view component with custom drawable
  - Animates through 7 radar images in a loop
  - Display timing: 500ms per frame (2000ms on last frame)
  - CustomTimeRing drawable renders current radar frame
  - Progress arc shows animation position (90° to wraparound)
  - Error handling displays failed request code

- **BetterWeatherDelegate.mc** (Input Handler)
  - Handles swipe gestures
  - "Previous page" gesture triggers image refresh

**Permissions**: Communications, PersistedLocations, Positioning

**Resources**:
- Layouts: `resources/layouts/layout.xml`
- Menus: `resources/menus/menu.xml`
- Drawables: launcher icon, images
- Radar backgrounds: various PNG overlays (topography, roads, etc.)

### 3. Docker Deployment
**Location**: `webscraping/`

**Files**:
- `Dockerfile`: Multi-service container (Python app + Nginx)
- `docker-compose.yml`: Orchestration with volume persistence
- `requirements.txt`: Python dependencies
- `.dockerignore`: Build optimization

**Services**:
- FTP scraper (Python background process)
- Nginx web server (serves images on port 80)
- Managed by supervisord

## Key Technical Details

### Image Processing Pipeline
1. Download raw radar PNG from BOM (variable resolution)
2. Crop: Remove 86px from top/left, 70px from bottom/right
3. Resize to 240x240 using Lanczos resampling
4. Rolling buffer: Shift existing images, add new image as #6
5. Composite: Arrange 7 images in 3-column grid

### Watch App Behavior
- Startup: Download all 7 images sequentially
- Storage: Images stored in watch persistent storage
- Animation loop: Continuous cycling through frames
- Network: 5-minute refresh interval
- Error display: Shows HTTP response code on failure
- Visual indicator: Red arc when downloading (imgs_remaining != 0)

### Server Configuration
- FTP Source: `ftp.bom.gov.au/anon/gen/radar/`
- Radar ID: IDR714 (specific Australian radar station)
- Update frequency: Every 60 seconds
- Image format: PNG with transparency
- DNS update: Called after each successful update

## Directory Structure
```
BetterWeather/
├── source/              # MonkeyC source files
│   ├── BetterWeatherApp.mc
│   ├── BetterWeatherView.mc
│   ├── BetterWeatherDelegate.mc
│   └── BetterWeatherMenuDelegate.mc
├── resources/           # Garmin app resources
│   ├── layouts/
│   ├── menus/
│   ├── drawables/
│   ├── strings/
│   ├── radar/           # Sample radar images
│   └── radar_backgrounds/  # Map overlays
├── webscraping/         # Python backend
│   ├── ftpscraper.py
│   ├── images/          # Generated radar images (0-6.png)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
├── bin/                 # Build output
├── manifest.xml         # Garmin app manifest
└── monkey.jungle        # Build configuration
```

## URLs and Endpoints

### Current Server
- Production: `http://betterweather.nickhespe.com/images/`
- Docker deployment: `http://<host-ip>/images/`

### Image Endpoints
- Individual frames: `/images/0.png` through `/images/6.png`
- Composite view: `/images/radar.png`

## Build System
- Garmin SDK: Connect IQ SDK (MonkeyC compiler)
- Min API Level: 3.2.0
- Build tool: VSCode Monkey C extension
- Debug: `.vscode/launch.json` configured for FR745

## State Management
- Watch storage keys:
  - `radar_imgaes`: Array of 7 BitmapResource objects
  - `weatherPage`: Current animation frame index (0-6)
- Global variables:
  - `IMG_NUM`: Constant 7 (number of radar frames)
  - `imgs_remaining`: Download progress counter
  - `img_request_response`: Last HTTP response code
