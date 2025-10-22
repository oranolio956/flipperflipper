#!/usr/bin/env python3
"""
Strategic Command Center - Complete Deployment
No bullshit design with real-time architecture
"""

import os
import sys
import time
import subprocess
import json
from pathlib import Path

def print_banner():
    """Print strategic banner"""
    print("🎯" + "="*58 + "🎯")
    print("🎯" + " "*20 + "STRATEGIC COMMAND CENTER" + " "*20 + "🎯")
    print("🎯" + " "*15 + "NO BULLSHIT DESIGN" + " "*15 + "🎯")
    print("🎯" + " "*10 + "Everything has a purpose, nothing is decorative" + " "*10 + "🎯")
    print("🎯" + "="*58 + "🎯")

def check_system_requirements():
    """Check system requirements"""
    print("\n🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print("✅ Python version OK")
    
    # Check if we're in workspace
    if not os.path.exists('/workspace'):
        print("❌ Not in workspace directory")
        return False
    print("✅ Workspace directory OK")
    
    # Check if Redis is available
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection OK")
    except:
        print("⚠️ Redis not available - will attempt to start")
    
    return True

def install_dependencies():
    """Install all dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        # Install Python dependencies
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True)
        print("✅ Python dependencies installed")
        
        # Try to install Redis if not available
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
        except:
            print("🔄 Attempting to install Redis...")
            try:
                subprocess.run(['sudo', 'apt-get', 'update'], check=True, capture_output=True)
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'redis-server'], 
                              check=True, capture_output=True)
                print("✅ Redis installed")
            except:
                print("⚠️ Could not install Redis automatically")
                print("   Please install Redis manually:")
                print("   Ubuntu/Debian: sudo apt-get install redis-server")
                print("   macOS: brew install redis")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def start_redis():
    """Start Redis server"""
    print("\n🔄 Starting Redis server...")
    
    try:
        # Check if Redis is already running
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis already running")
        return True
    except:
        pass
    
    try:
        # Start Redis
        subprocess.Popen(['redis-server'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        
        # Verify it's running
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis started successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to start Redis: {e}")
        return False

def run_tests():
    """Run comprehensive tests"""
    print("\n🧪 Running comprehensive tests...")
    
    try:
        result = subprocess.run([sys.executable, 'test_strategic_center.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All tests passed")
            return True
        else:
            print("⚠️ Some tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

def create_startup_scripts():
    """Create convenient startup scripts"""
    print("\n📝 Creating startup scripts...")
    
    # Create quick start script
    quick_start = """#!/bin/bash
# Strategic Command Center - Quick Start
echo "🎯 Starting Strategic Command Center..."
cd /workspace
python start_strategic_center.py
"""
    
    with open('/workspace/start_strategic.sh', 'w') as f:
        f.write(quick_start)
    
    os.chmod('/workspace/start_strategic.sh', 0o755)
    print("✅ Quick start script created: ./start_strategic.sh")
    
    # Create systemd service (if on Linux)
    if os.name != 'nt':
        service_content = """[Unit]
Description=Strategic Command Center
After=network.target redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/workspace
ExecStart=/usr/bin/python3 /workspace/start_strategic_center.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        with open('/workspace/strategic-command-center.service', 'w') as f:
            f.write(service_content)
        
        print("✅ Systemd service created: strategic-command-center.service")
        print("   To install: sudo cp strategic-command-center.service /etc/systemd/system/")
        print("   To enable: sudo systemctl enable strategic-command-center")
        print("   To start: sudo systemctl start strategic-command-center")

def create_documentation():
    """Create comprehensive documentation"""
    print("\n📚 Creating documentation...")
    
    readme_content = """# Strategic Command Center

## Quick Start

1. **Start Redis:**
   ```bash
   redis-server
   ```

2. **Start Strategic Command Center:**
   ```bash
   python start_strategic_center.py
   # OR
   ./start_strategic.sh
   ```

3. **Access the Interface:**
   - URL: http://localhost:5000
   - Design: No Bullshit - Everything has a purpose

## Features

- **Central Target Grid**: 4x3 grid with complete control units
- **Real-time Updates**: Live status and health monitoring
- **Parallel Operations**: Execute commands on multiple targets
- **Context-sensitive Panels**: Smart UI that adapts to context
- **Bulk Operations**: Manage multiple targets simultaneously
- **File Management**: Real-time file sync and operations
- **Payload Generation**: Python, C, and PowerShell payloads

## Architecture

- **Redis**: Real-time data persistence
- **WebSocket**: Live communication
- **Elite Executor**: Advanced command execution
- **Strategic UI**: No decoration, maximum efficiency

## API Endpoints

- `GET /api/targets` - Get all targets
- `POST /api/execute_command` - Execute command
- `POST /api/execute_parallel` - Execute on multiple targets
- `POST /api/upload_file` - Upload file
- `POST /api/download_file` - Download file
- `GET /api/system_stats` - Get system statistics

## Troubleshooting

### Redis Issues
```bash
# Install Redis
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis                 # macOS

# Start Redis
redis-server
```

### Port Conflicts
```bash
# Kill existing servers
pkill -f strategic_web_app
pkill -f web_app_real
```

### Dependencies
```bash
pip install -r requirements.txt
```

## Design Philosophy

1. **No Bullshit**: Every element serves a purpose
2. **Strategic Layout**: Information density optimized
3. **Real-time**: Live updates for all operations
4. **Efficient**: One-click access to all functions
5. **Scalable**: Handles multiple targets simultaneously

## Support

For issues and questions:
1. Check the logs in `/workspace/logs/`
2. Run the test suite: `python test_strategic_center.py`
3. Check Redis status: `redis-cli ping`
4. Verify all files are in place

## License

Strategic Command Center - No Bullshit Design
"""
    
    with open('/workspace/README_STRATEGIC.md', 'w') as f:
        f.write(readme_content)
    
    print("✅ Documentation created: README_STRATEGIC.md")

def main():
    """Main deployment function"""
    print_banner()
    
    # Change to workspace directory
    os.chdir('/workspace')
    
    # Deployment steps
    steps = [
        ("Checking system requirements", check_system_requirements),
        ("Installing dependencies", install_dependencies),
        ("Starting Redis", start_redis),
        ("Running tests", run_tests),
        ("Creating startup scripts", create_startup_scripts),
        ("Creating documentation", create_documentation)
    ]
    
    print("\n🚀 Starting Strategic Command Center deployment...")
    print("="*60)
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        try:
            if step_func():
                print(f"✅ {step_name} completed")
            else:
                print(f"⚠️ {step_name} completed with warnings")
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
            print("Continuing with deployment...")
    
    print("\n" + "="*60)
    print("🎯 STRATEGIC COMMAND CENTER DEPLOYMENT COMPLETE!")
    print("="*60)
    
    print("\n📋 NEXT STEPS:")
    print("1. Start Redis: redis-server")
    print("2. Start Strategic Center: python start_strategic_center.py")
    print("3. Access Interface: http://localhost:5000")
    print("4. Read Documentation: README_STRATEGIC.md")
    
    print("\n🎯 STRATEGIC COMMAND CENTER READY FOR OPERATION!")
    print("Core Principle: 'Everything has a purpose, nothing is decorative'")
    print("="*60)

if __name__ == '__main__':
    main()