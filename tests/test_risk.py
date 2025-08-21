"""
Unit tests for risk manager
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.risk_manager import RiskManager, RiskLevel

class TestRiskManager(unittest.TestCase):
    """Test cases for RiskManager"""
    
    def setUp(self):
        """Setup test environment"""
        self.config = {
            'max_risk_per_trade': 0.02,
            'max_daily_loss': 0.05,
            'max_total_exposure': 0.8,
            'max_positions': 5,
            'account_balance': 10000,
            'risk_level': 'moderate',
            'daily_trade_limit': 10,
            'position_size_limits': {
                'min_position_size': 0.001,
                'max_position_size': 0.1
            },
            'default_stop_loss_pct': 0.02
        }
        self.risk_manager = RiskManager(self.config)
    
    def test_initialization(self):
        """Test risk manager initialization"""
        self.assertEqual(self.risk_manager.max_risk_per_trade, 0.02)
        self.assertEqual(self.risk_manager.max_daily_loss, 0.05)
        self.assertEqual(self.risk_manager.account_balance, 10000)
        self.assertEqual(self.risk_manager.risk_level, RiskLevel.MODERATE)
        self.assertEqual(self.risk_manager.daily_trades, 0)
        self.assertEqual(self.risk_manager.daily_pnl, 0.0)
    
    def test_risk_level_adjustment(self):
        """Test risk level adjustment"""
        # Test conservative
        self.risk_manager.adjust_risk_level(RiskLevel.CONSERVATIVE)
        self.assertEqual(self.risk_manager.risk_level, RiskLevel.CONSERVATIVE)
        self.assertEqual(self.risk_manager.risk_multiplier, 0.5)
        
        # Test aggressive
        self.risk_manager.adjust_risk_level(RiskLevel.AGGRESSIVE)
        self.assertEqual(self.risk_manager.risk_level, RiskLevel.AGGRESSIVE)
        self.assertEqual(self.risk_manager.risk_multiplier, 1.5)
    
    def test_position_size_calculation(self):
        """Test position size calculation"""
        symbol = "BTCUSDT"
        entry_price = 50000
        stop_loss_price = 49000  # 2% stop loss
        
        position_size = self.risk_manager.calculate_position_size(
            symbol, entry_price, stop_loss_price
        )
        
        # Check that position size is reasonable
        self.assertGreater(position_size, 0)
        self.assertLessEqual(position_size, self.config['position_size_limits']['max_position_size'] * self.config['account_balance'] / entry_price)
        
        # Test with invalid prices
        invalid_size = self.risk_manager.calculate_position_size(symbol, 0, stop_loss_price)
        self.assertEqual(invalid_size, 0)
        
        invalid_size = self.risk_manager.calculate_position_size(symbol, entry_price, entry_price)
        self.assertEqual(invalid_size, 0)
    
    def test_trade_validation(self):
        """Test trade validation"""
        symbol = "BTCUSDT"
        side = "buy"
        size = 0.001
        price = 50000
        
        # Test valid trade
        is_valid = self.risk_manager.validate_trade(symbol, side, size, price)
        self.assertTrue(is_valid)
        
        # Test trade with size too small
        is_valid = self.risk_manager.validate_trade(symbol, side, 0.0001, price)
        self.assertFalse(is_valid)
        
        # Test trade exceeding daily limit
        self.risk_manager.daily_trades = self.config['daily_trade_limit']
        is_valid = self.risk_manager.validate_trade(symbol, side, size, price)
        self.assertFalse(is_valid)
        
        # Reset for next test
        self.risk_manager.daily_trades = 0
        
        # Test trade when daily loss limit reached
        self.risk_manager.daily_pnl = -self.config['max_daily_loss'] * self.config['account_balance'] - 1
        is_valid = self.risk_manager.validate_trade(symbol, side, size, price)
        self.assertFalse(is_valid)
    
    def test_stop_loss_calculation(self):
        """Test stop loss calculation"""
        symbol = "BTCUSDT"
        entry_price = 50000
        
        # Test buy order
        stop_loss_buy = self.risk_manager.calculate_stop_loss(symbol, entry_price, "buy")
        expected_stop_loss = entry_price * (1 - self.config['default_stop_loss_pct'])
        self.assertAlmostEqual(stop_loss_buy, expected_stop_loss, places=2)
        
        # Test sell order
        stop_loss_sell = self.risk_manager.calculate_stop_loss(symbol, entry_price, "sell")
        expected_stop_loss = entry_price * (1 + self.config['default_stop_loss_pct'])
        self.assertAlmostEqual(stop_loss_sell, expected_stop_loss, places=2)
        
        # Test with ATR
        atr = 1000
        stop_loss_atr = self.risk_manager.calculate_stop_loss(symbol, entry_price, "buy", atr)
        expected_stop_loss_atr = entry_price - (atr * 2)
        self.assertAlmostEqual(stop_loss_atr, expected_stop_loss_atr, places=2)
    
    def test_take_profit_calculation(self):
        """Test take profit calculation"""
        symbol = "BTCUSDT"
        entry_price = 50000
        risk_reward_ratio = 2.0
        
        # Test buy order
        take_profit_buy = self.risk_manager.calculate_take_profit(
            symbol, entry_price, "buy", risk_reward_ratio
        )
        
        # Calculate expected take profit
        stop_loss = self.risk_manager.calculate_stop_loss(symbol, entry_price, "buy")
        risk_amount = abs(entry_price - stop_loss)
        expected_take_profit = entry_price + (risk_amount * risk_reward_ratio)
        
        self.assertAlmostEqual(take_profit_buy, expected_take_profit, places=2)
        
        # Test sell order
        take_profit_sell = self.risk_manager.calculate_take_profit(
            symbol, entry_price, "sell", risk_reward_ratio
        )
        
        stop_loss = self.risk_manager.calculate_stop_loss(symbol, entry_price, "sell")
        risk_amount = abs(entry_price - stop_loss)
        expected_take_profit = entry_price - (risk_amount * risk_reward_ratio)
        
        self.assertAlmostEqual(take_profit_sell, expected_take_profit, places=2)
    
    def test_position_management(self):
        """Test position management"""
        symbol = "BTCUSDT"
        position_data = {
            'size': 0.001,
            'price': 50000,
            'side': 'long'
        }
        
        # Test position update
        self.risk_manager.update_position(symbol, position_data)
        self.assertIn(symbol, self.risk_manager.open_positions)
        self.assertEqual(self.risk_manager.open_positions[symbol], position_data)
        
        # Test position closing
        pnl = 100
        self.risk_manager.close_position(symbol, pnl)
        self.assertNotIn(symbol, self.risk_manager.open_positions)
        self.assertEqual(self.risk_manager.daily_pnl, pnl)
    
    def test_risk_limits_check(self):
        """Test risk limits checking"""
        # Test with normal conditions
        risk_status = self.risk_manager.check_risk_limits()
        self.assertEqual(risk_status['status'], 'SAFE')
        self.assertEqual(len(risk_status['violations']), 0)
        
        # Test with daily loss violation
        self.risk_manager.daily_pnl = -self.config['max_daily_loss'] * self.config['account_balance'] - 1
        risk_status = self.risk_manager.check_risk_limits()
        self.assertEqual(risk_status['status'], 'VIOLATION')
        self.assertGreater(len(risk_status['violations']), 0)
        
        # Reset for next test
        self.risk_manager.daily_pnl = 0
        
        # Test with position limit violation
        for i in range(self.config['max_positions'] + 1):
            self.risk_manager.open_positions[f"SYMBOL{i}"] = {'size': 0.001, 'price': 50000}
        
        risk_status = self.risk_manager.check_risk_limits()
        self.assertEqual(risk_status['status'], 'VIOLATION')
        
        # Test warning conditions
        self.risk_manager.open_positions.clear()
        self.risk_manager.daily_pnl = -self.config['max_daily_loss'] * self.config['account_balance'] * 0.9
        
        risk_status = self.risk_manager.check_risk_limits()
        self.assertEqual(risk_status['status'], 'WARNING')
        self.assertGreater(len(risk_status['warnings']), 0)
    
    def test_daily_counters_reset(self):
        """Test daily counters reset"""
        # Set some values
        self.risk_manager.daily_pnl = -500
        self.risk_manager.daily_trades = 5
        self.risk_manager.risk_violations = ['test violation']
        
        # Reset counters
        self.risk_manager.reset_daily_counters()
        
        # Check reset values
        self.assertEqual(self.risk_manager.daily_pnl, 0.0)
        self.assertEqual(self.risk_manager.daily_trades, 0)
        self.assertEqual(len(self.risk_manager.risk_violations), 0)
    
    def test_risk_report_generation(self):
        """Test risk report generation"""
        # Add some test data
        self.risk_manager.daily_pnl = 100
        self.risk_manager.daily_trades = 3
        self.risk_manager.open_positions['BTCUSDT'] = {'size': 0.001, 'price': 50000}
        
        report = self.risk_manager.get_risk_report()
        
        # Check report structure
        required_sections = ['risk_status', 'risk_parameters', 'current_metrics', 'position_details']
        for section in required_sections:
            self.assertIn(section, report)
        
        # Check current metrics
        metrics = report['current_metrics']
        self.assertEqual(metrics['daily_pnl'], 100)
        self.assertEqual(metrics['daily_trades'], 3)
        self.assertEqual(metrics['open_positions'], 1)
    
    def test_emergency_stop(self):
        """Test emergency stop functionality"""
        result = self.risk_manager.emergency_stop()
        
        self.assertTrue(result['success'])
        self.assertIn('emergency_record', result)
        self.assertEqual(len(self.risk_manager.risk_violations), 1)

if __name__ == '__main__':
    unittest.main()