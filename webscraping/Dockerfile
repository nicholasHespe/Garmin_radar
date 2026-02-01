# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    nginx \
    supervisor && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY ftpscraper.py .
COPY api_server.py .

# Create images directory
RUN mkdir -p images

# Create nginx configuration
RUN echo 'server {\n\
    listen 80;\n\
    server_name _;\n\
    root /app;\n\
    \n\
    # Proxy API requests to Flask\n\
    location /api/ {\n\
        proxy_pass http://127.0.0.1:5000/api/;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
    }\n\
    \n\
    # Proxy image requests to Flask for auto-generation\n\
    location /images/ {\n\
        proxy_pass http://127.0.0.1:5000/images/;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
        proxy_read_timeout 120s;\n\
    }\n\
}' > /etc/nginx/sites-available/default

# Create supervisor configuration
RUN echo '[supervisord]\n\
nodaemon=true\n\
user=root\n\
\n\
[program:api_server]\n\
command=python /app/api_server.py\n\
autostart=true\n\
autorestart=true\n\
stdout_logfile=/dev/stdout\n\
stdout_logfile_maxbytes=0\n\
stderr_logfile=/dev/stderr\n\
stderr_logfile_maxbytes=0\n\
priority=1\n\
\n\
[program:ftpscraper]\n\
command=python /app/ftpscraper.py\n\
autostart=true\n\
autorestart=true\n\
stdout_logfile=/dev/stdout\n\
stdout_logfile_maxbytes=0\n\
stderr_logfile=/dev/stderr\n\
stderr_logfile_maxbytes=0\n\
priority=2\n\
\n\
[program:nginx]\n\
command=nginx -g "daemon off;"\n\
autostart=true\n\
autorestart=true\n\
stdout_logfile=/dev/stdout\n\
stdout_logfile_maxbytes=0\n\
stderr_logfile=/dev/stderr\n\
stderr_logfile_maxbytes=0\n\
priority=3\n\
' > /etc/supervisor/conf.d/supervisord.conf

# Create a stub updateDNS.sh script (since the original is not in the repo)
RUN echo '#!/bin/bash\n\
# Placeholder for DNS update script\n\
# Add your DNS update logic here\n\
echo "DNS update called at $(date)"\n\
' > /app/updateDNS.sh && chmod +x /app/updateDNS.sh

# Expose port 80 for HTTP
EXPOSE 80

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD test -f /app/images/0.png || exit 1

# Run supervisor to manage both processes
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
