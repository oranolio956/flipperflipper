#!/usr/bin/env python3
"""
Quick script to check and display current Stitch credentials
"""
import os

print("\n" + "="*60)
print("🔐 Stitch RAT - Credential Checker")
print("="*60)

username = os.getenv('STITCH_ADMIN_USER')
password = os.getenv('STITCH_ADMIN_PASSWORD')

if username and password:
    print(f"\n✅ Credentials are SET in environment:")
    print(f"   Username: {username}")
    print(f"   Password: {'*' * len(password)} ({len(password)} characters)")
    print(f"\n📝 Use these to log in to the web interface.")
else:
    print("\n⚠️  No credentials set in environment!")
    print("   The app will use defaults:")
    print("   Username: admin")
    print("   Password: stitch2024")

print("\n" + "="*60)
print("To change credentials, set environment variables:")
print("  export STITCH_ADMIN_USER='your_username'")
print("  export STITCH_ADMIN_PASSWORD='your_password'")
print("="*60 + "\n")
