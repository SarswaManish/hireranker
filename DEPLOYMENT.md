# HireRanker Deployment Guide

This guide covers deploying HireRanker on a Ubuntu 22.04 LTS VPS using Docker,
Docker Compose, Nginx, and Let's Encrypt SSL.

Estimated deployment time: 30-45 minutes.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Server Setup](#2-server-setup)
3. [Install Docker](#3-install-docker)
4. [Clone the Repository](#4-clone-the-repository)
5. [Configure Environment Variables](#5-configure-environment-variables)
6. [Build and Start Containers](#6-build-and-start-containers)
7. [Run Database Migrations](#7-run-database-migrations)
8. [Create a Superuser](#8-create-a-superuser)
9. [Configure SSL with Let's Encrypt](#9-configure-ssl-with-lets-encrypt)
10. [Configure Systemd for Auto-restart](#10-configure-systemd-for-auto-restart)
11. [Backup Strategy](#11-backup-strategy)
12. [Monitoring and Logs](#12-monitoring-and-logs)
13. [Updating the Application](#13-updating-the-application)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Prerequisites

### VPS Requirements

| Resource | Minimum    | Recommended            |
|----------|------------|------------------------|
| CPU      | 2 vCPU     | 4 vCPU                 |
| RAM      | 4 GB       | 8 GB                   |
| Disk     | 40 GB SSD  | 80 GB SSD              |
| OS       | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| Network  | 1 Gbps     | 1 Gbps                 |

Providers that work well: DigitalOcean, Hetzner, Linode, Vultr, AWS EC2.

### DNS

Point your domain's A record to the server's IP address before starting.
Let's Encrypt needs this to issue the SSL certificate.

```
A    yourdomain.com         ->  YOUR_SERVER_IP
A    www.yourdomain.com     ->  YOUR_SERVER_IP
```

Wait for DNS propagation (can take a few minutes to a few hours). Verify with:

```bash
dig +short yourdomain.com
```

---

## 2. Server Setup

SSH into your server as root or a sudo user.

```bash
# Update the system
apt-get update && apt-get upgrade -y

# Install essential utilities
apt-get install -y \
  curl \
  git \
  ufw \
  htop \
  unzip \
  ca-certificates \
  gnupg \
  lsb-release

# Create a deploy user (optional but recommended)
adduser deploy
usermod -aG sudo deploy
# Copy your SSH key to the deploy user:
# rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy

# Configure firewall
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
ufw status

# Set timezone
timedatectl set-timezone UTC
```

---

## 3. Install Docker

```bash
# Add Docker's official GPG key
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine and Docker Compose
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
systemctl enable docker
systemctl start docker

# Add your deploy user to the docker group (avoid running docker as root)
usermod -aG docker deploy

# Verify installation
docker --version
docker compose version
```

Log out and back in (or `newgrp docker`) for the group change to take effect.

---

## 4. Clone the Repository

```bash
# Switch to the deploy user
su - deploy

# Create app directory
mkdir -p /opt/hireranker
cd /opt/hireranker

# Clone the repo
git clone https://github.com/your-org/hireranker.git .

# Verify structure
ls -la
```

---

## 5. Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Open for editing
nano .env
```

Update these values at minimum:

```bash
# Generate a strong secret key:
# openssl rand -base64 50
SECRET_KEY=<output_of_openssl_command>

# Set your domain
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Set a strong database password
POSTGRES_PASSWORD=<strong_random_password>
DATABASE_URL=postgresql://hireranker:<strong_random_password>@postgres:5432/hireranker

# OpenAI
OPENAI_API_KEY=sk-...

# Stripe (use live keys for production)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Frontend URLs (your actual domain)
NEXT_PUBLIC_API_URL=https://yourdomain.com
NEXT_PUBLIC_APP_URL=https://yourdomain.com
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...

# Email (Sendgrid or similar)
EMAIL_HOST_PASSWORD=<sendgrid_api_key>
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

Secure the env file:

```bash
chmod 600 .env
```

---

## 6. Build and Start Containers

```bash
cd /opt/hireranker

# Build production images
docker compose -f docker-compose.prod.yml build

# Start in detached mode
docker compose -f docker-compose.prod.yml up -d

# Verify all containers are running
docker compose -f docker-compose.prod.yml ps
```

Expected output: all services should show `Up` or `healthy`:
- postgres
- redis
- backend
- celery_worker (x2)
- celery_beat
- frontend
- nginx

If a container is not healthy, check its logs:

```bash
docker compose -f docker-compose.prod.yml logs backend
```

---

## 7. Run Database Migrations

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

Expected output ends with:
```
Running migrations:
  Applying accounts.0001_initial... OK
  Applying projects.0001_initial... OK
  ...
```

Collect static files (already done in the Dockerfile build, but run manually if needed):

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

---

## 8. Create a Superuser

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

Follow the prompts to set email and password. The Django admin panel will be
accessible at `https://yourdomain.com/admin/` once SSL is configured.

---

## 9. Configure SSL with Let's Encrypt

### Install Certbot

```bash
# Install certbot (standalone, not snap)
apt-get install -y certbot

# Stop nginx temporarily so certbot can bind to port 80
docker compose -f docker-compose.prod.yml stop nginx

# Obtain certificate
certbot certonly --standalone \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --email your@email.com \
  --agree-tos \
  --no-eff-email

# Verify certificate was issued
ls /etc/letsencrypt/live/yourdomain.com/
```

### Update nginx.conf

Edit `/opt/hireranker/nginx/nginx.conf` and replace the placeholder domain:

```bash
# Replace "yourdomain.com" with your actual domain in nginx.conf
sed -i 's/yourdomain.com/YOUR_ACTUAL_DOMAIN/g' nginx/nginx.conf
```

### Restart Nginx

```bash
docker compose -f docker-compose.prod.yml start nginx

# Test the configuration
docker compose -f docker-compose.prod.yml exec nginx nginx -t
```

Visit `https://yourdomain.com` — you should see the HireRanker app with a
valid SSL certificate.

### Auto-renew Certificates

```bash
# Test renewal (dry run)
certbot renew --dry-run

# Add cron job to renew every 12 hours
crontab -e
```

Add this line to the crontab:

```
0 */12 * * * certbot renew --quiet --deploy-hook "docker exec hireranker-nginx-1 nginx -s reload"
```

---

## 10. Configure Systemd for Auto-restart

Create a systemd service so Docker Compose starts automatically on boot and
restarts if the host reboots.

```bash
cat > /etc/systemd/system/hireranker.service << 'EOF'
[Unit]
Description=HireRanker Docker Compose Application
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/hireranker
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d --remove-orphans
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
TimeoutStartSec=300
TimeoutStopSec=120
User=deploy
Group=deploy

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable the service
systemctl daemon-reload
systemctl enable hireranker.service
systemctl start hireranker.service

# Check status
systemctl status hireranker.service
```

---

## 11. Backup Strategy

### Automated PostgreSQL Backups

```bash
# Create backup directory
mkdir -p /opt/backups/postgres
chmod 700 /opt/backups/postgres

# Create backup script
cat > /opt/backups/backup_postgres.sh << 'EOF'
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/opt/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/hireranker_$TIMESTAMP.sql.gz"
RETENTION_DAYS=7

# Run pg_dump inside the postgres container
docker compose -f /opt/hireranker/docker-compose.prod.yml exec -T postgres \
  pg_dump -U hireranker hireranker | gzip > "$BACKUP_FILE"

echo "Backup created: $BACKUP_FILE ($(du -sh "$BACKUP_FILE" | cut -f1))"

# Remove backups older than RETENTION_DAYS days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
echo "Cleaned up backups older than $RETENTION_DAYS days"
EOF

chmod +x /opt/backups/backup_postgres.sh

# Test it
/opt/backups/backup_postgres.sh

# Schedule daily backups at 2am UTC
crontab -e
```

Add to crontab:

```
0 2 * * * /opt/backups/backup_postgres.sh >> /var/log/hireranker-backup.log 2>&1
```

### Restore from Backup

```bash
# List available backups
ls -lh /opt/backups/postgres/

# Restore (replace TIMESTAMP with the backup file name)
gunzip -c /opt/backups/postgres/hireranker_TIMESTAMP.sql.gz | \
  docker compose -f /opt/hireranker/docker-compose.prod.yml exec -T postgres \
  psql -U hireranker hireranker
```

### Media File Backup (Uploaded Resumes)

If using local storage (not S3), back up the media volume:

```bash
# Back up the media volume
docker run --rm \
  -v hireranker_media_files:/data \
  -v /opt/backups:/backup \
  alpine tar czf /backup/media_$(date +%Y%m%d).tar.gz -C /data .
```

If using S3, files are durable by default. Enable S3 versioning for extra
protection.

---

## 12. Monitoring and Logs

### View Logs

```bash
# All services
docker compose -f /opt/hireranker/docker-compose.prod.yml logs -f

# Specific service
docker compose -f /opt/hireranker/docker-compose.prod.yml logs -f backend
docker compose -f /opt/hireranker/docker-compose.prod.yml logs -f celery_worker
docker compose -f /opt/hireranker/docker-compose.prod.yml logs -f nginx

# Last 100 lines
docker compose -f /opt/hireranker/docker-compose.prod.yml logs --tail=100 backend
```

### Health Check

```bash
# Check application health
curl -s https://yourdomain.com/api/health/ | python3 -m json.tool

# Check all container statuses
docker compose -f /opt/hireranker/docker-compose.prod.yml ps

# Check resource usage
docker stats --no-stream
```

### Sentry (Error Tracking)

Set `SENTRY_DSN` in your `.env` file to enable automatic exception reporting.
Create a free account at sentry.io and create a new Django project to get
your DSN.

### Uptime Monitoring

Use a free external monitor (UptimeRobot, BetterUptime, or Freshping) to ping
`https://yourdomain.com/api/health/` every minute and alert you on downtime.

---

## 13. Updating the Application

```bash
cd /opt/hireranker

# Pull latest code
git pull origin main

# Rebuild images with new code
docker compose -f docker-compose.prod.yml build

# Rolling restart (zero-downtime if you have multiple backend replicas):
# 1. Start new containers
docker compose -f docker-compose.prod.yml up -d --no-deps --build backend celery_worker celery_beat frontend

# 2. Run any new migrations
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# 3. Verify everything is healthy
docker compose -f docker-compose.prod.yml ps

# For a full restart (brief downtime):
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

### Rollback

```bash
# Roll back to the previous commit
git log --oneline -5   # find the commit hash to roll back to
git checkout <commit_hash>
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

---

## 14. Troubleshooting

### Container won't start

```bash
# Check logs for the failing container
docker compose -f docker-compose.prod.yml logs <service_name>

# Check if port is already in use
ss -tlnp | grep ':80\|:443\|:8000'

# Force recreate all containers
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --force-recreate
```

### Database connection errors

```bash
# Check postgres is healthy
docker compose -f docker-compose.prod.yml ps postgres

# Connect to postgres manually
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U hireranker -d hireranker -c '\dt'

# Check DATABASE_URL in .env matches postgres credentials
grep -E "POSTGRES|DATABASE_URL" .env
```

### Nginx SSL errors

```bash
# Test nginx configuration inside the container
docker compose -f docker-compose.prod.yml exec nginx nginx -t

# Check if certificate files exist on the host
ls -la /etc/letsencrypt/live/yourdomain.com/

# Re-obtain certificate if expired
docker compose -f docker-compose.prod.yml stop nginx
certbot renew --force-renewal
docker compose -f docker-compose.prod.yml start nginx
```

### Celery tasks not processing

```bash
# Check celery worker logs
docker compose -f docker-compose.prod.yml logs -f celery_worker

# Inspect active tasks
docker compose -f docker-compose.prod.yml exec celery_worker \
  celery -A celery_app inspect active

# Check Redis connectivity
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
# Should return: PONG

# Purge a stuck queue (WARNING: this discards all pending tasks)
docker compose -f docker-compose.prod.yml exec celery_worker \
  celery -A celery_app purge -Q evaluations
```

### Out of disk space

```bash
# Check disk usage
df -h

# Check Docker space usage
docker system df

# Remove unused Docker resources (images, stopped containers, unused volumes)
# WARNING: This will remove unused volumes. Make sure you have backups first.
docker system prune -f
docker volume prune -f   # only removes volumes not attached to any container

# Remove old Docker images
docker image prune -a -f --filter "until=72h"
```

### Backend returning 500 errors

```bash
# Check Django logs
docker compose -f docker-compose.prod.yml logs backend

# Run Django checks
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py check --deploy

# Open Django shell to investigate
docker compose -f docker-compose.prod.yml exec backend python manage.py shell
```

### OpenAI API errors

Common issues:
- **401 Unauthorized**: Check `OPENAI_API_KEY` in `.env`
- **429 Rate limit**: You've exceeded your OpenAI quota; check your billing
- **Context length exceeded**: Resume text may be too long; check `MAX_RESUME_SIZE_MB`

```bash
# Check the evaluation celery logs for OpenAI errors
docker compose -f docker-compose.prod.yml logs celery_worker | grep -i openai
```

### Frontend not loading

```bash
# Check frontend container
docker compose -f docker-compose.prod.yml logs frontend

# Verify NEXT_PUBLIC_API_URL is set correctly
grep NEXT_PUBLIC_API_URL .env

# Rebuild frontend image
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d --no-deps frontend
```
