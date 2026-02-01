#!/bin/bash
# DNS update script for BetterWeather
# Called after each successful radar image update

LOG_FILE="/app/dns_update.log"

# Log the update
echo "DNS update called at $(date)" >> "$LOG_FILE"

# Since you're using Cloudflare with proxy enabled, no dynamic DNS update is needed
# Cloudflare handles the routing from domain to your IP

# Optional: Uncomment below if you need to update Cloudflare DNS record dynamically
# This is useful if your home IP address changes frequently

# CLOUDFLARE_ZONE_ID="your_zone_id_here"
# CLOUDFLARE_RECORD_ID="your_record_id_here"
# CLOUDFLARE_API_TOKEN="your_api_token_here"
# DOMAIN="betterweather.nickhespe.com"
#
# # Get current public IP
# PUBLIC_IP=$(curl -s https://api.ipify.org)
#
# # Update Cloudflare DNS record
# RESPONSE=$(curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/dns_records/$CLOUDFLARE_RECORD_ID" \
#      -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
#      -H "Content-Type: application/json" \
#      --data "{\"type\":\"A\",\"name\":\"$DOMAIN\",\"content\":\"$PUBLIC_IP\",\"ttl\":120,\"proxied\":true}")
#
# # Log the response
# echo "Cloudflare update response: $RESPONSE" >> "$LOG_FILE"

exit 0
