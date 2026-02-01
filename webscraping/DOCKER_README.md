# BetterWeather Radar Server - Docker Deployment

This Docker container runs the BetterWeather radar server, which downloads weather radar images from the Australian Bureau of Meteorology and serves them to Garmin devices.

## What's Included

The container runs two services using Supervisor:
1. **FTP Scraper** - Downloads and processes radar images every 60 seconds
2. **Nginx Web Server** - Serves the processed images via HTTP on port 80

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Navigate to the webscraping directory
cd webscraping

# Build and start the container
docker compose up -d

# View logs
docker compose logs -f

# Stop the container
docker compose down
```

### Using Docker CLI

```bash
# Navigate to the webscraping directory
cd webscraping

# Build the image
docker build -t betterweather-server .

# Run the container
docker run -d \
  --name betterweather-radar \
  -p 80:80 \
  -v $(pwd)/images:/app/images \
  --restart unless-stopped \
  betterweather-server

# View logs
docker logs -f betterweather-radar

# Stop the container
docker stop betterweather-radar
docker rm betterweather-radar
```

## Configuration

### Port Mapping

By default, the server listens on port 80. To use a different port:

```bash
# Docker Compose: Edit docker-compose.yml
ports:
  - "8080:80"  # Host port 8080 -> Container port 80

# Docker CLI:
docker run -d -p 8080:80 betterweather-server
```

### Volume Persistence

The `images/` directory is mounted as a volume to persist radar images between container restarts. This avoids re-downloading images when you restart the container.

### DNS Update Script

The original code references `./updateDNS.sh` for dynamic DNS updates. A placeholder script is included in the Docker image. To use your own:

1. Create `updateDNS.sh` in the `webscraping/` directory
2. Uncomment the volume mount in `docker-compose.yml`:
   ```yaml
   - ./updateDNS.sh:/app/updateDNS.sh:ro
   ```
3. Rebuild and restart the container

### Timezone

The container defaults to `Australia/Sydney` timezone. To change:

```yaml
# In docker-compose.yml
environment:
  - TZ=Australia/Melbourne  # or your preferred timezone
```

## Accessing Radar Images

Once running, radar images are available at:

```
http://your-server-ip/images/0.png
http://your-server-ip/images/1.png
...
http://your-server-ip/images/6.png
http://your-server-ip/images/radar.png
```

## Monitoring

### Health Check

The container includes a health check that verifies images are being downloaded:

```bash
# Check container health
docker ps

# View detailed health status
docker inspect betterweather-radar | grep -A 10 Health
```

### Logs

```bash
# Docker Compose
docker compose logs -f

# Docker CLI
docker logs -f betterweather-radar

# View only scraper logs
docker exec betterweather-radar tail -f /var/log/supervisor/ftpscraper-stdout---supervisor-*.log

# View only nginx logs
docker exec betterweather-radar tail -f /var/log/nginx/access.log
```

## Troubleshooting

### Container won't start

```bash
# Check logs for errors
docker logs betterweather-radar

# Verify the image built correctly
docker images | grep betterweather-server
```

### No images being downloaded

```bash
# Check FTP scraper logs
docker compose logs betterweather-server

# Verify network connectivity from container
docker exec betterweather-radar ping -c 3 ftp.bom.gov.au

# Check if images directory exists
docker exec betterweather-radar ls -la /app/images/
```

### Cannot access images via HTTP

```bash
# Verify nginx is running
docker exec betterweather-radar supervisorctl status

# Test from inside container
docker exec betterweather-radar curl -I http://localhost/images/0.png

# Check port mapping
docker port betterweather-radar
```

## Updating

```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose down
docker compose up -d --build
```

## Resource Usage

The container is lightweight:
- **Image Size**: ~200MB
- **Memory Usage**: ~50-100MB
- **CPU Usage**: Minimal (only active during FTP downloads every 60s)

## Security Considerations

1. **Exposed Port**: The container exposes port 80. Consider using a reverse proxy (nginx, Caddy, Traefik) with HTTPS in production.
2. **DNS Script**: Review and secure your `updateDNS.sh` script before mounting it.
3. **Firewall**: Ensure your firewall allows inbound connections on the exposed port.

## Production Deployment

For production, consider:

1. **Use a reverse proxy with HTTPS**:
   ```yaml
   version: '3.8'
   services:
     betterweather-server:
       # ... existing config ...
       expose:
         - "80"
       networks:
         - traefik-network
       labels:
         - "traefik.enable=true"
         - "traefik.http.routers.radar.rule=Host(`garminradar.mooo.com`)"
         - "traefik.http.routers.radar.entrypoints=websecure"
         - "traefik.http.routers.radar.tls.certresolver=letsencrypt"
   ```

2. **Set up log rotation** (already configured in docker-compose.yml)

3. **Monitor with health checks** (already included)

4. **Use Docker secrets** for sensitive data if needed

## Garmin App Configuration

Update your Garmin app's URL to point to your Docker container:

```monkey-c
// In BetterWeatherApp.mc
var url = "http://your-docker-host-ip/images/" + i + ".png";
```

## Support

For issues specific to the Docker setup, check the logs. For issues with the radar scraper itself, refer to the main project documentation.
