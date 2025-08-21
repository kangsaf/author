"""
Strategy Manager for kang_bot trading system
Mengelola berbagai strategi trading dan eksekusi order
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd

from .utils import get_jakarta_time, safe_float, ConfigManager
from .ai_signal import AISignalGenerator
from .risk_manager import RiskManager

class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

class OrderSide(Enum):
    """Order sides"""
    BUY = "buy"
    SELL = "sell"

class StrategyType(Enum):
    """Available strategy types"""
    AI_SIGNAL = "ai_signal"
    SCALPING = "scalping"
    SWING = "swing"
    DCA = "dca"
    GRID = "grid"

class Position:
    """Trading position representation"""
    
    def __init__(self, symbol: str, side: str, size: float, entry_price: float, 
                 timestamp: datetime = None):
        self.symbol = symbol
        self.side = side  # 'long' or 'short'
        self.size = size
        self.entry_price = entry_price
        self.timestamp = timestamp or get_jakarta_time()
        self.unrealized_pnl = 0.0
        self.stop_loss = None
        self.take_profit = None
        
    def update_pnl(self, current_price: float):
        """Update unrealized PnL"""
        if self.side == 'long':
            self.unrealized_pnl = (current_price - self.entry_price) * self.size
        else:
            self.unrealized_pnl = (self.entry_price - current_price) * self.size
    
    def to_dict(self) -> Dict:
        """Convert position to dictionary"""
        return {
            'symbol': self.symbol,
            'side': self.side,
            'size': self.size,
            'entry_price': self.entry_price,
            'timestamp': self.timestamp.isoformat(),
            'unrealized_pnl': self.unrealized_pnl,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit
        }

class StrategyManager:
    """
    Main strategy manager that coordinates different trading strategies
    """
    
    def __init__(self, config_manager: ConfigManager = None):
        """
        Initialize Strategy Manager
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager or ConfigManager()
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self.config_manager.get_config('config')
        self.strategy_config = self.config.get('strategy', {})
        
        # Initialize components
        self.ai_signal = AISignalGenerator(self.strategy_config.get('ai_signal', {}))
        self.risk_manager = RiskManager(self.config.get('risk_management', {}))
        
        # Active positions and orders
        self.positions: Dict[str, Position] = {}
        self.pending_orders: List[Dict] = []
        
        # Strategy state
        self.active_strategy = StrategyType(self.strategy_config.get('active_strategy', 'ai_signal'))
        self.is_trading_enabled = self.strategy_config.get('enabled', False)
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        
        self.logger.info(f"Strategy Manager initialized with {self.active_strategy.value} strategy")
    
    def set_strategy(self, strategy_type: StrategyType) -> bool:
        """
        Set active trading strategy
        
        Args:
            strategy_type: Strategy type to activate
            
        Returns:
            bool: True if successful
        """
        try:
            self.active_strategy = strategy_type
            self.logger.info(f"Strategy changed to: {strategy_type.value}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting strategy: {e}")
            return False
    
    def analyze_market(self, symbol: str, timeframe: str = '1h', 
                      limit: int = 100) -> Dict:
        """
        Analyze market for given symbol
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe for analysis
            limit: Number of candles to analyze
            
        Returns:
            dict: Market analysis results
        """
        try:
            # In production, this should fetch real data from exchange
            # For now, we'll use sample data
            from .ai_signal import create_sample_data
            df = create_sample_data(symbol, limit)
            
            # Generate comprehensive analysis
            analysis = self.ai_signal.generate_comprehensive_analysis(df)
            
            # Add strategy-specific recommendations
            analysis['strategy_recommendation'] = self._get_strategy_recommendation(
                analysis, symbol
            )
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing market for {symbol}: {e}")
            return {'error': str(e)}
    
    def _get_strategy_recommendation(self, analysis: Dict, symbol: str) -> Dict:
        """
        Get strategy-specific trading recommendation
        
        Args:
            analysis: Market analysis results
            symbol: Trading symbol
            
        Returns:
            dict: Strategy recommendation
        """
        try:
            signal = analysis.get('signal', {})
            trend = analysis.get('trend', {})
            levels = analysis.get('levels', {})
            
            recommendation = {
                'action': 'HOLD',
                'confidence': 'LOW',
                'reason': 'Default hold recommendation',
                'entry_price': None,
                'stop_loss': None,
                'take_profit': None,
                'position_size': 0.0
            }
            
            if self.active_strategy == StrategyType.AI_SIGNAL:
                recommendation = self._ai_signal_recommendation(signal, trend, levels, symbol)
            elif self.active_strategy == StrategyType.SCALPING:
                recommendation = self._scalping_recommendation(signal, trend, levels, symbol)
            elif self.active_strategy == StrategyType.SWING:
                recommendation = self._swing_recommendation(signal, trend, levels, symbol)
            elif self.active_strategy == StrategyType.DCA:
                recommendation = self._dca_recommendation(signal, trend, levels, symbol)
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f"Error getting strategy recommendation: {e}")
            return {'error': str(e)}
    
    def _ai_signal_recommendation(self, signal: Dict, trend: Dict, 
                                 levels: Dict, symbol: str) -> Dict:
        """AI Signal strategy recommendation"""
        try:
            signal_type = signal.get('signal_type', 'HOLD')
            score = signal.get('score', 50)
            confidence = signal.get('confidence', 'LOW')
            
            # Risk management check
            position_size = self.risk_manager.calculate_position_size(
                symbol, levels.get('current_price', 0)
            )
            
            if signal_type in ['STRONG_BUY', 'BUY'] and score > 60:
                return {
                    'action': 'BUY',
                    'confidence': confidence,
                    'reason': f"AI Signal: {signal_type} with score {score}",
                    'entry_price': levels.get('current_price'),
                    'stop_loss': levels.get('buy_stop_loss'),
                    'take_profit': levels.get('buy_take_profit'),
                    'position_size': position_size
                }
            elif signal_type in ['STRONG_SELL', 'SELL'] and score < 40:
                return {
                    'action': 'SELL',
                    'confidence': confidence,
                    'reason': f"AI Signal: {signal_type} with score {score}",
                    'entry_price': levels.get('current_price'),
                    'stop_loss': levels.get('sell_stop_loss'),
                    'take_profit': levels.get('sell_take_profit'),
                    'position_size': position_size
                }
            else:
                return {
                    'action': 'HOLD',
                    'confidence': 'LOW',
                    'reason': f"Signal not strong enough: {signal_type} (score: {score})",
                    'position_size': 0.0
                }
                
        except Exception as e:
            self.logger.error(f"Error in AI signal recommendation: {e}")
            return {'error': str(e)}
    
    def _scalping_recommendation(self, signal: Dict, trend: Dict, 
                               levels: Dict, symbol: str) -> Dict:
        """Scalping strategy recommendation"""
        # Quick in-and-out trades based on short-term signals
        return {
            'action': 'HOLD',
            'confidence': 'LOW',
            'reason': 'Scalping strategy not implemented yet',
            'position_size': 0.0
        }
    
    def _swing_recommendation(self, signal: Dict, trend: Dict, 
                            levels: Dict, symbol: str) -> Dict:
        """Swing trading strategy recommendation"""
        # Medium-term trades based on trend analysis
        return {
            'action': 'HOLD',
            'confidence': 'LOW',
            'reason': 'Swing strategy not implemented yet',
            'position_size': 0.0
        }
    
    def _dca_recommendation(self, signal: Dict, trend: Dict, 
                          levels: Dict, symbol: str) -> Dict:
        """Dollar Cost Averaging strategy recommendation"""
        # Regular buying regardless of price
        return {
            'action': 'HOLD',
            'confidence': 'LOW',
            'reason': 'DCA strategy not implemented yet',
            'position_size': 0.0
        }
    
    def execute_trade(self, symbol: str, action: str, size: float, 
                     price: float = None, order_type: OrderType = OrderType.MARKET) -> Dict:
        """
        Execute trade order (placeholder - should integrate with exchange)
        
        Args:
            symbol: Trading symbol
            action: 'BUY' or 'SELL'
            size: Order size
            price: Order price (for limit orders)
            order_type: Order type
            
        Returns:
            dict: Order execution result
        """
        try:
            # Risk management check
            if not self.risk_manager.validate_trade(symbol, action, size, price or 0):
                return {
                    'success': False,
                    'error': 'Trade rejected by risk management',
                    'timestamp': get_jakarta_time()
                }
            
            # Simulate order execution
            order_id = f"ORDER_{symbol}_{int(datetime.now().timestamp())}"
            
            # Create order
            order = {
                'order_id': order_id,
                'symbol': symbol,
                'side': action.lower(),
                'size': size,
                'price': price,
                'type': order_type.value,
                'status': 'filled',  # Simulated
                'timestamp': get_jakarta_time()
            }
            
            # Update positions
            self._update_position(order)
            
            # Track performance
            self.total_trades += 1
            
            self.logger.info(f"Trade executed: {order}")
            
            return {
                'success': True,
                'order': order,
                'timestamp': get_jakarta_time()
            }
            
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': get_jakarta_time()
            }
    
    def _update_position(self, order: Dict):
        """Update position based on order execution"""
        try:
            symbol = order['symbol']
            side = order['side']
            size = order['size']
            price = order['price']
            
            if symbol not in self.positions:
                # New position
                position_side = 'long' if side == 'buy' else 'short'
                self.positions[symbol] = Position(
                    symbol=symbol,
                    side=position_side,
                    size=size,
                    entry_price=price
                )
            else:
                # Update existing position
                existing = self.positions[symbol]
                if (existing.side == 'long' and side == 'sell') or \
                   (existing.side == 'short' and side == 'buy'):
                    # Closing position
                    if size >= existing.size:
                        # Complete close
                        pnl = existing.unrealized_pnl
                        self.total_pnl += pnl
                        if pnl > 0:
                            self.winning_trades += 1
                        del self.positions[symbol]
                    else:
                        # Partial close
                        existing.size -= size
                else:
                    # Adding to position
                    total_size = existing.size + size
                    existing.entry_price = (existing.entry_price * existing.size + price * size) / total_size
                    existing.size = total_size
            
        except Exception as e:
            self.logger.error(f"Error updating position: {e}")
    
    def get_portfolio_status(self) -> Dict:
        """
        Get current portfolio status
        
        Returns:
            dict: Portfolio information
        """
        try:
            total_positions = len(self.positions)
            total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
            
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
            
            return {
                'total_positions': total_positions,
                'active_positions': [pos.to_dict() for pos in self.positions.values()],
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'win_rate': round(win_rate, 2),
                'total_realized_pnl': round(self.total_pnl, 4),
                'total_unrealized_pnl': round(total_unrealized_pnl, 4),
                'active_strategy': self.active_strategy.value,
                'trading_enabled': self.is_trading_enabled,
                'timestamp': get_jakarta_time()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio status: {e}")
            return {'error': str(e)}
    
    def enable_trading(self) -> bool:
        """Enable trading"""
        self.is_trading_enabled = True
        self.logger.info("Trading enabled")
        return True
    
    def disable_trading(self) -> bool:
        """Disable trading"""
        self.is_trading_enabled = False
        self.logger.info("Trading disabled")
        return True
    
    def close_all_positions(self) -> Dict:
        """
        Close all open positions
        
        Returns:
            dict: Closure results
        """
        try:
            closed_positions = []
            
            for symbol, position in self.positions.items():
                # Simulate closing the position
                close_side = 'sell' if position.side == 'long' else 'buy'
                
                result = self.execute_trade(
                    symbol=symbol,
                    action=close_side.upper(),
                    size=position.size
                )
                
                if result.get('success'):
                    closed_positions.append(symbol)
            
            return {
                'success': True,
                'closed_positions': closed_positions,
                'timestamp': get_jakarta_time()
            }
            
        except Exception as e:
            self.logger.error(f"Error closing all positions: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': get_jakarta_time()
            }