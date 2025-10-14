#!/bin/bash
# Deploy updated Nest refresh token to Raspberry Pi
# Usage: ./scripts/deploy_nest_token.sh [pi_host]

set -e

PI_HOST="${1:-192.168.50.189}"
PI_USER="pi"
PI_PATH="/home/pi/py_home"

echo "=== Deploying Nest Refresh Token ==="
echo "Target: ${PI_USER}@${PI_HOST}:${PI_PATH}"
echo

# Check if .env exists locally
if [ ! -f "config/.env" ]; then
    echo "❌ Error: config/.env not found"
    exit 1
fi

# Extract new token from local .env
NEW_TOKEN=$(grep NEST_REFRESH_TOKEN config/.env | cut -d'=' -f2)

if [ -z "$NEW_TOKEN" ]; then
    echo "❌ Error: NEST_REFRESH_TOKEN not found in config/.env"
    exit 1
fi

echo "✓ Found new refresh token: ${NEW_TOKEN:0:20}..."
echo

# SSH to Pi and update token in place
echo "Updating token on Pi..."
ssh ${PI_USER}@${PI_HOST} "sed -i 's/^NEST_REFRESH_TOKEN=.*/NEST_REFRESH_TOKEN=${NEW_TOKEN}/' ${PI_PATH}/config/.env"

if [ $? -eq 0 ]; then
    echo "✓ Token updated successfully"
    echo

    # Restart Flask service
    echo "Restarting py_home service..."
    ssh ${PI_USER}@${PI_HOST} "sudo systemctl restart py_home"

    if [ $? -eq 0 ]; then
        echo "✓ Service restarted"
        echo
        echo "✅ Deployment complete!"
        echo
        echo "Test with:"
        echo "  curl -X POST http://${PI_HOST}:5000/api/good-morning"
    else
        echo "❌ Failed to restart service"
        exit 1
    fi
else
    echo "❌ Failed to update token"
    exit 1
fi
