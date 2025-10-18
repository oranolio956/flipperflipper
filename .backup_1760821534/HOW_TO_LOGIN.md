# 🔐 How to Login to Stitch RAT

## Your Current Credentials

Your Stitch RAT uses credentials from **Replit Secrets**:

```
Username: oranolio
Password: [Your 14-character password from Secrets]
```

## How to Find Your Password

1. Click the **"Secrets" tab** (🔒 icon) on the left sidebar in Replit
2. Look for `STITCH_ADMIN_PASSWORD`
3. Click the eye icon (👁️) to reveal your password
4. Copy and use it to log in

## Login Steps

1. Open your Stitch Web Interface
2. Enter username: `oranolio`
3. Enter your password from Secrets
4. Click "LOGIN"
5. You'll be redirected to the dashboard

## Need to Change Credentials?

Edit the Replit Secrets:
- `STITCH_ADMIN_USER` - Change username
- `STITCH_ADMIN_PASSWORD` - Change password (min 12 characters)

After changing, restart the server.

## Troubleshooting

**Still can't login?**
Run this command to check your current credentials:
```bash
python3 check_credentials.py
```

This will show your username and password length without revealing the password.
