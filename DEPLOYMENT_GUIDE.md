# 🚀 KangBot Deployment Guide

Guide lengkap untuk deploy KangBot di VPS production.

## 📋 Pre-requisites

### System Requirements
- Ubuntu 20.04+ atau CentOS 8+
- Python 3.8+
- 2GB+ RAM
- 10GB+ storage
- Stable internet connection

### API Requirements
- Binance API Key & Secret (dengan trading permissions)
- Telegram Bot Token & Chat ID
- Twilio Account (optional, untuk WhatsApp)

## 🛠️ Installation Steps

### 1. Prepare VPS Environment

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv git -y

# Create user for bot
sudo useradd -m -s /bin/bash kangbot
sudo usermod -aG sudo kangbot
```

### 2. Setup Project

```bash
# Switch to kangbot user
sudo su - kangbot

# Clone or upload project
git clone <your-repo> kang_bot
# OR upload files to /home/kangbot/kang_bot/

cd kang_bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy and edit configuration
cp config/config.json config/config.json.backup

# Edit main configuration
nano config/config.json
```

#### Essential Configuration Changes:

```json
{
  "trading": {
    "enabled": false,  // Start with false for safety
    "default_symbol": "BTCUSDT",
    "auto_trading": false
  },
  "exchanges": {
    "binance": {
      "enabled": true,
      "testnet": true,  // Use testnet first!
      "api_key": "YOUR_BINANCE_API_KEY",
      "api_secret": "YOUR_BINANCE_SECRET"
    }
  },
  "notifications": {
    "telegram": {
      "enabled": true,
      "bot_token": "YOUR_BOT_TOKEN",
      "chat_id": "YOUR_CHAT_ID",
      "send_signals": true,
      "send_trades": true,
      "send_errors": true
    }
  },
  "risk_management": {
    "account_balance": 1000,  // Your actual balance
    "max_risk_per_trade": 0.01,  // Start conservative
    "max_daily_loss": 0.03,
    "risk_level": "conservative"
  }
}
```

### 4. Test Installation

```bash
# Test structure
python3 simple_test.py

# Test connections (should show API errors - expected without real keys)
python3 run.py --mode test

# Test bot initialization
python3 run.py --help
```

## 🔒 Security Setup

### 1. Secure Configuration Files

```bash
# Set proper permissions
chmod 600 config/*.json
chmod 700 config/

# Create backup
cp config/config.json config/config.json.prod
```

### 2. Environment Variables (Recommended)

```bash
# Create .env file
nano .env
```

Add to `.env`:
```bash
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_secret_here
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. Firewall Configuration

```bash
# Basic firewall setup
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 8501/tcp  # For Streamlit UI (optional)
```

## 🔄 Process Management

### 1. Using systemd (Recommended)

Create service file:
```bash
sudo nano /etc/systemd/system/kangbot.service
```

Service file content:
```ini
[Unit]
Description=KangBot Trading System
After=network.target

[Service]
Type=simple
User=kangbot
WorkingDirectory=/home/kangbot/kang_bot
Environment=PATH=/home/kangbot/kang_bot/venv/bin
ExecStart=/home/kangbot/kang_bot/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable kangbot
sudo systemctl start kangbot

# Check status
sudo systemctl status kangbot

# View logs
sudo journalctl -u kangbot -f
```

### 2. Using Screen (Alternative)

```bash
# Install screen
sudo apt install screen

# Start bot in screen
screen -S kangbot
cd kang_bot
source venv/bin/activate
python3 run.py

# Detach: Ctrl+A, then D
# Reattach: screen -r kangbot
```

## 📊 Monitoring & Maintenance

### 1. Log Monitoring

```bash
# View real-time logs
tail -f logs/trading.log
tail -f logs/error.log

# Log rotation setup
sudo nano /etc/logrotate.d/kangbot
```

Logrotate config:
```
/home/kangbot/kang_bot/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

### 2. Health Monitoring Script

Create monitoring script:
```bash
nano monitor_kangbot.sh
```

```bash
#!/bin/bash
# KangBot Health Monitor

SERVICE_NAME="kangbot"
LOG_FILE="/home/kangbot/kang_bot/logs/monitor.log"
TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID="YOUR_CHAT_ID"

# Check if service is running
if ! systemctl is-active --quiet $SERVICE_NAME; then
    echo "$(date): $SERVICE_NAME is not running. Attempting restart..." >> $LOG_FILE
    sudo systemctl restart $SERVICE_NAME
    
    # Send alert
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
         -d chat_id="$TELEGRAM_CHAT_ID" \
         -d text="🚨 KangBot restarted on $(hostname)"
fi
```

Add to crontab:
```bash
crontab -e
# Add line:
*/5 * * * * /home/kangbot/monitor_kangbot.sh
```

### 3. Backup Strategy

```bash
# Create backup script
nano backup_kangbot.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/kangbot/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup configuration and logs
tar -czf $BACKUP_DIR/kangbot_backup_$DATE.tar.gz \
    config/ logs/ \
    --exclude='logs/*.log'

# Keep only last 7 backups
find $BACKUP_DIR -name "kangbot_backup_*.tar.gz" -mtime +7 -delete
```

## 🚀 Production Deployment Steps

### Phase 1: Testing (1-2 weeks)
1. Deploy with `testnet: true`
2. Enable notifications
3. Monitor for 1 week
4. Verify all functions work correctly

### Phase 2: Paper Trading (1-2 weeks)  
1. Switch to mainnet but keep `trading.enabled: false`
2. Monitor signals and analysis
3. Verify risk management
4. Fine-tune parameters

### Phase 3: Live Trading (Gradual)
1. Set very conservative risk limits
2. Enable trading with small amounts
3. Monitor closely for first week
4. Gradually increase limits if stable

### Configuration Progression:

**Week 1-2 (Testnet):**
```json
{
  "trading": {"enabled": false},
  "exchanges": {"binance": {"testnet": true}},
  "risk_management": {"max_risk_per_trade": 0.005}
}
```

**Week 3-4 (Paper Trading):**
```json
{
  "trading": {"enabled": false},
  "exchanges": {"binance": {"testnet": false}},
  "risk_management": {"max_risk_per_trade": 0.01}
}
```

**Week 5+ (Live Trading):**
```json
{
  "trading": {"enabled": true},
  "exchanges": {"binance": {"testnet": false}},
  "risk_management": {"max_risk_per_trade": 0.02}
}
```

## ⚠️ Safety Checklist

Before going live:

- [ ] Tested on testnet for 1+ weeks
- [ ] All notifications working
- [ ] Risk limits properly configured  
- [ ] Stop-loss mechanisms tested
- [ ] Emergency stop procedures documented
- [ ] Backup and recovery tested
- [ ] Monitoring alerts configured
- [ ] Started with minimal capital
- [ ] Team trained on emergency procedures

## 🆘 Emergency Procedures

### Emergency Stop
```bash
# Stop trading immediately
sudo systemctl stop kangbot

# Or via bot interface
python3 -c "from kang_bot import KangBot; bot = KangBot(); bot.stop()"
```

### Recovery Steps
1. Stop the bot
2. Check logs for errors
3. Verify account status
4. Fix configuration issues  
5. Test on testnet
6. Restart gradually

### Contact Information
- Keep emergency contact list
- Document all API keys locations
- Have recovery procedures printed

---

**Remember: Never risk more than you can afford to lose! 🚨**