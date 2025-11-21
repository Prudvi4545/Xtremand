#!/bin/bash

################################################################################
# 🔄 RESTART SERVICES SCRIPT
# Usage: ./restart_services.sh
# Gracefully restarts all services
################################################################################

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}          RESTARTING XTREMAND SERVICES${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "❌ This script must be run as root"
    exit 1
fi

# Stop services
echo -e "${YELLOW}🛑 Stopping services...${NC}"
sudo systemctl stop xtremand-django.service
sudo systemctl stop xtremand-celery.service
sleep 2
echo -e "${GREEN}✅ Services stopped${NC}"
echo ""

# Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
sudo systemctl start xtremand-django.service
sleep 2
sudo systemctl start xtremand-celery.service
sleep 2
echo -e "${GREEN}✅ Services started${NC}"
echo ""

# Verify
echo -e "${YELLOW}📊 Verifying status...${NC}"
echo ""

if sudo systemctl is-active --quiet xtremand-django.service; then
    echo -e "   ${GREEN}✅ Django service is RUNNING${NC}"
else
    echo -e "   ❌ Django service is NOT running"
fi

if sudo systemctl is-active --quiet xtremand-celery.service; then
    echo -e "   ${GREEN}✅ Celery service is RUNNING${NC}"
else
    echo -e "   ❌ Celery service is NOT running"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Services restarted successfully!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}View logs:${NC}"
echo "  Django:  sudo journalctl -u xtremand-django.service -f"
echo "  Celery:  sudo journalctl -u xtremand-celery.service -f"
echo ""
