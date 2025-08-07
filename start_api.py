#!/usr/bin/env python3
"""
Startup script for the Headless Infographic Generator API
"""

import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """Check if the environment is properly set up"""
    print("🔍 Checking environment...")
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not running in a virtual environment")
        print("   Consider activating your virtual environment first")
    else:
        print("✅ Virtual environment detected")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("   Please create a .env file with your GOOGLE_API_KEY")
        print("   Example: GOOGLE_API_KEY=your_api_key_here")
        return False
    else:
        print("✅ .env file found")
    
    # Check if required packages are installed
    try:
        import fastapi
        import uvicorn
        import playwright
        import google.generativeai
        print("✅ Required packages are installed")
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    # Check if Playwright browsers are installed
    try:
        result = subprocess.run([sys.executable, '-m', 'playwright', 'install', '--dry-run'], 
                              capture_output=True, text=True)
        if "chromium" not in result.stdout.lower():
            print("⚠️  Playwright browsers may not be installed")
            print("   Run: python -m playwright install chromium")
        else:
            print("✅ Playwright browsers are available")
    except:
        print("⚠️  Could not check Playwright browser installation")
    
    return True

def main():
    """Main startup function"""
    print("🚀 HEADLESS INFOGRAPHIC GENERATOR API")
    print("=" * 50)
    
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above.")
        sys.exit(1)
    
    print("\n🎯 Starting FastAPI server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔗 Health Check: http://localhost:8000/health")
    print("🛑 Press Ctrl+C to stop the server")
    print()
    
    # Change to src directory and start the API
    src_dir = Path("src")
    if src_dir.exists():
        os.chdir(src_dir)
    
    try:
        # Start the API server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api_headless_infographic:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
