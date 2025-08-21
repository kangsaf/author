"""
KangBot Streamlit Dashboard
Dashboard lengkap untuk monitoring dan kontrol trading bot
"""
import streamlit as st
import sys
import os
from pathlib import Path
import json
import pandas as pd
from datetime import datetime, timedelta
import time
import plotly.graph_objects as go
import plotly.express as px

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Page configuration
st.set_page_config(
    page_title="KangBot Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .status-running {
        color: #28a745;
        font-weight: bold;
    }
    .status-stopped {
        color: #dc3545;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=30)
def load_config():
    """Load configuration with caching"""
    try:
        with open(ROOT / "config" / "config.json", 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading config: {e}")
        return {}

@st.cache_data(ttl=30)
def load_profit_data():
    """Load profit data with caching"""
    try:
        with open(ROOT / "config" / "profit.json", 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading profit data: {e}")
        return {}

def get_bot_status():
    """Get bot status (mock data for now)"""
    # In production, this would connect to the actual bot
    return {
        'is_running': False,
        'is_trading_enabled': False,
        'uptime': '0:00:00',
        'last_signal_time': None,
        'total_cycles': 0,
        'active_positions': 0,
        'daily_pnl': 0.0,
        'total_pnl': 0.0
    }

def create_performance_chart(profit_data):
    """Create performance chart"""
    # Mock data for demonstration
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    cumulative_pnl = [0]
    
    for i in range(1, len(dates)):
        change = (hash(str(dates[i])) % 200 - 100) / 100  # Random-ish data
        cumulative_pnl.append(cumulative_pnl[-1] + change)
    
    df = pd.DataFrame({
        'Date': dates,
        'Cumulative_PnL': cumulative_pnl
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Cumulative_PnL'],
        mode='lines',
        name='Cumulative P&L',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig.update_layout(
        title='Trading Performance',
        xaxis_title='Date',
        yaxis_title='Cumulative P&L ($)',
        hovermode='x unified'
    )
    
    return fig

def main():
    """Main dashboard function"""
    
    # Header
    st.markdown('<h1 class="main-header">🤖 KangBot Trading Dashboard</h1>', unsafe_allow_html=True)
    
    # Load data
    config = load_config()
    profit_data = load_profit_data()
    bot_status = get_bot_status()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Control Panel")
        
        # Bot Control
        st.subheader("🤖 Bot Control")
        
        if st.button("🚀 Start Bot", type="primary", use_container_width=True):
            st.success("Bot start command sent!")
            
        if st.button("🛑 Stop Bot", use_container_width=True):
            st.warning("Bot stop command sent!")
        
        if st.button("⏸️ Pause Trading", use_container_width=True):
            st.info("Trading paused!")
        
        st.divider()
        
        # Strategy Selection
        st.subheader("🎯 Strategy")
        strategy_options = ["ai_signal", "scalping", "swing", "dca"]
        current_strategy = config.get('strategy', {}).get('active_strategy', 'ai_signal')
        
        selected_strategy = st.selectbox(
            "Active Strategy",
            strategy_options,
            index=strategy_options.index(current_strategy) if current_strategy in strategy_options else 0
        )
        
        if st.button("Update Strategy"):
            st.success(f"Strategy changed to: {selected_strategy}")
        
        st.divider()
        
        # Risk Settings
        st.subheader("⚠️ Risk Settings")
        risk_config = config.get('risk_management', {})
        
        max_risk = st.slider(
            "Max Risk per Trade (%)",
            min_value=0.1,
            max_value=5.0,
            value=risk_config.get('max_risk_per_trade', 0.02) * 100,
            step=0.1
        )
        
        daily_loss_limit = st.slider(
            "Daily Loss Limit (%)",
            min_value=1.0,
            max_value=10.0,
            value=risk_config.get('max_daily_loss', 0.05) * 100,
            step=0.5
        )
        
        if st.button("Update Risk Settings"):
            st.success("Risk settings updated!")
    
    # Main content
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🤖 Bot Status",
            value="Running" if bot_status['is_running'] else "Stopped",
            delta="Online" if bot_status['is_running'] else "Offline"
        )
    
    with col2:
        st.metric(
            label="💰 Trading Status",
            value="Enabled" if bot_status['is_trading_enabled'] else "Disabled",
            delta="Active" if bot_status['is_trading_enabled'] else "Safe Mode"
        )
    
    with col3:
        st.metric(
            label="📊 Active Positions",
            value=bot_status['active_positions'],
            delta=f"Total: {bot_status['active_positions']}"
        )
    
    with col4:
        st.metric(
            label="💵 Daily P&L",
            value=f"${bot_status['daily_pnl']:.2f}",
            delta=f"Total: ${bot_status['total_pnl']:.2f}"
        )
    
    # Performance Chart
    st.subheader("📈 Performance Overview")
    
    if profit_data:
        performance_chart = create_performance_chart(profit_data)
        st.plotly_chart(performance_chart, use_container_width=True)
    else:
        st.info("No performance data available yet. Start trading to see charts!")
    
    # Tabs for detailed information
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Signals", "💼 Positions", "⚠️ Risk", "📱 Notifications", "⚙️ Settings"])
    
    with tab1:
        st.subheader("🎯 Latest Trading Signals")
        
        # Mock signal data
        signals_data = [
            {"Time": "10:30:15", "Symbol": "BTCUSDT", "Signal": "BUY", "Score": 75, "Confidence": "HIGH", "Price": "$43,250"},
            {"Time": "10:25:42", "Symbol": "ETHUSDT", "Signal": "HOLD", "Score": 55, "Confidence": "MEDIUM", "Price": "$2,650"},
            {"Time": "10:20:18", "Symbol": "BTCUSDT", "Signal": "SELL", "Score": 35, "Confidence": "LOW", "Price": "$43,180"},
        ]
        
        df_signals = pd.DataFrame(signals_data)
        st.dataframe(df_signals, use_container_width=True)
        
        # Signal Distribution
        col1, col2 = st.columns(2)
        
        with col1:
            signal_counts = df_signals['Signal'].value_counts()
            fig_signals = px.pie(
                values=signal_counts.values,
                names=signal_counts.index,
                title="Signal Distribution"
            )
            st.plotly_chart(fig_signals, use_container_width=True)
        
        with col2:
            confidence_counts = df_signals['Confidence'].value_counts()
            fig_confidence = px.bar(
                x=confidence_counts.index,
                y=confidence_counts.values,
                title="Confidence Levels"
            )
            st.plotly_chart(fig_confidence, use_container_width=True)
    
    with tab2:
        st.subheader("💼 Current Positions")
        
        # Mock position data
        positions_data = [
            {"Symbol": "BTCUSDT", "Side": "LONG", "Size": "0.001", "Entry": "$43,200", "Current": "$43,250", "P&L": "+$0.05", "P&L%": "+0.12%"},
            {"Symbol": "ETHUSDT", "Side": "SHORT", "Size": "0.1", "Entry": "$2,680", "Current": "$2,650", "P&L": "+$3.00", "P&L%": "+1.12%"},
        ]
        
        if positions_data:
            df_positions = pd.DataFrame(positions_data)
            st.dataframe(df_positions, use_container_width=True)
            
            # Position Summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Positions", len(positions_data))
            with col2:
                total_pnl = sum([float(p["P&L"].replace("$", "").replace("+", "")) for p in positions_data])
                st.metric("Unrealized P&L", f"${total_pnl:.2f}")
            with col3:
                long_positions = sum([1 for p in positions_data if p["Side"] == "LONG"])
                st.metric("Long/Short", f"{long_positions}/{len(positions_data)-long_positions}")
        else:
            st.info("No open positions")
    
    with tab3:
        st.subheader("⚠️ Risk Management")
        
        # Risk Metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Daily Trades", "3", delta="Limit: 10")
        
        with col2:
            st.metric("Daily Loss", "-$25.50", delta="Limit: -$500")
        
        with col3:
            st.metric("Exposure", "45%", delta="Limit: 80%")
        
        # Risk Status
        st.subheader("🛡️ Risk Status")
        
        risk_status = "SAFE"  # Mock status
        
        if risk_status == "SAFE":
            st.success("✅ All risk parameters within limits")
        elif risk_status == "WARNING":
            st.warning("⚠️ Approaching risk limits")
        else:
            st.error("🚨 Risk limits exceeded!")
        
        # Risk Chart
        risk_data = {
            "Metric": ["Daily Loss", "Position Size", "Total Exposure", "Trade Frequency"],
            "Current": [5, 2, 45, 30],
            "Limit": [10, 5, 80, 100]
        }
        
        df_risk = pd.DataFrame(risk_data)
        fig_risk = px.bar(
            df_risk,
            x="Metric",
            y=["Current", "Limit"],
            title="Risk Metrics vs Limits (%)",
            barmode="group"
        )
        st.plotly_chart(fig_risk, use_container_width=True)
    
    with tab4:
        st.subheader("📱 Notification Settings")
        
        # Notification Status
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Telegram**")
            telegram_enabled = config.get('notifications', {}).get('telegram', {}).get('enabled', False)
            st.write(f"Status: {'✅ Enabled' if telegram_enabled else '❌ Disabled'}")
            
            if telegram_enabled:
                st.write("✅ Signal notifications")
                st.write("✅ Trade notifications")
                st.write("✅ Error alerts")
        
        with col2:
            st.write("**WhatsApp**")
            whatsapp_enabled = config.get('notifications', {}).get('whatsapp', {}).get('enabled', False)
            st.write(f"Status: {'✅ Enabled' if whatsapp_enabled else '❌ Disabled'}")
            
            if whatsapp_enabled:
                st.write("✅ Trade notifications")
                st.write("✅ Error alerts")
                st.write("❌ Reports (disabled)")
        
        # Test Notifications
        st.subheader("🧪 Test Notifications")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Send Test Telegram"):
                st.success("Test message sent to Telegram!")
        
        with col2:
            if st.button("Send Test WhatsApp"):
                st.success("Test message sent to WhatsApp!")
    
    with tab5:
        st.subheader("⚙️ Configuration")
        
        # Exchange Settings
        st.write("**Exchange Configuration**")
        exchanges = config.get('exchanges', {})
        
        for exchange_name, exchange_config in exchanges.items():
            if exchange_name != 'default_exchange':
                enabled = exchange_config.get('enabled', False)
                testnet = exchange_config.get('testnet', True)
                
                st.write(f"**{exchange_name.upper()}**")
                st.write(f"Status: {'✅ Enabled' if enabled else '❌ Disabled'}")
                st.write(f"Mode: {'🧪 Testnet' if testnet else '🔴 Live'}")
                st.divider()
        
        # System Info
        st.subheader("🖥️ System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Bot Version**")
            try:
                with open(ROOT / "VERSION", 'r') as f:
                    version = f.read().strip()
                st.code(version)
            except:
                st.code("1.0.0")
            
            st.write("**Python Version**")
            st.code(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        
        with col2:
            st.write("**Configuration Files**")
            config_files = ["config.json", "profit.json"]
            for file in config_files:
                file_path = ROOT / "config" / file
                if file_path.exists():
                    st.write(f"✅ {file}")
                else:
                    st.write(f"❌ {file}")
            
            st.write("**Log Files**")
            log_files = ["trading.log", "error.log"]
            for file in log_files:
                log_path = ROOT / "logs" / file
                if log_path.exists():
                    st.write(f"✅ {file}")
                else:
                    st.write(f"❌ {file}")
    
    # Footer
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Last Updated:**")
        st.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    with col2:
        st.write("**Uptime:**")
        st.write(bot_status['uptime'])
    
    with col3:
        st.write("**Total Cycles:**")
        st.write(f"{bot_status['total_cycles']:,}")
    
    # Auto refresh
    if st.sidebar.checkbox("Auto Refresh (30s)"):
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()