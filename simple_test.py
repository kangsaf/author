#!/usr/bin/env python3
"""
Simple structure test for KangBot system
Test struktur file dan import dasar tanpa dependencies external
"""
import sys
import os
from pathlib import Path

# Ensure project root is in Python path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def test_file_structure():
    """Test file structure completeness"""
    print("🧪 Testing file structure...")
    
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

def test_config_files():
    """Test configuration files"""
    print("\n🧪 Testing configuration files...")
    
    try:
        import json
        
        # Test main config
        with open(ROOT / "config" / "config.json", 'r') as f:
            config = json.load(f)
        
        required_sections = ['trading', 'strategy', 'risk_management', 'exchanges', 'notifications']
        for section in required_sections:
            if section not in config:
                print(f"❌ Missing config section: {section}")
                return False
        
        print("✅ Main configuration valid")
        
        # Test profit config
        with open(ROOT / "config" / "profit.json", 'r') as f:
            profit_config = json.load(f)
        
        if 'total_profit' not in profit_config:
            print("❌ Profit config invalid")
            return False
        
        print("✅ Profit configuration valid")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_python_syntax():
    """Test Python syntax of all modules"""
    print("\n🧪 Testing Python syntax...")
    
    python_files = [
        "run.py",
        "kang_bot.py",
        "core/ai_signal.py",
        "core/strategy_manager.py", 
        "core/risk_manager.py",
        "core/utils.py",
        "handlers/binance_handler.py",
        "handlers/bybit_handler.py",
        "handlers/telegram_handler.py",
        "handlers/whatsapp_handler.py"
    ]
    
    import ast
    
    for file_path in python_files:
        full_path = ROOT / file_path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Parse the AST to check syntax
            ast.parse(source)
            print(f"✅ {file_path} - syntax OK")
            
        except SyntaxError as e:
            print(f"❌ {file_path} - syntax error: {e}")
            return False
        except Exception as e:
            print(f"❌ {file_path} - error: {e}")
            return False
    
    print("✅ All Python files have valid syntax")
    return True

def test_requirements():
    """Test requirements.txt"""
    print("\n🧪 Testing requirements.txt...")
    
    try:
        with open(ROOT / "requirements.txt", 'r') as f:
            requirements = f.read()
        
        # Check for key dependencies
        key_deps = ['pandas', 'numpy', 'requests', 'ta', 'python-dotenv']
        for dep in key_deps:
            if dep not in requirements:
                print(f"❌ Missing key dependency: {dep}")
                return False
        
        print("✅ Requirements.txt contains key dependencies")
        
        # Count total dependencies
        lines = [line.strip() for line in requirements.split('\n') if line.strip() and not line.startswith('#')]
        print(f"✅ Total dependencies: {len(lines)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Requirements test failed: {e}")
        return False

def test_documentation():
    """Test documentation files"""
    print("\n🧪 Testing documentation...")
    
    doc_files = ["README_KANG_BOT.md"]
    
    for doc_file in doc_files:
        full_path = ROOT / doc_file
        if not full_path.exists():
            print(f"❌ Missing documentation: {doc_file}")
            return False
        
        # Check file size (should have content)
        if full_path.stat().st_size < 1000:
            print(f"❌ Documentation too short: {doc_file}")
            return False
    
    print("✅ Documentation files present and substantial")
    return True

def test_imports_structure():
    """Test basic import structure without executing"""
    print("\n🧪 Testing import structure...")
    
    try:
        # Test that we can at least parse imports
        import ast
        
        # Check core modules
        core_files = [
            "core/utils.py",
            "core/ai_signal.py", 
            "core/strategy_manager.py",
            "core/risk_manager.py"
        ]
        
        for file_path in core_files:
            full_path = ROOT / file_path
            with open(full_path, 'r') as f:
                tree = ast.parse(f.read())
            
            # Check for class definitions
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            if not classes:
                print(f"⚠️ {file_path} has no classes")
            else:
                print(f"✅ {file_path} has classes: {classes}")
        
        # Check handlers
        handler_files = [
            "handlers/binance_handler.py",
            "handlers/telegram_handler.py"
        ]
        
        for file_path in handler_files:
            full_path = ROOT / file_path
            with open(full_path, 'r') as f:
                tree = ast.parse(f.read())
            
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            if not classes:
                print(f"❌ {file_path} has no handler classes")
                return False
            else:
                print(f"✅ {file_path} has handler: {classes[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import structure test failed: {e}")
        return False

def main():
    """Run all simple tests"""
    print("🚀 Starting KangBot Simple Structure Tests")
    print("=" * 50)
    
    tests = [
        test_file_structure,
        test_config_files,
        test_python_syntax,
        test_requirements,
        test_documentation,
        test_imports_structure
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
    print("📊 Simple Test Results")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All structure tests passed!")
        print("📁 KangBot project structure is complete and valid!")
        print("\n📋 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Configure API keys in config/config.json")
        print("3. Run integration tests: python test_integration.py")
        print("4. Start the bot: python run.py")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please fix issues.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)