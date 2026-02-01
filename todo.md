# BetterWeather TODO

Priority: 5=Critical, 4=High, 3=Medium, 2=Low, 1=Nice-to-have

## Critical Issues (5)

- [ ] **[5]** Update server URL in BetterWeatherApp.mc to actual deployment endpoint
- [ ] **[5]** Create or document updateDNS.sh script (currently missing, called by ftpscraper.py)
- [ ] **[5]** Test BOM FTP server connectivity and verify IDR714 radar still available
- [ ] **[5]** Deploy server and verify image generation pipeline works
- [ ] **[5]** Test watch app builds with current Garmin Connect IQ SDK

## High Priority (4)

- [ ] **[4]** Add error handling and retry logic for FTP connection failures
- [ ] **[4]** Implement proper logging in Python server (currently only print statements)
- [ ] **[4]** Update Python dependencies to current stable versions
- [ ] **[4]** Fix typo in storage key ("radar_imgaes" should be "radar_images")
- [ ] **[4]** Add health check endpoint to verify server is running
- [ ] **[4]** Test image download on actual FR745 device
- [ ] **[4]** Verify YUV image format still supported by current Garmin SDK
- [ ] **[4]** Add graceful handling when images directory doesn't exist

## Medium Priority (3)

- [ ] **[3]** Create configuration file for server (radar ID, update interval, etc.)
- [ ] **[3]** Add environment variable support for Docker deployment
- [ ] **[3]** Implement proper error messages on watch instead of just HTTP codes
- [ ] **[3]** Add server-side image caching to reduce FTP requests
- [ ] **[3]** Create startup validation script to check all dependencies
- [ ] **[3]** Add HTTPS support for production deployment
- [ ] **[3]** Document radar station IDs for different Australian locations
- [ ] **[3]** Add metrics/monitoring for server uptime and image freshness
- [ ] **[3]** Optimize Docker image size (currently ~200MB)
- [ ] **[3]** Support configurable number of radar frames (currently hardcoded to 7)

## Low Priority (2)

- [ ] **[2]** Add automated tests for image processing pipeline
- [ ] **[2]** Optimize image compression while maintaining quality
- [ ] **[2]** Add progress indicator during initial image download
- [ ] **[2]** Create build script for automated compilation
- [ ] **[2]** Add support for different image resolutions based on watch model
- [ ] **[2]** Implement rate limiting on server to prevent abuse
- [ ] **[2]** Clean up commented-out code in ftpscraper.py
- [ ] **[2]** Add option to display composite radar.png instead of animation
- [ ] **[2]** Create user manual with screenshots
- [ ] **[2]** Add background color customization for watch display

## Nice-to-Have (1)

- [ ] **[1]** Create web dashboard to view current radar images
- [ ] **[1]** Support multiple Garmin device models (not just FR745)
- [ ] **[1]** Add automatic radar station selection based on GPS location
- [ ] **[1]** Implement CI/CD pipeline for automated builds
- [ ] **[1]** Create Connect IQ Store listing and publish app
- [ ] **[1]** Add settings menu on watch to configure refresh rate
- [ ] **[1]** Support international weather radar sources (not just Australia)
- [ ] **[1]** Add weather alerts/warnings overlay
- [ ] **[1]** Create mobile companion app for configuration
- [ ] **[1]** Add animation speed control via watch buttons

## Code Quality

- [ ] **[3]** Add comments explaining complex image processing logic
- [ ] **[3]** Standardize error handling patterns across codebase
- [ ] **[2]** Add type hints to all Python functions
- [ ] **[2]** Create developer documentation for codebase architecture
- [ ] **[2]** Add unit tests for image cropping/resizing functions
- [ ] **[1]** Set up pre-commit hooks for code formatting

## Infrastructure

- [ ] **[4]** Set up automated backups for server configuration
- [ ] **[3]** Create deployment guide for cloud hosting (AWS/Azure/GCP)
- [ ] **[3]** Add SSL certificate automation (Let's Encrypt)
- [ ] **[2]** Create Kubernetes manifests as alternative to Docker Compose
- [ ] **[2]** Set up monitoring and alerting for server failures
- [ ] **[1]** Add CDN for image distribution

## Security

- [ ] **[4]** Remove any hardcoded credentials or sensitive data
- [ ] **[3]** Add input validation for FTP filenames
- [ ] **[3]** Implement CORS policies for production API
- [ ] **[2]** Add authentication for server admin endpoints
- [ ] **[2]** Security audit of Docker container
- [ ] **[1]** Add DDoS protection for public deployment

## Documentation

- [ ] **[3]** Add inline code documentation to MonkeyC files
- [ ] **[3]** Create troubleshooting guide for common issues
- [ ] **[2]** Document BOM radar data format and API
- [ ] **[2]** Create video tutorial for setup and deployment
- [ ] **[1]** Add contributing guidelines for open source

## Known Bugs

- [ ] **[4]** Fix storage initialization logic (lines 58-62 in BetterWeatherApp.mc)
- [ ] **[3]** Handle case where all 7 image downloads fail
- [ ] **[3]** Timer doesn't restart properly after consecutive failures
- [ ] **[2]** Animation stutters on last frame transition
- [ ] **[2]** Arc drawing calculation incorrect for wraparound (line 95 BetterWeatherView.mc)
