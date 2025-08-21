"""
KangBot - Main Trading Bot Class
Koordinasi semua modul trading bot
"""
import logging
import asyncio
import signal
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import threading
import time

from core.utils import setup_logging, ConfigManager, get_jakarta_time
from core.strategy_manager import StrategyManager, StrategyType
from core.risk_manager import RiskManager
from core.ai_signal import AISignalGenerator

from handlers.binance_handler import BinanceHandler
from handlers.bybit_handler import BybitHandler
from handlers.telegram_handler import TelegramHandler
from handlers.whatsapp_handler import WhatsAppHandler

class KangBot:
    """
    Main trading bot class that coordinates all modules
    """
    
    def __init__(self, config_path: str = "/workspace/config"):
        """
        Initialize KangBot
        
        Args:
            config_path (str): Path to configuration directory
        """
        # Setup logging first
        setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config('config')
        
        # Bot state
        self.is_running = False
        self.is_trading_enabled = self.config.get('trading', {}).get('enabled', False)
        self.shutdown_requested = False
        
        # Initialize components
        self._initialize_components()
        
        # Trading loop
        self.trading_thread = None
        self.monitoring_thread = None
        
        # Performance tracking
        self.start_time = None
        self.last_signal_time = None
        self.total_cycles = 0
        
        self.logger.info("KangBot initialized successfully")
    
    def _initialize_components(self):
        """Initialize all bot components"""
        try:
            # Strategy Manager
            self.strategy_manager = StrategyManager(self.config_manager)
            
            # Risk Manager
            risk_config = self.config.get('risk_management', {})
            self.risk_manager = RiskManager(risk_config)
            
            # Exchange Handlers
            self.exchanges = {}
            self._initialize_exchanges()
            
            # Notification Handlers
            self.notifications = {}
            self._initialize_notifications()
            
            # Set default exchange
            default_exchange = self.config.get('exchanges', {}).get('default_exchange', 'binance')
            self.active_exchange = self.exchanges.get(default_exchange)
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            raise
    
    def _initialize_exchanges(self):
        """Initialize exchange handlers"""
        exchanges_config = self.config.get('exchanges', {})
        
        # Binance
        if exchanges_config.get('binance', {}).get('enabled', False):
            try:
                self.exchanges['binance'] = BinanceHandler(exchanges_config.get('binance', {}))
                self.logger.info("Binance handler initialized")
            except Exception as e:
                self.logger.error(f"Error initializing Binance handler: {e}")
        
        # Bybit
        if exchanges_config.get('bybit', {}).get('enabled', False):
            try:
                self.exchanges['bybit'] = BybitHandler(exchanges_config.get('bybit', {}))
                self.logger.info("Bybit handler initialized")
            except Exception as e:
                self.logger.error(f"Error initializing Bybit handler: {e}")
    
    def _initialize_notifications(self):
        """Initialize notification handlers"""
        notifications_config = self.config.get('notifications', {})
        
        # Telegram
        if notifications_config.get('telegram', {}).get('enabled', False):
            try:
                self.notifications['telegram'] = TelegramHandler(notifications_config.get('telegram', {}))
                self.logger.info("Telegram handler initialized")
            except Exception as e:
                self.logger.error(f"Error initializing Telegram handler: {e}")
        
        # WhatsApp
        if notifications_config.get('whatsapp', {}).get('enabled', False):
            try:
                self.notifications['whatsapp'] = WhatsAppHandler(notifications_config.get('whatsapp', {}))
                self.logger.info("WhatsApp handler initialized")
            except Exception as e:
                self.logger.error(f"Error initializing WhatsApp handler: {e}")
    
    def start(self):
        """Start the trading bot"""
        try:
            if self.is_running:
                self.logger.warning("Bot is already running")
                return False
            
            self.is_running = True
            self.start_time = get_jakarta_time()
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Send startup notification
            self._send_notification(
                f"🚀 KangBot started successfully!\nStrategy: {self.strategy_manager.active_strategy.value}\nTrading: {'Enabled' if self.is_trading_enabled else 'Disabled'}",
                'success'
            )
            
            # Start threads
            self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            
            self.trading_thread.start()
            self.monitoring_thread.start()
            
            self.logger.info("KangBot started successfully")
            
            # Keep main thread alive
            try:
                while self.is_running and not self.shutdown_requested:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting bot: {e}")
            self._send_notification(f"❌ Error starting KangBot: {e}", 'error')
            return False
    
    def stop(self):
        """Stop the trading bot"""
        try:
            self.logger.info("Stopping KangBot...")
            self.is_running = False
            self.shutdown_requested = True
            
            # Close all positions if trading is enabled
            if self.is_trading_enabled:
                self.strategy_manager.close_all_positions()
            
            # Wait for threads to finish
            if self.trading_thread and self.trading_thread.is_alive():
                self.trading_thread.join(timeout=5)
            
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            
            # Send shutdown notification
            uptime = get_jakarta_time() - self.start_time if self.start_time else timedelta(0)
            self._send_notification(
                f"🛑 KangBot stopped\nUptime: {uptime}\nTotal cycles: {self.total_cycles}",
                'info'
            )
            
            self.logger.info("KangBot stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping bot: {e}")
            return False
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown_requested = True
    
    def _trading_loop(self):
        """Main trading loop"""
        self.logger.info("Trading loop started")
        
        while self.is_running and not self.shutdown_requested:
            try:
                cycle_start = time.time()
                
                # Get trading symbols
                symbols = self._get_trading_symbols()
                
                for symbol in symbols:
                    if self.shutdown_requested:
                        break
                    
                    # Analyze market
                    analysis = self.strategy_manager.analyze_market(symbol)
                    
                    if 'error' not in analysis:
                        # Process trading signal
                        self._process_trading_signal(symbol, analysis)
                    else:
                        self.logger.error(f"Error analyzing {symbol}: {analysis['error']}")
                
                # Update performance metrics
                self.total_cycles += 1
                self.last_signal_time = get_jakarta_time()
                
                # Sleep until next cycle (avoid too frequent calls)
                cycle_time = time.time() - cycle_start
                sleep_time = max(0, 60 - cycle_time)  # 1-minute cycles
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                self._send_notification(f"❌ Trading loop error: {e}", 'error')
                time.sleep(60)  # Wait before retrying
        
        self.logger.info("Trading loop stopped")
    
    def _monitoring_loop(self):
        """Monitoring and maintenance loop"""
        self.logger.info("Monitoring loop started")
        
        while self.is_running and not self.shutdown_requested:
            try:
                # Check risk limits
                risk_status = self.risk_manager.check_risk_limits()
                
                if risk_status.get('status') == 'VIOLATION':
                    self.logger.warning("Risk violation detected!")
                    self._send_notification(
                        f"⚠️ Risk Violation!\n{', '.join(risk_status.get('violations', []))}",
                        'warning'
                    )
                    # Disable trading temporarily
                    self.is_trading_enabled = False
                
                # Send periodic status updates (every hour)
                if self.total_cycles % 60 == 0 and self.total_cycles > 0:
                    self._send_status_update()
                
                # Daily report (at configured time)
                current_time = get_jakarta_time()
                if current_time.hour == 0 and current_time.minute < 5:  # Near midnight
                    self._send_daily_report()
                    self.risk_manager.reset_daily_counters()
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)
        
        self.logger.info("Monitoring loop stopped")
    
    def _get_trading_symbols(self) -> List[str]:
        """Get list of symbols to trade"""
        try:
            default_symbol = self.config.get('trading', {}).get('default_symbol', 'BTCUSDT')
            
            # For now, return default symbol
            # In future, this could be dynamic based on market conditions
            return [default_symbol]
            
        except Exception as e:
            self.logger.error(f"Error getting trading symbols: {e}")
            return ['BTCUSDT']
    
    def _process_trading_signal(self, symbol: str, analysis: Dict):
        """Process trading signal and execute trades if needed"""
        try:
            signal = analysis.get('signal', {})
            recommendation = analysis.get('strategy_recommendation', {})
            
            # Send signal notification
            if self.notifications:
                signal_data = {
                    'symbol': symbol,
                    'signal_type': signal.get('signal_type', 'HOLD'),
                    'score': signal.get('score', 50),
                    'confidence': signal.get('confidence', 'LOW'),
                    'price': signal.get('price', 0),
                    'recommendation': recommendation.get('reason', 'No recommendation')
                }
                
                self._send_signal_notification(signal_data)
            
            # Execute trade if trading is enabled and recommendation is strong
            if self.is_trading_enabled and recommendation.get('action') in ['BUY', 'SELL']:
                confidence = recommendation.get('confidence', 'LOW')
                
                if confidence in ['MEDIUM', 'HIGH']:
                    self._execute_trade(symbol, recommendation)
            
        except Exception as e:
            self.logger.error(f"Error processing trading signal: {e}")
    
    def _execute_trade(self, symbol: str, recommendation: Dict):
        """Execute trade based on recommendation"""
        try:
            if not self.active_exchange:
                self.logger.error("No active exchange configured")
                return
            
            action = recommendation.get('action')
            position_size = recommendation.get('position_size', 0)
            entry_price = recommendation.get('entry_price')
            
            if position_size <= 0:
                self.logger.info(f"Position size too small for {symbol}: {position_size}")
                return
            
            # Execute the trade
            result = self.strategy_manager.execute_trade(
                symbol=symbol,
                action=action,
                size=position_size,
                price=entry_price
            )
            
            if result.get('success'):
                self.logger.info(f"Trade executed successfully: {result}")
                
                # Send trade notification
                if self.notifications:
                    trade_data = result.get('order', {})
                    trade_data['symbol'] = symbol
                    self._send_trade_notification(trade_data)
            else:
                self.logger.error(f"Trade execution failed: {result.get('error')}")
                
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
    
    def _send_notification(self, message: str, message_type: str = 'info'):
        """Send notification to all enabled channels"""
        for name, handler in self.notifications.items():
            try:
                handler.send_message(message, message_type)
            except Exception as e:
                self.logger.error(f"Error sending {name} notification: {e}")
    
    def _send_signal_notification(self, signal_data: Dict):
        """Send signal notification"""
        for name, handler in self.notifications.items():
            try:
                handler.send_signal_notification(signal_data)
            except Exception as e:
                self.logger.error(f"Error sending {name} signal notification: {e}")
    
    def _send_trade_notification(self, trade_data: Dict):
        """Send trade notification"""
        for name, handler in self.notifications.items():
            try:
                handler.send_trade_notification(trade_data)
            except Exception as e:
                self.logger.error(f"Error sending {name} trade notification: {e}")
    
    def _send_status_update(self):
        """Send periodic status update"""
        try:
            portfolio = self.strategy_manager.get_portfolio_status()
            risk_status = self.risk_manager.check_risk_limits()
            
            uptime = get_jakarta_time() - self.start_time if self.start_time else timedelta(0)
            
            message = f"""📊 KangBot Status Update
            
⏰ Uptime: {uptime}
🔄 Cycles: {self.total_cycles}
📈 Strategy: {portfolio.get('active_strategy', 'Unknown')}
💰 Positions: {portfolio.get('total_positions', 0)}
🎯 Win Rate: {portfolio.get('win_rate', 0)}%
💵 Total PnL: ${portfolio.get('total_realized_pnl', 0):.2f}
⚠️ Risk Status: {risk_status.get('status', 'Unknown')}"""
            
            self._send_notification(message, 'info')
            
        except Exception as e:
            self.logger.error(f"Error sending status update: {e}")
    
    def _send_daily_report(self):
        """Send daily trading report"""
        try:
            portfolio = self.strategy_manager.get_portfolio_status()
            
            report_data = {
                'total_trades': portfolio.get('total_trades', 0),
                'winning_trades': portfolio.get('winning_trades', 0),
                'win_rate': portfolio.get('win_rate', 0),
                'total_pnl': portfolio.get('total_realized_pnl', 0),
                'active_positions': portfolio.get('total_positions', 0),
                'account_balance': self.risk_manager.account_balance,
                'active_strategy': portfolio.get('active_strategy', 'Unknown')
            }
            
            for name, handler in self.notifications.items():
                try:
                    handler.send_daily_report(report_data)
                except Exception as e:
                    self.logger.error(f"Error sending {name} daily report: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error sending daily report: {e}")
    
    def get_status(self) -> Dict:
        """Get current bot status"""
        try:
            uptime = get_jakarta_time() - self.start_time if self.start_time else timedelta(0)
            
            return {
                'is_running': self.is_running,
                'is_trading_enabled': self.is_trading_enabled,
                'uptime': str(uptime),
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'total_cycles': self.total_cycles,
                'last_signal_time': self.last_signal_time.isoformat() if self.last_signal_time else None,
                'active_exchange': list(self.exchanges.keys())[0] if self.exchanges else None,
                'active_notifications': list(self.notifications.keys()),
                'portfolio': self.strategy_manager.get_portfolio_status(),
                'risk_status': self.risk_manager.check_risk_limits()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {'error': str(e)}
    
    def enable_trading(self):
        """Enable trading"""
        self.is_trading_enabled = True
        self.strategy_manager.enable_trading()
        self._send_notification("✅ Trading enabled", 'success')
        self.logger.info("Trading enabled")
    
    def disable_trading(self):
        """Disable trading"""
        self.is_trading_enabled = False
        self.strategy_manager.disable_trading()
        self._send_notification("⏸️ Trading disabled", 'warning')
        self.logger.info("Trading disabled")
    
    def change_strategy(self, strategy_name: str):
        """Change active trading strategy"""
        try:
            strategy_type = StrategyType(strategy_name)
            if self.strategy_manager.set_strategy(strategy_type):
                self._send_notification(f"🔄 Strategy changed to: {strategy_name}", 'info')
                return True
            return False
        except ValueError:
            self.logger.error(f"Invalid strategy: {strategy_name}")
            return False
    
    def test_connections(self) -> Dict:
        """Test all connections"""
        results = {}
        
        # Test exchanges
        for name, handler in self.exchanges.items():
            results[f"exchange_{name}"] = handler.test_connectivity()
        
        # Test notifications
        for name, handler in self.notifications.items():
            results[f"notification_{name}"] = handler.test_connection()
        
        return results