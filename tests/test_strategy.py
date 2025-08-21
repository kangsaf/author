"""
Unit tests for strategy manager
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.strategy_manager import StrategyManager, StrategyType, Position
from core.utils import ConfigManager
from core.ai_signal import create_sample_data

class TestStrategyManager(unittest.TestCase):
    """Test cases for StrategyManager"""
    
    def setUp(self):
        """Setup test environment"""
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.get_config.return_value = {
            'strategy': {
                'active_strategy': 'ai_signal',
                'enabled': True,
                'ai_signal': {
                    'rsi_period': 14,
                    'rsi_oversold': 30,
                    'rsi_overbought': 70
                }
            },
            'risk_management': {
                'max_risk_per_trade': 0.02,
                'account_balance': 10000
            }
        }
        
        self.strategy_manager = StrategyManager(self.config_manager)
    
    def test_initialization(self):
        """Test strategy manager initialization"""
        self.assertIsInstance(self.strategy_manager, StrategyManager)
        self.assertEqual(self.strategy_manager.active_strategy, StrategyType.AI_SIGNAL)
        self.assertFalse(self.strategy_manager.is_trading_enabled)
    
    def test_set_strategy(self):
        """Test strategy switching"""
        # Test valid strategy
        result = self.strategy_manager.set_strategy(StrategyType.SWING)
        self.assertTrue(result)
        self.assertEqual(self.strategy_manager.active_strategy, StrategyType.SWING)
        
        # Test same strategy
        result = self.strategy_manager.set_strategy(StrategyType.SWING)
        self.assertTrue(result)
    
    def test_enable_disable_trading(self):
        """Test enabling and disabling trading"""
        # Initially disabled
        self.assertFalse(self.strategy_manager.is_trading_enabled)
        
        # Enable trading
        result = self.strategy_manager.enable_trading()
        self.assertTrue(result)
        self.assertTrue(self.strategy_manager.is_trading_enabled)
        
        # Disable trading
        result = self.strategy_manager.disable_trading()
        self.assertTrue(result)
        self.assertFalse(self.strategy_manager.is_trading_enabled)
    
    def test_analyze_market(self):
        """Test market analysis"""
        symbol = "BTCUSDT"
        
        with patch('core.ai_signal.create_sample_data') as mock_data:
            # Mock sample data
            mock_data.return_value = create_sample_data(symbol, 50)
            
            analysis = self.strategy_manager.analyze_market(symbol)
            
            # Check analysis structure
            self.assertIn('signal', analysis)
            self.assertIn('trend', analysis)
            self.assertIn('levels', analysis)
            self.assertIn('strategy_recommendation', analysis)
            
            # Check signal structure
            signal = analysis['signal']
            self.assertIn('signal_type', signal)
            self.assertIn('score', signal)
            self.assertIn('confidence', signal)
    
    def test_execute_trade(self):
        """Test trade execution"""
        symbol = "BTCUSDT"
        action = "BUY"
        size = 0.001
        price = 50000
        
        result = self.strategy_manager.execute_trade(symbol, action, size, price)
        
        # Check result structure
        self.assertIn('success', result)
        self.assertIn('timestamp', result)
        
        if result['success']:
            self.assertIn('order', result)
            order = result['order']
            self.assertEqual(order['symbol'], symbol)
            self.assertEqual(order['side'], action.lower())
            self.assertEqual(order['size'], size)
    
    def test_portfolio_status(self):
        """Test portfolio status retrieval"""
        status = self.strategy_manager.get_portfolio_status()
        
        # Check status structure
        required_fields = [
            'total_positions', 'active_positions', 'total_trades',
            'winning_trades', 'win_rate', 'total_realized_pnl',
            'total_unrealized_pnl', 'active_strategy', 'trading_enabled'
        ]
        
        for field in required_fields:
            self.assertIn(field, status)
        
        # Check data types
        self.assertIsInstance(status['total_positions'], int)
        self.assertIsInstance(status['total_trades'], int)
        self.assertIsInstance(status['win_rate'], (int, float))
        self.assertIsInstance(status['active_strategy'], str)
        self.assertIsInstance(status['trading_enabled'], bool)

class TestPosition(unittest.TestCase):
    """Test cases for Position class"""
    
    def test_position_creation(self):
        """Test position creation"""
        symbol = "BTCUSDT"
        side = "long"
        size = 0.001
        entry_price = 50000
        
        position = Position(symbol, side, size, entry_price)
        
        self.assertEqual(position.symbol, symbol)
        self.assertEqual(position.side, side)
        self.assertEqual(position.size, size)
        self.assertEqual(position.entry_price, entry_price)
        self.assertEqual(position.unrealized_pnl, 0.0)
    
    def test_pnl_calculation(self):
        """Test PnL calculation"""
        position = Position("BTCUSDT", "long", 0.001, 50000)
        
        # Test profit
        position.update_pnl(51000)
        self.assertEqual(position.unrealized_pnl, 1.0)  # (51000 - 50000) * 0.001
        
        # Test loss
        position.update_pnl(49000)
        self.assertEqual(position.unrealized_pnl, -1.0)  # (49000 - 50000) * 0.001
        
        # Test short position
        short_position = Position("BTCUSDT", "short", 0.001, 50000)
        short_position.update_pnl(49000)
        self.assertEqual(short_position.unrealized_pnl, 1.0)  # (50000 - 49000) * 0.001
    
    def test_position_to_dict(self):
        """Test position serialization"""
        position = Position("BTCUSDT", "long", 0.001, 50000)
        position_dict = position.to_dict()
        
        required_fields = [
            'symbol', 'side', 'size', 'entry_price',
            'timestamp', 'unrealized_pnl', 'stop_loss', 'take_profit'
        ]
        
        for field in required_fields:
            self.assertIn(field, position_dict)

if __name__ == '__main__':
    unittest.main()