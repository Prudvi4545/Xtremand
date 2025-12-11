#!/bin/bash

################################################################################
# 📊 CHECK STATUS SCRIPT
# Usage: ./check_status.sh
# Shows current status of all services
################################################################################

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

clear

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}          XTREMAND SERVICES STATUS CHECK${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Check Django
echo -e "${YELLOW}📱 Django Service:${NC}"
if sudo systemctl is-active --quiet xtremand-django.service; then
    echo -e "   ${GREEN}✅ RUNNING${NC}"
else
    echo -e "   ${RED}❌ NOT RUNNING${NC}"
fi
echo ""

# Check Celery
echo -e "${YELLOW}⚙️  Celery Service:${NC}"
if sudo systemctl is-active --quiet xtremand-celery.service; then
    echo -e "   ${GREEN}✅ RUNNING${NC}"
else
    echo -e "   ${RED}❌ NOT RUNNING${NC}"
fi
echo ""

# Check MongoDB
echo -e "${YELLOW}🗄️  MongoDB:${NC}"
if sudo systemctl is-active --quiet mongodb; then
    echo -e "   ${GREEN}✅ RUNNING${NC}"
else
    echo -e "   ${RED}❌ NOT RUNNING${NC}"
fi
echo ""

# Check Redis
echo -e "${YELLOW}⚡ Redis:${NC}"
if sudo systemctl is-active --quiet redis-server; then
    echo -e "   ${GREEN}✅ RUNNING${NC}"
    if redis-cli ping &> /dev/null; then
        echo -e "   ${GREEN}   └─ Responding to ping${NC}"
    else
        echo -e "   ${RED}   └─ NOT responding to ping${NC}"
    fi
else
    echo -e "   ${RED}❌ NOT RUNNING${NC}"
fi
echo ""

# Check Web Access
echo -e "${YELLOW}🌐 Web Access:${NC}"
if curl -s http://localhost:8000 > /dev/null; then
    echo -e "   ${GREEN}✅ Responding on :8000${NC}"
else
    echo -e "   ${RED}❌ Not responding on :8000${NC}"
fi
echo ""

# Celery Active Workers
echo -e "${YELLOW}👷 Celery Active Workers:${NC}"
WORKERS=$(cd /opt/xtremand/Xtremand && source venv/bin/activate && \
    python -c "from celery import Celery; app = Celery('web_project'); app.config_from_object('django.conf:settings', namespace='CELERY'); print('Checking workers...')" 2>/dev/null || echo "0")
echo -e "   Type: ${BLUE}celery -A web_project inspect active${NC}"
echo ""

# Disk Space
echo -e "${YELLOW}💾 Disk Space:${NC}"
df -h /opt/xtremand | tail -1 | awk '{printf "   Usage: %s (%s used)\n", $6, $5}'
echo ""

# Memory Usage
echo -e "${YELLOW}🧠 Memory Usage:${NC}"
free -h | grep Mem | awk '{printf "   Total: %s | Used: %s | Available: %s\n", $2, $3, $7}'
echo ""

# Recent Logs
echo -e "${YELLOW}📝 Recent Django Logs (last 5 lines):${NC}"
sudo journalctl -u xtremand-django.service -n 5 --no-pager | sed 's/^/   /'
echo ""

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Timestamp: $(date)${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}💡 Useful Commands:${NC}"
echo "   View Django logs:    sudo journalctl -u xtremand-django.service -f"
echo "   View Celery logs:    sudo journalctl -u xtremand-celery.service -f"
echo "   Restart services:    sudo systemctl restart xtremand-django.service"
echo "   Stop services:       ./stop_services.sh"
echo "   Start services:      ./start_services.sh"
echo ""
