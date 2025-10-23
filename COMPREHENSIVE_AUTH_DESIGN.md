# Comprehensive Access Key Authentication System

## Core Design Principles
1. **Security First**: Every decision prioritizes security
2. **User Experience**: Frictionless for legitimate users, impossible for attackers
3. **Failure Resilience**: Graceful degradation, clear error messages
4. **Performance**: Sub-100ms auth checks, optimized queries
5. **Auditability**: Every action logged, tamper-evident

---

## Database Schema (Optimized)

```sql
-- Access Keys Table
CREATE TABLE access_keys (
    id TEXT PRIMARY KEY,
    key_hash TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    last_used_at INTEGER,
    expires_at INTEGER,
    is_active INTEGER DEFAULT 1,
    usage_count INTEGER DEFAULT 0,
    max_uses INTEGER,
    ip_whitelist TEXT,
    permissions TEXT DEFAULT 'read,write',
    metadata TEXT
);

CREATE INDEX idx_key_hash ON access_keys(key_hash);
CREATE INDEX idx_active_keys ON access_keys(is_active, expires_at);
CREATE INDEX idx_created_by ON access_keys(created_by);

-- Access Links Table
CREATE TABLE access_links (
    id TEXT PRIMARY KEY,
    access_key_id TEXT NOT NULL,
    token_hash TEXT UNIQUE NOT NULL,
    created_by TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    max_uses INTEGER DEFAULT 1,
    usage_count INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    last_used_at INTEGER,
    last_used_ip TEXT,
    FOREIGN KEY (access_key_id) REFERENCES access_keys(id) ON DELETE CASCADE
);

CREATE INDEX idx_token_hash ON access_links(token_hash);
CREATE INDEX idx_link_active ON access_links(is_active, expires_at);

-- Auth Attempts Table (Security)
CREATE TABLE auth_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,
    key_prefix TEXT,
    success INTEGER NOT NULL,
    failure_reason TEXT,
    user_agent TEXT,
    timestamp INTEGER NOT NULL
);

CREATE INDEX idx_auth_ip_time ON auth_attempts(ip_address, timestamp);
CREATE INDEX idx_auth_success ON auth_attempts(success, timestamp);
```

---

## Authentication Flow (Detailed)

### Login Flow with Error Handling
```python
def authenticate_with_key(key: str, ip: str, user_agent: str):
    # Step 1: Input validation
    if not key or len(key) < 10:
        log_auth_attempt(ip, None, False, "Invalid key format")
        return {"error": "Invalid access key format", "code": "INVALID_FORMAT"}
    
    # Step 2: Rate limiting check
    if is_rate_limited(ip):
        remaining = get_rate_limit_reset_time(ip)
        return {"error": f"Too many attempts. Try again in {remaining}s", "code": "RATE_LIMITED"}
    
    # Step 3: Key normalization
    key = key.strip().replace(" ", "")
    
    # Step 4: Hash and lookup
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    key_record = db.query("SELECT * FROM access_keys WHERE key_hash = ?", [key_hash])
    
    if not key_record:
        log_auth_attempt(ip, key[:10], False, "Key not found")
        increment_rate_limit(ip)
        return {"error": "Invalid access key", "code": "KEY_NOT_FOUND"}
    
    # Step 5: Key validation
    if not key_record['is_active']:
        log_auth_attempt(ip, key[:10], False, "Key inactive")
        return {"error": "This access key has been revoked", "code": "KEY_REVOKED"}
    
    if key_record['expires_at'] and key_record['expires_at'] < time.time():
        log_auth_attempt(ip, key[:10], False, "Key expired")
        return {"error": "This access key has expired", "code": "KEY_EXPIRED"}
    
    if key_record['max_uses'] and key_record['usage_count'] >= key_record['max_uses']:
        log_auth_attempt(ip, key[:10], False, "Usage limit reached")
        return {"error": "Usage limit reached for this key", "code": "USAGE_LIMIT"}
    
    # Step 6: IP whitelist check
    if key_record['ip_whitelist']:
        allowed_ips = json.loads(key_record['ip_whitelist'])
        if not ip_in_whitelist(ip, allowed_ips):
            log_auth_attempt(ip, key[:10], False, "IP not whitelisted")
            return {"error": "Access denied from this IP address", "code": "IP_DENIED"}
    
    # Step 7: Success - update key
    db.execute("""
        UPDATE access_keys 
        SET usage_count = usage_count + 1, last_used_at = ? 
        WHERE id = ?
    """, [time.time(), key_record['id']])
    
    # Step 8: Create session
    session_id = create_session(key_record['id'], ip, user_agent)
    
    # Step 9: Log success
    log_auth_attempt(ip, key[:10], True, None)
    
    return {"success": True, "session_id": session_id, "permissions": key_record['permissions']}
```

---

## Frontend Implementation (Complete)

### Login Page HTML
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Oranolio RAT - Access</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #f1f5f9;
        }
        
        .login-container {
            background: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(20px);
            border-radius: 16px;
            padding: 48px;
            width: 100%;
            max-width: 440px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .logo {
            text-align: center;
            margin-bottom: 32px;
        }
        
        .logo h1 {
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }
        
        .logo p {
            color: #94a3b8;
            font-size: 14px;
        }
        
        .form-group {
            margin-bottom: 24px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-size: 14px;
            font-weight: 500;
            color: #cbd5e1;
        }
        
        input[type="text"] {
            width: 100%;
            padding: 12px 16px;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid #334155;
            border-radius: 8px;
            color: #f1f5f9;
            font-size: 15px;
            font-family: 'Monaco', 'Courier New', monospace;
            transition: all 0.2s;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #6366f1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }
        
        input[type="text"]::placeholder {
            color: #64748b;
        }
        
        .btn-primary {
            width: 100%;
            padding: 12px;
            background: #6366f1;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn-primary:hover {
            background: #4f46e5;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        }
        
        .btn-primary:active {
            transform: translateY(0);
        }
        
        .btn-primary:disabled {
            background: #475569;
            cursor: not-allowed;
            transform: none;
        }
        
        .error-message {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #fca5a5;
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 24px;
            font-size: 14px;
            display: none;
        }
        
        .error-message.show {
            display: block;
            animation: slideDown 0.3s ease;
        }
        
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .loading-spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .help-text {
            text-align: center;
            margin-top: 24px;
            font-size: 13px;
            color: #94a3b8;
        }
        
        .help-text a {
            color: #6366f1;
            text-decoration: none;
        }
        
        .help-text a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>⚡ Oranolio</h1>
            <p>Command & Control Platform</p>
        </div>
        
        <div id="errorMessage" class="error-message"></div>
        
        <form id="loginForm">
            <div class="form-group">
                <label for="accessKey">Access Key</label>
                <input 
                    type="text" 
                    id="accessKey" 
                    name="accessKey"
                    placeholder="orat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    autocomplete="off"
                    spellcheck="false"
                    required
                    aria-label="Access Key"
                    aria-describedby="keyHelp"
                >
            </div>
            
            <button type="submit" class="btn-primary" id="submitBtn">
                <span id="btnText">Access Dashboard</span>
                <span id="btnSpinner" class="loading-spinner" style="display: none;"></span>
            </button>
        </form>
        
        <div class="help-text">
            <p id="keyHelp">Enter your access key to continue</p>
        </div>
    </div>
    
    <script>
        const form = document.getElementById('loginForm');
        const input = document.getElementById('accessKey');
        const submitBtn = document.getElementById('submitBtn');
        const btnText = document.getElementById('btnText');
        const btnSpinner = document.getElementById('btnSpinner');
        const errorMessage = document.getElementById('errorMessage');
        
        // Auto-focus input
        input.focus();
        
        // Handle form submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const key = input.value.trim();
            
            // Client-side validation
            if (!key) {
                showError('Please enter an access key');
                return;
            }
            
            if (!key.startsWith('orat_')) {
                showError('Invalid access key format. Keys must start with "orat_"');
                return;
            }
            
            // Show loading state
            setLoading(true);
            hideError();
            
            try {
                const response = await fetch('/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ access_key: key })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Success - redirect
                    window.location.href = data.redirect || '/dashboard';
                } else {
                    // Show error
                    showError(data.error || 'Authentication failed');
                    setLoading(false);
                }
            } catch (error) {
                showError('Network error. Please check your connection and try again.');
                setLoading(false);
            }
        });
        
        function setLoading(loading) {
            submitBtn.disabled = loading;
            btnText.style.display = loading ? 'none' : 'inline';
            btnSpinner.style.display = loading ? 'inline-block' : 'none';
        }
        
        function showError(message) {
            errorMessage.textContent = message;
            errorMessage.classList.add('show');
        }
        
        function hideError() {
            errorMessage.classList.remove('show');
        }
        
        // Clear error on input
        input.addEventListener('input', hideError);
    </script>
</body>
</html>
```

---

## Performance Optimizations

### Database Query Optimization
```python
# Bad: Multiple queries
key = db.query("SELECT * FROM access_keys WHERE key_hash = ?", [hash])
if key:
    db.execute("UPDATE access_keys SET usage_count = usage_count + 1 WHERE id = ?", [key['id']])

# Good: Single query with RETURNING
key = db.query("""
    UPDATE access_keys 
    SET usage_count = usage_count + 1, last_used_at = ?
    WHERE key_hash = ? AND is_active = 1 AND (expires_at IS NULL OR expires_at > ?)
    RETURNING *
""", [time.time(), hash, time.time()])
```

### Caching Strategy
```python
from functools import lru_cache
import time

# Cache key lookups for 60 seconds
@lru_cache(maxsize=1000)
def get_key_by_hash(key_hash: str, cache_time: int):
    return db.query("SELECT * FROM access_keys WHERE key_hash = ?", [key_hash])

# Use with current minute as cache key
def lookup_key(key_hash: str):
    current_minute = int(time.time() / 60)
    return get_key_by_hash(key_hash, current_minute)
```

---

## Security Hardening

### Rate Limiting Implementation
```python
import redis
from datetime import timedelta

redis_client = redis.Redis()

def is_rate_limited(ip: str) -> bool:
    key = f"rate_limit:{ip}"
    attempts = redis_client.get(key)
    return attempts and int(attempts) >= 5

def increment_rate_limit(ip: str):
    key = f"rate_limit:{ip}"
    redis_client.incr(key)
    redis_client.expire(key, 900)  # 15 minutes

def get_rate_limit_reset_time(ip: str) -> int:
    key = f"rate_limit:{ip}"
    return redis_client.ttl(key)
```

### IP Whitelist Validation
```python
import ipaddress

def ip_in_whitelist(ip: str, whitelist: list) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
        for allowed in whitelist:
            if '/' in allowed:
                # CIDR notation
                if ip_obj in ipaddress.ip_network(allowed):
                    return True
            else:
                # Single IP
                if ip_obj == ipaddress.ip_address(allowed):
                    return True
        return False
    except ValueError:
        return False
```

---

## Admin Interface (Complete)

### Key Management Dashboard
```html
<div class="admin-dashboard">
    <header>
        <h1>Access Key Management</h1>
        <button class="btn-primary" onclick="showCreateKeyModal()">
            + New Access Key
        </button>
    </header>
    
    <div class="filters">
        <input type="search" placeholder="Search keys..." id="searchKeys">
        <select id="filterStatus">
            <option value="all">All Keys</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="expired">Expired</option>
        </select>
        <select id="sortBy">
            <option value="created">Created Date</option>
            <option value="used">Last Used</option>
            <option value="name">Name</option>
        </select>
    </div>
    
    <div class="keys-grid" id="keysGrid">
        <!-- Keys will be populated here -->
    </div>
</div>
```

This is a more focused, production-ready design. Should I continue with the dashboard design with the same level of detail?