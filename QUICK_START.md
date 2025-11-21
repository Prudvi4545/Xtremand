# 🚀 QUICK START GUIDE - Server Deployment

## 📋 TL;DR - Three Simple Steps

### Step 1: Run Deployment Script (5-10 minutes)
```bash
# SSH to your server
ssh root@your-server-ip

# Download and run deployment script
wget https://raw.githubusercontent.com/Prudvi4545/Xtremand/main/scripts/deploy.sh
chmod +x deploy.sh
./deploy.sh
```

### Step 2: Edit .env Configuration (2 minutes)
```bash
nano /opt/xtremand/Xtremand/.env
```

**Key things to change:**
- `DJANGO_SECRET_KEY` → Set to a long random string
- `DJANGO_ALLOWED_HOSTS` → Add your server IP/domain
- `MONGODB_URI` → If MongoDB is on different server
- `CELERY_BROKER_URL` → If Redis is on different server

### Step 3: Services Auto-Run 24/7 ✅
```bash
# Restart to apply .env changes
./scripts/restart_services.sh

# Done! Services run automatically now
```

---

## 🎯 Where to Change Code: LOCAL vs SERVER

### ✅ DO NOT CHANGE CODE FILES!

All configuration is done through **environment variables**, NOT code changes.

**Here's how it works:**

```
minio_client.py (Line 23):
    DB_ENV = os.getenv("DJANGO_DB_ENV", "local")
           ↓
    If environment variable "DJANGO_DB_ENV" = "server"
           ↓
    Uses server MinIO credentials automatically
           ↓
    If environment variable "DJANGO_DB_ENV" = "local"
           ↓
    Uses local MinIO credentials automatically
```

### Environment Variable Controls Everything

| Setting | Environment Variable | Local Value | Server Value |
|---------|----------------------|-------------|--------------|
| Environment | `DJANGO_DB_ENV` | `local` | `server` |
| MinIO Host | `MINIO_HOST` | `localhost:9000` | `154.210.235.101:9000` |
| MinIO User | `MINIO_ACCESS_KEY` | `minioadmin` | `Xtremand` |
| Debug Mode | `DJANGO_DEBUG` | `True` | `False` |
| MongoDB | `MONGODB_URI` | `mongodb://localhost:27017/xtremand_db` | Same or different |
| Redis | `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Same or different |

**How to set for SERVER (in .env file):**
```env
DJANGO_DB_ENV=server
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=154.210.235.101,your-domain.com
```

**How to set for LOCAL (Windows/Mac):**
```powershell
$env:DJANGO_DB_ENV = "local"
python manage.py runserver
```

---

## 📖 Understanding Auto-Run (Systemd Services)

### How It Works

1. **Service Definition:** `/etc/systemd/system/xtremand-django.service`
2. **Runs on Boot:** Automatically starts when server boots
3. **Auto-Restart:** If service crashes, it restarts automatically
4. **No User Login Required:** Runs in background 24/7

### Service Management Commands

```bash
# View current status
systemctl status xtremand-django.service
systemctl status xtremand-celery.service

# Start services
systemctl start xtremand-django.service
systemctl start xtremand-celery.service

# Stop services
systemctl stop xtremand-django.service
systemctl stop xtremand-celery.service

# Restart services
systemctl restart xtremand-django.service
systemctl restart xtremand-celery.service

# View logs (real-time)
journalctl -u xtremand-django.service -f
journalctl -u xtremand-celery.service -f

# View last 50 lines of logs
journalctl -u xtremand-django.service -n 50

# Enable/Disable auto-start on boot
systemctl enable xtremand-django.service
systemctl disable xtremand-django.service
```

### Automation Scripts (Helper Scripts)

Located in `/opt/xtremand/Xtremand/scripts/`:

```bash
# View status of all services
./check_status.sh

# Start all services
./start_services.sh

# Stop all services
./stop_services.sh

# Restart all services
./restart_services.sh
```

---

## 🔍 Git Workflow on Server

### Initial Clone (First Time)
```bash
cd /opt/xtremand
git clone https://github.com/Prudvi4545/Xtremand.git
cd Xtremand
```

### Update Code (Pull Latest Changes)
```bash
cd /opt/xtremand/Xtremand
git pull origin main

# If you made local .env changes, tell git to ignore it
git update-index --skip-worktree .env
```

### Push Local Changes to GitHub
```bash
git status
git add <files>
git commit -m "Description of changes"
git push origin main
```

### Troubleshooting Git Issues
```bash
# If .env file keeps being tracked
git rm --cached .env
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Stop tracking .env"
git push

# If you want to reset to remote version
git fetch origin
git reset --hard origin/main
```

---

## 🛠️ Troubleshooting

### Service Won't Start
```bash
# Check status
systemctl status xtremand-django.service

# View recent logs
journalctl -u xtremand-django.service -n 30

# Check if port 8000 is already in use
netstat -tulpn | grep 8000

# Kill process on port 8000
fuser -k 8000/tcp
```

### MongoDB Connection Error
```bash
# Check if MongoDB is running
systemctl status mongodb

# Start MongoDB
systemctl start mongodb

# Check MongoDB version
mongod --version

# Test connection
mongo --eval "db.adminCommand('ping')"
```

### Redis Connection Error
```bash
# Check if Redis is running
systemctl status redis-server

# Start Redis
systemctl start redis-server

# Test connection
redis-cli ping
```

### Celery Not Processing Tasks
```bash
# Check active workers
celery -A web_project inspect active

# View Celery logs
journalctl -u xtremand-celery.service -f

# Restart Celery worker
systemctl restart xtremand-celery.service
```

### MinIO Webhook Not Triggering
```bash
# Check if webhook endpoint is accessible
curl http://your-server-ip:8000/minio_event_webhook/

# Check Django logs for webhook events
journalctl -u xtremand-django.service -f

# Reconfigure MinIO webhook (see DEPLOYMENT_GUIDE.md)
```

---

## 📊 Complete Command Reference

| Task | Command |
|------|---------|
| **Installation** | `./scripts/deploy.sh` |
| **Check Status** | `./scripts/check_status.sh` |
| **Start Services** | `./scripts/start_services.sh` |
| **Stop Services** | `./scripts/stop_services.sh` |
| **Restart Services** | `./scripts/restart_services.sh` |
| **View Django Logs** | `journalctl -u xtremand-django.service -f` |
| **View Celery Logs** | `journalctl -u xtremand-celery.service -f` |
| **Edit .env** | `nano /opt/xtremand/Xtremand/.env` |
| **Update Code** | `cd /opt/xtremand/Xtremand && git pull origin main` |
| **Check Web Access** | `curl http://localhost:8000` |
| **Check Redis** | `redis-cli ping` |
| **Check MongoDB** | `mongo --eval "db.adminCommand('ping')"` |
| **Kill Django** | `fuser -k 8000/tcp` |
| **List Running Services** | `systemctl list-units --type=service --all` |

---

## ✅ Verification Checklist After Deployment

- [ ] Django service is running: `systemctl status xtremand-django.service`
- [ ] Celery service is running: `systemctl status xtremand-celery.service`
- [ ] MongoDB is running: `mongo --eval "db.adminCommand('ping')"`
- [ ] Redis is running: `redis-cli ping` (returns PONG)
- [ ] Web access works: `curl http://localhost:8000`
- [ ] .env file is configured: `nano /opt/xtremand/Xtremand/.env`
- [ ] MinIO webhook is configured (in MinIO web UI)
- [ ] Processing bucket exists: `mc ls minio/processing`
- [ ] Archive bucket exists: `mc ls minio/archive`
- [ ] Services auto-restart enabled: `systemctl is-enabled xtremand-django.service`

---

## 🎉 You're Done!

Your application is now:
- ✅ Running on your server
- ✅ Accessible at `http://your-server-ip:8000`
- ✅ Processing files automatically via MinIO webhook
- ✅ Saving data to MongoDB
- ✅ Auto-restarting if services crash
- ✅ Auto-starting on server reboot
- ✅ Running 24/7

**No more manual intervention needed!** 🚀

---

## 📞 Need Help?

Check logs for detailed error messages:
```bash
journalctl -u xtremand-django.service -n 100
journalctl -u xtremand-celery.service -n 100
```

---

## 🔐 Security Reminder

Before going to production:
1. [ ] Change `DJANGO_SECRET_KEY` in `.env`
2. [ ] Set `DJANGO_DEBUG=False` in `.env`
3. [ ] Use HTTPS for Django (use Nginx/Apache proxy)
4. [ ] Set up firewall rules
5. [ ] Enable SSL for MinIO
6. [ ] Backup MongoDB regularly
7. [ ] Monitor disk space
8. [ ] Set up log rotation
