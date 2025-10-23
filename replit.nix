# Nix configuration for Replit
# This file defines system-level dependencies

{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.setuptools
    pkgs.python311Packages.wheel
    
    # System dependencies
    pkgs.redis
    pkgs.sqlite
    pkgs.openssl
    pkgs.curl
    pkgs.wget
    pkgs.git
    pkgs.htop
    pkgs.vim
    pkgs.nano
    
    # Python system dependencies
    pkgs.python311Packages.cryptography
    pkgs.python311Packages.pycryptodome
    pkgs.python311Packages.psutil
    pkgs.python311Packages.requests
    pkgs.python311Packages.pillow
    pkgs.python311Packages.qrcode
    pkgs.python311Packages.flask
    pkgs.python311Packages.flask-socketio
    pkgs.python311Packages.flask-limiter
    pkgs.python311Packages.flask-wtf
    pkgs.python311Packages.flask-cors
    pkgs.python311Packages.werkzeug
    pkgs.python311Packages.pyotp
    pkgs.python311Packages.python-dotenv
    pkgs.python311Packages.colorama
    pkgs.python311Packages.bleach
    pkgs.python311Packages.sqlparse
    pkgs.python311Packages.python-magic
    pkgs.python311Packages.sqlalchemy
    pkgs.python311Packages.aiosqlite
    pkgs.python311Packages.redis
    pkgs.python311Packages.telethon
    pkgs.python311Packages.playwright
    pkgs.python311Packages.gunicorn
    pkgs.python311Packages.uvicorn
    pkgs.python311Packages.aiohttp
    pkgs.python311Packages.pyjwt
    pkgs.python311Packages.asyncio-mqtt
  ];
}