#!/usr/bin/env python3
"""
KangBot Trading System - Main Entry Point
Entrypoint utama untuk menjalankan trading bot
"""
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure project root is in Python path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Set timezone
os.environ.setdefault("TZ", "Asia/Jakarta")

from kang_bot import KangBot

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="KangBot Trading System")
    parser.add_argument(
        "--mode", 
        choices=["bot", "streamlit", "test"], 
        default="bot",
        help="Run mode: bot (trading), streamlit (UI), test (connections)"
    )
    parser.add_argument(
        "--config", 
        default="/workspace/config",
        help="Configuration directory path"
    )
    parser.add_argument(
        "--enable-trading", 
        action="store_true",
        help="Enable live trading (default: disabled for safety)"
    )
    parser.add_argument(
        "--strategy", 
        choices=["ai_signal", "scalping", "swing", "dca"],
        help="Trading strategy to use"
    )
    
    args = parser.parse_args()
    
    if args.mode == "streamlit":
        run_streamlit()
    elif args.mode == "test":
        run_tests(args.config)
    else:
        run_trading_bot(args)

def run_trading_bot(args):
    """Run the main trading bot"""
    try:
        print("🚀 Starting KangBot Trading System...")
        print(f"📁 Config path: {args.config}")
        print(f"📊 Mode: Trading Bot")
        print(f"💰 Live trading: {'Enabled' if args.enable_trading else 'Disabled (Safe Mode)'}")
        
        # Initialize bot
        bot = KangBot(config_path=args.config)
        
        # Configure bot based on arguments
        if args.enable_trading:
            bot.enable_trading()
        
        if args.strategy:
            bot.change_strategy(args.strategy)
            print(f"🎯 Strategy: {args.strategy}")
        
        # Start the bot
        print("\n" + "="*50)
        print("KangBot is now running...")
        print("Press Ctrl+C to stop the bot")
        print("="*50 + "\n")
        
        success = bot.start()
        
        if not success:
            print("❌ Failed to start KangBot")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
        if 'bot' in locals():
            bot.stop()
    except Exception as e:
        print(f"❌ Error running KangBot: {e}")
        sys.exit(1)
    finally:
        print("👋 KangBot stopped")

def run_streamlit():
    """Run Streamlit UI"""
    try:
        import subprocess
        
        # Check if streamlit app exists
        streamlit_apps = [
            "streamlit_app/app.py",
            "app_streamlit/Home.py"
        ]
        
        entry = None
        for app in streamlit_apps:
            if os.path.exists(app):
                entry = app
                break
        
        if not entry:
            print("❌ No Streamlit app found")
            sys.exit(1)
        
        port = os.environ.get("PORT", "8501")
        host = os.environ.get("HOST", "0.0.0.0")
        
        cmd = ["streamlit", "run", entry, "--server.port", port, "--server.address", host]
        print(f"🌐 Starting Streamlit UI: {' '.join(cmd)}")
        
        subprocess.run(cmd)
        
    except Exception as e:
        print(f"❌ Error running Streamlit: {e}")
        sys.exit(1)

def run_tests(config_path):
    """Run connection tests"""
    try:
        print("🧪 Running connection tests...")
        
        bot = KangBot(config_path=config_path)
        results = bot.test_connections()
        
        print("\n📊 Test Results:")
        print("=" * 40)
        
        for name, result in results.items():
            status = "✅" if result.get('status') == 'ok' else "❌"
            print(f"{status} {name}: {result.get('status', 'unknown')}")
            
            if 'error' in result:
                print(f"   Error: {result['error']}")
        
        print("=" * 40)
        print("✅ Tests completed")
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
