# Raspberry Pi Deployment Guide

## Step 1: Router Port Forwarding

Configure your router to forward external traffic to your Raspberry Pi.

### Find Your Raspberry Pi's Local IP

```bash
# On the Raspberry Pi
hostname -I
```

Note the first IP address (e.g., 192.168.1.100)

### Configure Router

1. Access your router admin panel (usually http://192.168.1.1 or http://192.168.0.1)
2. Find "Port Forwarding" or "Virtual Server" settings
3. Add new rule:
   - **Service Name**: BetterWeather
   - **External Port**: 80
   - **Internal IP**: Your Pi's IP (from above)
   - **Internal Port**: 80
   - **Protocol**: TCP
4. Save and enable the rule

### Optional: Set Static IP for Raspberry Pi

To prevent the Pi's IP from changing:

1. Router settings → DHCP → Reserved IP or Static Lease
2. Bind your Pi's MAC address to a fixed IP
3. Or configure static IP on the Pi itself:

```bash
# Edit dhcpcd.conf
sudo nano /etc/dhcpcd.conf

# Add at the end:
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

## Step 2: Install Docker on Raspberry Pi

### Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker

# Verify installation
docker --version
```

### Install Docker Compose

```bash
# Install dependencies
sudo apt install -y libffi-dev libssl-dev python3-dev python3-pip

# Install Docker Compose
sudo pip3 install docker-compose

# Verify installation
docker-compose --version
```

## Step 3: Deploy BetterWeather Server

### Transfer Files to Raspberry Pi

From your Windows machine:

```powershell
# Using SCP (from PowerShell or WSL)
scp -r "d:\Files\2023\Garmin Apps\BetterWeather\webscraping" pi@<pi-ip>:~/

# Or use WinSCP, FileZilla, or VS Code Remote SSH
```

### On the Raspberry Pi

```bash
cd ~/webscraping

# Verify files are present
ls -la
```

### Create updateDNS.sh Script

```bash
# Create the script
nano updateDNS.sh
```

Add the following content:

```bash
#!/bin/bash
# DNS update script for Cloudflare
# Since you're using Cloudflare proxy, no dynamic DNS update needed
# This script logs when it's called

LOG_FILE="/app/dns_update.log"
echo "DNS update called at $(date)" >> "$LOG_FILE"

# Optional: Add Cloudflare API update if needed
# Uncomment and configure if your home IP changes frequently
# ZONE_ID="your_cloudflare_zone_id"
# RECORD_ID="your_dns_record_id"
# API_TOKEN="your_api_token"
#
# curl -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
#      -H "Authorization: Bearer $API_TOKEN" \
#      -H "Content-Type: application/json" \
#      --data '{"type":"A","name":"betterweather.nickhespe.com","content":"'$(curl -s ifconfig.me)'","ttl":120,"proxied":true}'
```

Save (Ctrl+O, Enter, Ctrl+X) and make executable:

```bash
chmod +x updateDNS.sh
```

### Start the Server

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f
```

## Step 4: Test Server

### Local Testing (on Raspberry Pi)

```bash
# Wait 60-90 seconds for first image download
sleep 90

# Check if images were created
ls -lh images/

# Test HTTP access locally
curl -I http://localhost/images/0.png

# View logs
docker-compose logs
```

### Test from Windows Machine

```powershell
# Test local network access
curl http://<pi-ip>/images/0.png --output test.png

# If successful, view test.png
```

### Test External Access

```powershell
# Test via domain
curl http://betterweather.nickhespe.com/images/0.png --output test-external.png
```

## Step 5: Verify Everything Works

### Check Cloudflare

1. Log into Cloudflare dashboard
2. Go to your domain → DNS Records
3. Verify A record for betterweather.nickhespe.com points to your public IP
4. Ensure "Proxy status" is enabled (orange cloud icon)

### Monitor Server

```bash
# On Raspberry Pi

# Check container status
docker ps

# Check logs for errors
docker-compose logs --tail=50

# Check if images are being updated
watch -n 60 ls -lh images/

# Check FTP connection
docker-compose logs | grep -i "downloaded\|error\|failed"
```

### Verify Image Updates

```bash
# Check image timestamps - should update every 60 seconds
watch -n 5 "ls -lth images/ | head -n 10"
```

## Step 6: Configure for Production

### Enable Auto-start on Boot

```bash
# Create systemd service
sudo nano /etc/systemd/system/betterweather.service
```

Add:

```ini
[Unit]
Description=BetterWeather Radar Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/pi/webscraping
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=pi

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable betterweather.service
sudo systemctl start betterweather.service

# Check status
sudo systemctl status betterweather.service
```

### Set up Log Rotation (Optional)

Docker Compose already configured log rotation, but you can add system-level rotation:

```bash
sudo nano /etc/logrotate.d/betterweather
```

Add:

```
/home/pi/webscraping/dns_update.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

## Troubleshooting

### Container won't start

```bash
# Check Docker is running
sudo systemctl status docker

# Check compose file syntax
docker-compose config

# Rebuild
docker-compose down
docker-compose up --build
```

### No images downloading

```bash
# Check FTP connectivity
docker exec betterweather-radar ping -c 3 ftp.bom.gov.au

# Check Python script logs
docker-compose logs betterweather-server | grep -i error

# Manually test FTP
docker exec -it betterweather-radar python3 -c "from ftplib import FTP; ftp = FTP('ftp.bom.gov.au'); ftp.login(); print('FTP OK')"
```

### Can't access from external network

```bash
# Check if port 80 is listening
sudo netstat -tlnp | grep :80

# Test from Pi to itself via public IP
curl -I http://$(curl -s ifconfig.me)/images/0.png

# Check router port forwarding is enabled
# Check firewall on Pi
sudo ufw status
```

### Cloudflare Issues

- Verify DNS propagation: https://dnschecker.org
- Check Cloudflare SSL/TLS mode is "Flexible" or "Full"
- Ensure "Proxy status" is enabled for the A record
- Check Cloudflare firewall rules aren't blocking requests

## Monitoring Commands

```bash
# Container health
docker ps

# Real-time logs
docker-compose logs -f

# Resource usage
docker stats betterweather-radar

# Disk space
df -h

# Image update status
tail -f dns_update.log
```

## Useful Commands

```bash
# Restart server
docker-compose restart

# Stop server
docker-compose down

# Update and rebuild
git pull  # if you make code changes
docker-compose down
docker-compose up -d --build

# Clean up old images
docker system prune -a
```

## Next Steps

Once server is confirmed working:
1. Update watch app URL to use betterweather.nickhespe.com
2. Test watch app downloads
3. Set up monitoring/alerting for server downtime
4. Document any custom configuration
