# 🤖 KangBot - Trading Bot System

KangBot adalah sistem trading bot yang modular dan siap production untuk cryptocurrency trading dengan AI signal analysis, risk management, dan multi-exchange support.

## 🏗️ Struktur Project

```
kang_bot/
├── run.py                  # 🚀 Entry point utama
├── kang_bot.py            # 🤖 Main bot class
├── core/                  # 🧠 Core modules
│   ├── __init__.py
│   ├── ai_signal.py       # 📊 AI signal generator
│   ├── strategy_manager.py # 🎯 Strategy management
│   ├── risk_manager.py    # ⚠️ Risk management
│   └── utils.py           # 🛠️ Utility functions
├── handlers/              # 🔌 External service handlers
│   ├── __init__.py
│   ├── binance_handler.py # 🟡 Binance integration
│   ├── bybit_handler.py   # 🟠 Bybit integration
│   ├── telegram_handler.py # 📱 Telegram notifications
│   └── whatsapp_handler.py # 💬 WhatsApp notifications
├── config/                # ⚙️ Configuration files
│   ├── config.json        # 🔧 Main configuration
│   └── profit.json        # 💰 Profit tracking
├── logs/                  # 📝 Log files
│   ├── trading.log        # 📈 Trading logs
│   └── error.log          # ❌ Error logs
├── tests/                 # 🧪 Unit tests
│   ├── __init__.py
│   ├── test_strategy.py   # Test strategy manager
│   ├── test_handlers.py   # Test handlers
│   └── test_risk.py       # Test risk manager
└── requirements.txt       # 📦 Dependencies
```

## 🚀 Quick Start

### 1. Instalasi Dependencies

```bash
pip install -r requirements.txt
```

### 2. Konfigurasi

Edit file `config/config.json` untuk mengatur:
- API keys exchange (Binance/Bybit)
- Telegram bot token dan chat ID
- Risk management parameters
- Trading strategy settings

### 3. Jalankan Bot

```bash
# Mode trading bot (safe mode - trading disabled)
python run.py

# Enable live trading (HATI-HATI!)
python run.py --enable-trading

# Pilih strategy tertentu
python run.py --strategy ai_signal

# Test koneksi saja
python run.py --mode test

# Jalankan UI Streamlit
python run.py --mode streamlit
```

## 📊 Fitur Utama

### 🧠 AI Signal Analysis
- RSI, MACD, Bollinger Bands analysis
- Multi-timeframe signal scoring
- Trend analysis dan volatility detection
- Confidence scoring system

### 🎯 Strategy Management
- Multiple strategy support (AI Signal, Scalping, Swing, DCA)
- Dynamic strategy switching
- Portfolio management
- Performance tracking

### ⚠️ Risk Management
- Position sizing based on risk tolerance
- Daily loss limits
- Maximum exposure controls
- Stop loss dan take profit automation
- Emergency stop functionality

### 🔌 Multi-Exchange Support
- Binance Spot & Futures
- Bybit Spot & Derivatives
- Easy integration untuk exchange baru

### 📱 Smart Notifications
- Telegram integration dengan rich formatting
- WhatsApp notifications via Twilio
- Signal alerts, trade confirmations
- Daily/weekly reports

## ⚙️ Konfigurasi

### Trading Settings
```json
{
  "trading": {
    "enabled": false,           // Enable/disable trading
    "default_symbol": "BTCUSDT",
    "default_timeframe": "1h",
    "auto_trading": false
  }
}
```

### Risk Management
```json
{
  "risk_management": {
    "max_risk_per_trade": 0.02,    // 2% max risk per trade
    "max_daily_loss": 0.05,        // 5% max daily loss
    "max_total_exposure": 0.8,     // 80% max total exposure
    "account_balance": 10000,
    "risk_level": "moderate"       // conservative/moderate/aggressive
  }
}
```

### Exchange Configuration
```json
{
  "exchanges": {
    "binance": {
      "enabled": true,
      "testnet": true,              // Use testnet for safety
      "api_key": "your_api_key",
      "api_secret": "your_secret"
    }
  }
}
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_strategy.py

# Run with coverage
python -m pytest tests/ --cov=core --cov=handlers
```

## 🔒 Security & Safety

### 🛡️ Built-in Safety Features
- **Default Safe Mode**: Trading disabled by default
- **Testnet Support**: Test dengan paper trading
- **Risk Limits**: Multiple layers of risk protection
- **Emergency Stop**: Manual dan automatic emergency stops
- **Position Limits**: Maximum positions dan exposure controls

### 🔐 API Security
- Secure credential management
- Rate limiting untuk API calls
- Error handling dan retry logic
- Signature validation

## 📈 Performance Monitoring

### 📊 Real-time Metrics
- Win rate tracking
- PnL monitoring
- Drawdown analysis
- Risk exposure monitoring

### 📱 Notifications
- Trade execution alerts
- Risk violation warnings
- Daily performance reports
- System status updates

## 🛠️ Development

### Adding New Strategy
1. Extend `StrategyManager` class
2. Implement strategy logic in `_your_strategy_recommendation()`
3. Add strategy configuration
4. Update `StrategyType` enum

### Adding New Exchange
1. Create handler in `handlers/` directory
2. Implement required methods (get_balance, place_order, etc.)
3. Add configuration in `config.json`
4. Update `KangBot` initialization

### Adding New Notifications
1. Create handler in `handlers/` directory  
2. Implement notification methods
3. Add configuration
4. Integrate in `KangBot` class

## 🚨 Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Ensure you're in project root
export PYTHONPATH="${PYTHONPATH}:/workspace"
```

**2. API Connection Errors**
```bash
# Test connections
python run.py --mode test
```

**3. Permission Errors**
```bash
# Check file permissions
chmod +x run.py
```

### Log Files
- `logs/trading.log` - All trading activities
- `logs/error.log` - Error messages dan stack traces

## 📞 Support

- 📧 Check logs untuk troubleshooting
- 🧪 Run tests untuk validate functionality  
- ⚙️ Verify configuration files
- 🔧 Test API connections

## ⚠️ Disclaimer

**TRADING CRYPTOCURRENCY INVOLVES SUBSTANTIAL RISK OF LOSS.**

- Bot ini untuk educational purposes
- Test thoroughly sebelum live trading
- Never invest more than you can afford to lose
- Past performance tidak guarantee future results
- Selalu gunakan proper risk management

## 🔄 Updates

Bot ini dirancang untuk:
- ✅ **Modular**: Easy to extend dan customize
- ✅ **Production Ready**: Robust error handling dan logging
- ✅ **Secure**: Multiple safety layers
- ✅ **Scalable**: Support multiple exchanges dan strategies
- ✅ **Maintainable**: Clean code structure dan comprehensive tests

---

**Happy Trading! 🚀💰**