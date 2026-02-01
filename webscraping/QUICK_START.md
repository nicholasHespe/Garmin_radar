# Quick Start - Raspberry Pi Setup

Follow these commands in order. SSH into your Raspberry Pi first.

## 1. Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install -y libffi-dev libssl-dev python3-dev python3-pip
sudo pip3 install docker-compose

# Verify
docker --version
docker-compose --version
```

## 2. Transfer Files

On your Windows machine, navigate to the webscraping folder and transfer to Pi:

```powershell
# Option 1: Using scp (if you have it)
scp -r . pi@<your-pi-ip>:~/webscraping

# Option 2: Use VS Code Remote SSH extension
# Option 3: Use WinSCP or FileZilla
```

## 3. Deploy on Raspberry Pi

```bash
# Navigate to folder
cd ~/webscraping

# Make updateDNS.sh executable
chmod +x updateDNS.sh

# Start the server
docker-compose up -d

# Watch logs (Ctrl+C to exit)
docker-compose logs -f
```

## 4. Test

Wait 90 seconds for first images to download, then:

```bash
# Check images were created
ls -lh images/

# Should see: 0.png, 1.png, 2.png, 3.png, 4.png, 5.png, 6.png, radar.png

# Test local HTTP access
curl -I http://localhost/images/0.png

# Should return: HTTP/1.1 200 OK
```

## 5. Test External Access

From your Windows machine:

```powershell
# Test local network
curl http://<pi-ip>/images/0.png --output test.png

# Test via domain
curl http://betterweather.nickhespe.com/images/0.png --output test-domain.png

# Open test.png and test-domain.png to verify radar images
```

## 6. Router Port Forwarding

If external access doesn't work:

1. Get Pi's IP: `hostname -I` (e.g., 192.168.1.100)
2. Access router admin (usually 192.168.1.1 or 192.168.0.1)
3. Find "Port Forwarding" or "Virtual Server"
4. Add rule:
   - External Port: 80
   - Internal IP: <your-pi-ip>
   - Internal Port: 80
   - Protocol: TCP
5. Save and enable

## Common Issues

**Images not downloading:**
```bash
docker-compose logs | grep -i error
```

**Container not running:**
```bash
docker ps
docker-compose up -d
```

**Port 80 already in use:**
```bash
# Check what's using port 80
sudo netstat -tlnp | grep :80

# If Apache or nginx is running, stop it:
sudo systemctl stop apache2
sudo systemctl stop nginx
sudo systemctl disable apache2
sudo systemctl disable nginx
```

**Can't access from internet:**
```bash
# Verify port forwarding
# Test from phone (disconnect from WiFi, use mobile data)
# Check Cloudflare proxy is enabled
```

## Useful Commands

```bash
# View logs
docker-compose logs -f

# Restart server
docker-compose restart

# Stop server
docker-compose down

# Check container status
docker ps

# Check images are updating
watch -n 10 "ls -lth images/ | head"
```

## Auto-start on Boot

```bash
# Create service file
sudo nano /etc/systemd/system/betterweather.service
```

Paste:
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

Save and enable:
```bash
sudo systemctl enable betterweather.service
sudo systemctl start betterweather.service
```

## Success Checklist

- [ ] Docker installed and running
- [ ] Files transferred to Pi
- [ ] Container running (`docker ps` shows betterweather-radar)
- [ ] Images exist in `images/` directory
- [ ] Local access works (`curl http://localhost/images/0.png`)
- [ ] Network access works (`curl http://<pi-ip>/images/0.png`)
- [ ] Router port 80 forwarded to Pi
- [ ] External access works (`curl http://betterweather.nickhespe.com/images/0.png`)
- [ ] Images update every 60 seconds
- [ ] Auto-start enabled for reboots
