#!/usr/bin/env python3
"""
Setup script for Headless Infographic Generator API
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is 3.8+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def check_node():
    """Check if Node.js is available"""
    try:
        result = subprocess.run("node --version", shell=True, capture_output=True, text=True)
        print(f"✅ Node.js {result.stdout.strip()} detected")
        return True
    except:
        print("⚠️  Node.js not found - Playwright may need manual browser installation")
        return False

def setup_virtual_environment():
    """Create and activate virtual environment"""
    if os.path.exists("venv"):
        print("✅ Virtual environment already exists")
        return True
    
    return run_command("python -m venv venv", "Creating virtual environment")

def install_requirements():
    """Install Python requirements"""
    if os.name == 'nt':  # Windows
        pip_command = "venv\\Scripts\\pip install -r requirements.txt"
    else:  # Linux/macOS
        pip_command = "venv/bin/pip install -r requirements.txt"
    
    return run_command(pip_command, "Installing Python requirements")

def install_playwright():
    """Install Playwright browsers"""
    if os.name == 'nt':  # Windows
        playwright_command = "venv\\Scripts\\playwright install chromium"
    else:  # Linux/macOS
        playwright_command = "venv/bin/playwright install chromium"
    
    return run_command(playwright_command, "Installing Playwright browsers")

def setup_env_file():
    """Create .env file from template"""
    if os.path.exists(".env"):
        print("✅ .env file already exists")
        return True
    
    if os.path.exists(".env.example"):
        shutil.copy(".env.example", ".env")
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file and add your GEMINI_API_KEY")
        return True
    else:
        print("❌ .env.example not found")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ["src/generated", "logs", "temp"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    print("✅ Created necessary directories")
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up Headless Infographic Generator API")
    print("=" * 50)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    check_node()
    
    # Setup steps
    steps = [
        setup_virtual_environment,
        install_requirements,
        install_playwright,
        setup_env_file,
        create_directories
    ]
    
    for step in steps:
        if not step():
            print(f"❌ Setup failed at step: {step.__name__}")
            sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your GEMINI_API_KEY")
    print("2. Activate virtual environment:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Linux/macOS
        print("   source venv/bin/activate")
    print("3. Start the API:")
    print("   cd src")
    print("   python -m uvicorn api_headless_infographic:app --host 0.0.0.0 --port 8000 --reload")
    print("4. Visit http://localhost:8000/docs for API documentation")

if __name__ == "__main__":
    main()
