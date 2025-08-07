#!/usr/bin/env python3
"""
Deployment script for the Headless Infographic Generator API
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def install_dependencies():
    """Install all required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        # Install Python packages
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Python packages installed")
        
        # Install Playwright browsers
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        print("✅ Playwright browsers installed")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_environment():
    """Check deployment environment"""
    print("🔍 Checking deployment environment...")
    
    # Check .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("   Please create a .env file with your GOOGLE_API_KEY")
        return False
    
    # Check if API key is set
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ GOOGLE_API_KEY not set in .env file")
            return False
        print("✅ Environment variables configured")
    except ImportError:
        print("⚠️  python-dotenv not installed, skipping env check")
    
    return True

def start_development_server():
    """Start development server with uvicorn"""
    print("🚀 Starting development server...")
    
    os.chdir("src")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "api_headless_infographic:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Development server stopped")

def start_production_server(workers=4, port=8000):
    """Start production server with gunicorn"""
    print(f"🏭 Starting production server with {workers} workers on port {port}...")
    
    try:
        # Check if gunicorn is installed
        subprocess.run([sys.executable, "-m", "pip", "install", "gunicorn"], check=True)
        
        os.chdir("src")
        
        subprocess.run([
            "gunicorn",
            "api_headless_infographic:app",
            "-w", str(workers),
            "-k", "uvicorn.workers.UvicornWorker",
            "--bind", f"0.0.0.0:{port}",
            "--timeout", "300",  # 5 minutes timeout for long-running requests
            "--log-level", "info"
        ])
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start production server: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Production server stopped")

def create_systemd_service(port=8000, workers=4):
    """Create a systemd service file for Linux deployment"""
    service_content = f"""[Unit]
Description=Headless Infographic Generator API
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory={Path.cwd().absolute()}/src
Environment=PATH={Path.cwd().absolute()}/venv/bin
ExecStart={Path.cwd().absolute()}/venv/bin/gunicorn api_headless_infographic:app -w {workers} -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:{port} --timeout 300
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
    
    service_file = Path("headless-infographic-api.service")
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print(f"📄 Systemd service file created: {service_file}")
    print("   To install:")
    print(f"   sudo cp {service_file} /etc/systemd/system/")
    print("   sudo systemctl daemon-reload")
    print("   sudo systemctl enable headless-infographic-api")
    print("   sudo systemctl start headless-infographic-api")

def create_docker_files():
    """Create Docker deployment files"""
    
    # Dockerfile
    dockerfile_content = """FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    wget \\
    gnupg \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
RUN python -m playwright install chromium
RUN python -m playwright install-deps chromium

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["uvicorn", "src.api_headless_infographic:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    # docker-compose.yml
    compose_content = """version: '3.8'

services:
  infographic-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    volumes:
      - ./generated:/app/generated
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
"""
    
    with open("Dockerfile", 'w') as f:
        f.write(dockerfile_content)
    
    with open("docker-compose.yml", 'w') as f:
        f.write(compose_content)
    
    print("🐳 Docker files created:")
    print("   - Dockerfile")
    print("   - docker-compose.yml")
    print("\n   To deploy with Docker:")
    print("   docker-compose up -d")

def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy Headless Infographic Generator API")
    parser.add_argument("--mode", choices=["dev", "prod", "install", "systemd", "docker"], 
                       default="dev", help="Deployment mode")
    parser.add_argument("--port", type=int, default=8000, help="Port to run on")
    parser.add_argument("--workers", type=int, default=4, help="Number of workers for production")
    
    args = parser.parse_args()
    
    print("🚀 HEADLESS INFOGRAPHIC API DEPLOYMENT")
    print("=" * 50)
    
    if args.mode == "install":
        print("📦 Installing dependencies...")
        if install_dependencies():
            print("✅ Installation completed successfully")
        else:
            print("❌ Installation failed")
            sys.exit(1)
    
    elif args.mode == "systemd":
        create_systemd_service(args.port, args.workers)
    
    elif args.mode == "docker":
        create_docker_files()
    
    elif args.mode in ["dev", "prod"]:
        if not check_environment():
            print("❌ Environment check failed")
            sys.exit(1)
        
        if args.mode == "dev":
            start_development_server()
        else:
            start_production_server(args.workers, args.port)

if __name__ == "__main__":
    main()
