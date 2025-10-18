
import sys
import os
sys.path.insert(0, '/workspace')
os.environ['STITCH_ADMIN_USER'] = 'testadmin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'testpassword123'

print("[Web] Starting web interface...")

from web_app_real import app, socketio, start_stitch_server
import threading

# Start background server
server_thread = threading.Thread(target=start_stitch_server, daemon=True)
server_thread.start()

print("[Web] Web interface starting on port 5000...")

# Run web interface
socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
