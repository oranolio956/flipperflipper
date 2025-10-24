# 🔐 ORANOLIO C2 - ACCESS KEYS

**KEEP THIS FILE SECURE - DO NOT SHARE**

## Access Keys for Approved Emails

### admin@oranolio.local
```
Access Key 1: AK_7x9mP2nQ8vL4wR6tY3hJ5kN1bV0cX
Access Key 2: SK_9zF4gH7jK2mN5pQ8rT1vW3xY6aC0bD
```

### test@oranolio.local
```
Access Key 1: AK_3bC5dE7fG9hJ1kL4mN6pQ8rS0tU2vW
Access Key 2: SK_5xY7zA9bC1dE3fG5hJ7kL9mN1pQ3rS
```

---

## How to Login

1. **Go to:** [Login Page](https://3000--019a1353-e7f6-7f23-af98-087b326beeca.us-east-1-01.gitpod.dev/login)

2. **Step 1:** Enter your email
   - `admin@oranolio.local` OR
   - `test@oranolio.local`

3. **Step 2:** Enter BOTH access keys
   - Copy and paste both keys exactly as shown above
   - Keys are case-sensitive
   - No spaces before or after

4. **Done!** You'll be logged into the dashboard

---

## Security Features

✅ **Permanent Keys**
- Never expire
- Unique per email
- Cryptographically secure (SHA-256)

✅ **Two-Factor Authentication**
- Requires both keys to login
- Constant-time comparison (prevents timing attacks)
- Failed attempts are logged

✅ **Email Whitelist**
- Only approved emails can access
- Unauthorized emails are rejected immediately

✅ **Audit Logging**
- All login attempts logged
- Failed attempts tracked
- IP addresses recorded

---

## Adding New Users

To add a new user, edit `production_app.py`:

1. Generate new keys:
```python
from production_app import generate_secure_key

key1 = generate_secure_key('AK')
key2 = generate_secure_key('SK')
print(f"Key 1: {key1}")
print(f"Key 2: {key2}")
```

2. Add to ACCESS_KEYS dictionary:
```python
ACCESS_KEYS = {
    'admin@oranolio.local': ('AK_...', 'SK_...'),
    'test@oranolio.local': ('AK_...', 'SK_...'),
    'newuser@example.com': ('AK_...', 'SK_...'),  # Add here
}
```

3. Restart the server

---

## Security Best Practices

⚠️ **IMPORTANT:**
- Keep these keys secret
- Don't commit this file to public repos
- Don't share keys via insecure channels
- Rotate keys if compromised
- Use different keys for each environment

🔒 **Storage:**
- Store keys in a password manager
- Use environment variables in production
- Never hardcode in client-side code
- Consider using a secrets management service

📝 **Monitoring:**
- Check audit logs regularly
- Monitor failed login attempts
- Set up alerts for suspicious activity
- Review access patterns

---

**Last Updated:** 2025-10-24
**System Version:** 2.0.0
