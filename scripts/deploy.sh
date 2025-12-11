#!/bin/bash

################################################################################
# 🚀 XTREMAND AUTOMATED DEPLOYMENT SCRIPT
# Usage: ./deploy.sh
# This script handles complete setup from clone to running services 24/7
################################################################################

set -e

# ============================================================================
# CONFIGURATION
# ============================================================================
PROJECT_NAME="Xtremand"
REPO_URL="https://github.com/Prudvi4545/Xtremand.git"
INSTALL_DIR="/opt/xtremand"
PROJECT_DIR="$INSTALL_DIR/$PROJECT_NAME"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="/var/log/xtremand"
USER="xtremand"
GROUP="xtremand"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

print_header() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️ $1${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        return 1
    fi
    return 0
}

# ============================================================================
# STEP 1: SYSTEM CHECKS
# ============================================================================

step_system_checks() {
    print_header "STEP 1: System Checks"
    
    # Check OS
    if [[ ! -f /etc/os-release ]]; then
        print_error "Linux OS not detected"
        exit 1
    fi
    
    print_info "Checking required commands..."
    
    local missing=0
    local commands=("git" "python3" "pip3" "curl" "wget")
    
    for cmd in "${commands[@]}"; do
        if check_command "$cmd"; then
            print_success "$cmd is installed"
        else
            print_error "$cmd is NOT installed"
            missing=$((missing + 1))
        fi
    done
    
    if [ $missing -gt 0 ]; then
        print_error "$missing required commands missing. Installing..."
        apt-get update
        apt-get install -y git python3 python3-pip curl wget build-essential
    fi
}

# ============================================================================
# STEP 2: INSTALL SYSTEM DEPENDENCIES
# ============================================================================

step_install_dependencies() {
    print_header "STEP 2: Installing System Dependencies"
    
    print_info "Updating package manager..."
    apt-get update
    
    print_info "Installing required packages..."
    apt-get install -y \
        python3-pip \
        python3-venv \
        python3-dev \
        redis-server \
        mongodb \
        ffmpeg \
        libmagic1 \
        libreoffice \
        supervisor \
        nano
    
    print_success "All system dependencies installed"
}

# ============================================================================
# STEP 3: CREATE USER AND DIRECTORIES
# ============================================================================

step_create_user_dirs() {
    print_header "STEP 3: Creating User and Directories"
    
    # Create user if not exists
    if ! id "$USER" &>/dev/null; then
        print_info "Creating user: $USER"
        useradd -m -s /bin/bash $USER
        print_success "User created: $USER"
    else
        print_info "User $USER already exists"
    fi
    
    # Create directories
    print_info "Creating directories..."
    mkdir -p $INSTALL_DIR
    mkdir -p $LOG_DIR
    mkdir -p /var/run/xtremand
    
    # Set permissions
    chown -R $USER:$GROUP $INSTALL_DIR
    chown -R $USER:$GROUP $LOG_DIR
    chown -R $USER:$GROUP /var/run/xtremand
    
    print_success "Directories created and permissions set"
}

# ============================================================================
# STEP 4: CLONE REPOSITORY
# ============================================================================

step_clone_repo() {
    print_header "STEP 4: Cloning Repository"
    
    if [ -d "$PROJECT_DIR" ]; then
        print_info "Project directory already exists, updating..."
        cd $PROJECT_DIR
        sudo -u $USER git pull origin main
        print_success "Repository updated"
    else
        print_info "Cloning repository..."
        mkdir -p $INSTALL_DIR
        cd $INSTALL_DIR
        sudo -u $USER git clone $REPO_URL
        print_success "Repository cloned"
    fi
}

# ============================================================================
# STEP 5: CREATE VIRTUAL ENVIRONMENT
# ============================================================================

step_virtual_env() {
    print_header "STEP 5: Creating Virtual Environment"
    
    print_info "Creating venv..."
    cd $PROJECT_DIR
    sudo -u $USER python3 -m venv venv
    
    print_success "Virtual environment created"
}

# ============================================================================
# STEP 6: INSTALL PYTHON DEPENDENCIES
# ============================================================================

step_install_python() {
    print_header "STEP 6: Installing Python Dependencies"
    
    cd $PROJECT_DIR
    
    print_info "Upgrading pip..."
    sudo -u $USER $VENV_DIR/bin/pip install --upgrade pip setuptools wheel
    
    print_info "Installing requirements..."
    sudo -u $USER $VENV_DIR/bin/pip install -r requirements.txt
    
    print_success "Python dependencies installed"
}

# ============================================================================
# STEP 7: CREATE .ENV FILE
# ============================================================================

step_create_env() {
    print_header "STEP 7: Creating .env Configuration File"
    
    ENV_FILE="$PROJECT_DIR/.env"
    
    if [ -f "$ENV_FILE" ]; then
        print_info ".env already exists. Skipping..."
        return
    fi
    
    print_info "Creating .env file..."
    
    cat > $ENV_FILE << 'EOF'
# Django Configuration
DJANGO_DB_ENV=server
DJANGO_SECRET_KEY=your-super-secret-key-change-this-in-production
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=154.210.235.101,your-domain.com

# MinIO Configuration
MINIO_HOST=154.210.235.101:9000
MINIO_ACCESS_KEY=Xtremand
MINIO_SECRET_KEY=Xtremand@321

# Redis/Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/xtremand_db

# Whisper Model Configuration
WHISPER_MODEL=tiny
FFMPEG_PATH=/usr/bin/ffmpeg
FFPROBE_PATH=/usr/bin/ffprobe
EOF
    
    chown $USER:$GROUP $ENV_FILE
    chmod 600 $ENV_FILE
    
    print_success ".env file created at $ENV_FILE"
    print_info "⚠️  IMPORTANT: Edit this file and change DJANGO_SECRET_KEY and other credentials!"
    print_info "  nano $ENV_FILE"
}

# ============================================================================
# STEP 8: SETUP DATABASES
# ============================================================================

step_setup_databases() {
    print_header "STEP 8: Setting up Databases"
    
    # Start MongoDB
    print_info "Starting MongoDB..."
    systemctl start mongodb
    systemctl enable mongodb
    sleep 2
    
    if systemctl is-active --quiet mongodb; then
        print_success "MongoDB is running"
    else
        print_error "MongoDB failed to start"
        return 1
    fi
    
    # Start Redis
    print_info "Starting Redis..."
    systemctl start redis-server
    systemctl enable redis-server
    sleep 2
    
    if systemctl is-active --quiet redis-server; then
        print_success "Redis is running"
    else
        print_error "Redis failed to start"
        return 1
    fi
}

# ============================================================================
# STEP 9: CREATE SYSTEMD SERVICES
# ============================================================================

step_create_services() {
    print_header "STEP 9: Creating Systemd Services"
    
    # Django Service
    print_info "Creating Django service..."
    cat > /etc/systemd/system/xtremand-django.service << EOF
[Unit]
Description=Xtremand Django Application
After=network.target mongodb.service redis-server.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$VENV_DIR/bin/python manage.py runserver 0.0.0.0:8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # Celery Service
    print_info "Creating Celery service..."
    cat > /etc/systemd/system/xtremand-celery.service << EOF
[Unit]
Description=Xtremand Celery Worker
After=network.target redis-server.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$VENV_DIR/bin/celery -A web_project worker --loglevel=info --concurrency=4
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    print_success "Systemd services created"
}

# ============================================================================
# STEP 10: START SERVICES
# ============================================================================

step_start_services() {
    print_header "STEP 10: Starting Services"
    
    print_info "Reloading systemd daemon..."
    systemctl daemon-reload
    
    print_info "Enabling services..."
    systemctl enable xtremand-django.service
    systemctl enable xtremand-celery.service
    
    print_info "Starting Django service..."
    systemctl start xtremand-django.service
    sleep 3
    
    print_info "Starting Celery service..."
    systemctl start xtremand-celery.service
    sleep 3
    
    print_success "Services started"
}

# ============================================================================
# STEP 11: VERIFY INSTALLATION
# ============================================================================

step_verify() {
    print_header "STEP 11: Verifying Installation"
    
    echo ""
    print_info "Checking services..."
    
    if systemctl is-active --quiet xtremand-django.service; then
        print_success "Django service is RUNNING"
    else
        print_error "Django service is NOT running"
    fi
    
    if systemctl is-active --quiet xtremand-celery.service; then
        print_success "Celery service is RUNNING"
    else
        print_error "Celery service is NOT running"
    fi
    
    if systemctl is-active --quiet mongodb; then
        print_success "MongoDB is RUNNING"
    else
        print_error "MongoDB is NOT running"
    fi
    
    if systemctl is-active --quiet redis-server; then
        print_success "Redis is RUNNING"
    else
        print_error "Redis is NOT running"
    fi
    
    echo ""
    print_info "Testing connectivity..."
    if redis-cli ping &> /dev/null; then
        print_success "Redis responds to ping"
    else
        print_error "Redis not responding"
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    clear
    print_header "🚀 XTREMAND AUTOMATED DEPLOYMENT"
    
    check_root
    
    step_system_checks
    step_install_dependencies
    step_create_user_dirs
    step_clone_repo
    step_virtual_env
    step_install_python
    step_create_env
    step_setup_databases
    step_create_services
    step_start_services
    step_verify
    
    print_header "✅ DEPLOYMENT COMPLETE!"
    
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Installation completed successfully!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}📝 NEXT STEPS:${NC}"
    echo -e "1. Edit .env file: ${BLUE}nano $ENV_FILE${NC}"
    echo -e "   - Change DJANGO_SECRET_KEY to a unique value"
    echo -e "   - Update DJANGO_ALLOWED_HOSTS if needed"
    echo -e "   - Set correct MinIO credentials if different"
    echo ""
    echo -e "${YELLOW}📊 SERVICE MANAGEMENT:${NC}"
    echo -e "  Start services:   ${BLUE}systemctl start xtremand-django.service xtremand-celery.service${NC}"
    echo -e "  Stop services:    ${BLUE}systemctl stop xtremand-django.service xtremand-celery.service${NC}"
    echo -e "  View status:      ${BLUE}systemctl status xtremand-django.service${NC}"
    echo -e "  View logs:        ${BLUE}journalctl -u xtremand-django.service -f${NC}"
    echo ""
    echo -e "${YELLOW}🌐 ACCESS:${NC}"
    echo -e "  Django:  ${BLUE}http://your-server-ip:8000${NC}"
    echo -e "  MinIO:   ${BLUE}http://154.210.235.101:9000${NC}"
    echo ""
    echo -e "${YELLOW}⚙️  CONFIGURE MINIO WEBHOOK:${NC}"
    echo -e "  1. Go to: http://154.210.235.101:9000"
    echo -e "  2. Navigate to: Buckets → processing → Events"
    echo -e "  3. Add Event:"
    echo -e "     - Type: s3:ObjectCreated:*"
    echo -e "     - Endpoint: http://your-server-ip:8000/minio_event_webhook/"
    echo ""
}

# Run main function
main "$@"
