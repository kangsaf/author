"""
WhatsApp Notification Handler for kang_bot trading system
Using Twilio API for WhatsApp messaging
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests

from core.utils import get_jakarta_time, ConfigManager

class WhatsAppHandler:
    """
    Handler for WhatsApp notifications using Twilio
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize WhatsApp handler
        
        Args:
            config (dict): WhatsApp/Twilio configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Twilio configuration
        self.account_sid = self.config.get('twilio_account_sid', '')
        self.auth_token = self.config.get('twilio_auth_token', '')
        self.from_number = self.config.get('from_number', '')  # Twilio WhatsApp number
        self.to_number = self.config.get('to_number', '')     # Your WhatsApp number
        
        # API URL
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"
        
        # Notification settings
        self.enabled = self.config.get('enabled', False)
        self.send_signals = self.config.get('send_signals', True)
        self.send_trades = self.config.get('send_trades', True)
        self.send_errors = self.config.get('send_errors', True)
        self.send_reports = self.config.get('send_reports', False)  # Usually disabled for WhatsApp
        
        # Rate limiting
        self.last_message_time = 0
        self.min_message_interval = self.config.get('min_message_interval', 5)  # 5 seconds
        
        # Message settings
        self.include_timestamp = self.config.get('include_timestamp', True)
        self.max_message_length = 1600  # WhatsApp limit
        
        self.logger.info(f"WhatsApp handler initialized (enabled: {self.enabled})")
    
    def _format_message(self, message: str, message_type: str = 'info') -> str:
        """
        Format message with timestamp and type
        
        Args:
            message (str): Message content
            message_type (str): Message type
            
        Returns:
            str: Formatted message
        """
        try:
            # Add emoji based on message type
            emoji_map = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌',
                'success': '✅',
                'signal': '📊',
                'trade': '💰',
                'report': '📈'
            }
            
            emoji = emoji_map.get(message_type, 'ℹ️')
            
            # Add timestamp if enabled
            if self.include_timestamp:
                timestamp = get_jakarta_time().strftime('%H:%M WIB')
                formatted_message = f"{emoji} [{timestamp}] {message}"
            else:
                formatted_message = f"{emoji} {message}"
            
            # Truncate if too long
            if len(formatted_message) > self.max_message_length:
                formatted_message = formatted_message[:self.max_message_length-3] + "..."
            
            return formatted_message
            
        except Exception as e:
            self.logger.error(f"Error formatting message: {e}")
            return message
    
    def send_message(self, message: str, message_type: str = 'info') -> Dict:
        """
        Send message via WhatsApp
        
        Args:
            message (str): Message to send
            message_type (str): Type of message
            
        Returns:
            dict: Send result
        """
        try:
            if not self.enabled:
                return {'success': False, 'error': 'WhatsApp notifications disabled'}
            
            if not all([self.account_sid, self.auth_token, self.from_number, self.to_number]):
                return {'success': False, 'error': 'WhatsApp credentials not fully configured'}
            
            # Rate limiting
            current_time = datetime.now().timestamp()
            if current_time - self.last_message_time < self.min_message_interval:
                return {'success': False, 'error': 'Rate limit exceeded'}
            
            # Format message
            formatted_message = self._format_message(message, message_type)
            
            # Prepare request
            url = f"{self.base_url}/Messages.json"
            
            data = {
                'From': f"whatsapp:{self.from_number}",
                'To': f"whatsapp:{self.to_number}",
                'Body': formatted_message
            }
            
            # Send request with basic auth
            auth = (self.account_sid, self.auth_token)
            response = requests.post(url, data=data, auth=auth, timeout=15)
            
            self.last_message_time = current_time
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.logger.debug(f"WhatsApp message sent successfully: {message_type}")
                return {
                    'success': True,
                    'message_sid': result.get('sid'),
                    'status': result.get('status')
                }
            else:
                error_msg = f"HTTP error {response.status_code}: {response.text}"
                self.logger.error(error_msg)
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            self.logger.error(f"Error sending WhatsApp message: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_signal_notification(self, signal_data: Dict) -> Dict:
        """
        Send trading signal notification
        
        Args:
            signal_data (dict): Signal information
            
        Returns:
            dict: Send result
        """
        try:
            if not self.send_signals:
                return {'success': False, 'error': 'Signal notifications disabled'}
            
            # Extract signal information
            symbol = signal_data.get('symbol', 'UNKNOWN')
            signal_type = signal_data.get('signal_type', 'HOLD')
            score = signal_data.get('score', 0)
            confidence = signal_data.get('confidence', 'LOW')
            price = signal_data.get('price', 0)
            
            # Create concise message for WhatsApp
            message = f"""🎯 {symbol} Signal
{signal_type} | Score: {score}/100
Confidence: {confidence}
Price: ${price:.4f}

{signal_data.get('recommendation', 'No recommendation')}"""
            
            return self.send_message(message, 'signal')
            
        except Exception as e:
            self.logger.error(f"Error sending signal notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_trade_notification(self, trade_data: Dict) -> Dict:
        """
        Send trade execution notification
        
        Args:
            trade_data (dict): Trade information
            
        Returns:
            dict: Send result
        """
        try:
            if not self.send_trades:
                return {'success': False, 'error': 'Trade notifications disabled'}
            
            # Extract trade information
            symbol = trade_data.get('symbol', 'UNKNOWN')
            side = trade_data.get('side', 'UNKNOWN')
            size = trade_data.get('size', 0)
            price = trade_data.get('price', 0)
            status = trade_data.get('status', 'UNKNOWN')
            
            # Determine emoji based on side
            side_emoji = '🟢' if side.upper() == 'BUY' else '🔴'
            
            # Create concise message
            message = f"""{side_emoji} {symbol} Trade
{side.upper()} | Size: {size}
Price: ${price:.4f}
Value: ${size * price:.2f}
Status: {status}"""
            
            return self.send_message(message, 'trade')
            
        except Exception as e:
            self.logger.error(f"Error sending trade notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_error_notification(self, error_data: Dict) -> Dict:
        """
        Send error notification
        
        Args:
            error_data (dict): Error information
            
        Returns:
            dict: Send result
        """
        try:
            if not self.send_errors:
                return {'success': False, 'error': 'Error notifications disabled'}
            
            # Extract error information
            error_type = error_data.get('type', 'UNKNOWN_ERROR')
            error_message = error_data.get('message', 'No error message')
            module = error_data.get('module', 'Unknown')
            
            # Create concise message
            message = f"""❌ Error Alert
Module: {module}
Type: {error_type}
Message: {error_message}"""
            
            return self.send_message(message, 'error')
            
        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_daily_report(self, report_data: Dict) -> Dict:
        """
        Send daily trading report (if enabled)
        
        Args:
            report_data (dict): Report information
            
        Returns:
            dict: Send result
        """
        try:
            if not self.send_reports:
                return {'success': False, 'error': 'Report notifications disabled'}
            
            # Extract report information
            total_trades = report_data.get('total_trades', 0)
            winning_trades = report_data.get('winning_trades', 0)
            total_pnl = report_data.get('total_pnl', 0)
            win_rate = report_data.get('win_rate', 0)
            
            # Determine PnL emoji
            pnl_emoji = '📈' if total_pnl >= 0 else '📉'
            
            # Create concise message
            message = f"""📊 Daily Report
Date: {get_jakarta_time().strftime('%Y-%m-%d')}

Trades: {total_trades}
Wins: {winning_trades} ({win_rate:.1f}%)
{pnl_emoji} PnL: ${total_pnl:.2f}

Strategy: {report_data.get('active_strategy', 'Unknown')}"""
            
            return self.send_message(message, 'report')
            
        except Exception as e:
            self.logger.error(f"Error sending daily report: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_alert(self, alert_message: str, priority: str = 'normal') -> Dict:
        """
        Send urgent alert message
        
        Args:
            alert_message (str): Alert message
            priority (str): Alert priority (normal, high, critical)
            
        Returns:
            dict: Send result
        """
        try:
            # Add priority indicator
            priority_emoji = {
                'normal': '⚠️',
                'high': '🚨',
                'critical': '🔥'
            }
            
            emoji = priority_emoji.get(priority, '⚠️')
            message = f"{emoji} ALERT: {alert_message}"
            
            return self.send_message(message, 'warning')
            
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_connection(self) -> Dict:
        """
        Test WhatsApp connection by sending a test message
        
        Returns:
            dict: Connection test result
        """
        try:
            if not all([self.account_sid, self.auth_token, self.from_number, self.to_number]):
                return {'success': False, 'error': 'WhatsApp credentials not fully configured'}
            
            test_message = "🤖 KangBot WhatsApp connection test successful!"
            result = self.send_message(test_message, 'info')
            
            if result.get('success'):
                return {
                    'success': True,
                    'message': 'Test message sent successfully',
                    'message_sid': result.get('message_sid')
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_message_status(self, message_sid: str) -> Dict:
        """
        Get message delivery status
        
        Args:
            message_sid (str): Message SID from Twilio
            
        Returns:
            dict: Message status
        """
        try:
            if not self.account_sid or not self.auth_token:
                return {'error': 'Credentials not configured'}
            
            url = f"{self.base_url}/Messages/{message_sid}.json"
            auth = (self.account_sid, self.auth_token)
            
            response = requests.get(url, auth=auth, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            self.logger.error(f"Error getting message status: {e}")
            return {'error': str(e)}