"""
Binance Exchange Handler for kang_bot trading system
"""
import logging
import hashlib
import hmac
import time
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd

from core.utils import get_jakarta_time, safe_float, ConfigManager

class BinanceHandler:
    """
    Handler for Binance exchange operations
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize Binance handler
        
        Args:
            config (dict): Binance configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # API configuration
        self.api_key = self.config.get('api_key', '')
        self.api_secret = self.config.get('api_secret', '')
        self.base_url = self.config.get('base_url', 'https://api.binance.com')
        self.testnet = self.config.get('testnet', True)
        
        if self.testnet:
            self.base_url = 'https://testnet.binance.vision'
        
        # Request settings
        self.timeout = self.config.get('timeout', 10)
        self.recv_window = self.config.get('recv_window', 5000)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        self.logger.info(f"Binance handler initialized (testnet: {self.testnet})")
    
    def _generate_signature(self, query_string: str) -> str:
        """
        Generate HMAC SHA256 signature for API requests
        
        Args:
            query_string (str): Query string to sign
            
        Returns:
            str: HMAC signature
        """
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                     signed: bool = False) -> Dict:
        """
        Make HTTP request to Binance API
        
        Args:
            method (str): HTTP method
            endpoint (str): API endpoint
            params (dict): Request parameters
            signed (bool): Whether request needs signature
            
        Returns:
            dict: API response
        """
        try:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.min_request_interval:
                time.sleep(self.min_request_interval)
            
            url = f"{self.base_url}{endpoint}"
            headers = {}
            
            if params is None:
                params = {}
            
            # Add API key to headers if available
            if self.api_key:
                headers['X-MBX-APIKEY'] = self.api_key
            
            # Add signature for signed requests
            if signed:
                params['timestamp'] = int(time.time() * 1000)
                params['recvWindow'] = self.recv_window
                
                query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                signature = self._generate_signature(query_string)
                params['signature'] = signature
            
            # Make request
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, data=params, headers=headers, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            self.last_request_time = time.time()
            
            # Check response
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"API error {response.status_code}: {response.text}"
                self.logger.error(error_msg)
                return {'error': error_msg}
                
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return {'error': str(e)}
    
    def get_server_time(self) -> Dict:
        """
        Get Binance server time
        
        Returns:
            dict: Server time information
        """
        return self._make_request('GET', '/api/v3/time')
    
    def get_exchange_info(self, symbol: str = None) -> Dict:
        """
        Get exchange information
        
        Args:
            symbol (str): Specific symbol to get info for
            
        Returns:
            dict: Exchange information
        """
        params = {}
        if symbol:
            params['symbol'] = symbol.upper()
        
        return self._make_request('GET', '/api/v3/exchangeInfo', params)
    
    def get_ticker_price(self, symbol: str) -> Dict:
        """
        Get current ticker price
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            dict: Ticker price information
        """
        params = {'symbol': symbol.upper()}
        return self._make_request('GET', '/api/v3/ticker/price', params)
    
    def get_ticker_24hr(self, symbol: str) -> Dict:
        """
        Get 24hr ticker statistics
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            dict: 24hr ticker statistics
        """
        params = {'symbol': symbol.upper()}
        return self._make_request('GET', '/api/v3/ticker/24hr', params)
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100, 
                  start_time: int = None, end_time: int = None) -> List[List]:
        """
        Get kline/candlestick data
        
        Args:
            symbol (str): Trading symbol
            interval (str): Kline interval
            limit (int): Number of klines to retrieve
            start_time (int): Start time in milliseconds
            end_time (int): End time in milliseconds
            
        Returns:
            list: Kline data
        """
        params = {
            'symbol': symbol.upper(),
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        return self._make_request('GET', '/api/v3/klines', params)
    
    def get_ohlcv_data(self, symbol: str, interval: str = '1h', limit: int = 100) -> pd.DataFrame:
        """
        Get OHLCV data as pandas DataFrame
        
        Args:
            symbol (str): Trading symbol
            interval (str): Timeframe
            limit (int): Number of candles
            
        Returns:
            pd.DataFrame: OHLCV data
        """
        try:
            klines = self.get_klines(symbol, interval, limit)
            
            if 'error' in klines:
                self.logger.error(f"Error getting klines: {klines['error']}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert data types
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            # Convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Select relevant columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error processing OHLCV data: {e}")
            return pd.DataFrame()
    
    def get_account_info(self) -> Dict:
        """
        Get account information
        
        Returns:
            dict: Account information
        """
        if not self.api_key or not self.api_secret:
            return {'error': 'API credentials not configured'}
        
        return self._make_request('GET', '/api/v3/account', signed=True)
    
    def get_balance(self, asset: str = None) -> Dict:
        """
        Get account balance
        
        Args:
            asset (str): Specific asset to get balance for
            
        Returns:
            dict: Balance information
        """
        try:
            account_info = self.get_account_info()
            
            if 'error' in account_info:
                return account_info
            
            balances = account_info.get('balances', [])
            
            if asset:
                for balance in balances:
                    if balance['asset'] == asset.upper():
                        return {
                            'asset': balance['asset'],
                            'free': safe_float(balance['free']),
                            'locked': safe_float(balance['locked']),
                            'total': safe_float(balance['free']) + safe_float(balance['locked'])
                        }
                return {'error': f'Asset {asset} not found'}
            
            # Return all non-zero balances
            non_zero_balances = []
            for balance in balances:
                total = safe_float(balance['free']) + safe_float(balance['locked'])
                if total > 0:
                    non_zero_balances.append({
                        'asset': balance['asset'],
                        'free': safe_float(balance['free']),
                        'locked': safe_float(balance['locked']),
                        'total': total
                    })
            
            return {'balances': non_zero_balances}
            
        except Exception as e:
            self.logger.error(f"Error getting balance: {e}")
            return {'error': str(e)}
    
    def place_order(self, symbol: str, side: str, order_type: str, quantity: float,
                   price: float = None, stop_price: float = None, 
                   time_in_force: str = 'GTC') -> Dict:
        """
        Place a new order
        
        Args:
            symbol (str): Trading symbol
            side (str): 'BUY' or 'SELL'
            order_type (str): Order type ('MARKET', 'LIMIT', 'STOP_LOSS', etc.)
            quantity (float): Order quantity
            price (float): Order price (for limit orders)
            stop_price (float): Stop price (for stop orders)
            time_in_force (str): Time in force
            
        Returns:
            dict: Order result
        """
        try:
            if not self.api_key or not self.api_secret:
                return {'error': 'API credentials not configured'}
            
            params = {
                'symbol': symbol.upper(),
                'side': side.upper(),
                'type': order_type.upper(),
                'quantity': quantity
            }
            
            if order_type.upper() in ['LIMIT', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT']:
                if not price:
                    return {'error': 'Price required for limit orders'}
                params['price'] = price
                params['timeInForce'] = time_in_force
            
            if order_type.upper() in ['STOP_LOSS', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT']:
                if not stop_price:
                    return {'error': 'Stop price required for stop orders'}
                params['stopPrice'] = stop_price
            
            result = self._make_request('POST', '/api/v3/order', params, signed=True)
            
            if 'error' not in result:
                self.logger.info(f"Order placed successfully: {result.get('orderId')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return {'error': str(e)}
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """
        Cancel an existing order
        
        Args:
            symbol (str): Trading symbol
            order_id (int): Order ID to cancel
            
        Returns:
            dict: Cancellation result
        """
        try:
            if not self.api_key or not self.api_secret:
                return {'error': 'API credentials not configured'}
            
            params = {
                'symbol': symbol.upper(),
                'orderId': order_id
            }
            
            result = self._make_request('DELETE', '/api/v3/order', params, signed=True)
            
            if 'error' not in result:
                self.logger.info(f"Order cancelled successfully: {order_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            return {'error': str(e)}
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict:
        """
        Get order status
        
        Args:
            symbol (str): Trading symbol
            order_id (int): Order ID
            
        Returns:
            dict: Order status
        """
        try:
            if not self.api_key or not self.api_secret:
                return {'error': 'API credentials not configured'}
            
            params = {
                'symbol': symbol.upper(),
                'orderId': order_id
            }
            
            return self._make_request('GET', '/api/v3/order', params, signed=True)
            
        except Exception as e:
            self.logger.error(f"Error getting order status: {e}")
            return {'error': str(e)}
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """
        Get all open orders
        
        Args:
            symbol (str): Specific symbol to get orders for
            
        Returns:
            list: List of open orders
        """
        try:
            if not self.api_key or not self.api_secret:
                return [{'error': 'API credentials not configured'}]
            
            params = {}
            if symbol:
                params['symbol'] = symbol.upper()
            
            result = self._make_request('GET', '/api/v3/openOrders', params, signed=True)
            
            if isinstance(result, list):
                return result
            else:
                return [result]  # Return as list for consistency
                
        except Exception as e:
            self.logger.error(f"Error getting open orders: {e}")
            return [{'error': str(e)}]
    
    def get_trade_history(self, symbol: str, limit: int = 100) -> List[Dict]:
        """
        Get trade history
        
        Args:
            symbol (str): Trading symbol
            limit (int): Number of trades to retrieve
            
        Returns:
            list: Trade history
        """
        try:
            if not self.api_key or not self.api_secret:
                return [{'error': 'API credentials not configured'}]
            
            params = {
                'symbol': symbol.upper(),
                'limit': limit
            }
            
            result = self._make_request('GET', '/api/v3/myTrades', params, signed=True)
            
            if isinstance(result, list):
                return result
            else:
                return [result]
                
        except Exception as e:
            self.logger.error(f"Error getting trade history: {e}")
            return [{'error': str(e)}]
    
    def test_connectivity(self) -> Dict:
        """
        Test API connectivity
        
        Returns:
            dict: Connectivity test result
        """
        try:
            # Test public endpoint
            server_time = self.get_server_time()
            if 'error' in server_time:
                return {'status': 'failed', 'error': server_time['error']}
            
            # Test private endpoint if credentials available
            if self.api_key and self.api_secret:
                account_info = self.get_account_info()
                if 'error' in account_info:
                    return {
                        'status': 'partial',
                        'public': 'ok',
                        'private': 'failed',
                        'error': account_info['error']
                    }
                
                return {
                    'status': 'ok',
                    'public': 'ok',
                    'private': 'ok',
                    'server_time': server_time.get('serverTime'),
                    'account_type': account_info.get('accountType', 'unknown')
                }
            
            return {
                'status': 'partial',
                'public': 'ok',
                'private': 'not_configured',
                'server_time': server_time.get('serverTime')
            }
            
        except Exception as e:
            self.logger.error(f"Connectivity test failed: {e}")
            return {'status': 'failed', 'error': str(e)}