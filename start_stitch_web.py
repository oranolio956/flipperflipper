#!/usr/bin/env python3
"""
Stitch Web Interface Startup Script
Properly configures and starts the web interface with all dependencies
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set default environment variables if not set
if not os.getenv('STITCH_ADMIN_USER'):
    os.environ['STITCH_ADMIN_USER'] = 'admin'
if not os.getenv('STITCH_ADMIN_PASSWORD'):
    os.environ['STITCH_ADMIN_PASSWORD'] = 'stitch2024secure'
if not os.getenv('STITCH_SECRET_KEY'):
    os.environ['STITCH_SECRET_KEY'] = 'change-this-secret-key-in-production'

def main():
    """Main startup function"""
    try:
        print("🚀 Starting Stitch Web Interface...")
        print("📋 Loading configuration...")
        
        # Import and start the web application
        from web_app_real import app
        
        print("✅ Configuration loaded successfully")
        print("🌐 Starting web server...")
        print("📍 Access the interface at: http://localhost:5000")
        print("👤 Default login: admin / stitch2024secure")
        print("⚠️  Change default credentials in production!")
        print("-" * 50)
        
        # Start the Flask application
        app.run(
            host=os.getenv('STITCH_HOST', '0.0.0.0'),
            port=int(os.getenv('STITCH_PORT', 5000)),
            debug=os.getenv('STITCH_DEBUG', 'false').lower() == 'true'
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Stitch Web Interface...")
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()