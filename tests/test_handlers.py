"""
Unit tests for exchange and notification handlers
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import requests

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from handlers.binance_handler import BinanceHandler
from handlers.bybit_handler import BybitHandler
from handlers.telegram_handler import TelegramHandler
from handlers.whatsapp_handler import WhatsAppHandler

class TestBinanceHandler(unittest.TestCase):
    """Test cases for BinanceHandler"""
    
    def setUp(self):
        """Setup test environment"""
        self.config = {
            'api_key': 'test_key',
            'api_secret': 'test_secret',
            'testnet': True,
            'timeout': 10
        }
        self.handler = BinanceHandler(self.config)
    
    def test_initialization(self):
        """Test handler initialization"""
        self.assertEqual(self.handler.api_key, 'test_key')
        self.assertEqual(self.handler.api_secret, 'test_secret')
        self.assertTrue(self.handler.testnet)
        self.assertEqual(self.handler.base_url, 'https://testnet.binance.vision')
    
    def test_signature_generation(self):
        """Test HMAC signature generation"""
        query_string = "symbol=BTCUSDT&side=BUY&type=LIMIT&quantity=1&price=50000&timestamp=1234567890"
        signature = self.handler._generate_signature(query_string)
        
        self.assertIsInstance(signature, str)
        self.assertEqual(len(signature), 64)  # SHA256 hex string length
    
    @patch('requests.get')
    def test_get_server_time(self, mock_get):
        """Test server time retrieval"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'serverTime': 1234567890}
        mock_get.return_value = mock_response
        
        result = self.handler.get_server_time()
        
        self.assertEqual(result['serverTime'], 1234567890)
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_get_ticker_price(self, mock_get):
        """Test ticker price retrieval"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'symbol': 'BTCUSDT',
            'price': '50000.00'
        }
        mock_get.return_value = mock_response
        
        result = self.handler.get_ticker_price('BTCUSDT')
        
        self.assertEqual(result['symbol'], 'BTCUSDT')
        self.assertEqual(result['price'], '50000.00')
    
    @patch('requests.get')
    def test_get_klines(self, mock_get):
        """Test klines data retrieval"""
        # Mock successful response with sample kline data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            [1234567890, '50000', '51000', '49000', '50500', '100', 1234567950, '5000000', 100, '50', '2500000', '0']
        ]
        mock_get.return_value = mock_response
        
        result = self.handler.get_klines('BTCUSDT', '1h', 1)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), 12)  # Standard kline data length
    
    def test_get_ohlcv_data(self):
        """Test OHLCV DataFrame creation"""
        with patch.object(self.handler, 'get_klines') as mock_get_klines:
            # Mock klines data
            mock_get_klines.return_value = [
                [1234567890, '50000', '51000', '49000', '50500', '100', 1234567950, '5000000', 100, '50', '2500000', '0'],
                [1234567950, '50500', '51500', '49500', '51000', '150', 1234568010, '7500000', 150, '75', '3750000', '0']
            ]
            
            df = self.handler.get_ohlcv_data('BTCUSDT', '1h', 2)
            
            # Check DataFrame structure
            self.assertEqual(len(df), 2)
            expected_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            for col in expected_columns:
                self.assertIn(col, df.columns)
            
            # Check data types
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                self.assertTrue(df[col].dtype in ['float64', 'int64'])
    
    def test_test_connectivity(self):
        """Test connectivity testing"""
        with patch.object(self.handler, 'get_server_time') as mock_server_time:
            with patch.object(self.handler, 'get_account_info') as mock_account_info:
                # Test successful connection
                mock_server_time.return_value = {'serverTime': 1234567890}
                mock_account_info.return_value = {'accountType': 'SPOT'}
                
                result = self.handler.test_connectivity()
                
                self.assertEqual(result['status'], 'ok')
                self.assertEqual(result['public'], 'ok')
                self.assertEqual(result['private'], 'ok')

class TestBybitHandler(unittest.TestCase):
    """Test cases for BybitHandler"""
    
    def setUp(self):
        """Setup test environment"""
        self.config = {
            'api_key': 'test_key',
            'api_secret': 'test_secret',
            'testnet': True
        }
        self.handler = BybitHandler(self.config)
    
    def test_initialization(self):
        """Test handler initialization"""
        self.assertEqual(self.handler.api_key, 'test_key')
        self.assertEqual(self.handler.api_secret, 'test_secret')
        self.assertTrue(self.handler.testnet)
        self.assertEqual(self.handler.base_url, 'https://api-testnet.bybit.com')
    
    def test_signature_generation(self):
        """Test signature generation"""
        timestamp = "1234567890"
        params = "symbol=BTCUSDT&side=Buy"
        
        signature = self.handler._generate_signature(timestamp, params)
        
        self.assertIsInstance(signature, str)
        self.assertEqual(len(signature), 64)  # SHA256 hex string length

class TestTelegramHandler(unittest.TestCase):
    """Test cases for TelegramHandler"""
    
    def setUp(self):
        """Setup test environment"""
        self.config = {
            'bot_token': 'test_token',
            'chat_id': 'test_chat_id',
            'enabled': True,
            'use_markdown': True
        }
        self.handler = TelegramHandler(self.config)
    
    def test_initialization(self):
        """Test handler initialization"""
        self.assertEqual(self.handler.bot_token, 'test_token')
        self.assertEqual(self.handler.chat_id, 'test_chat_id')
        self.assertTrue(self.handler.enabled)
        self.assertTrue(self.handler.use_markdown)
    
    def test_message_formatting(self):
        """Test message formatting"""
        message = "Test message"
        
        # Test with timestamp
        formatted = self.handler._format_message(message, 'info')
        self.assertIn('ℹ️', formatted)
        self.assertIn(message, formatted)
        
        # Test different message types
        types_and_emojis = {
            'warning': '⚠️',
            'error': '❌',
            'success': '✅',
            'signal': '📊',
            'trade': '💰'
        }
        
        for msg_type, emoji in types_and_emojis.items():
            formatted = self.handler._format_message(message, msg_type)
            self.assertIn(emoji, formatted)
    
    @patch('requests.post')
    def test_send_message(self, mock_post):
        """Test message sending"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': {'message_id': 123}
        }
        mock_post.return_value = mock_response
        
        result = self.handler.send_message("Test message", 'info')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message_id'], 123)
        mock_post.assert_called_once()
    
    def test_signal_notification(self):
        """Test signal notification formatting"""
        signal_data = {
            'symbol': 'BTCUSDT',
            'signal_type': 'BUY',
            'score': 75,
            'confidence': 'HIGH',
            'price': 50000,
            'recommendation': 'Strong buy signal'
        }
        
        with patch.object(self.handler, 'send_message') as mock_send:
            mock_send.return_value = {'success': True}
            
            result = self.handler.send_signal_notification(signal_data)
            
            self.assertTrue(result['success'])
            mock_send.assert_called_once()
            
            # Check that the message contains key information
            call_args = mock_send.call_args[0]
            message = call_args[0]
            self.assertIn('BTCUSDT', message)
            self.assertIn('BUY', message)
            self.assertIn('75', message)

class TestWhatsAppHandler(unittest.TestCase):
    """Test cases for WhatsAppHandler"""
    
    def setUp(self):
        """Setup test environment"""
        self.config = {
            'twilio_account_sid': 'test_sid',
            'twilio_auth_token': 'test_token',
            'from_number': '+1234567890',
            'to_number': '+0987654321',
            'enabled': True
        }
        self.handler = WhatsAppHandler(self.config)
    
    def test_initialization(self):
        """Test handler initialization"""
        self.assertEqual(self.handler.account_sid, 'test_sid')
        self.assertEqual(self.handler.auth_token, 'test_token')
        self.assertEqual(self.handler.from_number, '+1234567890')
        self.assertEqual(self.handler.to_number, '+0987654321')
        self.assertTrue(self.handler.enabled)
    
    def test_message_formatting(self):
        """Test message formatting"""
        message = "Test message"
        
        formatted = self.handler._format_message(message, 'info')
        self.assertIn('ℹ️', formatted)
        self.assertIn(message, formatted)
        
        # Test message length limit
        long_message = "x" * 2000
        formatted_long = self.handler._format_message(long_message, 'info')
        self.assertLessEqual(len(formatted_long), self.handler.max_message_length)
    
    @patch('requests.post')
    def test_send_message(self, mock_post):
        """Test message sending"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'sid': 'test_message_sid',
            'status': 'queued'
        }
        mock_post.return_value = mock_response
        
        result = self.handler.send_message("Test message", 'info')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message_sid'], 'test_message_sid')
        mock_post.assert_called_once()

if __name__ == '__main__':
    unittest.main()