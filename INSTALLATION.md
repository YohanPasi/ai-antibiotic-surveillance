# Installation & Deployment Guide

## Sentinel AMR Surveillance Platform

This guide covers the complete setup and deployment process for the Sentinel platform.

---

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, Linux (Ubuntu 20.04+), or macOS 11+
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB free space
- **Docker**: Docker Desktop 20.10+ or Docker Engine 20.10+
- **Docker Compose**: v2.0+

### Recommended Requirements
- **RAM**: 16GB for optimal performance
- **CPU**: 4+ cores
- **Storage**: 20GB SSD

---

## Quick Start Guide

### 1. Clone the Repository

```bash
git clone https://github.com/YohanPasi/ai-antibiotic-surveillance.git
cd ai-antibiotic-surveillance
```

### 2. Environment Configuration

The application uses Docker Compose with environment variables already configured in `docker-compose.yml`. For production deployment, create a `.env` file:

```env
# Database Configuration
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=sentinel_db

# API Configuration
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Frontend Configuration
VITE_API_URL=http://localhost:8000
```

### 3. Start the Application

```bash
# Start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### 4. Access the Platform

- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/api/docs
- **API Health Check**: http://localhost:8000/health

---

## Development Setup

### Running Services Individually

**Frontend Only:**
```bash
cd frontend
npm install
npm run dev
```

**Backend Only:**
```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload
```

**Database:**
```bash
docker-compose up db
```

### Hot Reload

Both frontend and backend support hot reload:
- React (Vite) automatically reloads on file changes
- FastAPI reloads with `--reload` flag

---

## Production Deployment

### 1. Build Production Images

```bash
docker-compose -f docker-compose.prod.yml build
```

### 2. Security Checklist

- [ ] Change default database credentials
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS/SSL certificates
- [ ] Configure CORS properly
- [ ] Set up firewall rules
- [ ] Enable database backups
- [ ] Implement rate limiting
- [ ] Set up monitoring and logging

### 3. Deploy to Server

```bash
# On your production server
git clone https://github.com/YohanPasi/ai-antibiotic-surveillance.git
cd ai-antibiotic-surveillance

# Configure production environment
nano .env.production

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Reverse Proxy Setup (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Database Management

### Backup Database

```bash
docker-compose exec db pg_dump -U postgres sentinel_db > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
docker-compose exec -T db psql -U postgres sentinel_db < backup_file.sql
```

### Access Database

```bash
docker-compose exec db psql -U postgres -d sentinel_db
```

---

## Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Check what's using the port
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# Stop the process or change ports in docker-compose.yml
```

**Docker Build Fails:**
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

**Database Connection Issues:**
```bash
# Check database logs
docker-compose logs db

# Restart database service
docker-compose restart db
```

**Frontend Not Loading:**
```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose up --build frontend
```

---

## Monitoring & Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
docker-compose logs -f api
docker-compose logs -f db

# Last 100 lines
docker-compose logs --tail=100
```

### Health Checks

```bash
# Check service status
docker-compose ps

# API health
curl http://localhost:8000/health

# Database health
docker-compose exec db pg_isready -U postgres
```

---

## Maintenance

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### Clean Up

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

---

## Support

For technical support or issues:
- Create an issue on GitHub
- Contact: SLIIT Research Team
- Email: Teaching Hospital Peradeniya Collaboration

---

**Last Updated**: January 2026  
**Version**: 2.0.0
