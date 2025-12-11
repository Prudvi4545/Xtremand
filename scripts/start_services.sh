#!/bin/bash

################################################################################
# 🚀 START SERVICES SCRIPT
# Usage: ./start_services.sh
################################################################################

echo "🚀 Starting Xtremand Services..."
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "❌ This script must be run as root"
    exit 1
fi

PROJECT_DIR="/opt/xtremand/Xtremand"

# Start services
echo "Starting Django service..."
sudo systemctl start xtremand-django.service
sleep 2

echo "Starting Celery service..."
sudo systemctl start xtremand-celery.service
sleep 2

# Verify
echo ""
echo "✅ Checking service status..."
sudo systemctl status xtremand-django.service --no-pager
echo ""
sudo systemctl status xtremand-celery.service --no-pager

echo ""
echo "✅ All services started successfully!"
echo ""
echo "📊 View logs:"
echo "  Django:  sudo journalctl -u xtremand-django.service -f"
echo "  Celery:  sudo journalctl -u xtremand-celery.service -f"
