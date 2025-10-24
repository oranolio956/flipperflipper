#!/usr/bin/env python3
"""
Production Startup Script
Starts the Oranolio RAT system with proper initialization and graceful shutdown
"""

import os
import sys
import signal
import subprocess
import time
import atexit
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import production modules
from production_logging import setup_production_logging, get_logger
from production_health import HealthChecker

# Global state
shutdown_requested = False
redis_process = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    logger = get_logger(__name__)
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True
    sys.exit(0)

def cleanup():
    """Cleanup function called on exit"""
    logger = get_logger(__name__)
    logger.info("Performing cleanup...")
    
    # Stop Redis if we started it
    global redis_process
    if redis_process:
        try:
            logger.info("Stopping Redis server...")
            subprocess.run(['redis-cli', 'shutdown'], timeout=5, capture_output=True)
        except:
            pass
    
    logger.info("Cleanup complete")

def check_python_version():
    """Ensure Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)

def create_required_directories():
    """Create all required directories"""
    logger = get_logger(__name__)
    
    directories = [
        "data",
        "logs",
        "uploads",
        "downloads",
        "backups",
        "payloads"
    ]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_name}")

def start_redis():
    """Start Redis server"""
    global redis_process
    logger = get_logger(__name__)
    
    try:
        # Check if Redis is already running
        result = subprocess.run(
            ['redis-cli', 'ping'],
            capture_output=True,
            timeout=2
        )
        
        if result.returncode == 0:
            logger.info("Redis is already running")
            return True
    except:
        pass
    
    # Try to start Redis
    try:
        logger.info("Starting Redis server...")
        result = subprocess.run(
            ['bash', 'start_redis.sh'],
            capture_output=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logger.info("Redis started successfully")
            return True
        else:
            logger.warning("Redis not available, using memory backend")
            return False
    except Exception as e:
        logger.warning(f"Could not start Redis: {e}, using memory backend")
        return False

def initialize_databases():
    """Initialize all databases"""
    logger = get_logger(__name__)
    logger.info("Initializing databases...")
    
    try:
        result = subprocess.run(
            [sys.executable, 'init_all_databases.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info("Databases initialized successfully")
            return True
        else:
            logger.error(f"Database initialization failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error initializing databases: {e}")
        return False

def run_health_check():
    """Run initial health check"""
    logger = get_logger(__name__)
    logger.info("Running health check...")
    
    try:
        checker = HealthChecker()
        report = checker.get_full_health_report()
        
        logger.info(f"Health check status: {report['status']}")
        
        if report['status'] == 'unhealthy':
            logger.error("System health check failed!")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return False

def start_application():
    """Start the main application"""
    logger = get_logger(__name__)
    logger.info("Starting Oranolio RAT application...")
    
    try:
        # Import and start the application
        from main import app
        
        # Get configuration from environment
        host = os.getenv('STITCH_HOST', '0.0.0.0')
        port = int(os.getenv('STITCH_PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
        
        logger.info(f"Starting Flask application on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        
        # Start the application
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=False
        )
        
    except ImportError as e:
        logger.error(f"Failed to import application: {e}")
        logger.info("Attempting to start with alternative entry point...")
        
        try:
            # Try alternative entry points
            if Path('main_entry.py').exists():
                import main_entry
                main_entry.main()
            elif Path('web_app.py').exists():
                import web_app
                web_app.main()
            else:
                logger.error("No valid entry point found")
                return False
        except Exception as e2:
            logger.error(f"Failed to start application: {e2}")
            return False
    
    except Exception as e:
        logger.error(f"Application error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    return True

def print_banner():
    """Print startup banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                    ORANOLIO RAT FRAMEWORK                     ║
║                   Production Environment                      ║
║                      Version 1.1.0                            ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def main():
    """Main startup function"""
    # Print banner
    print_banner()
    
    # Check Python version
    check_python_version()
    
    # Setup logging
    setup_production_logging(
        app_name="oranolio_rat",
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
        enable_json=os.getenv('ENABLE_JSON_LOGGING', 'true').lower() == 'true',
        enable_console=True
    )
    
    logger = get_logger(__name__)
    logger.info("=" * 70)
    logger.info("ORANOLIO RAT - PRODUCTION STARTUP")
    logger.info("=" * 70)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup)
    
    # Create required directories
    logger.info("Creating required directories...")
    create_required_directories()
    
    # Start Redis
    logger.info("Starting Redis server...")
    start_redis()
    
    # Initialize databases
    logger.info("Initializing databases...")
    if not initialize_databases():
        logger.error("Failed to initialize databases")
        return 1
    
    # Run health check
    logger.info("Running health check...")
    if not run_health_check():
        logger.warning("Health check reported issues, but continuing...")
    
    # Start application
    logger.info("=" * 70)
    logger.info("STARTING APPLICATION")
    logger.info("=" * 70)
    
    try:
        start_application()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    logger.info("Application shutdown complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())
