#!/usr/bin/env python3
"""
Replit Setup Script for Stitch Elite RAT System
This script sets up the environment and installs all dependencies
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and return success status"""
    print(f"🔧 {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def install_dependencies():
    """Install all Python dependencies"""
    print("📦 Installing Python Dependencies...")
    
    # Upgrade pip first
    if not run_command("python3 -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command("python3 -m pip install -r requirements.txt", "Installing main requirements"):
        return False
    
    # Install playwright browsers
    if not run_command("python3 -m playwright install", "Installing Playwright browsers"):
        return False
    
    # Install additional system dependencies if needed
    if not run_command("python3 -m pip install --upgrade setuptools wheel", "Upgrading build tools"):
        return False
    
    return True

def setup_directories():
    """Create necessary directories"""
    print("📁 Setting up directories...")
    
    directories = [
        "logs",
        "uploads", 
        "data",
        "static",
        "templates",
        "Application/Stitch_Vars",
        "Core",
        "Configuration"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_environment():
    """Set up environment variables and configuration"""
    print("⚙️ Setting up environment...")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# Stitch Elite RAT System Environment Configuration
STITCH_DEBUG=true
STITCH_ADMIN_USER=admin
STITCH_ADMIN_PASSWORD=SuperSecurePass123!
STITCH_REDIS_URL=memory://
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=your-secret-key-here-change-in-production
"""
        env_file.write_text(env_content)
        print("✅ Created .env file")
    
    # Set up database
    run_command("python3 create_mfa_tables.py", "Setting up MFA database")
    run_command("python3 create_email_tables.py", "Setting up email database")

def verify_installation():
    """Verify that everything is installed correctly"""
    print("🔍 Verifying installation...")
    
    try:
        # Test imports
        import flask
        import flask_socketio
        import pycryptodome
        import cryptography
        import pyotp
        import qrcode
        import pillow
        import psutil
        import requests
        import redis
        import telethon
        import playwright
        import sqlalchemy
        import aiohttp
        import jwt
        
        print("✅ All core dependencies imported successfully")
        
        # Test web app import
        from web_app_real import app
        print("✅ Web application imports successfully")
        
        # Test backend import
        from Application.stitch_cmd import stitch_server
        print("✅ Backend services import successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Stitch Elite RAT System - Replit Setup")
    print("=" * 60)
    
    # Setup directories
    setup_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Verify installation
    if not verify_installation():
        print("❌ Installation verification failed")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    print("✅ All dependencies installed")
    print("✅ Environment configured")
    print("✅ Directories created")
    print("✅ Database tables created")
    print("=" * 60)
    print("🚀 Ready to start! Run: python main.py")
    print("=" * 60)

if __name__ == "__main__":
    main()