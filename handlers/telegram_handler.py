"""
Telegram Notification Handler for kang_bot trading system
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
import requests
from datetime import datetime

from core.utils import get_jakarta_time, ConfigManager

class TelegramHandler:
    """
    Handler for Telegram notifications
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize Telegram handler
        
        Args:
            config (dict): Telegram configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Bot configuration
        self.bot_token = self.config.get('bot_token', '')
        self.chat_id = self.config.get('chat_id', '')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Notification settings
        self.enabled = self.config.get('enabled', False)
        self.send_signals = self.config.get('send_signals', True)
        self.send_trades = self.config.get('send_trades', True)
        self.send_errors = self.config.get('send_errors', True)
        self.send_reports = self.config.get('send_reports', True)
        
        # Rate limiting
        self.last_message_time = 0
        self.min_message_interval = self.config.get('min_message_interval', 1)  # seconds
        
        # Message formatting
        self.use_markdown = self.config.get('use_markdown', True)
        self.include_timestamp = self.config.get('include_timestamp', True)
        
        self.logger.info(f"Telegram handler initialized (enabled: {self.enabled})")
    
    def _format_message(self, message: str, message_type: str = 'info') -> str:
        """
        Format message with timestamp and type
        
        Args:
            message (str): Message content
            message_type (str): Message type (info, warning, error, success)
            
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
                timestamp = get_jakarta_time().strftime('%H:%M:%S WIB')
                formatted_message = f"{emoji} [{timestamp}] {message}"
            else:
                formatted_message = f"{emoji} {message}"
            
            return formatted_message
            
        except Exception as e:
            self.logger.error(f"Error formatting message: {e}")
            return message
    
    def send_message(self, message: str, message_type: str = 'info', 
                    chat_id: str = None, disable_notification: bool = False) -> Dict:
        """
        Send message to Telegram
        
        Args:
            message (str): Message to send
            message_type (str): Type of message
            chat_id (str): Override default chat ID
            disable_notification (bool): Send silently
            
        Returns:
            dict: Send result
        """
        try:
            if not self.enabled:
                return {'success': False, 'error': 'Telegram notifications disabled'}
            
            if not self.bot_token or not self.chat_id:
                return {'success': False, 'error': 'Telegram credentials not configured'}
            
            # Rate limiting
            current_time = datetime.now().timestamp()
            if current_time - self.last_message_time < self.min_message_interval:
                return {'success': False, 'error': 'Rate limit exceeded'}
            
            # Format message
            formatted_message = self._format_message(message, message_type)
            
            # Prepare request
            target_chat_id = chat_id or self.chat_id
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                'chat_id': target_chat_id,
                'text': formatted_message,
                'disable_notification': disable_notification
            }
            
            if self.use_markdown:
                payload['parse_mode'] = 'Markdown'
            
            # Send request
            response = requests.post(url, json=payload, timeout=10)
            self.last_message_time = current_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    self.logger.debug(f"Message sent successfully: {message_type}")
                    return {'success': True, 'message_id': result.get('result', {}).get('message_id')}
                else:
                    error_msg = result.get('description', 'Unknown error')
                    self.logger.error(f"Telegram API error: {error_msg}")
                    return {'success': False, 'error': error_msg}
            else:
                error_msg = f"HTTP error {response.status_code}: {response.text}"
                self.logger.error(error_msg)
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
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
            
            # Create message
            if self.use_markdown:
                message = f"""
*🎯 Trading Signal - {symbol}*

📊 *Signal:* {signal_type}
📈 *Score:* {score}/100
🎯 *Confidence:* {confidence}
💰 *Price:* ${price:.4f}

*Recommendation:* {signal_data.get('recommendation', 'No specific recommendation')}
"""
            else:
                message = f"""
🎯 Trading Signal - {symbol}

📊 Signal: {signal_type}
📈 Score: {score}/100
🎯 Confidence: {confidence}
💰 Price: ${price:.4f}

Recommendation: {signal_data.get('recommendation', 'No specific recommendation')}
"""
            
            return self.send_message(message.strip(), 'signal')
            
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
            order_type = trade_data.get('type', 'MARKET')
            status = trade_data.get('status', 'UNKNOWN')
            
            # Determine emoji based on side
            side_emoji = '🟢' if side.upper() == 'BUY' else '🔴'
            
            # Create message
            if self.use_markdown:
                message = f"""
*{side_emoji} Trade Executed - {symbol}*

📝 *Order ID:* {trade_data.get('order_id', 'N/A')}
🔄 *Side:* {side.upper()}
📊 *Type:* {order_type}
💎 *Size:* {size}
💰 *Price:* ${price:.4f}
✅ *Status:* {status}
💵 *Value:* ${size * price:.2f}
"""
            else:
                message = f"""
{side_emoji} Trade Executed - {symbol}

📝 Order ID: {trade_data.get('order_id', 'N/A')}
🔄 Side: {side.upper()}
📊 Type: {order_type}
💎 Size: {size}
💰 Price: ${price:.4f}
✅ Status: {status}
💵 Value: ${size * price:.2f}
"""
            
            return self.send_message(message.strip(), 'trade')
            
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
            error_message = error_data.get('message', 'No error message provided')
            module = error_data.get('module', 'Unknown')
            
            # Create message
            if self.use_markdown:
                message = f"""
*❌ Error Alert*

🔧 *Module:* {module}
⚠️ *Type:* {error_type}
📝 *Message:* {error_message}

*Time:* {get_jakarta_time().strftime('%Y-%m-%d %H:%M:%S WIB')}
"""
            else:
                message = f"""
❌ Error Alert

🔧 Module: {module}
⚠️ Type: {error_type}
📝 Message: {error_message}

Time: {get_jakarta_time().strftime('%Y-%m-%d %H:%M:%S WIB')}
"""
            
            return self.send_message(message.strip(), 'error')
            
        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_daily_report(self, report_data: Dict) -> Dict:
        """
        Send daily trading report
        
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
            active_positions = report_data.get('active_positions', 0)
            
            # Determine PnL emoji
            pnl_emoji = '📈' if total_pnl >= 0 else '📉'
            
            # Create message
            if self.use_markdown:
                message = f"""
*📊 Daily Trading Report*

📅 *Date:* {get_jakarta_time().strftime('%Y-%m-%d')}

📈 *Performance:*
• Total Trades: {total_trades}
• Winning Trades: {winning_trades}
• Win Rate: {win_rate:.1f}%
• {pnl_emoji} Total PnL: ${total_pnl:.2f}

📊 *Portfolio:*
• Active Positions: {active_positions}
• Account Balance: ${report_data.get('account_balance', 0):.2f}

*Strategy:* {report_data.get('active_strategy', 'Unknown')}
"""
            else:
                message = f"""
📊 Daily Trading Report

📅 Date: {get_jakarta_time().strftime('%Y-%m-%d')}

📈 Performance:
• Total Trades: {total_trades}
• Winning Trades: {winning_trades}
• Win Rate: {win_rate:.1f}%
• {pnl_emoji} Total PnL: ${total_pnl:.2f}

📊 Portfolio:
• Active Positions: {active_positions}
• Account Balance: ${report_data.get('account_balance', 0):.2f}

Strategy: {report_data.get('active_strategy', 'Unknown')}
"""
            
            return self.send_message(message.strip(), 'report')
            
        except Exception as e:
            self.logger.error(f"Error sending daily report: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_custom_message(self, message: str, parse_mode: str = None) -> Dict:
        """
        Send custom formatted message
        
        Args:
            message (str): Custom message
            parse_mode (str): Parse mode (Markdown, HTML)
            
        Returns:
            dict: Send result
        """
        try:
            if not self.enabled:
                return {'success': False, 'error': 'Telegram notifications disabled'}
            
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                'chat_id': self.chat_id,
                'text': message
            }
            
            if parse_mode:
                payload['parse_mode'] = parse_mode
            elif self.use_markdown:
                payload['parse_mode'] = 'Markdown'
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return {'success': True, 'message_id': result.get('result', {}).get('message_id')}
                else:
                    return {'success': False, 'error': result.get('description')}
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.logger.error(f"Error sending custom message: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_connection(self) -> Dict:
        """
        Test Telegram bot connection
        
        Returns:
            dict: Connection test result
        """
        try:
            if not self.bot_token:
                return {'success': False, 'error': 'Bot token not configured'}
            
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    bot_info = result.get('result', {})
                    return {
                        'success': True,
                        'bot_info': {
                            'id': bot_info.get('id'),
                            'username': bot_info.get('username'),
                            'first_name': bot_info.get('first_name')
                        }
                    }
                else:
                    return {'success': False, 'error': result.get('description')}
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return {'success': False, 'error': str(e)}

# Convenience functions for backward compatibility
def telegram_send_direct(message: str, config: Dict = None) -> bool:
    """
    Direct function to send Telegram message (for backward compatibility)
    
    Args:
        message (str): Message to send
        config (dict): Telegram configuration
        
    Returns:
        bool: True if successful
    """
    try:
        handler = TelegramHandler(config)
        result = handler.send_message(message)
        return result.get('success', False)
    except Exception:
        return False