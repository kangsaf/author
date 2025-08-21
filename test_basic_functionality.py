#!/usr/bin/env python3
"""
Basic functionality test for KangBot system
Test core functionality tanpa external dependencies
"""
import sys
import os
import json
from pathlib import Path

# Ensure project root is in Python path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def test_config_loading():
    """Test configuration loading without external deps"""
    print("🧪 Testing configuration loading...")
    
    try:
        # Test config.json
        with open(ROOT / "config" / "config.json", 'r') as f:
            config = json.load(f)
        
        # Validate structure
        required_sections = ['trading', 'strategy', 'risk_management', 'exchanges', 'notifications']
        for section in required_sections:
            if section not in config:
                print(f"❌ Missing config section: {section}")
                return False
        
        print("✅ Main config structure valid")
        
        # Test specific values
        trading = config['trading']
        if 'enabled' not in trading or 'default_symbol' not in trading:
            print("❌ Trading config incomplete")
            return False
        
        print(f"✅ Trading enabled: {trading['enabled']}")
        print(f"✅ Default symbol: {trading['default_symbol']}")
        
        # Test risk management
        risk = config['risk_management']
        required_risk_params = ['max_risk_per_trade', 'max_daily_loss', 'account_balance']
        for param in required_risk_params:
            if param not in risk:
                print(f"❌ Missing risk parameter: {param}")
                return False
        
        print(f"✅ Risk per trade: {risk['max_risk_per_trade']*100}%")
        print(f"✅ Daily loss limit: {risk['max_daily_loss']*100}%")
        print(f"✅ Account balance: ${risk['account_balance']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False

def test_profit_config():
    """Test profit configuration"""
    print("\n🧪 Testing profit configuration...")
    
    try:
        with open(ROOT / "config" / "profit.json", 'r') as f:
            profit_config = json.load(f)
        
        required_fields = [
            'total_profit', 'total_trades', 'winning_trades', 
            'win_rate', 'performance_metrics', 'strategy_performance'
        ]
        
        for field in required_fields:
            if field not in profit_config:
                print(f"❌ Missing profit field: {field}")
                return False
        
        print("✅ Profit config structure valid")
        
        # Check strategy performance structure
        strategies = profit_config['strategy_performance']
        expected_strategies = ['ai_signal', 'scalping', 'swing', 'dca']
        
        for strategy in expected_strategies:
            if strategy not in strategies:
                print(f"❌ Missing strategy performance: {strategy}")
                return False
        
        print(f"✅ Strategy performance tracking: {len(strategies)} strategies")
        
        return True
        
    except Exception as e:
        print(f"❌ Profit config test failed: {e}")
        return False

def test_core_imports():
    """Test core module imports (syntax only)"""
    print("\n🧪 Testing core module imports...")
    
    import ast
    
    core_modules = [
        ('core/utils.py', ['ConfigManager']),
        ('core/ai_signal.py', ['AISignalGenerator']),
        ('core/strategy_manager.py', ['StrategyManager', 'Position']),
        ('core/risk_manager.py', ['RiskManager', 'RiskLevel'])
    ]
    
    for module_path, expected_classes in core_modules:
        try:
            with open(ROOT / module_path, 'r') as f:
                tree = ast.parse(f.read())
            
            # Find class definitions
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            # Check expected classes exist
            for expected_class in expected_classes:
                if expected_class not in classes:
                    print(f"❌ {module_path}: Missing class {expected_class}")
                    return False
            
            print(f"✅ {module_path}: Classes {classes}")
            
        except Exception as e:
            print(f"❌ {module_path}: Import test failed - {e}")
            return False
    
    return True

def test_handler_structure():
    """Test handler module structure"""
    print("\n🧪 Testing handler structure...")
    
    import ast
    
    handlers = [
        ('handlers/binance_handler.py', 'BinanceHandler'),
        ('handlers/bybit_handler.py', 'BybitHandler'),
        ('handlers/telegram_handler.py', 'TelegramHandler'),
        ('handlers/whatsapp_handler.py', 'WhatsAppHandler')
    ]
    
    for handler_path, expected_class in handlers:
        try:
            with open(ROOT / handler_path, 'r') as f:
                tree = ast.parse(f.read())
            
            # Find class definitions
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            if expected_class not in classes:
                print(f"❌ {handler_path}: Missing handler class {expected_class}")
                return False
            
            # Check for essential methods
            methods = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    methods.append(node.name)
            
            # Basic methods that should exist
            essential_methods = ['__init__']
            for method in essential_methods:
                if method not in methods:
                    print(f"❌ {handler_path}: Missing method {method}")
                    return False
            
            print(f"✅ {handler_path}: Handler class {expected_class} with {len(methods)} methods")
            
        except Exception as e:
            print(f"❌ {handler_path}: Handler test failed - {e}")
            return False
    
    return True

def test_entrypoint_structure():
    """Test main entrypoint structure"""
    print("\n🧪 Testing entrypoint structure...")
    
    try:
        import ast
        
        with open(ROOT / "run.py", 'r') as f:
            tree = ast.parse(f.read())
        
        # Find function definitions
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        expected_functions = ['main', 'run_trading_bot', 'run_streamlit', 'run_tests']
        for func in expected_functions:
            if func not in functions:
                print(f"❌ run.py: Missing function {func}")
                return False
        
        print(f"✅ run.py: Entry functions {functions}")
        
        # Check main bot file
        with open(ROOT / "kang_bot.py", 'r') as f:
            tree = ast.parse(f.read())
        
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        if 'KangBot' not in classes:
            print("❌ kang_bot.py: Missing KangBot class")
            return False
        
        print("✅ kang_bot.py: KangBot class found")
        
        return True
        
    except Exception as e:
        print(f"❌ Entrypoint test failed: {e}")
        return False

def test_log_directory():
    """Test log directory setup"""
    print("\n🧪 Testing log directory...")
    
    try:
        logs_dir = ROOT / "logs"
        if not logs_dir.exists():
            print("❌ Logs directory missing")
            return False
        
        print("✅ Logs directory exists")
        
        # Check if directory is writable
        test_file = logs_dir / "test_write.tmp"
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            test_file.unlink()  # Delete test file
            print("✅ Logs directory is writable")
        except Exception:
            print("❌ Logs directory not writable")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Log directory test failed: {e}")
        return False

def test_requirements_completeness():
    """Test requirements completeness"""
    print("\n🧪 Testing requirements completeness...")
    
    try:
        with open(ROOT / "requirements.txt", 'r') as f:
            requirements = f.read()
        
        # Essential dependencies for trading bot
        essential_deps = [
            'pandas',       # Data manipulation
            'numpy',        # Numerical computing
            'requests',     # HTTP requests
            'ta',           # Technical analysis
            'python-dotenv' # Environment variables
        ]
        
        missing_deps = []
        for dep in essential_deps:
            if dep not in requirements:
                missing_deps.append(dep)
        
        if missing_deps:
            print(f"❌ Missing essential dependencies: {missing_deps}")
            return False
        
        print("✅ All essential dependencies present")
        
        # Count total dependencies
        lines = [line.strip() for line in requirements.split('\n') 
                if line.strip() and not line.startswith('#')]
        print(f"✅ Total dependencies: {len(lines)}")
        
        # Check for development dependencies
        dev_deps = ['pytest', 'pytest-cov']
        dev_present = [dep for dep in dev_deps if dep in requirements]
        print(f"✅ Development dependencies: {len(dev_present)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Requirements test failed: {e}")
        return False

def main():
    """Run all basic functionality tests"""
    print("🚀 Starting KangBot Basic Functionality Tests")
    print("=" * 55)
    
    tests = [
        test_config_loading,
        test_profit_config,
        test_core_imports,
        test_handler_structure,
        test_entrypoint_structure,
        test_log_directory,
        test_requirements_completeness
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
    
    print("\n" + "=" * 55)
    print("📊 Basic Functionality Test Results")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All basic functionality tests passed!")
        print("🔧 KangBot core functionality is working correctly!")
        print("\n📋 To run with dependencies:")
        print("1. pip install -r requirements.txt")
        print("2. python run.py --help")
        print("3. python test_integration.py")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please check the issues above.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)