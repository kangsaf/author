#!/usr/bin/env python3
"""
Integration test for KangBot system
Test semua komponen bekerja dengan harmonis
"""
import sys
import os
from pathlib import Path

# Ensure project root is in Python path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kang_bot import KangBot
from core.utils import ConfigManager
from core.strategy_manager import StrategyType

def test_basic_initialization():
    """Test basic bot initialization"""
    print("🧪 Testing basic initialization...")
    
    try:
        bot = KangBot()
        print("✅ Bot initialized successfully")
        
        # Test status
        status = bot.get_status()
        print(f"✅ Status retrieved: {status.get('is_running', 'Unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

def test_configuration_loading():
    """Test configuration loading"""
    print("\n🧪 Testing configuration loading...")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config('config')
        
        required_sections = ['trading', 'strategy', 'risk_management', 'exchanges', 'notifications']
        for section in required_sections:
            if section not in config:
                print(f"❌ Missing config section: {section}")
                return False
        
        print("✅ All configuration sections present")
        
        # Test profit config
        profit_config = config_manager.get_config('profit')
        if 'total_profit' not in profit_config:
            print("❌ Profit config invalid")
            return False
        
        print("✅ Profit configuration loaded")
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

def test_strategy_manager():
    """Test strategy manager functionality"""
    print("\n🧪 Testing strategy manager...")
    
    try:
        bot = KangBot()
        
        # Test strategy switching
        for strategy in [StrategyType.AI_SIGNAL, StrategyType.SWING]:
            result = bot.change_strategy(strategy.value)
            if not result:
                print(f"❌ Failed to change to {strategy.value}")
                return False
        
        print("✅ Strategy switching works")
        
        # Test market analysis
        analysis = bot.strategy_manager.analyze_market("BTCUSDT")
        
        required_keys = ['signal', 'trend', 'levels', 'strategy_recommendation']
        for key in required_keys:
            if key not in analysis:
                print(f"❌ Missing analysis key: {key}")
                return False
        
        print("✅ Market analysis works")
        
        # Test portfolio status
        portfolio = bot.strategy_manager.get_portfolio_status()
        if 'total_positions' not in portfolio:
            print("❌ Portfolio status invalid")
            return False
        
        print("✅ Portfolio status works")
        return True
        
    except Exception as e:
        print(f"❌ Strategy manager test failed: {e}")
        return False

def test_risk_manager():
    """Test risk manager functionality"""
    print("\n🧪 Testing risk manager...")
    
    try:
        bot = KangBot()
        
        # Test position size calculation
        position_size = bot.risk_manager.calculate_position_size("BTCUSDT", 50000, 49000)
        if position_size <= 0:
            print("❌ Position size calculation failed")
            return False
        
        print("✅ Position size calculation works")
        
        # Test trade validation
        is_valid = bot.risk_manager.validate_trade("BTCUSDT", "buy", 0.001, 50000)
        print(f"✅ Trade validation works: {is_valid}")
        
        # Test risk limits check
        risk_status = bot.risk_manager.check_risk_limits()
        if 'status' not in risk_status:
            print("❌ Risk limits check failed")
            return False
        
        print("✅ Risk limits check works")
        
        # Test risk report
        report = bot.risk_manager.get_risk_report()
        if 'risk_status' not in report:
            print("❌ Risk report generation failed")
            return False
        
        print("✅ Risk report generation works")
        return True
        
    except Exception as e:
        print(f"❌ Risk manager test failed: {e}")
        return False

def test_handlers():
    """Test exchange and notification handlers"""
    print("\n🧪 Testing handlers...")
    
    try:
        bot = KangBot()
        
        # Test exchange handlers
        if bot.exchanges:
            print(f"✅ Exchange handlers loaded: {list(bot.exchanges.keys())}")
            
            # Test connectivity (will fail without real credentials, but shouldn't crash)
            for name, handler in bot.exchanges.items():
                try:
                    result = handler.test_connectivity()
                    print(f"✅ {name} connectivity test completed: {result.get('status', 'unknown')}")
                except Exception as e:
                    print(f"⚠️ {name} connectivity test error (expected): {str(e)[:50]}...")
        else:
            print("⚠️ No exchange handlers configured")
        
        # Test notification handlers  
        if bot.notifications:
            print(f"✅ Notification handlers loaded: {list(bot.notifications.keys())}")
            
            # Test connection (will fail without real credentials, but shouldn't crash)
            for name, handler in bot.notifications.items():
                try:
                    result = handler.test_connection()
                    print(f"✅ {name} connection test completed: {result.get('success', False)}")
                except Exception as e:
                    print(f"⚠️ {name} connection test error (expected): {str(e)[:50]}...")
        else:
            print("⚠️ No notification handlers configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Handlers test failed: {e}")
        return False

def test_logging_system():
    """Test logging system"""
    print("\n🧪 Testing logging system...")
    
    try:
        # Check if logs directory exists
        logs_dir = Path("/workspace/logs")
        if not logs_dir.exists():
            print("❌ Logs directory not found")
            return False
        
        print("✅ Logs directory exists")
        
        # Test logging
        import logging
        logger = logging.getLogger("integration_test")
        logger.info("Integration test log message")
        
        print("✅ Logging system works")
        return True
        
    except Exception as e:
        print(f"❌ Logging system test failed: {e}")
        return False

def test_file_structure():
    """Test file structure completeness"""
    print("\n🧪 Testing file structure...")
    
    required_files = [
        "run.py",
        "kang_bot.py",
        "core/__init__.py",
        "core/ai_signal.py", 
        "core/strategy_manager.py",
        "core/risk_manager.py",
        "core/utils.py",
        "handlers/__init__.py",
        "handlers/binance_handler.py",
        "handlers/bybit_handler.py", 
        "handlers/telegram_handler.py",
        "handlers/whatsapp_handler.py",
        "config/config.json",
        "config/profit.json",
        "tests/__init__.py",
        "tests/test_strategy.py",
        "tests/test_handlers.py", 
        "tests/test_risk.py",
        "requirements.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = ROOT / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present")
    
    # Check directories
    required_dirs = ["core", "handlers", "config", "logs", "tests"]
    for dir_name in required_dirs:
        dir_path = ROOT / dir_name
        if not dir_path.exists():
            print(f"❌ Missing directory: {dir_name}")
            return False
    
    print("✅ All required directories present")
    return True

def main():
    """Run all integration tests"""
    print("🚀 Starting KangBot Integration Tests")
    print("=" * 50)
    
    tests = [
        test_file_structure,
        test_configuration_loading,
        test_logging_system,
        test_basic_initialization,
        test_strategy_manager,
        test_risk_manager,
        test_handlers
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print("📊 Integration Test Results")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All integration tests passed!")
        print("🚀 KangBot is ready for deployment!")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please fix issues before deployment.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)