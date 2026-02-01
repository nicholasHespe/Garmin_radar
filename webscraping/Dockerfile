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

# Create images directory
RUN mkdir -p images

# Create nginx configuration
RUN echo 'server {\n\
    listen 80;\n\
    server_name _;\n\
    root /app;\n\
    location /images/ {\n\
        alias /app/images/;\n\
        autoindex off;\n\
        add_header Cache-Control "no-cache, must-revalidate";\n\
    }\n\
}' > /etc/nginx/sites-available/default

# Create supervisor configuration
RUN echo '[supervisord]\n\
nodaemon=true\n\
user=root\n\
\n\
[program:ftpscraper]\n\
command=python /app/ftpscraper.py\n\
autostart=true\n\
autorestart=true\n\
stdout_logfile=/dev/stdout\n\
stdout_logfile_maxbytes=0\n\
stderr_logfile=/dev/stderr\n\
stderr_logfile_maxbytes=0\n\
\n\
[program:nginx]\n\
command=nginx -g "daemon off;"\n\
autostart=true\n\
autorestart=true\n\
stdout_logfile=/dev/stdout\n\
stdout_logfile_maxbytes=0\n\
stderr_logfile=/dev/stderr\n\
stderr_logfile_maxbytes=0\n\
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
