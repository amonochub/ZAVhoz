# ZAVhoz Bot - Production Deployment Guide

**Version:** 1.0.0  
**Last Updated:** October 19, 2024

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### Infrastructure Requirements
- [ ] PostgreSQL 12+ database server
- [ ] Python 3.11+ runtime
- [ ] Docker & Docker Compose (for containerized deployment)
- [ ] 2GB RAM minimum
- [ ] 10GB storage minimum
- [ ] Telegram Bot Token obtained from @BotFather

### Code Quality Gates
- [ ] All tests passing: `pytest` (target: 133+ tests)
- [ ] Code coverage: 40%+ (target: 80%+)
- [ ] Linting: `ruff check` passes
- [ ] Type checking: `mypy --strict` passes
- [ ] Security: `bandit -r src` shows no critical issues

### Database Readiness
- [ ] PostgreSQL server running
- [ ] Database created: `zavhoz`
- [ ] Alembic migrations ready
- [ ] Backup strategy documented
- [ ] Recovery procedures tested

### Monitoring Setup
- [ ] Logging configured (structlog ready)
- [ ] Sentry DSN obtained (optional)
- [ ] Log rotation configured
- [ ] Error tracking enabled
- [ ] Performance monitoring setup

---

## 🚀 DEPLOYMENT STEPS

### 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd zavhoz

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with production values
nano .env  # or your preferred editor
```

**Required settings:**
```env
BOT_TOKEN=your_telegram_token_here
ADMIN_USER_ID=your_admin_id
DATABASE_URL=postgresql://user:password@host:5432/zavhoz
LOG_LEVEL=INFO
LOG_FORMAT=json
SENTRY_ENABLED=true
SENTRY_DSN=your_sentry_url
SENTRY_ENVIRONMENT=production
```

### 3. Database Setup

```bash
# Initialize database
createdb zavhoz -U postgres

# Apply migrations
alembic upgrade head

# Verify tables created
psql -U postgres -d zavhoz -c "\dt"
```

### 4. Pre-flight Checks

```bash
# Run all tests
pytest -v --cov=. --cov-report=html

# Run linting checks
ruff check .
black . --check
isort . --check-only

# Run type checking
mypy .

# Security audit
bandit -r src/
safety check

# Database connection test
python -c "from database.connection import engine; print('DB: OK')"

# Logging test
python -c "from utils.logging_config import get_logger; \
            logger = get_logger('test'); \
            logger.info('test', status='ok')"
```

### 5. Start Services

**Option A: Docker Compose (Recommended)**

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f bot
```

**Option B: Manual Startup**

```bash
# Start PostgreSQL (if not running)
# psql -U postgres -d zavhoz

# Activate venv
source venv/bin/activate

# Run bot
python bot/main.py
```

### 6. Post-Deployment Verification

```bash
# Test bot connectivity
# Send test message to bot

# Check logs
tail -f logs/app.log

# Monitor Sentry dashboard (if enabled)
# Visit: https://sentry.io/...

# Verify database
psql -U postgres -d zavhoz -c "SELECT COUNT(*) FROM users;"
```

---

## 📊 PRODUCTION CONFIGURATION

### Logging Configuration

```env
# Production logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/zavhoz/app.log
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5      # Keep 5 backup files
```

**Log files:**
- Main: `/var/log/zavhoz/app.log`
- Rotated: `/var/log/zavhoz/app.log.1`, `.2`, etc.

### Error Tracking

```env
# Sentry configuration
SENTRY_ENABLED=true
SENTRY_DSN=https://YOUR_KEY@YOUR_ORG.ingest.sentry.io/YOUR_PROJECT
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions
```

### Database Configuration

```env
DATABASE_URL=postgresql://user:password@localhost:5432/zavhoz

# Connection pooling
# - Uses NullPool for reliability
# - No connection persistence
# - Fresh connection per operation
```

---

## 🔒 SECURITY CONSIDERATIONS

### Bot Token Security
- ✅ Never commit `.env` to git
- ✅ Rotate token if compromised
- ✅ Use environment variables only
- ✅ Restrict access to logs containing tokens

### Database Security
- ✅ Use strong password for DB user
- ✅ Restrict database network access
- ✅ Enable SSL connections
- ✅ Regular backups to secure location

### Application Security
- ✅ Run as non-root user
- ✅ Enable SELinux/AppArmor if available
- ✅ Use firewall rules
- ✅ Monitor access logs
- ✅ Keep dependencies updated

### Secrets Management
```bash
# Option 1: Environment variables
export BOT_TOKEN="..."

# Option 2: .env file (git-ignored)
# Ensure .env is in .gitignore

# Option 3: Secrets manager (AWS Secrets, Vault, etc.)
# Configure through your orchestration platform
```

---

## 📈 MONITORING & ALERTS

### Key Metrics to Track

1. **Bot Health**
   - Uptime percentage
   - Message processing rate
   - Response times
   - Error rate

2. **Database**
   - Connection pool usage
   - Query performance
   - Disk usage
   - Backup status

3. **Infrastructure**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network traffic

### Alert Configuration

**Sentry Alerts:**
- New error types
- Error rate spike (>10% increase)
- Performance degradation
- Release tracking

**Custom Alerts:**
- Bot offline for >5 minutes
- Database connection failures
- Log errors in last hour >100
- Disk usage >80%

---

## 🔄 BACKUP & RECOVERY

### Database Backups

```bash
# Daily backup (add to crontab)
0 2 * * * pg_dump -U postgres zavhoz > /backups/zavhoz-$(date +\%Y\%m\%d).sql

# Backup script
#!/bin/bash
BACKUP_DIR="/backups/zavhoz"
mkdir -p $BACKUP_DIR
pg_dump -U postgres zavhoz | gzip > $BACKUP_DIR/zavhoz-$(date +%Y%m%d-%H%M%S).sql.gz

# Keep last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

### Recovery Procedure

```bash
# Restore from backup
gunzip < /backups/zavhoz/zavhoz-20241019.sql.gz | psql -U postgres zavhoz

# Verify recovery
psql -U postgres -d zavhoz -c "SELECT COUNT(*) FROM users;"
```

### Log Archival

```bash
# Logs older than 30 days
find /var/log/zavhoz -name "*.log.*" -mtime +30 -delete

# Archive to cold storage (AWS S3, etc.)
aws s3 cp /var/log/zavhoz/ s3://backups/zavhoz-logs/ --recursive
```

---

## 📋 MIGRATION PROCEDURES

### Applying Migrations

```bash
# Show current version
alembic current

# Show migration history
alembic history

# Apply pending migrations
alembic upgrade head

# Rollback last migration (if needed)
alembic downgrade -1

# Show SQL before applying
alembic upgrade head --sql
```

### Creating New Migrations

```bash
# For schema changes
alembic revision --autogenerate -m "Add new column to users"

# Review generated migration
nano alembic/versions/XXX_*.py

# Apply migration
alembic upgrade head
```

---

## 🚨 TROUBLESHOOTING

### Bot Not Starting

```bash
# Check error logs
tail -100 logs/app.log

# Verify database connection
python -c "
from database.connection import engine
with engine.connect() as conn:
    print('DB connection OK')
"

# Check bot token
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('BOT_TOKEN')
print(f'Token set: {bool(token)}')"
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U postgres -h localhost -d zavhoz -c "SELECT 1"

# Check DATABASE_URL format
# Format: postgresql://user:password@host:port/database

# Verify firewall
netstat -tlnp | grep 5432
```

### Logging Not Working

```bash
# Check log directory exists
mkdir -p logs

# Check permissions
ls -la logs/

# Verify log level
python -c "
from utils.logging_config import LOG_LEVEL
print(f'Log level: {LOG_LEVEL}')
"
```

### Sentry Not Sending

```bash
# Check Sentry DSN
python -c "
from utils.sentry_config import SENTRY_DSN, SENTRY_ENABLED
print(f'Enabled: {SENTRY_ENABLED}')
print(f'DSN: {SENTRY_DSN[:50]}...')
"

# Test Sentry connection
python -c "
import sentry_sdk
sentry_sdk.init('YOUR_DSN')
sentry_sdk.capture_message('test')
"
```

---

## 🔍 MONITORING COMMANDS

### Check Bot Status

```bash
# Check process
ps aux | grep "python bot/main.py"

# Check port listening (if using webhook)
netstat -tlnp | grep LISTEN

# Check logs in real-time
tail -f logs/app.log | grep -E "ERROR|WARNING"
```

### Database Monitoring

```bash
# Active connections
psql -U postgres -d zavhoz -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'zavhoz';"

# Table sizes
psql -U postgres -d zavhoz -c "
SELECT schemaname, tablename, 
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname != 'pg_catalog' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Index usage
psql -U postgres -d zavhoz -c "
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;"
```

### Resource Monitoring

```bash
# CPU and memory
top -b -n 1 | head -20

# Disk usage
du -sh /*
df -h

# Network
netstat -i
```

---

## 📚 USEFUL COMMANDS

### Database

```bash
# Create backup
pg_dump zavhoz > backup.sql

# Restore backup
psql zavhoz < backup.sql

# Connect to database
psql -U postgres -d zavhoz

# List databases
psql -l

# List tables
psql -d zavhoz -c "\dt"
```

### Application

```bash
# Run with debug logging
LOG_LEVEL=DEBUG python bot/main.py

# Run tests with coverage
pytest --cov=. --cov-report=html

# Format code
black .
isort .

# Check for issues
ruff check . --fix
```

### Docker

```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f bot

# Execute command in container
docker-compose exec bot python -c "..."
```

---

## 🎯 PRODUCTION READINESS CHECKLIST

Before going live, verify:

- [x] All tests passing
- [x] Code coverage >40%
- [x] Security checks passed
- [x] Logging configured
- [x] Error tracking ready
- [x] Database backups working
- [x] Monitoring dashboards created
- [x] Alerts configured
- [x] Runbooks documented
- [x] Team trained on operations

---

## 🚀 DEPLOYMENT TIMELINE

**Pre-deployment:** 1-2 hours
- Environment setup
- Configuration
- Pre-flight checks

**Deployment:** 30 minutes
- Database migrations
- Service startup
- Verification

**Post-deployment:** Ongoing
- Monitoring
- Log analysis
- Performance tracking

---

## 📞 SUPPORT & ESCALATION

### On-Call Procedures

1. **Alert received** → Check logs
2. **Issue identified** → Review recent changes
3. **Impact assessment** → Determine severity
4. **Mitigation** → Apply fix or rollback
5. **Post-mortem** → Document incident

### Escalation Contacts

- Database: DBA team
- Infrastructure: Ops team
- Application: Development team
- Emergency: On-call lead

---

## 🎉 GO-LIVE CHECKLIST

```
Day 1 - Pre-launch:
[ ] Final code review
[ ] Load testing completed
[ ] Security audit passed
[ ] Documentation reviewed
[ ] Team trained

Day 2 - Launch:
[ ] Database backups verified
[ ] Monitoring active
[ ] Alert recipients notified
[ ] Team on standby
[ ] Communication channel active

Day 3-7 - Stability:
[ ] No critical errors
[ ] Performance nominal
[ ] User feedback positive
[ ] Metrics healthy
[ ] Full go-live approval
```

---

**Status: DEPLOYMENT GUIDE COMPLETE - READY FOR PRODUCTION** 🚀
