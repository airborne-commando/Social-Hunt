# 🚀 Quick Start Guide - Social-Hunt Docker

Welcome! This is the easiest way to get Social-Hunt up and running.

## ⚡ Fastest Way to Start (All Operating Systems)

### Option 1: Double-Click to Start (Easiest!)

**Windows**: Double-click `start.bat`

**Linux/macOS**: Double-click `start.sh` (or run `./start.sh` in terminal)

### Option 2: Use Python Script

```bash
python start.py
```

That's it! The script will:
- ✅ Detect your operating system automatically
- ✅ Check if Docker is running
- ✅ Offer to start Docker if it's not running
- ✅ Launch all Social-Hunt containers
- ✅ Show you the access URL

## 🌐 Access Your Application

Once started, open your browser and go to:

**http://localhost:8000**

## 🔑 Default Admin Token

The default admin token is set in two places:

1. **docker-compose.yml** (environment variable): `your_secure_token_here`
2. **data/settings.json** (fallback): `ChangeME`

**⚠️ IMPORTANT**: Change the admin token before deploying to production!

Edit `docker-compose.yml`:
```yaml
- admin_token=YourSecurePassword123!
```

Or edit `data/settings.json`:
```json
{
  "admin_token": "YourSecurePassword123!"
}
```

## 📋 Prerequisites

- Docker Desktop (Windows/macOS) or Docker Engine (Linux) installed
- Docker must be running
- Python 3.6+ (optional, for universal scripts)

## 🛠️ Useful Commands

### View Logs
```bash
docker compose logs -f social-hunt
```

### Stop Social-Hunt
```bash
docker compose down
```

### Restart Social-Hunt
```bash
docker compose restart
```

### Check Status
```bash
docker compose ps
```

### Update to Latest Version
```bash
docker compose pull
docker compose up -d
```

## 🔄 Auto-Start on Boot

Want Social-Hunt to start automatically when your computer boots?

**Windows**:
1. Press `Win + R`, type `shell:startup`, press Enter
2. Create a shortcut to `start.bat` in that folder
3. Make sure Docker Desktop is set to start on login

**Linux/macOS**: See `STARTUP_SCRIPTS.md` for detailed instructions

## 📚 More Information

- **Detailed Startup Options**: See `STARTUP_SCRIPTS.md`
- **Docker Configuration**: See `README_DOCKER.md`
- **Project Overview**: See `OVERVIEW.md`
- **Main Documentation**: See `../README.md`

## ❓ Troubleshooting

### "Can't reach this page" or "ERR_ADDRESS_INVALID"

❌ Don't use: `http://0.0.0.0:8000`

✅ Use instead: `http://localhost:8000` or `http://127.0.0.1:8000`

### Port 8000 Already in Use

Edit `docker-compose.yml` and change the port:
```yaml
ports:
  - "8080:8000"  # Now use http://localhost:8080
```

### Docker Not Running

**Windows/macOS**: Open Docker Desktop manually

**Linux**: 
```bash
sudo systemctl start docker
```

### Container Won't Start

Check the logs for errors:
```bash
docker compose logs social-hunt
```

## 🎯 Next Steps

1. ✅ Start the application (you just did this!)
2. 🔐 Change the default admin token
3. 🌐 Access http://localhost:8000
4. 📖 Explore the features in the web dashboard
5. ⚙️ Configure settings as needed

## 🆘 Need Help?

- Check `STARTUP_SCRIPTS.md` for detailed troubleshooting
- Review Docker logs: `docker compose logs`
- Visit: https://github.com/AfterPacket/Social-Hunt

---

**Happy Hunting! 🎯**