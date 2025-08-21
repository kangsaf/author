"""
Bybit Exchange Handler for kang_bot trading system
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

class BybitHandler:
    """
    Handler for Bybit exchange operations
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize Bybit handler
        
        Args:
            config (dict): Bybit configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # API configuration
        self.api_key = self.config.get('api_key', '')
        self.api_secret = self.config.get('api_secret', '')
        self.testnet = self.config.get('testnet', True)
        
        if self.testnet:
            self.base_url = 'https://api-testnet.bybit.com'
        else:
            self.base_url = 'https://api.bybit.com'
        
        # Request settings
        self.timeout = self.config.get('timeout', 10)
        self.recv_window = self.config.get('recv_window', 5000)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        self.logger.info(f"Bybit handler initialized (testnet: {self.testnet})")
    
    def _generate_signature(self, timestamp: str, params: str) -> str:
        """
        Generate HMAC SHA256 signature for API requests
        
        Args:
            timestamp (str): Request timestamp
            params (str): Request parameters
            
        Returns:
            str: HMAC signature
        """
        param_str = f"{timestamp}{self.api_key}{self.recv_window}{params}"
        return hmac.new(
            bytes(self.api_secret, "utf-8"),
            param_str.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                     signed: bool = False) -> Dict:
        """
        Make HTTP request to Bybit API
        
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
            headers = {'Content-Type': 'application/json'}
            
            if params is None:
                params = {}
            
            # Add signature for signed requests
            if signed:
                if not self.api_key or not self.api_secret:
                    return {'error': 'API credentials not configured'}
                
                timestamp = str(int(time.time() * 1000))
                param_str = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
                
                signature = self._generate_signature(timestamp, param_str)
                
                headers.update({
                    'X-BAPI-API-KEY': self.api_key,
                    'X-BAPI-SIGN': signature,
                    'X-BAPI-SIGN-TYPE': '2',
                    'X-BAPI-TIMESTAMP': timestamp,
                    'X-BAPI-RECV-WINDOW': str(self.recv_window)
                })
            
            # Make request
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=params, headers=headers, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            self.last_request_time = time.time()
            
            # Check response
            if response.status_code == 200:
                data = response.json()
                if data.get('retCode') == 0:
                    return data.get('result', data)
                else:
                    error_msg = f"API error {data.get('retCode')}: {data.get('retMsg')}"
                    self.logger.error(error_msg)
                    return {'error': error_msg}
            else:
                error_msg = f"HTTP error {response.status_code}: {response.text}"
                self.logger.error(error_msg)
                return {'error': error_msg}
                
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return {'error': str(e)}
    
    def get_server_time(self) -> Dict:
        """
        Get Bybit server time
        
        Returns:
            dict: Server time information
        """
        result = self._make_request('GET', '/v5/market/time')
        if 'error' not in result:
            return {'serverTime': result.get('timeSecond', 0) * 1000}
        return result
    
    def get_ticker_price(self, symbol: str, category: str = 'spot') -> Dict:
        """
        Get current ticker price
        
        Args:
            symbol (str): Trading symbol
            category (str): Product category (spot, linear, inverse)
            
        Returns:
            dict: Ticker price information
        """
        params = {
            'category': category,
            'symbol': symbol.upper()
        }
        return self._make_request('GET', '/v5/market/tickers', params)
    
    def get_klines(self, symbol: str, interval: str = '60', limit: int = 100,
                  category: str = 'spot', start_time: int = None, end_time: int = None) -> Dict:
        """
        Get kline/candlestick data
        
        Args:
            symbol (str): Trading symbol
            interval (str): Kline interval (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M)
            limit (int): Number of klines to retrieve (max 1000)
            category (str): Product category
            start_time (int): Start time in milliseconds
            end_time (int): End time in milliseconds
            
        Returns:
            dict: Kline data
        """
        params = {
            'category': category,
            'symbol': symbol.upper(),
            'interval': interval,
            'limit': min(limit, 1000)
        }
        
        if start_time:
            params['start'] = start_time
        if end_time:
            params['end'] = end_time
        
        return self._make_request('GET', '/v5/market/kline', params)
    
    def get_ohlcv_data(self, symbol: str, interval: str = '60', limit: int = 100,
                      category: str = 'spot') -> pd.DataFrame:
        """
        Get OHLCV data as pandas DataFrame
        
        Args:
            symbol (str): Trading symbol
            interval (str): Timeframe
            limit (int): Number of candles
            category (str): Product category
            
        Returns:
            pd.DataFrame: OHLCV data
        """
        try:
            result = self.get_klines(symbol, interval, limit, category)
            
            if 'error' in result:
                self.logger.error(f"Error getting klines: {result['error']}")
                return pd.DataFrame()
            
            klines = result.get('list', [])
            if not klines:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
            ])
            
            # Convert data types
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            # Convert timestamp (Bybit returns timestamp in milliseconds)
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
            
            # Sort by timestamp (Bybit returns data in reverse chronological order)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
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
        
        return self._make_request('GET', '/v5/account/info', signed=True)
    
    def get_wallet_balance(self, account_type: str = 'UNIFIED', coin: str = None) -> Dict:
        """
        Get wallet balance
        
        Args:
            account_type (str): Account type (UNIFIED, CONTRACT, SPOT)
            coin (str): Specific coin to get balance for
            
        Returns:
            dict: Balance information
        """
        try:
            if not self.api_key or not self.api_secret:
                return {'error': 'API credentials not configured'}
            
            params = {'accountType': account_type}
            if coin:
                params['coin'] = coin.upper()
            
            result = self._make_request('GET', '/v5/account/wallet-balance', params, signed=True)
            
            if 'error' in result:
                return result
            
            # Format balance information
            balances = []
            for account in result.get('list', []):
                for coin_info in account.get('coin', []):
                    balance = {
                        'asset': coin_info.get('coin'),
                        'free': safe_float(coin_info.get('availableToWithdraw', 0)),
                        'locked': safe_float(coin_info.get('locked', 0)),
                        'total': safe_float(coin_info.get('walletBalance', 0))
                    }
                    if balance['total'] > 0:
                        balances.append(balance)
            
            return {'balances': balances}
            
        except Exception as e:
            self.logger.error(f"Error getting wallet balance: {e}")
            return {'error': str(e)}
    
    def place_order(self, symbol: str, side: str, order_type: str, qty: str,
                   price: str = None, category: str = 'spot') -> Dict:
        """
        Place a new order
        
        Args:
            symbol (str): Trading symbol
            side (str): 'Buy' or 'Sell'
            order_type (str): Order type ('Market', 'Limit')
            qty (str): Order quantity
            price (str): Order price (for limit orders)
            category (str): Product category
            
        Returns:
            dict: Order result
        """
        try:
            if not self.api_key or not self.api_secret:
                return {'error': 'API credentials not configured'}
            
            params = {
                'category': category,
                'symbol': symbol.upper(),
                'side': side.capitalize(),
                'orderType': order_type.capitalize(),
                'qty': str(qty)
            }
            
            if order_type.lower() == 'limit':
                if not price:
                    return {'error': 'Price required for limit orders'}
                params['price'] = str(price)
            
            result = self._make_request('POST', '/v5/order/create', params, signed=True)
            
            if 'error' not in result:
                self.logger.info(f"Order placed successfully: {result.get('orderId')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return {'error': str(e)}
    
    def cancel_order(self, symbol: str, order_id: str = None, order_link_id: str = None,
                    category: str = 'spot') -> Dict:
        """
        Cancel an existing order
        
        Args:
            symbol (str): Trading symbol
            order_id (str): Order ID to cancel
            order_link_id (str): User customized order ID
            category (str): Product category
            
        Returns:
            dict: Cancellation result
        """
        try:
            if not self.api_key or not self.api_secret:
                return {'error': 'API credentials not configured'}
            
            params = {
                'category': category,
                'symbol': symbol.upper()
            }
            
            if order_id:
                params['orderId'] = order_id
            elif order_link_id:
                params['orderLinkId'] = order_link_id
            else:
                return {'error': 'Either orderId or orderLinkId is required'}
            
            result = self._make_request('POST', '/v5/order/cancel', params, signed=True)
            
            if 'error' not in result:
                self.logger.info(f"Order cancelled successfully")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            return {'error': str(e)}
    
    def get_open_orders(self, symbol: str = None, category: str = 'spot') -> Dict:
        """
        Get all open orders
        
        Args:
            symbol (str): Specific symbol to get orders for
            category (str): Product category
            
        Returns:
            dict: List of open orders
        """
        try:
            if not self.api_key or not self.api_secret:
                return {'error': 'API credentials not configured'}
            
            params = {'category': category}
            if symbol:
                params['symbol'] = symbol.upper()
            
            return self._make_request('GET', '/v5/order/realtime', params, signed=True)
                
        except Exception as e:
            self.logger.error(f"Error getting open orders: {e}")
            return {'error': str(e)}
    
    def get_order_history(self, symbol: str = None, category: str = 'spot', limit: int = 50) -> Dict:
        """
        Get order history
        
        Args:
            symbol (str): Trading symbol
            category (str): Product category
            limit (int): Number of orders to retrieve
            
        Returns:
            dict: Order history
        """
        try:
            if not self.api_key or not self.api_secret:
                return {'error': 'API credentials not configured'}
            
            params = {
                'category': category,
                'limit': limit
            }
            if symbol:
                params['symbol'] = symbol.upper()
            
            return self._make_request('GET', '/v5/order/history', params, signed=True)
                
        except Exception as e:
            self.logger.error(f"Error getting order history: {e}")
            return {'error': str(e)}
    
    def get_execution_history(self, symbol: str = None, category: str = 'spot', limit: int = 50) -> Dict:
        """
        Get execution history
        
        Args:
            symbol (str): Trading symbol
            category (str): Product category
            limit (int): Number of executions to retrieve
            
        Returns:
            dict: Execution history
        """
        try:
            if not self.api_key or not self.api_secret:
                return {'error': 'API credentials not configured'}
            
            params = {
                'category': category,
                'limit': limit
            }
            if symbol:
                params['symbol'] = symbol.upper()
            
            return self._make_request('GET', '/v5/execution/list', params, signed=True)
                
        except Exception as e:
            self.logger.error(f"Error getting execution history: {e}")
            return {'error': str(e)}
    
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
                    'account_info': account_info
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