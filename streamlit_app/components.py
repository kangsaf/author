"""
Reusable components for KangBot Streamlit dashboard
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

def status_indicator(status: str, label: str = "Status"):
    """Create a status indicator with color coding"""
    colors = {
        "running": "🟢",
        "stopped": "🔴", 
        "warning": "🟡",
        "error": "🔴",
        "safe": "🟢",
        "enabled": "🟢",
        "disabled": "⚪"
    }
    
    color = colors.get(status.lower(), "⚪")
    return f"{color} {label}: {status.title()}"

def create_gauge_chart(value: float, max_value: float, title: str, unit: str = "%"):
    """Create a gauge chart for metrics"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        delta = {'reference': max_value * 0.8},
        gauge = {
            'axis': {'range': [None, max_value]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, max_value * 0.5], 'color': "lightgray"},
                {'range': [max_value * 0.5, max_value * 0.8], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_value * 0.9
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

def create_candlestick_chart(df: pd.DataFrame, title: str = "Price Chart"):
    """Create a candlestick chart"""
    fig = go.Figure(data=go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close']
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title="Price ($)",
        xaxis_rangeslider_visible=False
    )
    
    return fig

def create_pnl_chart(dates: list, pnl_values: list, title: str = "P&L Chart"):
    """Create P&L line chart"""
    fig = go.Figure()
    
    # Add P&L line
    fig.add_trace(go.Scatter(
        x=dates,
        y=pnl_values,
        mode='lines+markers',
        name='P&L',
        line=dict(color='blue', width=2),
        fill='tonexty' if any(v < 0 for v in pnl_values) else 'tozeroy',
        fillcolor='rgba(0,100,80,0.2)' if pnl_values[-1] > 0 else 'rgba(255,0,0,0.2)'
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="P&L ($)",
        hovermode='x unified'
    )
    
    return fig

def create_strategy_performance_table(strategy_data: dict):
    """Create strategy performance comparison table"""
    data = []
    for strategy, metrics in strategy_data.items():
        data.append({
            "Strategy": strategy.replace("_", " ").title(),
            "Total Trades": metrics.get('total_trades', 0),
            "Win Rate": f"{metrics.get('win_rate', 0):.1f}%",
            "Total P&L": f"${metrics.get('total_profit', 0):.2f}",
            "Avg Trade": f"${metrics.get('total_profit', 0) / max(metrics.get('total_trades', 1), 1):.2f}"
        })
    
    return pd.DataFrame(data)

def risk_alert_box(risk_level: str, message: str):
    """Create a risk alert box"""
    if risk_level.lower() == "safe":
        st.success(f"✅ {message}")
    elif risk_level.lower() == "warning":
        st.warning(f"⚠️ {message}")
    elif risk_level.lower() == "danger":
        st.error(f"🚨 {message}")
    else:
        st.info(f"ℹ️ {message}")

def trading_signal_card(signal_data: dict):
    """Create a trading signal card"""
    symbol = signal_data.get('symbol', 'UNKNOWN')
    signal_type = signal_data.get('signal_type', 'HOLD')
    score = signal_data.get('score', 50)
    confidence = signal_data.get('confidence', 'LOW')
    price = signal_data.get('price', 0)
    
    # Color coding for signals
    colors = {
        'STRONG_BUY': '🟢',
        'BUY': '🟢',
        'HOLD': '🟡',
        'SELL': '🔴',
        'STRONG_SELL': '🔴'
    }
    
    signal_color = colors.get(signal_type, '⚪')
    
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Symbol", symbol)
        
        with col2:
            st.metric("Signal", f"{signal_color} {signal_type}")
        
        with col3:
            st.metric("Score", f"{score}/100")
        
        with col4:
            st.metric("Price", f"${price:.4f}")
        
        # Progress bar for score
        progress_color = "green" if score >= 60 else "orange" if score >= 40 else "red"
        st.progress(score/100)
        st.caption(f"Confidence: {confidence}")

def position_summary_card(position_data: dict):
    """Create a position summary card"""
    symbol = position_data.get('symbol', 'UNKNOWN')
    side = position_data.get('side', 'UNKNOWN')
    size = position_data.get('size', 0)
    entry_price = position_data.get('entry_price', 0)
    current_price = position_data.get('current_price', entry_price)
    unrealized_pnl = position_data.get('unrealized_pnl', 0)
    
    # Calculate P&L percentage
    pnl_pct = (unrealized_pnl / (entry_price * size)) * 100 if entry_price * size > 0 else 0
    
    with st.container():
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Position",
                value=f"{symbol} {side.upper()}",
                delta=f"Size: {size}"
            )
        
        with col2:
            st.metric(
                label="Entry Price",
                value=f"${entry_price:.4f}",
                delta=f"Current: ${current_price:.4f}"
            )
        
        with col3:
            st.metric(
                label="Unrealized P&L",
                value=f"${unrealized_pnl:.2f}",
                delta=f"{pnl_pct:+.2f}%"
            )

def notification_status_card(notification_type: str, config: dict):
    """Create notification status card"""
    enabled = config.get('enabled', False)
    
    with st.container():
        st.subheader(f"📱 {notification_type.title()}")
        
        if enabled:
            st.success("✅ Enabled")
            
            # Show enabled features
            features = []
            if config.get('send_signals', False):
                features.append("📊 Signals")
            if config.get('send_trades', False):
                features.append("💰 Trades")
            if config.get('send_errors', False):
                features.append("❌ Errors")
            if config.get('send_reports', False):
                features.append("📈 Reports")
            
            if features:
                st.write("**Active notifications:**")
                for feature in features:
                    st.write(f"• {feature}")
        else:
            st.error("❌ Disabled")
            st.write("Configure API credentials to enable")

def create_trading_heatmap(data: dict):
    """Create trading performance heatmap"""
    # Mock heatmap data - in production this would come from actual trading data
    hours = list(range(24))
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Generate mock performance data
    import random
    z_data = [[random.uniform(-2, 3) for _ in hours] for _ in days]
    
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=hours,
        y=days,
        colorscale='RdYlGn',
        hoverongaps=False
    ))
    
    fig.update_layout(
        title="Trading Performance Heatmap (P&L by Hour & Day)",
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week"
    )
    
    return fig

def create_asset_allocation_pie(positions: list):
    """Create asset allocation pie chart"""
    if not positions:
        return None
    
    # Calculate allocation by symbol
    allocation = {}
    for pos in positions:
        symbol = pos.get('symbol', 'UNKNOWN')
        value = abs(pos.get('size', 0) * pos.get('entry_price', 0))
        
        if symbol in allocation:
            allocation[symbol] += value
        else:
            allocation[symbol] = value
    
    if not allocation:
        return None
    
    fig = px.pie(
        values=list(allocation.values()),
        names=list(allocation.keys()),
        title="Asset Allocation"
    )
    
    return fig