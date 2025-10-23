# 🔐 Admin Setup Guide - One-Time Secure URL

## ✅ What Was Created

A secure, one-time admin account setup system with:
- **Unique token URLs** that expire in 24 hours
- **One-time use only** - token becomes invalid after use
- **Beautiful setup interface** with password requirements
- **Admin dashboard** to manage users and access keys
- **Secure token tracking** with IP address logging

---

## 🚀 Quick Start

### Step 1: Generate Your Admin Setup URL

Run this command to generate a unique setup URL:

```bash
cd /workspaces/flipperflipper
python3 admin_setup.py
```

**Output:**
```
======================================================================
🔐 ONE-TIME ADMIN SETUP TOKEN GENERATOR
======================================================================

✅ One-time admin setup token generated!

📋 SETUP INFORMATION:
----------------------------------------------------------------------
Token:      NJX8lCxt0FHXWF15AyqfCIzNZCsmp_oZJZURHewWNns
Expires:    24 hours from now

🔗 SETUP URL (use this once):
----------------------------------------------------------------------
http://localhost:5000/admin/setup?token=NJX8lCxt0FHXWF15AyqfCIzNZCsmp_oZJZURHewWNns

⚠️  IMPORTANT:
  • This URL can only be used ONCE
  • It expires in 24 hours
  • Keep this URL secret and secure
  • After setup, you can manage users from the admin panel

======================================================================
```

### Step 2: Access the Setup URL

**For Gitpod:**
Replace `localhost:5000` with your Gitpod workspace URL:
```
https://5000-<your-workspace-id>.gitpod.io/admin/setup?token=<your-token>
```

**For Local Development:**
```
http://localhost:5000/admin/setup?token=<your-token>
```

### Step 3: Create Your Admin Account

1. Open the setup URL in your browser
2. You'll see a beautiful setup page with:
   - Username field (minimum 3 characters)
   - Password field (minimum 12 characters)
   - Password confirmation
3. Fill in your credentials
4. Click "Create Admin Account"
5. You'll be automatically logged in and redirected to the admin dashboard

---

## 🎯 Admin Dashboard Features

After setup, you'll have access to:

### 👥 User Management
- Create and manage user accounts
- Set user permissions
- Control access levels
- **URL:** `/auth/admin/users`

### 🔑 Access Keys
- Generate API access keys
- Set expiration dates
- Configure IP whitelisting
- Track key usage
- **URL:** `/dashboard/admin/keys`

### 🔗 Access Links
- Create time-limited access links
- Share temporary access
- Track link usage
- **URL:** `/auth/admin/links`

### 📊 Dashboard
- View system status
- Monitor connections
- Track activity
- **URL:** `/dashboard`

### 🔔 Webhooks
- Configure webhook integrations
- View webhook stats
- Manage webhook authentication
- **URL:** `/webhook/stats`

---

## 🔒 Security Features

### Token Security
- **Cryptographically secure:** Uses `secrets.token_urlsafe(32)`
- **One-time use:** Token marked as used after account creation
- **Time-limited:** Expires after 24 hours
- **Tracked:** IP address and timestamp logged

### Password Requirements
- Minimum 12 characters
- Must match confirmation
- Stored as SHA-256 hash
- No plaintext storage

### Session Security
- Admin session created automatically
- Session flags: `is_admin=True`
- Protected admin routes
- Logout functionality

---

## 📁 File Structure

```
/workspaces/flipperflipper/
├── admin_setup.py                    # Token generator CLI
├── admin_setup_routes.py             # Flask routes
├── Application/
│   └── admin_setup.db                # Admin accounts database
├── templates/
│   ├── admin_setup.html              # Setup form
│   ├── admin_setup_error.html        # Error page
│   └── admin_dashboard.html          # Admin panel
└── web_app.py                        # Main app (integrated)
```

---

## 🗄️ Database Schema

### `setup_tokens` Table
```sql
CREATE TABLE setup_tokens (
    token TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used INTEGER DEFAULT 0,
    used_at TEXT,
    ip_address TEXT
);
```

### `admin_accounts` Table
```sql
CREATE TABLE admin_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    setup_token TEXT,
    FOREIGN KEY (setup_token) REFERENCES setup_tokens(token)
);
```

---

## 🔧 Advanced Usage

### Check if Admin Exists

```bash
python3 -c "from admin_setup import AdminSetupManager; print('Admin exists:', AdminSetupManager().admin_exists())"
```

### Generate Multiple Tokens (if needed)

```bash
# Only works if no admin exists yet
python3 admin_setup.py
```

### Reset Admin Setup

```bash
# Delete the database to start over
rm Application/admin_setup.db
python3 admin_setup.py
```

### Custom Expiration Time

```python
from admin_setup import AdminSetupManager

manager = AdminSetupManager()
token = manager.generate_setup_token(expires_hours=48)  # 48 hours
print(f"Token: {token}")
```

---

## 🌐 API Endpoints

### GET `/admin/setup?token=<token>`
Display admin setup form if token is valid

**Responses:**
- `200` - Setup form displayed
- `400` - No token provided
- `403` - Invalid, expired, or used token

### POST `/admin/setup`
Create admin account

**Form Data:**
```
token: <setup-token>
username: <admin-username>
password: <password>
password_confirm: <password-confirmation>
```

**Responses:**
```json
{
  "success": true,
  "message": "Admin account created successfully",
  "redirect": "/admin/dashboard"
}
```

### GET `/admin/dashboard`
Admin control panel (requires admin session)

### GET `/admin/check-setup`
Check if admin setup is needed

**Response:**
```json
{
  "needs_setup": false,
  "admin_exists": true
}
```

---

## ⚠️ Important Notes

### One-Time Use
- Each token can only be used **once**
- After account creation, token is marked as used
- Generate a new token if needed (requires deleting database)

### Expiration
- Tokens expire after 24 hours by default
- Expired tokens cannot be used
- Check expiration before sharing URL

### Security Best Practices
1. **Never share the token URL publicly**
2. **Use HTTPS in production**
3. **Delete the token after use** (automatic)
4. **Use strong passwords** (12+ characters)
5. **Keep admin credentials secure**

### Multiple Admins
- Currently supports one admin account
- To add more admins, use the admin dashboard
- Or modify the code to allow multiple setup tokens

---

## 🐛 Troubleshooting

### "Admin account already exists"
```bash
# Check if admin exists
python3 -c "from admin_setup import AdminSetupManager; print(AdminSetupManager().admin_exists())"

# To reset (WARNING: Deletes all admin accounts)
rm Application/admin_setup.db
python3 admin_setup.py
```

### "Token expired"
```bash
# Generate a new token
python3 admin_setup.py
```

### "Token already used"
```bash
# Check token status
sqlite3 Application/admin_setup.db "SELECT * FROM setup_tokens;"

# Generate new token (if admin doesn't exist)
python3 admin_setup.py
```

### Setup page not loading
```bash
# Check if app is running
ps aux | grep "python3 web_app.py"

# Check logs
tail -f /tmp/webapp.log

# Restart app
pkill -f "python3 web_app.py"
python3 web_app.py &
```

---

## 📊 Example Workflow

### Initial Setup
```bash
# 1. Generate token
python3 admin_setup.py

# Output: http://localhost:5000/admin/setup?token=ABC123...

# 2. Open URL in browser
# 3. Create admin account
# 4. Redirected to admin dashboard
```

### Managing Users
```bash
# From admin dashboard:
# 1. Click "User Management"
# 2. Create new user accounts
# 3. Set permissions
# 4. Generate access keys
```

### Generating Access Keys
```bash
# From admin dashboard:
# 1. Click "Access Keys"
# 2. Generate new key
# 3. Set expiration
# 4. Configure IP whitelist
# 5. Share key with user
```

---

## ✅ Testing

### Test Token Generation
```bash
python3 -c "
from admin_setup import AdminSetupManager
manager = AdminSetupManager()
token = manager.generate_setup_token()
print(f'Token: {token}')
valid, msg = manager.validate_token(token)
print(f'Valid: {valid}, Message: {msg}')
"
```

### Test Setup Endpoint
```bash
# Generate token
TOKEN=$(python3 -c "from admin_setup import AdminSetupManager; print(AdminSetupManager().generate_setup_token())")

# Test endpoint
curl "http://localhost:5000/admin/setup?token=$TOKEN"
```

---

## 🎉 Success!

You now have:
- ✅ Secure one-time admin setup
- ✅ Beautiful setup interface
- ✅ Admin dashboard for management
- ✅ Token-based security
- ✅ Complete audit trail

**Next Steps:**
1. Generate your admin setup URL
2. Create your admin account
3. Start managing users and access keys!

---

*Created: 2025-10-23*  
*System: One-Time Admin Setup v1.0*
