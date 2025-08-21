"""
AI Signal Generator for kang_bot trading system
Menggunakan AI untuk menganalisis market dan menghasilkan sinyal trading
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import ta
from .utils import safe_float, get_jakarta_time

class AISignalGenerator:
    """
    AI-based signal generator using technical analysis and machine learning
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize AI Signal Generator
        
        Args:
            config (dict): Configuration parameters
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Signal parameters
        self.rsi_period = self.config.get('rsi_period', 14)
        self.macd_fast = self.config.get('macd_fast', 12)
        self.macd_slow = self.config.get('macd_slow', 26)
        self.macd_signal = self.config.get('macd_signal', 9)
        self.bb_period = self.config.get('bb_period', 20)
        self.bb_std = self.config.get('bb_std', 2)
        
        # Signal thresholds
        self.rsi_oversold = self.config.get('rsi_oversold', 30)
        self.rsi_overbought = self.config.get('rsi_overbought', 70)
        self.volume_threshold = self.config.get('volume_threshold', 1.5)
        
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for price data
        
        Args:
            df (pd.DataFrame): OHLCV data
            
        Returns:
            pd.DataFrame: Data with technical indicators
        """
        try:
            # Ensure required columns exist
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")
            
            # RSI
            df['rsi'] = ta.momentum.RSIIndicator(
                close=df['close'], 
                window=self.rsi_period
            ).rsi()
            
            # MACD
            macd = ta.trend.MACD(
                close=df['close'],
                window_fast=self.macd_fast,
                window_slow=self.macd_slow,
                window_sign=self.macd_signal
            )
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_histogram'] = macd.macd_diff()
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(
                close=df['close'],
                window=self.bb_period,
                window_dev=self.bb_std
            )
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_middle'] = bb.bollinger_mavg()
            df['bb_lower'] = bb.bollinger_lband()
            
            # Moving Averages
            df['sma_20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
            df['sma_50'] = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()
            df['ema_12'] = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator()
            df['ema_26'] = ta.trend.EMAIndicator(df['close'], window=26).ema_indicator()
            
            # Volume indicators
            df['volume_sma'] = ta.volume.VolumeSMAIndicator(
                close=df['close'], 
                volume=df['volume'], 
                window=20
            ).volume_sma()
            
            # Stochastic
            stoch = ta.momentum.StochasticOscillator(
                high=df['high'],
                low=df['low'],
                close=df['close']
            )
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
            
            # ATR for volatility
            df['atr'] = ta.volatility.AverageTrueRange(
                high=df['high'],
                low=df['low'],
                close=df['close']
            ).average_true_range()
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return df
    
    def generate_signal_score(self, df: pd.DataFrame, index: int = -1) -> Dict:
        """
        Generate AI signal score based on multiple indicators
        
        Args:
            df (pd.DataFrame): Data with technical indicators
            index (int): Index to analyze (-1 for latest)
            
        Returns:
            dict: Signal analysis with score and reasoning
        """
        try:
            row = df.iloc[index]
            signals = []
            score = 0
            max_score = 0
            
            # RSI Analysis
            max_score += 2
            if row['rsi'] < self.rsi_oversold:
                signals.append("RSI oversold - BUY signal")
                score += 2
            elif row['rsi'] > self.rsi_overbought:
                signals.append("RSI overbought - SELL signal")
                score -= 2
            elif 40 <= row['rsi'] <= 60:
                signals.append("RSI neutral")
                score += 0.5
            
            # MACD Analysis
            max_score += 2
            if row['macd'] > row['macd_signal']:
                if row['macd_histogram'] > 0:
                    signals.append("MACD bullish crossover - BUY signal")
                    score += 2
                else:
                    signals.append("MACD above signal line")
                    score += 1
            else:
                if row['macd_histogram'] < 0:
                    signals.append("MACD bearish crossover - SELL signal")
                    score -= 2
                else:
                    signals.append("MACD below signal line")
                    score -= 1
            
            # Bollinger Bands Analysis
            max_score += 2
            if row['close'] <= row['bb_lower']:
                signals.append("Price at lower Bollinger Band - BUY signal")
                score += 2
            elif row['close'] >= row['bb_upper']:
                signals.append("Price at upper Bollinger Band - SELL signal")
                score -= 2
            else:
                signals.append("Price within Bollinger Bands")
                score += 0.5
            
            # Moving Average Analysis
            max_score += 2
            if row['ema_12'] > row['ema_26'] and row['close'] > row['sma_20']:
                signals.append("Moving averages bullish - BUY signal")
                score += 2
            elif row['ema_12'] < row['ema_26'] and row['close'] < row['sma_20']:
                signals.append("Moving averages bearish - SELL signal")
                score -= 2
            else:
                signals.append("Moving averages mixed")
                score += 0
            
            # Volume Analysis
            max_score += 1
            if row['volume'] > row['volume_sma'] * self.volume_threshold:
                signals.append("High volume confirmation")
                score += 1
            else:
                signals.append("Normal volume")
                score += 0
            
            # Stochastic Analysis
            max_score += 1
            if row['stoch_k'] < 20 and row['stoch_d'] < 20:
                signals.append("Stochastic oversold")
                score += 1
            elif row['stoch_k'] > 80 and row['stoch_d'] > 80:
                signals.append("Stochastic overbought")
                score -= 1
            else:
                signals.append("Stochastic neutral")
                score += 0
            
            # Normalize score to 0-100 scale
            normalized_score = max(0, min(100, (score / max_score * 50) + 50))
            
            # Determine signal strength
            if normalized_score >= 70:
                signal_type = "STRONG_BUY"
                confidence = "HIGH"
            elif normalized_score >= 60:
                signal_type = "BUY"
                confidence = "MEDIUM"
            elif normalized_score >= 40:
                signal_type = "HOLD"
                confidence = "LOW"
            elif normalized_score >= 30:
                signal_type = "SELL"
                confidence = "MEDIUM"
            else:
                signal_type = "STRONG_SELL"
                confidence = "HIGH"
            
            return {
                'signal_type': signal_type,
                'score': round(normalized_score, 2),
                'confidence': confidence,
                'signals': signals,
                'timestamp': get_jakarta_time(),
                'price': safe_float(row['close']),
                'rsi': safe_float(row['rsi']),
                'macd': safe_float(row['macd']),
                'volume_ratio': safe_float(row['volume'] / row['volume_sma']) if row['volume_sma'] > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error generating signal score: {e}")
            return {
                'signal_type': 'HOLD',
                'score': 50.0,
                'confidence': 'LOW',
                'signals': ['Error in signal calculation'],
                'timestamp': get_jakarta_time(),
                'error': str(e)
            }
    
    def analyze_trend(self, df: pd.DataFrame, lookback: int = 20) -> Dict:
        """
        Analyze market trend over lookback period
        
        Args:
            df (pd.DataFrame): Price data
            lookback (int): Number of periods to analyze
            
        Returns:
            dict: Trend analysis
        """
        try:
            if len(df) < lookback:
                lookback = len(df)
            
            recent_data = df.tail(lookback)
            
            # Price trend
            price_change = (recent_data['close'].iloc[-1] - recent_data['close'].iloc[0]) / recent_data['close'].iloc[0] * 100
            
            # Volume trend
            volume_trend = recent_data['volume'].pct_change().mean() * 100
            
            # Moving average trend
            sma_slope = (recent_data['sma_20'].iloc[-1] - recent_data['sma_20'].iloc[0]) / lookback
            
            # Volatility (ATR trend)
            volatility = recent_data['atr'].mean()
            
            # Determine trend strength
            if abs(price_change) > 5:
                trend_strength = "STRONG"
            elif abs(price_change) > 2:
                trend_strength = "MODERATE"
            else:
                trend_strength = "WEAK"
            
            # Determine trend direction
            if price_change > 1:
                trend_direction = "BULLISH"
            elif price_change < -1:
                trend_direction = "BEARISH"
            else:
                trend_direction = "SIDEWAYS"
            
            return {
                'direction': trend_direction,
                'strength': trend_strength,
                'price_change_pct': round(price_change, 2),
                'volume_trend_pct': round(volume_trend, 2),
                'sma_slope': round(sma_slope, 4),
                'volatility': round(volatility, 4),
                'lookback_periods': lookback,
                'timestamp': get_jakarta_time()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing trend: {e}")
            return {
                'direction': 'UNKNOWN',
                'strength': 'WEAK',
                'error': str(e),
                'timestamp': get_jakarta_time()
            }
    
    def get_entry_exit_levels(self, df: pd.DataFrame) -> Dict:
        """
        Calculate entry and exit levels based on technical analysis
        
        Args:
            df (pd.DataFrame): Price data with indicators
            
        Returns:
            dict: Entry/exit levels and stop loss recommendations
        """
        try:
            latest = df.iloc[-1]
            
            # Support and resistance levels
            high_20 = df['high'].tail(20).max()
            low_20 = df['low'].tail(20).min()
            
            # ATR-based levels
            atr = latest['atr']
            current_price = latest['close']
            
            # Entry levels
            buy_entry = latest['bb_lower'] if not pd.isna(latest['bb_lower']) else current_price * 0.98
            sell_entry = latest['bb_upper'] if not pd.isna(latest['bb_upper']) else current_price * 1.02
            
            # Stop loss levels (2x ATR)
            buy_stop_loss = current_price - (2 * atr)
            sell_stop_loss = current_price + (2 * atr)
            
            # Take profit levels (3x ATR)
            buy_take_profit = current_price + (3 * atr)
            sell_take_profit = current_price - (3 * atr)
            
            return {
                'current_price': round(current_price, 4),
                'support_level': round(low_20, 4),
                'resistance_level': round(high_20, 4),
                'buy_entry': round(buy_entry, 4),
                'sell_entry': round(sell_entry, 4),
                'buy_stop_loss': round(buy_stop_loss, 4),
                'sell_stop_loss': round(sell_stop_loss, 4),
                'buy_take_profit': round(buy_take_profit, 4),
                'sell_take_profit': round(sell_take_profit, 4),
                'atr': round(atr, 4),
                'timestamp': get_jakarta_time()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating entry/exit levels: {e}")
            return {
                'error': str(e),
                'timestamp': get_jakarta_time()
            }
    
    def generate_comprehensive_analysis(self, df: pd.DataFrame) -> Dict:
        """
        Generate comprehensive market analysis combining all signals
        
        Args:
            df (pd.DataFrame): OHLCV data
            
        Returns:
            dict: Comprehensive analysis report
        """
        try:
            # Calculate indicators
            df_with_indicators = self.calculate_technical_indicators(df)
            
            # Generate signal
            signal_analysis = self.generate_signal_score(df_with_indicators)
            
            # Analyze trend
            trend_analysis = self.analyze_trend(df_with_indicators)
            
            # Get entry/exit levels
            levels = self.get_entry_exit_levels(df_with_indicators)
            
            # Combine all analysis
            comprehensive_analysis = {
                'signal': signal_analysis,
                'trend': trend_analysis,
                'levels': levels,
                'timestamp': get_jakarta_time(),
                'data_points': len(df),
                'analysis_version': '1.0'
            }
            
            self.logger.info(f"Generated comprehensive analysis: {signal_analysis['signal_type']} with score {signal_analysis['score']}")
            
            return comprehensive_analysis
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis: {e}")
            return {
                'error': str(e),
                'timestamp': get_jakarta_time()
            }

def create_sample_data(symbol: str = "BTCUSDT", periods: int = 100) -> pd.DataFrame:
    """
    Create sample OHLCV data for testing (in production, this should come from exchange)
    
    Args:
        symbol (str): Trading symbol
        periods (int): Number of periods to generate
        
    Returns:
        pd.DataFrame: Sample OHLCV data
    """
    import random
    
    # Generate sample data with realistic price movements
    base_price = 50000 if 'BTC' in symbol else 2000
    dates = pd.date_range(end=datetime.now(), periods=periods, freq='1H')
    
    data = []
    price = base_price
    
    for date in dates:
        # Random price movement
        change = random.uniform(-0.02, 0.02)  # ±2% change
        price = price * (1 + change)
        
        high = price * random.uniform(1.001, 1.01)
        low = price * random.uniform(0.99, 0.999)
        volume = random.uniform(1000, 10000)
        
        data.append({
            'timestamp': date,
            'open': price,
            'high': high,
            'low': low,
            'close': price,
            'volume': volume
        })
    
    return pd.DataFrame(data)