#!/bin/bash

################################################################################
# 🛑 STOP SERVICES SCRIPT
# Usage: ./stop_services.sh
################################################################################

echo "🛑 Stopping Xtremand Services..."
echo ""

# Stop Django
echo "Stopping Django service..."
sudo systemctl stop xtremand-django.service
sleep 1

# Stop Celery
echo "Stopping Celery service..."
sudo systemctl stop xtremand-celery.service
sleep 1

# Verify
echo ""
echo "✅ Checking service status..."
sudo systemctl status xtremand-django.service --no-pager
sudo systemctl status xtremand-celery.service --no-pager

echo ""
echo "✅ All services stopped successfully!"
