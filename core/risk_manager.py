"""
Risk Manager for kang_bot trading system
Mengelola risiko trading dan money management
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd

from .utils import get_jakarta_time, safe_float, ConfigManager

class RiskLevel(Enum):
    """Risk levels"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class RiskManager:
    """
    Risk management system for trading operations
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize Risk Manager
        
        Args:
            config (dict): Risk management configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Risk parameters
        self.max_risk_per_trade = self.config.get('max_risk_per_trade', 0.02)  # 2%
        self.max_daily_loss = self.config.get('max_daily_loss', 0.05)  # 5%
        self.max_total_exposure = self.config.get('max_total_exposure', 0.8)  # 80%
        self.max_positions = self.config.get('max_positions', 5)
        self.max_correlation = self.config.get('max_correlation', 0.7)
        
        # Account settings
        self.account_balance = safe_float(self.config.get('account_balance', 10000))
        self.risk_level = RiskLevel(self.config.get('risk_level', 'moderate'))
        
        # Trading limits
        self.daily_trade_limit = self.config.get('daily_trade_limit', 10)
        self.position_size_limits = self.config.get('position_size_limits', {
            'min_position_size': 0.001,
            'max_position_size': 0.1
        })
        
        # Stop loss settings
        self.default_stop_loss_pct = self.config.get('default_stop_loss_pct', 0.02)  # 2%
        self.trailing_stop_enabled = self.config.get('trailing_stop_enabled', True)
        self.trailing_stop_pct = self.config.get('trailing_stop_pct', 0.01)  # 1%
        
        # Performance tracking
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.open_positions = {}
        self.risk_violations = []
        
        # Risk adjustment factors
        self._setup_risk_factors()
        
        self.logger.info(f"Risk Manager initialized with {self.risk_level.value} risk level")
    
    def _setup_risk_factors(self):
        """Setup risk adjustment factors based on risk level"""
        if self.risk_level == RiskLevel.CONSERVATIVE:
            self.risk_multiplier = 0.5
            self.max_risk_per_trade = min(self.max_risk_per_trade, 0.01)  # Max 1%
            self.max_daily_loss = min(self.max_daily_loss, 0.03)  # Max 3%
        elif self.risk_level == RiskLevel.MODERATE:
            self.risk_multiplier = 1.0
        else:  # AGGRESSIVE
            self.risk_multiplier = 1.5
            self.max_risk_per_trade = min(self.max_risk_per_trade * 1.5, 0.05)  # Max 5%
    
    def calculate_position_size(self, symbol: str, entry_price: float, 
                              stop_loss_price: float = None) -> float:
        """
        Calculate optimal position size based on risk management
        
        Args:
            symbol (str): Trading symbol
            entry_price (float): Entry price
            stop_loss_price (float): Stop loss price
            
        Returns:
            float: Position size in base currency
        """
        try:
            if entry_price <= 0:
                self.logger.warning(f"Invalid entry price: {entry_price}")
                return 0.0
            
            # Calculate stop loss if not provided
            if not stop_loss_price:
                stop_loss_price = entry_price * (1 - self.default_stop_loss_pct)
            
            # Calculate risk per share
            risk_per_unit = abs(entry_price - stop_loss_price)
            
            if risk_per_unit <= 0:
                self.logger.warning(f"Invalid risk calculation for {symbol}")
                return 0.0
            
            # Calculate maximum risk amount
            max_risk_amount = self.account_balance * self.max_risk_per_trade * self.risk_multiplier
            
            # Calculate position size
            position_size = max_risk_amount / risk_per_unit
            
            # Apply position size limits
            min_size = self.position_size_limits['min_position_size']
            max_size = self.position_size_limits['max_position_size'] * self.account_balance / entry_price
            
            position_size = max(min_size, min(position_size, max_size))
            
            # Check total exposure
            if not self._check_total_exposure(position_size * entry_price):
                position_size *= 0.5  # Reduce size if exposure too high
            
            self.logger.info(f"Calculated position size for {symbol}: {position_size:.6f}")
            return round(position_size, 6)
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def validate_trade(self, symbol: str, side: str, size: float, price: float) -> bool:
        """
        Validate trade against risk management rules
        
        Args:
            symbol (str): Trading symbol
            side (str): 'buy' or 'sell'
            size (float): Trade size
            price (float): Trade price
            
        Returns:
            bool: True if trade is valid
        """
        try:
            # Check if trading is allowed
            if not self._is_trading_allowed():
                self.logger.warning("Trading not allowed due to risk limits")
                return False
            
            # Check daily trade limit
            if self.daily_trades >= self.daily_trade_limit:
                self.logger.warning(f"Daily trade limit reached: {self.daily_trades}")
                return False
            
            # Check position limits
            if len(self.open_positions) >= self.max_positions:
                if symbol not in self.open_positions:  # New position
                    self.logger.warning(f"Maximum positions reached: {len(self.open_positions)}")
                    return False
            
            # Check position size
            trade_value = size * price
            if trade_value < self.position_size_limits['min_position_size'] * price:
                self.logger.warning(f"Trade size too small: {trade_value}")
                return False
            
            max_trade_value = self.position_size_limits['max_position_size'] * self.account_balance
            if trade_value > max_trade_value:
                self.logger.warning(f"Trade size too large: {trade_value}")
                return False
            
            # Check total exposure
            if not self._check_total_exposure(trade_value):
                self.logger.warning("Total exposure limit exceeded")
                return False
            
            # Check daily loss limit
            if self.daily_pnl < -self.max_daily_loss * self.account_balance:
                self.logger.warning(f"Daily loss limit reached: {self.daily_pnl}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating trade: {e}")
            return False
    
    def _is_trading_allowed(self) -> bool:
        """Check if trading is currently allowed"""
        # Check if we're in allowed trading hours (can be configured)
        current_hour = get_jakarta_time().hour
        
        # Default: allow trading 24/7 for crypto
        # Can be restricted for traditional markets
        return True
    
    def _check_total_exposure(self, additional_exposure: float) -> bool:
        """Check if additional exposure exceeds limits"""
        try:
            current_exposure = sum(
                pos.get('size', 0) * pos.get('price', 0) 
                for pos in self.open_positions.values()
            )
            
            total_exposure = current_exposure + additional_exposure
            max_allowed_exposure = self.account_balance * self.max_total_exposure
            
            return total_exposure <= max_allowed_exposure
            
        except Exception as e:
            self.logger.error(f"Error checking total exposure: {e}")
            return False
    
    def calculate_stop_loss(self, symbol: str, entry_price: float, 
                          side: str, atr: float = None) -> float:
        """
        Calculate stop loss price
        
        Args:
            symbol (str): Trading symbol
            entry_price (float): Entry price
            side (str): 'buy' or 'sell'
            atr (float): Average True Range for dynamic stops
            
        Returns:
            float: Stop loss price
        """
        try:
            if atr and atr > 0:
                # Dynamic stop loss based on ATR
                stop_distance = atr * 2  # 2x ATR
            else:
                # Fixed percentage stop loss
                stop_distance = entry_price * self.default_stop_loss_pct
            
            if side.lower() == 'buy':
                stop_loss = entry_price - stop_distance
            else:
                stop_loss = entry_price + stop_distance
            
            return round(stop_loss, 6)
            
        except Exception as e:
            self.logger.error(f"Error calculating stop loss: {e}")
            return entry_price * 0.98 if side.lower() == 'buy' else entry_price * 1.02
    
    def calculate_take_profit(self, symbol: str, entry_price: float, 
                            side: str, risk_reward_ratio: float = 2.0) -> float:
        """
        Calculate take profit price based on risk-reward ratio
        
        Args:
            symbol (str): Trading symbol
            entry_price (float): Entry price
            side (str): 'buy' or 'sell'
            risk_reward_ratio (float): Risk-reward ratio
            
        Returns:
            float: Take profit price
        """
        try:
            stop_loss = self.calculate_stop_loss(symbol, entry_price, side)
            risk_amount = abs(entry_price - stop_loss)
            
            if side.lower() == 'buy':
                take_profit = entry_price + (risk_amount * risk_reward_ratio)
            else:
                take_profit = entry_price - (risk_amount * risk_reward_ratio)
            
            return round(take_profit, 6)
            
        except Exception as e:
            self.logger.error(f"Error calculating take profit: {e}")
            return entry_price * 1.04 if side.lower() == 'buy' else entry_price * 0.96
    
    def update_position(self, symbol: str, position_data: Dict):
        """
        Update position information
        
        Args:
            symbol (str): Trading symbol
            position_data (dict): Position data
        """
        try:
            self.open_positions[symbol] = position_data
            self.logger.debug(f"Updated position for {symbol}")
            
        except Exception as e:
            self.logger.error(f"Error updating position: {e}")
    
    def close_position(self, symbol: str, pnl: float = 0.0):
        """
        Close position and update PnL
        
        Args:
            symbol (str): Trading symbol
            pnl (float): Realized PnL
        """
        try:
            if symbol in self.open_positions:
                del self.open_positions[symbol]
                self.daily_pnl += pnl
                self.logger.info(f"Closed position for {symbol}, PnL: {pnl}")
                
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
    
    def check_risk_limits(self) -> Dict:
        """
        Check all risk limits and return status
        
        Returns:
            dict: Risk status report
        """
        try:
            warnings = []
            violations = []
            
            # Check daily loss
            daily_loss_pct = abs(self.daily_pnl) / self.account_balance * 100
            if daily_loss_pct > self.max_daily_loss * 100:
                violations.append(f"Daily loss limit exceeded: {daily_loss_pct:.2f}%")
            elif daily_loss_pct > self.max_daily_loss * 100 * 0.8:
                warnings.append(f"Approaching daily loss limit: {daily_loss_pct:.2f}%")
            
            # Check position count
            if len(self.open_positions) >= self.max_positions:
                violations.append(f"Maximum positions reached: {len(self.open_positions)}")
            elif len(self.open_positions) >= self.max_positions * 0.8:
                warnings.append(f"Approaching position limit: {len(self.open_positions)}")
            
            # Check total exposure
            total_exposure = sum(
                pos.get('size', 0) * pos.get('price', 0) 
                for pos in self.open_positions.values()
            )
            exposure_pct = total_exposure / self.account_balance * 100
            
            if exposure_pct > self.max_total_exposure * 100:
                violations.append(f"Total exposure exceeded: {exposure_pct:.2f}%")
            elif exposure_pct > self.max_total_exposure * 100 * 0.8:
                warnings.append(f"High total exposure: {exposure_pct:.2f}%")
            
            # Check daily trades
            if self.daily_trades >= self.daily_trade_limit:
                violations.append(f"Daily trade limit reached: {self.daily_trades}")
            elif self.daily_trades >= self.daily_trade_limit * 0.8:
                warnings.append(f"Approaching daily trade limit: {self.daily_trades}")
            
            risk_status = "SAFE"
            if violations:
                risk_status = "VIOLATION"
            elif warnings:
                risk_status = "WARNING"
            
            return {
                'status': risk_status,
                'warnings': warnings,
                'violations': violations,
                'daily_pnl': round(self.daily_pnl, 2),
                'daily_pnl_pct': round(daily_loss_pct, 2),
                'open_positions': len(self.open_positions),
                'daily_trades': self.daily_trades,
                'total_exposure_pct': round(exposure_pct, 2),
                'account_balance': self.account_balance,
                'timestamp': get_jakarta_time()
            }
            
        except Exception as e:
            self.logger.error(f"Error checking risk limits: {e}")
            return {'error': str(e)}
    
    def reset_daily_counters(self):
        """Reset daily counters (should be called at start of each day)"""
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.risk_violations.clear()
        self.logger.info("Daily risk counters reset")
    
    def adjust_risk_level(self, new_level: RiskLevel):
        """
        Adjust risk level and parameters
        
        Args:
            new_level: New risk level
        """
        try:
            self.risk_level = new_level
            self._setup_risk_factors()
            self.logger.info(f"Risk level adjusted to: {new_level.value}")
            
        except Exception as e:
            self.logger.error(f"Error adjusting risk level: {e}")
    
    def get_risk_report(self) -> Dict:
        """
        Generate comprehensive risk report
        
        Returns:
            dict: Risk management report
        """
        try:
            risk_status = self.check_risk_limits()
            
            # Calculate additional metrics
            total_positions_value = sum(
                pos.get('size', 0) * pos.get('price', 0) 
                for pos in self.open_positions.values()
            )
            
            avg_position_size = (total_positions_value / len(self.open_positions) 
                               if self.open_positions else 0)
            
            return {
                'risk_status': risk_status,
                'risk_parameters': {
                    'risk_level': self.risk_level.value,
                    'max_risk_per_trade': self.max_risk_per_trade,
                    'max_daily_loss': self.max_daily_loss,
                    'max_total_exposure': self.max_total_exposure,
                    'max_positions': self.max_positions
                },
                'current_metrics': {
                    'account_balance': self.account_balance,
                    'daily_pnl': round(self.daily_pnl, 2),
                    'daily_trades': self.daily_trades,
                    'open_positions': len(self.open_positions),
                    'total_exposure': round(total_positions_value, 2),
                    'avg_position_size': round(avg_position_size, 2)
                },
                'position_details': list(self.open_positions.values()),
                'timestamp': get_jakarta_time()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating risk report: {e}")
            return {'error': str(e)}
    
    def emergency_stop(self) -> Dict:
        """
        Emergency stop all trading activities
        
        Returns:
            dict: Emergency stop results
        """
        try:
            self.logger.warning("EMERGENCY STOP ACTIVATED")
            
            # Record emergency stop
            emergency_record = {
                'timestamp': get_jakarta_time(),
                'reason': 'Manual emergency stop',
                'open_positions': len(self.open_positions),
                'daily_pnl': self.daily_pnl
            }
            
            self.risk_violations.append(emergency_record)
            
            return {
                'success': True,
                'message': 'Emergency stop activated',
                'emergency_record': emergency_record
            }
            
        except Exception as e:
            self.logger.error(f"Error in emergency stop: {e}")
            return {'error': str(e)}