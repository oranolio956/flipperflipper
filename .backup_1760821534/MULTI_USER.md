# Multi-User Management Guide for Stitch RAT

## Current Implementation

The Stitch web interface currently supports **single-user authentication** with one admin account. All authenticated users have full administrative access.

## Adding Additional Users (Manual Method)

To add more users, modify `web_app_real.py`:

### Step 1: Update Credentials
```python
# In load_credentials() function, add multiple users:
def load_credentials():
    users = {}
    
    # Admin user
    admin_user = os.getenv('STITCH_ADMIN_USER', 'admin')
    admin_pass = os.getenv('STITCH_ADMIN_PASSWORD', 'stitch2024')
    users[admin_user] = generate_password_hash(admin_pass)
    
    # Additional users
    user2 = os.getenv('STITCH_USER2_NAME')
    pass2 = os.getenv('STITCH_USER2_PASSWORD')
    if user2 and pass2:
        users[user2] = generate_password_hash(pass2)
    
    return users
```

### Step 2: Set Environment Variables
Add to Replit Secrets:
- `STITCH_USER2_NAME` = username
- `STITCH_USER2_PASSWORD` = password (12+ characters)

### Step 3: Restart Server
Restart the workflow to apply changes.

## Future Enhancement: Role-Based Access Control (RBAC)

For production use, consider implementing these roles:

### Administrator Role
- ✅ Full system access
- ✅ Execute all commands
- ✅ Upload/download files
- ✅ View all connections
- ✅ Export data
- ✅ Manage users

### Operator Role
- ✅ Execute commands (except dangerous ones)
- ✅ View connections
- ✅ Upload/download files
- ❌ No user management
- ❌ No dangerous commands (clearev, avkill, etc.)

### Viewer Role
- ✅ View connections
- ✅ View command history
- ✅ View logs
- ❌ No command execution
- ❌ No file operations

## Implementing RBAC (Code Template)

### 1. Add Role Field to Users
```python
USERS = {
    'admin': {
        'password': generate_password_hash('admin_password'),
        'role': 'administrator'
    },
    'operator1': {
        'password': generate_password_hash('operator_password'),
        'role': 'operator'
    },
    'viewer1': {
        'password': generate_password_hash('viewer_password'),
        'role': 'viewer'
    }
}
```

### 2. Store Role in Session
```python
# In login route:
session['username'] = username
session['role'] = USERS[username]['role']
```

### 3. Create Role Decorator
```python
def role_required(allowed_roles):
    """Decorator to restrict access by role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session:
                return jsonify({'error': 'Unauthorized'}), 401
            if session['role'] not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

### 4. Apply to Routes
```python
# Administrator only
@app.route('/api/users/manage')
@login_required
@role_required(['administrator'])
def manage_users():
    pass

# Administrator and Operator
@app.route('/api/execute')
@login_required  
@role_required(['administrator', 'operator'])
def execute_command():
    # Check for dangerous commands
    if is_dangerous_command(cmd) and session['role'] != 'administrator':
        return jsonify({'error': 'Permission denied for dangerous commands'}), 403
    # ... execute command

# All authenticated users
@app.route('/api/connections')
@login_required
@role_required(['administrator', 'operator', 'viewer'])
def get_connections():
    pass
```

### 5. Update UI Based on Role
```javascript
// In app_real.js
fetch('/api/user/info')
    .then(res => res.json())
    .then(data => {
        if (data.role === 'viewer') {
            // Hide command execution UI
            document.getElementById('commands-section').style.display = 'none';
        } else if (data.role === 'operator') {
            // Show commands but disable dangerous ones
            disableDangerousCommands();
        }
    });
```

## Session Management

### Current Implementation
- Sessions expire after 30 minutes of inactivity (configurable via `STITCH_SESSION_TIMEOUT`)
- Sessions use secure HttpOnly cookies
- CSRF protection enabled

### Multi-Session Support
The current implementation supports multiple concurrent sessions. Each user gets their own session with isolated command history and logs.

## Audit Logging for Multi-User

All actions are already logged with username:
```python
log_debug(f"User {username} executed command: {command}", "INFO", "Command")
```

Logs include:
- Username
- Action performed
- Timestamp
- IP address
- Result (success/failure)

View audit logs in the Logs section or export them.

## Security Considerations

### User Management Best Practices
1. **Strong Passwords**: Enforce minimum 12 characters
2. **Unique Accounts**: Never share credentials
3. **Regular Rotation**: Change passwords quarterly
4. **Least Privilege**: Assign minimum necessary role
5. **Audit Regularly**: Review user actions in logs

### Account Lockout
Current implementation:
- 5 failed login attempts = 15-minute lockout
- Tracked per IP address
- Automatically resets after lockout period

### Session Security
- Sessions tied to IP address (optional)
- HttpOnly cookies prevent XSS
- SameSite=Lax prevents CSRF
- Secure flag for HTTPS

## Database-Backed User Management (Future)

For enterprise deployments, consider:
1. **PostgreSQL user table** with hashed passwords
2. **JWT tokens** for API authentication
3. **OAuth2/SAML** for SSO integration
4. **Two-factor authentication** (TOTP)

## Implementation Checklist

To add full multi-user support:
- [ ] Define user roles and permissions
- [ ] Update credential loading for multiple users
- [ ] Add role_required decorator
- [ ] Apply permissions to all routes
- [ ] Update UI based on user role
- [ ] Add user management interface (admin only)
- [ ] Test all permission combinations
- [ ] Document new user onboarding process

## Current Limitations

The single-user model is sufficient for:
- Personal use
- Small team (share one account)
- Development/testing

Consider full RBAC for:
- Multiple operators with different access levels
- Compliance requirements (audit per user)
- Large teams (5+ users)
- Production enterprise deployments

## Questions?

See `replit.md` for architecture details or `BACKUP_RESTORE.md` for user data backup.
