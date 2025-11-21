# 📋 Pre-Deployment Checklist

## ✅ Code Changes Completed

- [x] Fixed webhook CSRF exemption
- [x] Standardized MongoDB model fields
- [x] Added MongoDB connection to settings.py
- [x] Environment-based configuration (no hardcoding)

## ✅ Files to Push to GitHub

### Core Project Files
- [ ] `manage.py`
- [ ] `requirements.txt`
- [ ] `web_project/` directory (all files)
- [ ] `xtr/` directory (all files)

### Documentation & Scripts
- [ ] `DEPLOYMENT_GUIDE.md` (Complete deployment guide)
- [ ] `QUICK_START.md` (Quick reference)
- [ ] `scripts/deploy.sh` (Automated deployment)
- [ ] `scripts/start_services.sh` (Start services)
- [ ] `scripts/stop_services.sh` (Stop services)
- [ ] `scripts/restart_services.sh` (Restart services)
- [ ] `scripts/check_status.sh` (Status check)
- [ ] `README.md` (Project overview)

## ✅ Files to EXCLUDE from GitHub

```
# .gitignore - Make sure these are excluded:
.env                          # Don't push environment variables!
*.pyc                         # Python cache
__pycache__/                  # Python cache directories
.DS_Store                     # Mac files
*.log                         # Log files
venv/                         # Virtual environment
.venv/
env/
db.sqlite3                    # SQLite database (if used)
/staticfiles/                 # Static files
/media/                       # Media files
*.pot                         # Translation files
.idea/                        # IDE files
.vscode/
*.swp
*.swo
*~
```

Verify .gitignore:
```bash
git status
# Should NOT show .env, venv/, etc.
```

## 🔄 Git Workflow

### Step 1: Create/Update .gitignore
```bash
cd /path/to/Xtremand

# Make sure .gitignore exists and has the exclusions above
cat .gitignore
```

### Step 2: Check Git Status
```bash
git status
# Should NOT include: .env, venv/, __pycache__, *.pyc
```

### Step 3: Add Changes
```bash
git add -A
# OR selectively:
git add DEPLOYMENT_GUIDE.md QUICK_START.md scripts/ xtr/ web_project/ requirements.txt
```

### Step 4: Commit Changes
```bash
git commit -m "Add deployment automation scripts and documentation

- Add comprehensive DEPLOYMENT_GUIDE.md
- Add QUICK_START.md for quick reference
- Add automated deploy.sh script
- Add service management scripts (start, stop, restart, check_status)
- Fix webhook CSRF protection
- Standardize MongoDB model datetime fields
- Add MongoDB connection to settings.py
- Update requirements.txt with all dependencies"
```

### Step 5: Push to GitHub
```bash
git push origin main
```

## 📝 What to Tell Users After Deployment

Create a file called `SERVER_SETUP.md`:

```markdown
# 🚀 Server Setup Instructions

## Quick Start (5 minutes)

```bash
# 1. SSH to your server
ssh root@your-server-ip

# 2. Clone repository
git clone https://github.com/Prudvi4545/Xtremand.git
cd Xtremand

# 3. Run deployment
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# 4. Edit configuration
nano .env

# 5. Restart services
./scripts/restart_services.sh
```

## That's it! Services run 24/7 automatically.

For more details, see:
- DEPLOYMENT_GUIDE.md (Complete guide)
- QUICK_START.md (Quick reference)

## Service Management

```bash
# Check status
./scripts/check_status.sh

# View logs
journalctl -u xtremand-django.service -f
journalctl -u xtremand-celery.service -f

# Restart services
./scripts/restart_services.sh
```

## Environment Configuration

The only file you need to edit is `.env`:
- DJANGO_DB_ENV=server (for server) or local (for local)
- DJANGO_SECRET_KEY (change this!)
- DJANGO_ALLOWED_HOSTS (your server IP/domain)
- MONGODB_URI (if different)
- CELERY_BROKER_URL (if Redis is different)

NO CODE CHANGES NEEDED! Just set environment variables.
```

## ✅ Final Pre-Push Checklist

```bash
# 1. Remove sensitive files from git history (if accidentally committed)
git filter-branch --tree-filter 'rm -f .env' HEAD
# OR just add to .gitignore and future commits

# 2. Verify .gitignore is correct
git check-ignore -v .env venv/ __pycache__/

# 3. Test that deployment still works locally
python manage.py runserver

# 4. Verify requirements.txt has all packages
pip freeze > requirements.txt

# 5. Final status check
git status
# Should show only the files you want to push

# 6. Push to GitHub
git push origin main
```

## 🎯 What Your Users Will See

After running `./scripts/deploy.sh`, they will have:

✅ Django running on port 8000
✅ Celery worker processing files
✅ MongoDB storing data
✅ Redis managing tasks
✅ All services auto-starting on reboot
✅ All services auto-restarting if they crash

They ONLY need to:
1. Edit `.env` file
2. Configure MinIO webhook
3. That's it!

## 📊 Summary

**Before pushing to GitHub:**
- [ ] All deployment scripts are in `scripts/` directory
- [ ] All documentation files are in root directory
- [ ] `.env` file is NOT committed
- [ ] `venv/` directory is NOT committed
- [ ] `__pycache__/` directories are NOT committed
- [ ] All code fixes are applied and tested
- [ ] `requirements.txt` is updated with all packages
- [ ] Git history is clean (no sensitive data)

**After pushing to GitHub:**
- Users can clone
- Users can run `./scripts/deploy.sh`
- Services run 24/7 automatically
- No manual intervention needed!

✨ You're ready to deploy!
