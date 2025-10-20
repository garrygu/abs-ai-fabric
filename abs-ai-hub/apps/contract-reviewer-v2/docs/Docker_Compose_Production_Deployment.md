# Docker Compose Data Persistence vs Production PostgreSQL Installation

## Overview
This document clarifies the data persistence capabilities of Docker Compose and provides guidance on production PostgreSQL deployment options for workstations shipped to end users.

## Docker Compose Data Persistence

### ❌ **Your Understanding is Incorrect**
Docker Compose **DOES persist data** between restarts when configured properly.

### ✅ **Correct Understanding**
```yaml
# Docker Compose with persistent data
version: '3.8'
services:
  postgres:
    image: postgres:15
    volumes:
      - postgres-data:/var/lib/postgresql/data  # ← This persists data!
    environment:
      - POSTGRES_DB=document_hub
      - POSTGRES_USER=hub_user
      - POSTGRES_PASSWORD=secure_password

volumes:
  postgres-data:  # ← Named volume persists data
    driver: local
```

### **Data Persistence Options**

#### Option 1: Named Volumes (Recommended)
```yaml
volumes:
  postgres-data:
    driver: local
```
- ✅ **Data persists** across container restarts
- ✅ **Data persists** across Docker Compose down/up
- ✅ **Data persists** across system reboots
- ✅ **Easy backup** and restore

#### Option 2: Bind Mounts
```yaml
volumes:
  - /abs-shared-data/postgres:/var/lib/postgresql/data
```
- ✅ **Data persists** across container restarts
- ✅ **Data persists** across Docker Compose down/up
- ✅ **Data persists** across system reboots
- ✅ **Direct file access** to database files

#### Option 3: Host Directory Mount
```yaml
volumes:
  - ./postgres-data:/var/lib/postgresql/data
```
- ✅ **Data persists** across container restarts
- ✅ **Data persists** across Docker Compose down/up
- ✅ **Data persists** across system reboots
- ✅ **Easy backup** and restore

### **What Causes Data Loss**
```yaml
# ❌ This loses data on restart
services:
  postgres:
    image: postgres:15
    # No volumes = data lost on container restart
```

## Production Deployment Options

### Option 1: Docker Compose in Production (Recommended)
**Best for**: Workstations with Docker support

#### Advantages
- ✅ **Consistent environment** - Same setup as development
- ✅ **Easy updates** - Update PostgreSQL version easily
- ✅ **Isolation** - PostgreSQL runs in container
- ✅ **Easy backup** - Volume backup/restore
- ✅ **Easy maintenance** - Container management
- ✅ **Cross-platform** - Works on Windows/Ubuntu

#### Production Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    container_name: document-hub-postgres
    restart: unless-stopped
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./postgresql.conf:/etc/postgresql/postgresql.conf
      - ./backups:/backups
    environment:
      - POSTGRES_DB=document_hub
      - POSTGRES_USER=hub_user
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
    secrets:
      - postgres_password
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hub_user -d document_hub"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /abs-shared-data/postgres

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
```

### Option 2: Native PostgreSQL Installation
**Best for**: Workstations without Docker or maximum performance

#### Advantages
- ✅ **Maximum performance** - No container overhead
- ✅ **System integration** - Native system service
- ✅ **Familiar management** - Standard PostgreSQL tools
- ✅ **No Docker dependency** - Works on any system

#### Installation Script
```bash
#!/bin/bash
# install-postgresql.sh

# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Configure PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create application database
sudo -u postgres createdb document_hub
sudo -u postgres createuser hub_user
sudo -u postgres psql -c "ALTER USER hub_user PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE document_hub TO hub_user;"

# Configure PostgreSQL for production
sudo nano /etc/postgresql/15/main/postgresql.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Restart PostgreSQL
sudo systemctl restart postgresql
```

## Comparison: Docker vs Native Installation

### Performance Comparison
| Aspect | Docker Compose | Native Installation |
|--------|----------------|-------------------|
| **Startup Time** | 10-30 seconds | 2-5 seconds |
| **Memory Usage** | +50-100MB overhead | Base PostgreSQL only |
| **CPU Usage** | +5-10% overhead | Base PostgreSQL only |
| **Disk I/O** | Slight overhead | Direct disk access |
| **Network** | Port forwarding | Direct port binding |

### Management Comparison
| Aspect | Docker Compose | Native Installation |
|--------|----------------|-------------------|
| **Updates** | Easy (new image) | Manual (apt/yum) |
| **Backup** | Volume backup | pg_dump + files |
| **Configuration** | Environment variables | Config files |
| **Logs** | Docker logs | System logs |
| **Monitoring** | Docker stats | System tools |

## Recommended Production Strategy

### For Workstations with Docker Support
```yaml
# Use Docker Compose with persistent volumes
version: '3.8'
services:
  postgres:
    image: postgres:15
    restart: unless-stopped
    volumes:
      - postgres-data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=document_hub
      - POSTGRES_USER=hub_user
      - POSTGRES_PASSWORD=secure_password

volumes:
  postgres-data:
    driver: local
```

### For Workstations without Docker
```bash
# Install PostgreSQL natively
sudo apt install postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Configure for your application
sudo -u postgres createdb document_hub
sudo -u postgres createuser hub_user
```

## Data Backup and Recovery

### Docker Compose Backup
```bash
# Backup PostgreSQL data
docker-compose exec postgres pg_dump -U hub_user document_hub > backup.sql

# Backup volume data
docker run --rm -v document_hub_postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz -C /data .

# Restore from backup
docker run --rm -v document_hub_postgres-data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres-backup.tar.gz -C /data
```

### Native Installation Backup
```bash
# Backup PostgreSQL data
sudo -u postgres pg_dump document_hub > backup.sql

# Backup configuration
sudo cp -r /etc/postgresql /backup/postgresql-config

# Restore from backup
sudo -u postgres psql document_hub < backup.sql
```

## Workstation Deployment Options

### Option 1: Docker Compose Deployment
```bash
# Include in workstation setup
#!/bin/bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Start PostgreSQL
docker-compose up -d postgres
```

### Option 2: Native Installation Deployment
```bash
# Include in workstation setup
#!/bin/bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Configure PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Setup application database
sudo -u postgres createdb document_hub
sudo -u postgres createuser hub_user
```

## Final Recommendation

### ✅ **Docker Compose is Production-Ready**
- **Data persists** with proper volume configuration
- **Easy management** and updates
- **Consistent environment** across development and production
- **Easy backup** and restore

### ✅ **Choose Based on Requirements**
- **Docker Compose**: If workstations support Docker
- **Native Installation**: If maximum performance needed or no Docker support

### ✅ **Both Options Are Valid**
- **Docker Compose**: Modern, containerized approach
- **Native Installation**: Traditional, high-performance approach

**Bottom Line**: Docker Compose with persistent volumes is perfectly suitable for production workstations. The data will persist across restarts, updates, and system reboots. Choose the approach that best fits your workstation requirements and user preferences.
