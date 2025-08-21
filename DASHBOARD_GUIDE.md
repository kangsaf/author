# 📊 KangBot Dashboard Guide

Dashboard Streamlit lengkap untuk monitoring dan kontrol KangBot trading system.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Dashboard
```bash
# Method 1: Via run.py (recommended)
python run.py --mode streamlit

# Method 2: Direct Streamlit
streamlit run streamlit_app/app.py

# Method 3: Legacy (if app_streamlit/ exists)
streamlit run app_streamlit/Home.py
```

### 3. Access Dashboard
- **Local**: http://localhost:8501
- **VPS**: http://your-server-ip:8501

## 📋 Dashboard Features

### 🏠 **Main Dashboard**
- **Real-time Status**: Bot status, trading status, positions, P&L
- **Performance Chart**: Interactive trading performance visualization
- **Control Panel**: Start/stop bot, change strategies, update settings
- **Auto Refresh**: Optional 30-second auto-refresh

### 📊 **Signals Tab**
- **Latest Signals**: Real-time trading signals with timestamps
- **Signal Distribution**: Pie chart of BUY/SELL/HOLD signals
- **Confidence Levels**: Bar chart of signal confidence distribution
- **Score Analysis**: Signal strength scoring system

### 💼 **Positions Tab**
- **Active Positions**: All open positions with real-time P&L
- **Position Summary**: Total positions, unrealized P&L, long/short ratio
- **Performance Metrics**: Individual position performance tracking
- **Risk Exposure**: Position size and exposure analysis

### ⚠️ **Risk Management Tab**
- **Risk Metrics**: Daily trades, losses, exposure vs limits
- **Risk Status**: Real-time risk level monitoring
- **Visual Charts**: Risk metrics visualization
- **Alert System**: Risk violation warnings

### 📱 **Notifications Tab**
- **Status Overview**: Telegram and WhatsApp notification status
- **Feature Control**: Enable/disable specific notification types
- **Test Functions**: Send test messages to verify connectivity
- **Configuration**: Notification settings and preferences

### ⚙️ **Settings Tab**
- **Exchange Configuration**: Multi-exchange settings and status
- **System Information**: Bot version, Python version, file status
- **Configuration Files**: Config and log file status
- **Environment Details**: System and runtime information

## 🎛️ **Control Panel Features**

### 🤖 **Bot Control**
```
🚀 Start Bot     - Initialize and start the trading bot
🛑 Stop Bot      - Gracefully stop the trading bot  
⏸️ Pause Trading - Pause trading while keeping bot running
```

### 🎯 **Strategy Management**
- **Strategy Selection**: Choose from AI Signal, Scalping, Swing, DCA
- **Real-time Switching**: Change strategies without restarting
- **Performance Tracking**: Strategy-specific performance metrics

### ⚠️ **Risk Controls**
- **Max Risk per Trade**: Adjustable risk percentage (0.1% - 5.0%)
- **Daily Loss Limit**: Maximum daily loss threshold (1% - 10%)
- **Real-time Updates**: Instant risk parameter updates

## 📈 **Visualization Components**

### 📊 **Charts Available**
1. **Performance Chart**: Cumulative P&L over time
2. **Signal Distribution**: Pie chart of signal types
3. **Confidence Levels**: Bar chart of signal confidence
4. **Risk Metrics**: Bar chart comparing current vs limits
5. **Trading Heatmap**: Performance by time and day
6. **Asset Allocation**: Portfolio distribution pie chart

### 📋 **Data Tables**
1. **Latest Signals**: Time, Symbol, Signal, Score, Confidence, Price
2. **Active Positions**: Symbol, Side, Size, Entry, Current, P&L
3. **Strategy Performance**: Comparative strategy metrics
4. **Risk Status**: Current risk levels and limits

## 🔧 **Configuration**

### 📱 **Notification Setup**
```json
{
  "notifications": {
    "telegram": {
      "enabled": true,
      "bot_token": "YOUR_BOT_TOKEN",
      "chat_id": "YOUR_CHAT_ID"
    },
    "whatsapp": {
      "enabled": true,
      "twilio_account_sid": "YOUR_SID",
      "twilio_auth_token": "YOUR_TOKEN"
    }
  }
}
```

### 🔐 **Security Settings**
- Dashboard runs on localhost by default
- For VPS deployment, configure firewall rules
- Use environment variables for sensitive data
- Enable HTTPS for production deployment

## 🚀 **Production Deployment**

### 1. **VPS Setup**
```bash
# Install system dependencies
sudo apt update && sudo apt install python3 python3-pip -y

# Clone project
git clone <your-repo> kang_bot
cd kang_bot

# Install dependencies
pip3 install -r requirements.txt
```

### 2. **Run as Service**
```bash
# Create systemd service for dashboard
sudo nano /etc/systemd/system/kangbot-dashboard.service
```

Service file:
```ini
[Unit]
Description=KangBot Dashboard
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/kang_bot
Environment=PATH=/home/ubuntu/kang_bot/venv/bin
ExecStart=/home/ubuntu/kang_bot/venv/bin/streamlit run streamlit_app/app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. **Enable Service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable kangbot-dashboard
sudo systemctl start kangbot-dashboard
```

### 4. **Nginx Reverse Proxy** (Optional)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## 🧪 **Testing Dashboard**

### 1. **Syntax Test**
```bash
python3 -m py_compile streamlit_app/app.py
python3 -m py_compile streamlit_app/components.py
```

### 2. **Import Test**
```bash
python3 -c "
import sys
sys.path.append('.')
from streamlit_app.app import main
print('✅ Dashboard imports successfully')
"
```

### 3. **Configuration Test**
```bash
python3 -c "
from streamlit_app.app import load_config, load_profit_data
config = load_config()
profit = load_profit_data()
print(f'✅ Config loaded: {len(config)} sections')
print(f'✅ Profit data loaded: {len(profit)} fields')
"
```

## 🎨 **Customization**

### 🎨 **Styling**
- Custom CSS in `app.py` for branding
- Plotly charts with consistent color scheme
- Responsive layout for mobile devices
- Dark/light mode support

### 📊 **Adding Charts**
```python
# In components.py
def create_custom_chart(data):
    fig = go.Figure()
    # Your chart logic here
    return fig

# In app.py  
chart = create_custom_chart(your_data)
st.plotly_chart(chart, use_container_width=True)
```

### 🔧 **Adding Features**
1. Create function in `components.py`
2. Import in `app.py`
3. Add to appropriate tab
4. Update configuration if needed

## 📱 **Mobile Responsiveness**

Dashboard is optimized for:
- ✅ Desktop browsers
- ✅ Tablet devices  
- ✅ Mobile phones
- ✅ Different screen resolutions

## ⚠️ **Troubleshooting**

### Common Issues:

**1. Dashboard won't start**
```bash
# Check dependencies
pip install streamlit plotly pandas

# Check port availability
netstat -tulpn | grep 8501
```

**2. Config not loading**
```bash
# Verify config files exist
ls -la config/
cat config/config.json
```

**3. Charts not displaying**
```bash
# Install plotting dependencies
pip install plotly kaleido
```

**4. Permission errors**
```bash
# Fix file permissions
chmod 644 config/*.json
chmod 755 streamlit_app/
```

## 📚 **API Reference**

### Main Functions:
- `load_config()` - Load configuration with caching
- `load_profit_data()` - Load profit data with caching  
- `get_bot_status()` - Get current bot status
- `create_performance_chart()` - Generate performance visualization
- `main()` - Main dashboard function

### Components:
- `status_indicator()` - Status indicators with colors
- `create_gauge_chart()` - Gauge charts for metrics
- `trading_signal_card()` - Signal display cards
- `position_summary_card()` - Position summary cards
- `risk_alert_box()` - Risk alert notifications

---

## 🎉 **Dashboard Ready!**

KangBot Dashboard menyediakan:
- ✅ **Real-time Monitoring**: Live bot status and performance
- ✅ **Interactive Control**: Start/stop bot and change settings
- ✅ **Visual Analytics**: Charts and graphs for all metrics
- ✅ **Risk Management**: Real-time risk monitoring and alerts
- ✅ **Multi-device Support**: Works on desktop, tablet, mobile
- ✅ **Production Ready**: Suitable for VPS deployment

**Access your dashboard at: http://localhost:8501** 🚀