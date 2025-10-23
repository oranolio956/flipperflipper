# Access Key Authentication System - Design Specification

## Overview

Replace all existing authentication methods (email/password, MFA, webhook) with a simple, secure access key system. Admin can generate access keys and shareable links that bypass traditional login.

---

## 1. Authentication Flow

### User Login Flow
```
User visits site
  ↓
Presented with access key input field
  ↓
User enters access key
  ↓
System validates key:
  - Exists in database?
  - Is active?
  - Not expired?
  - Not revoked?
  ↓
Valid? → Create session → Redirect to dashboard
Invalid? → Show error → Stay on login page
```

### Admin Link Flow
```
Admin generates access link
  ↓
Link contains signed token with:
  - Access key ID
  - Expiration timestamp
  - HMAC signature
  ↓
User clicks link
  ↓
System validates token:
  - Signature valid?
  - Not expired?
  - Key still active?
  ↓
Valid? → Auto-login → Create session → Redirect to dashboard
Invalid? → Redirect to login page with error
```

---

## 2. Database Schema

### New Table: `access_keys`

```sql
CREATE TABLE access_keys (
    id TEXT PRIMARY KEY,                    -- UUID v4
    key_hash TEXT UNIQUE NOT NULL,          -- SHA-256 hash of actual key
    name TEXT NOT NULL,                     -- Human-readable name
    created_by TEXT,                        -- Admin who created it
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,                 -- Last successful auth
    expires_at TIMESTAMP,                   -- NULL = never expires
    is_active BOOLEAN DEFAULT TRUE,         -- Can be disabled
    usage_count INTEGER DEFAULT 0,          -- Number of times used
    max_uses INTEGER,                       -- NULL = unlimited
    ip_whitelist TEXT,                      -- JSON array of allowed IPs (NULL = any)
    metadata TEXT                           -- JSON for additional data
);
```

### New Table: `access_links`

```sql
CREATE TABLE access_links (
    id TEXT PRIMARY KEY,                    -- UUID v4
    access_key_id TEXT NOT NULL,            -- Foreign key to access_keys
    token_hash TEXT UNIQUE NOT NULL,        -- SHA-256 hash of token
    created_by TEXT NOT NULL,               -- Admin who created it
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,          -- Required expiration
    max_uses INTEGER DEFAULT 1,             -- Default: single-use
    usage_count INTEGER DEFAULT 0,          -- Times link was used
    is_active BOOLEAN DEFAULT TRUE,         -- Can be disabled
    last_used_at TIMESTAMP,                 -- Last click timestamp
    last_used_ip TEXT,                      -- Last IP that used it
    FOREIGN KEY (access_key_id) REFERENCES access_keys (id)
);
```

### Modified Table: `sessions`

```sql
-- Keep existing sessions table, add:
ALTER TABLE sessions ADD COLUMN access_key_id TEXT;
ALTER TABLE sessions ADD COLUMN auth_method TEXT DEFAULT 'access_key';
-- auth_method: 'access_key' or 'access_link'
```

---

## 3. Access Key Format

### Key Generation
```python
import secrets
import hashlib

def generate_access_key():
    """Generate a secure access key"""
    # Format: orat_<32 random bytes in base64url>
    # Example: orat_k7Hx9mP2vQ8wR3nL5tY6uZ1aB4cD0eF2gH3iJ4kL5mN6
    random_bytes = secrets.token_urlsafe(32)
    key = f"orat_{random_bytes}"
    return key

def hash_key(key: str) -> str:
    """Hash key for storage"""
    return hashlib.sha256(key.encode()).hexdigest()
```

### Key Properties
- **Prefix**: `orat_` (Oranolio RAT)
- **Length**: 48 characters total (5 prefix + 43 random)
- **Character set**: URL-safe base64 (A-Z, a-z, 0-9, -, _)
- **Entropy**: 256 bits (cryptographically secure)
- **Storage**: Only SHA-256 hash stored in database
- **Display**: Show once on creation, never again

---

## 4. Access Link Format

### Link Generation
```python
import secrets
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from urllib.parse import urlencode

def generate_access_link(access_key_id: str, expires_in_hours: int = 24):
    """Generate a signed access link"""
    # Create token payload
    payload = {
        'key_id': access_key_id,
        'exp': (datetime.utcnow() + timedelta(hours=expires_in_hours)).isoformat(),
        'nonce': secrets.token_urlsafe(16)
    }
    
    # Sign payload
    payload_json = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        SECRET_KEY.encode(),
        payload_json.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Create token
    token = f"{payload_json.encode().hex()}.{signature}"
    
    # Create URL
    params = urlencode({'token': token})
    url = f"https://your-domain.com/auth/link?{params}"
    
    return url, token
```

### Link Properties
- **Format**: `https://domain.com/auth/link?token=<payload>.<signature>`
- **Payload**: Hex-encoded JSON with key_id, expiration, nonce
- **Signature**: HMAC-SHA256 of payload
- **Expiration**: Configurable (default 24 hours)
- **Single-use**: Default behavior (configurable)
- **Revocable**: Can be disabled by admin

---

## 5. API Endpoints

### POST /auth/login
```json
Request:
{
    "access_key": "orat_k7Hx9mP2vQ8wR3nL5tY6uZ1aB4cD0eF2gH3iJ4kL5mN6"
}

Response (Success):
{
    "success": true,
    "message": "Authentication successful",
    "redirect": "/dashboard"
}

Response (Error):
{
    "success": false,
    "error": "Invalid or expired access key"
}
```

### GET /auth/link
```
URL: /auth/link?token=<payload>.<signature>

Success: Redirect to /dashboard with session cookie
Error: Redirect to /login with error message
```

### POST /admin/access-keys (Admin Only)
```json
Request:
{
    "name": "Production Key",
    "expires_in_days": 365,
    "max_uses": null,
    "ip_whitelist": ["192.168.1.0/24"]
}

Response:
{
    "success": true,
    "access_key": "orat_k7Hx9mP2vQ8wR3nL5tY6uZ1aB4cD0eF2gH3iJ4kL5mN6",
    "key_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Access key created. Save this key - it won't be shown again."
}
```

### POST /admin/access-links (Admin Only)
```json
Request:
{
    "access_key_id": "550e8400-e29b-41d4-a716-446655440000",
    "expires_in_hours": 24,
    "max_uses": 1
}

Response:
{
    "success": true,
    "link": "https://domain.com/auth/link?token=...",
    "expires_at": "2024-01-02T15:30:00Z",
    "max_uses": 1
}
```

### GET /admin/access-keys (Admin Only)
```json
Response:
{
    "access_keys": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Production Key",
            "created_at": "2024-01-01T10:00:00Z",
            "last_used_at": "2024-01-01T14:30:00Z",
            "expires_at": "2025-01-01T10:00:00Z",
            "is_active": true,
            "usage_count": 42
        }
    ]
}
```

### DELETE /admin/access-keys/:id (Admin Only)
```json
Response:
{
    "success": true,
    "message": "Access key revoked"
}
```

---

## 6. Security Features

### Rate Limiting
- **Login attempts**: 5 per IP per 15 minutes
- **Failed attempts**: Exponential backoff
- **Link generation**: 10 per admin per hour

### IP Whitelisting
- Optional per-key IP restrictions
- CIDR notation support
- Bypass for admin-generated links (optional)

### Audit Logging
Log all authentication events:
- Key usage (successful and failed)
- Link generation
- Link usage
- Key creation/revocation
- Admin actions

### Session Security
- HTTPOnly cookies
- SameSite=Strict
- Secure flag (HTTPS only)
- 30-minute timeout (configurable)
- Session regeneration on auth

---

## 7. Admin Interface

### Access Key Management Page

```
┌─────────────────────────────────────────────────────────────┐
│  Access Keys                                [+ New Key]      │
├─────────────────────────────────────────────────────────────┤
│  Search: [________________]  Filter: [All ▾]  Sort: [Date ▾]│
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Production Key                              [●] Active │  │
│  │ Created: Jan 1, 2024  •  Last used: 2 hours ago       │  │
│  │ Usage: 42 times  •  Expires: Jan 1, 2025              │  │
│  │ [Generate Link] [Revoke] [View Details]               │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Development Key                             [○] Inactive│  │
│  │ Created: Dec 15, 2023  •  Last used: Never            │  │
│  │ Usage: 0 times  •  Expires: Never                     │  │
│  │ [Generate Link] [Activate] [View Details]             │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### New Key Creation Modal

```
┌─────────────────────────────────────────────────────────────┐
│  Create New Access Key                              [×]      │
├─────────────────────────────────────────────────────────────┤
│  Key Name *                                                  │
│  [_____________________________]                             │
│                                                              │
│  Expiration                                                  │
│  ○ Never  ○ 30 days  ○ 90 days  ● 1 year  ○ Custom         │
│                                                              │
│  Usage Limit                                                 │
│  ● Unlimited  ○ Limited: [____] uses                        │
│                                                              │
│  IP Whitelist (optional)                                     │
│  [_____________________________]                             │
│  Example: 192.168.1.0/24, 10.0.0.1                          │
│                                                              │
│  [Cancel]                              [Create Access Key]  │
└─────────────────────────────────────────────────────────────┘
```

### Key Created Success Modal

```
┌─────────────────────────────────────────────────────────────┐
│  ✓ Access Key Created                                [×]     │
├─────────────────────────────────────────────────────────────┤
│  ⚠️ Save this key now - it won't be shown again!            │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ orat_k7Hx9mP2vQ8wR3nL5tY6uZ1aB4cD0eF2gH3iJ4kL5mN6 │ [📋]│
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Key Details:                                                │
│  • Name: Production Key                                      │
│  • Expires: January 1, 2025                                  │
│  • Usage: Unlimited                                          │
│                                                              │
│  [Generate Access Link]                          [Done]      │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Migration Strategy

### Phase 1: Implement New System
1. Create new database tables
2. Implement access key authentication
3. Implement access link generation
4. Create admin management interface
5. Test thoroughly

### Phase 2: Parallel Operation
1. Keep old auth system running
2. Add access key as alternative login method
3. Allow users to generate their own keys
4. Monitor usage and issues

### Phase 3: Migration
1. Generate access keys for existing users
2. Send migration emails
3. Set deadline for migration
4. Disable old auth methods

### Phase 4: Cleanup
1. Remove old authentication code
2. Remove old database tables
3. Remove old templates
4. Update documentation

---

## 9. Configuration

### Environment Variables

```bash
# Access Key Settings
ACCESS_KEY_PREFIX=orat_
ACCESS_KEY_LENGTH=32
ACCESS_KEY_HASH_ALGORITHM=sha256

# Access Link Settings
ACCESS_LINK_DEFAULT_EXPIRY_HOURS=24
ACCESS_LINK_MAX_USES_DEFAULT=1
ACCESS_LINK_SIGNATURE_ALGORITHM=hmac-sha256

# Security Settings
ACCESS_KEY_RATE_LIMIT_ATTEMPTS=5
ACCESS_KEY_RATE_LIMIT_WINDOW=900  # 15 minutes
ACCESS_KEY_LOCKOUT_DURATION=3600  # 1 hour

# Session Settings
SESSION_TIMEOUT_MINUTES=30
SESSION_REGENERATE_INTERVAL=1800  # 30 minutes
```

---

## 10. Implementation Checklist

### Backend
- [ ] Create database tables (access_keys, access_links)
- [ ] Implement AccessKeyManager class
- [ ] Implement AccessLinkManager class
- [ ] Create authentication middleware
- [ ] Implement rate limiting
- [ ] Implement IP whitelisting
- [ ] Add audit logging
- [ ] Create API endpoints
- [ ] Write unit tests
- [ ] Write integration tests

### Frontend
- [ ] Create new login page
- [ ] Create access key input component
- [ ] Create admin management interface
- [ ] Create key creation modal
- [ ] Create link generation modal
- [ ] Add copy-to-clipboard functionality
- [ ] Add QR code generation for links
- [ ] Implement error handling
- [ ] Add loading states
- [ ] Test responsive design

### Admin Features
- [ ] Key management dashboard
- [ ] Key creation wizard
- [ ] Link generation interface
- [ ] Usage statistics
- [ ] Audit log viewer
- [ ] Bulk operations (revoke multiple keys)
- [ ] Export functionality

### Documentation
- [ ] API documentation
- [ ] Admin guide
- [ ] User guide
- [ ] Migration guide
- [ ] Security best practices

---

## 11. Future Enhancements

### Advanced Features
- **Key rotation**: Automatic key rotation on schedule
- **Temporary keys**: Auto-expiring keys for contractors
- **Key scopes**: Limit keys to specific features/endpoints
- **2FA for admin**: Require 2FA for key generation
- **Webhook notifications**: Alert on key usage/creation
- **Analytics dashboard**: Key usage trends and patterns
- **API key management**: Separate API keys from access keys
- **SSO integration**: SAML/OAuth for enterprise customers

---

## 12. Security Considerations

### Threat Model
- **Brute force attacks**: Mitigated by rate limiting and key entropy
- **Key theft**: Mitigated by secure storage (hashed) and IP whitelisting
- **Link interception**: Mitigated by HTTPS, short expiry, single-use
- **Session hijacking**: Mitigated by HTTPOnly cookies, SameSite, regeneration
- **Admin compromise**: Mitigated by audit logging, 2FA (future)

### Best Practices
- Never log plaintext keys
- Always use HTTPS in production
- Implement proper rate limiting
- Monitor for suspicious activity
- Regular security audits
- Keep dependencies updated
- Follow OWASP guidelines

---

## Conclusion

This access key system provides a **simple, secure, and flexible** authentication mechanism that replaces the complex multi-system authentication currently in place. It's easier for users (just enter a key), easier for admins (generate and share links), and easier to maintain (single authentication path).

The design follows modern SaaS patterns (similar to Stripe API keys, GitHub personal access tokens) and provides enterprise-grade security features while maintaining simplicity.
