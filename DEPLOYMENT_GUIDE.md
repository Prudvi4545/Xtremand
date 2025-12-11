# 🚀 Complete Server Deployment Guide

## Table of Contents
1. [Git Clone & Setup](#git-clone--setup)
2. [Server Configuration](#server-configuration)
3. [Environment Variables](#environment-variables)
4. [Installation & Dependencies](#installation--dependencies)
5. [Database Setup](#database-setup)
6. [MinIO Setup](#minio-setup)
7. [Service Automation (Systemd/Supervisor)](#service-automation)
8. [Running 24/7](#running-247)

---

## 🔧 Git Clone & Setup

### Step 1: Clone Repository on Server

```bash
# SSH into your server
ssh user@154.210.235.101

# Navigate to home or desired directory
cd /home/xtremand  # or /opt/xtremand

# Clone the repository
git clone https://github.com/Prudvi4545/Xtremand.git
cd Xtremand

# Verify you're on main branch
git branch
git status
```

### Step 2: Create Virtual Environment

```bash
# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\Activate.ps1  # Windows PowerShell

# Upgrade pip
pip install --upgrade pip
```

### Step 3: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list
```

---

## 📋 Server Configuration

### Where to Change Code from LOCAL to SERVER

**File 1:** `xtr/minio_client.py` (Line 23)
```python
# Current (Local):
DB_ENV = os.getenv("DJANGO_DB_ENV", "local")

# For Server, set environment variable instead of changing code
# The code stays the same - configuration happens via ENV VAR
```

**File 2:** `web_project/settings.py` (Line 19)
```python
# No changes needed in code
# Environment variables control everything
DB_ENV = os.environ.get("DJANGO_DB_ENV", "local")
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"
```

**IMPORTANT: DO NOT CHANGE CODE! Use environment variables instead.**

---

## 🌍 Environment Variables

### Create `.env` file on Server

```bash
# Create .env file in project root
sudo nano /home/xtremand/Xtremand/.env
```

**Add these environment variables:**

```env
# Django Configuration
DJANGO_DB_ENV=server
DJANGO_SECRET_KEY=your-super-secret-key-change-this-in-production
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=154.210.235.101,your-domain.com

# MinIO Configuration (Already configured in code for server)
MINIO_HOST=154.210.235.101:9000
MINIO_ACCESS_KEY=Xtremand
MINIO_SECRET_KEY=Xtremand@321

# Redis/Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/xtremand_db

# Whisper Model (for audio/video transcription)
WHISPER_MODEL=tiny
FFMPEG_PATH=/usr/bin/ffmpeg
FFPROBE_PATH=/usr/bin/ffprobe
```

### Load `.env` file

Option 1: Using `python-dotenv`
```bash
pip install python-dotenv
```

Add to `web_project/settings.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

Option 2: Load manually before running
```bash
export $(cat .env | xargs)
python manage.py runserver
```

---

## 📦 Installation & Dependencies

### Install System Dependencies (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    redis-server \
    mongodb \
    ffmpeg \
    libmagic1 \
    libreoffice
```

### Install Python Dependencies

```bash
cd /home/xtremand/Xtremand
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Verify critical packages
pip show django celery mongoengine redis pymongo
```

---

## 🗄️ Database Setup

### 1. MongoDB

```bash
# Start MongoDB
sudo systemctl start mongodb
sudo systemctl enable mongodb  # Auto-start on reboot

# Verify MongoDB is running
mongo --version
mongo  # Enter MongoDB shell
```

In MongoDB shell:
```javascript
// Create database
use xtremand_db

// Create collections (optional - created automatically)
db.createCollection("audio_file")
db.createCollection("video_file")
db.createCollection("image_file")

// Exit
exit
```

### 2. Redis

```bash
# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify Redis is running
redis-cli ping  # Should return "PONG"
```

---

## 🪣 MinIO Setup

### Step 1: Create Buckets

```bash
# SSH to MinIO server (if different machine)
ssh user@154.210.235.101

# Or use MinIO Client from your machine
# Download MinIO client: https://min.io/docs/minio/linux/reference/minio-mc.html

# Set up alias
mc alias set minio http://154.210.235.101:9000 Xtremand Xtremand@321

# Create buckets
mc mb minio/processing
mc mb minio/archive

# Verify
mc ls minio
```

### Step 2: Configure Webhook Event Notification

**Option A: Using MinIO Client (mc)**

```bash
# Add HTTP notification target
mc admin config set minio notify_http \
  enable=on \
  queue_limit=0 \
  url=http://YOUR_SERVER_IP:8000/minio_event_webhook/ \
  auth_token=""

# Restart MinIO
mc admin service restart minio
```

**Option B: Using MinIO Web UI**

1. Go to `http://154.210.235.101:9000`
2. Login with: `Xtremand` / `Xtremand@321`
3. Navigate to **Buckets** → **processing**
4. Click **Events** → **Add Event**
5. Configure:
   - Event type: `s3:ObjectCreated:*`
   - Endpoint: `http://YOUR_SERVER_IP:8000/minio_event_webhook/`
   - Auth: None

---

## 🔄 Service Automation (Running 24/7)

### Option 1: Systemd Services (Recommended for Linux)

#### Create Django Service

```bash
sudo nano /etc/systemd/system/xtremand-django.service
```

Add:
```ini
[Unit]
Description=Xtremand Django Application
After=network.target mongodb.service redis-server.service

[Service]
Type=notify
User=xtremand
WorkingDirectory=/home/xtremand/Xtremand
Environment="PATH=/home/xtremand/Xtremand/venv/bin"
EnvironmentFile=/home/xtremand/Xtremand/.env
ExecStart=/home/xtremand/Xtremand/venv/bin/python manage.py runserver 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Create Celery Worker Service

```bash
sudo nano /etc/systemd/system/xtremand-celery.service
```

Add:
```ini
[Unit]
Description=Xtremand Celery Worker
After=network.target redis-server.service

[Service]
Type=forking
User=xtremand
WorkingDirectory=/home/xtremand/Xtremand
Environment="PATH=/home/xtremand/Xtremand/venv/bin"
EnvironmentFile=/home/xtremand/Xtremand/.env
ExecStart=/home/xtremand/Xtremand/venv/bin/celery -A web_project worker \
    --loglevel=info \
    --concurrency=4 \
    --logfile=/var/log/xtremand/celery.log \
    --pidfile=/var/run/xtremand/celery.pid
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Enable and Start Services

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable services to auto-start
sudo systemctl enable xtremand-django.service
sudo systemctl enable xtremand-celery.service

# Start services
sudo systemctl start xtremand-django.service
sudo systemctl start xtremand-celery.service

# Check status
sudo systemctl status xtremand-django.service
sudo systemctl status xtremand-celery.service

# View logs
sudo journalctl -u xtremand-django.service -f
sudo journalctl -u xtremand-celery.service -f

# Stop services
sudo systemctl stop xtremand-django.service
sudo systemctl stop xtremand-celery.service
```

---

### Option 2: Supervisor (Alternative)

#### Install Supervisor

```bash
sudo apt-get install -y supervisor
```

#### Create Django Program Configuration

```bash
sudo nano /etc/supervisor/conf.d/xtremand-django.conf
```

Add:
```ini
[program:xtremand-django]
directory=/home/xtremand/Xtremand
command=/home/xtremand/Xtremand/venv/bin/python manage.py runserver 0.0.0.0:8000
user=xtremand
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/xtremand/django.log
environment=DJANGO_DB_ENV=server,DJANGO_SETTINGS_MODULE=web_project.settings
```

#### Create Celery Program Configuration

```bash
sudo nano /etc/supervisor/conf.d/xtremand-celery.conf
```

Add:
```ini
[program:xtremand-celery]
directory=/home/xtremand/Xtremand
command=/home/xtremand/Xtremand/venv/bin/celery -A web_project worker --loglevel=info
user=xtremand
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/xtremand/celery.log
environment=DJANGO_DB_ENV=server,DJANGO_SETTINGS_MODULE=web_project.settings
```

#### Enable and Start

```bash
# Reload supervisor configuration
sudo supervisorctl reread
sudo supervisorctl update

# Start services
sudo supervisorctl start xtremand-django
sudo supervisorctl start xtremand-celery

# Check status
sudo supervisorctl status

# View logs
tail -f /var/log/xtremand/django.log
tail -f /var/log/xtremand/celery.log
```

---

### Option 3: Screen/Tmux (For Testing/Development)

#### Using Screen

```bash
# Terminal 1 - Django
screen -S django
cd /home/xtremand/Xtremand
source venv/bin/activate
export DJANGO_DB_ENV=server
python manage.py runserver 0.0.0.0:8000
# Press Ctrl+A then D to detach

# Terminal 2 - Celery
screen -S celery
cd /home/xtremand/Xtremand
source venv/bin/activate
export DJANGO_DB_ENV=server
celery -A web_project worker -l info
# Press Ctrl+A then D to detach

# Reattach to screen
screen -r django
screen -r celery

# Kill screen session
screen -X -S django quit
screen -X -S celery quit
```

#### Using Tmux

```bash
# Terminal 1 - Django
tmux new-session -d -s django -c /home/xtremand/Xtremand
tmux send-keys -t django "source venv/bin/activate && export DJANGO_DB_ENV=server && python manage.py runserver 0.0.0.0:8000" Enter

# Terminal 2 - Celery
tmux new-session -d -s celery -c /home/xtremand/Xtremand
tmux send-keys -t celery "source venv/bin/activate && export DJANGO_DB_ENV=server && celery -A web_project worker -l info" Enter

# Check sessions
tmux list-sessions

# Attach to session
tmux attach-session -t django
tmux attach-session -t celery

# Kill sessions
tmux kill-session -t django
tmux kill-session -t celery
```

---

## 📋 Running 24/7 - Complete Checklist

### Automated Startup Script

Create `/home/xtremand/Xtremand/start_services.sh`:

```bash
#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="/home/xtremand/Xtremand"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="/var/log/xtremand"

echo -e "${YELLOW}🚀 Starting Xtremand Services...${NC}"

# Create log directory
mkdir -p $LOG_DIR
chmod 755 $LOG_DIR

# Activate virtual environment
source $VENV_DIR/bin/activate

# Load environment variables
export $(cat $PROJECT_DIR/.env | xargs)
export DJANGO_DB_ENV=server

# Check dependencies
echo -e "${YELLOW}📋 Checking dependencies...${NC}"

# Check MongoDB
if ! command -v mongod &> /dev/null; then
    echo -e "${RED}❌ MongoDB not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ MongoDB found${NC}"

# Check Redis
if ! command -v redis-server &> /dev/null; then
    echo -e "${RED}❌ Redis not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Redis found${NC}"

# Start MongoDB if not running
if ! pgrep -x "mongod" > /dev/null; then
    echo -e "${YELLOW}Starting MongoDB...${NC}"
    sudo systemctl start mongodb
    sleep 2
    echo -e "${GREEN}✅ MongoDB started${NC}"
else
    echo -e "${GREEN}✅ MongoDB already running${NC}"
fi

# Start Redis if not running
if ! pgrep -x "redis-server" > /dev/null; then
    echo -e "${YELLOW}Starting Redis...${NC}"
    sudo systemctl start redis-server
    sleep 2
    echo -e "${GREEN}✅ Redis started${NC}"
else
    echo -e "${GREEN}✅ Redis already running${NC}"
fi

# Run migrations
echo -e "${YELLOW}Running migrations...${NC}"
python $PROJECT_DIR/manage.py migrate

# Collect static files
echo -e "${YELLOW}Collecting static files...${NC}"
python $PROJECT_DIR/manage.py collectstatic --noinput

# Start services using systemctl
echo -e "${YELLOW}Starting Django and Celery services...${NC}"
sudo systemctl start xtremand-django.service
sudo systemctl start xtremand-celery.service

# Verify services
sleep 3
if sudo systemctl is-active --quiet xtremand-django.service; then
    echo -e "${GREEN}✅ Django service started${NC}"
else
    echo -e "${RED}❌ Django service failed to start${NC}"
    sudo systemctl status xtremand-django.service
    exit 1
fi

if sudo systemctl is-active --quiet xtremand-celery.service; then
    echo -e "${GREEN}✅ Celery service started${NC}"
else
    echo -e "${RED}❌ Celery service failed to start${NC}"
    sudo systemctl status xtremand-celery.service
    exit 1
fi

echo -e "${GREEN}🎉 All services started successfully!${NC}"
echo -e "${YELLOW}Django running at: http://localhost:8000${NC}"
echo -e "${YELLOW}View logs:${NC}"
echo -e "  sudo journalctl -u xtremand-django.service -f"
echo -e "  sudo journalctl -u xtremand-celery.service -f"
```

Make it executable:
```bash
chmod +x /home/xtremand/Xtremand/start_services.sh
```

### Stop Script

Create `/home/xtremand/Xtremand/stop_services.sh`:

```bash
#!/bin/bash

echo "🛑 Stopping Xtremand Services..."

sudo systemctl stop xtremand-django.service
sudo systemctl stop xtremand-celery.service

echo "✅ Services stopped"
```

Make it executable:
```bash
chmod +x /home/xtremand/Xtremand/stop_services.sh
```

---

## 📊 Complete Server Setup Commands (One-by-One)

```bash
# 1. SSH to server
ssh user@154.210.235.101

# 2. Update system
sudo apt-get update && sudo apt-get upgrade -y

# 3. Install dependencies
sudo apt-get install -y python3-pip python3-venv redis-server mongodb ffmpeg

# 4. Create project directory
mkdir -p /home/xtremand
cd /home/xtremand

# 5. Clone repository
git clone https://github.com/Prudvi4545/Xtremand.git
cd Xtremand

# 6. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 7. Install Python packages
pip install --upgrade pip
pip install -r requirements.txt

# 8. Create .env file
nano .env
# Add contents from Environment Variables section above

# 9. Create log directory
mkdir -p /var/log/xtremand
sudo chown xtremand:xtremand /var/log/xtremand

# 10. Create systemd services (see above)
sudo nano /etc/systemd/system/xtremand-django.service
sudo nano /etc/systemd/system/xtremand-celery.service

# 11. Reload and enable services
sudo systemctl daemon-reload
sudo systemctl enable xtremand-django.service
sudo systemctl enable xtremand-celery.service

# 12. Start services
sudo systemctl start xtremand-django.service
sudo systemctl start xtremand-celery.service

# 13. Verify services
sudo systemctl status xtremand-django.service
sudo systemctl status xtremand-celery.service

# 14. View logs
sudo journalctl -u xtremand-django.service -f
sudo journalctl -u xtremand-celery.service -f
```

---

## ✅ Verification Checklist

```bash
# Check MongoDB
mongo --eval "db.adminCommand('ping')"

# Check Redis
redis-cli ping  # Should return PONG

# Check Django
curl http://localhost:8000

# Check Celery (should show active workers)
celery -A web_project inspect active

# Check MinIO buckets
mc ls minio
```

---

## 🎯 Summary

| Component | Command | Auto-Start | Logs |
|-----------|---------|-----------|------|
| Django | `sudo systemctl start xtremand-django.service` | ✅ Yes | `sudo journalctl -u xtremand-django.service -f` |
| Celery | `sudo systemctl start xtremand-celery.service` | ✅ Yes | `sudo journalctl -u xtremand-celery.service -f` |
| MongoDB | `sudo systemctl start mongodb` | ✅ Yes | `tail -f /var/log/mongodb/mongod.log` |
| Redis | `sudo systemctl start redis-server` | ✅ Yes | Check status: `redis-cli ping` |
| MinIO | Already running on 154.210.235.101:9000 | ✅ Yes | MinIO web UI |

**All services run 24/7 and auto-restart on failure!**
