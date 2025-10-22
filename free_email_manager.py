#!/usr/bin/env python3
"""
Free Email Manager - Multiple Free Methods for Sending Verification Codes
Underground/Free alternatives to paid email services
"""

import smtplib
import requests
import json
import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

logger = logging.getLogger(__name__)

class FreeEmailManager:
    """Free email sending with multiple fallback methods"""
    
    def __init__(self):
        self.methods = [
            'gmail_smtp',
            'outlook_smtp', 
            'telegram_bot',
            'discord_webhook',
            'webhook_site'
        ]
        self.current_method = 0
    
    def send_verification_email(self, email, code, ip_address=""):
        """
        Send verification code using free methods with fallbacks
        
        Args:
            email (str): Recipient email
            code (str): 6-digit verification code
            ip_address (str): IP address of requester
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        # Try each method until one succeeds
        for i, method in enumerate(self.methods):
            try:
                if method == 'gmail_smtp':
                    success = self._send_via_gmail_smtp(email, code, ip_address)
                elif method == 'outlook_smtp':
                    success = self._send_via_outlook_smtp(email, code, ip_address)
                elif method == 'telegram_bot':
                    success = self._send_via_telegram(email, code, ip_address)
                elif method == 'discord_webhook':
                    success = self._send_via_discord(email, code, ip_address)
                elif method == 'webhook_site':
                    success = self._send_via_webhook_site(email, code, ip_address)
                
                if success:
                    logger.info(f"✅ Verification code sent via {method} to {email}")
                    return True
                else:
                    logger.warning(f"❌ {method} failed for {email}, trying next method...")
                    
            except Exception as e:
                logger.error(f"❌ {method} error for {email}: {e}")
                continue
        
        logger.error(f"❌ All email methods failed for {email}")
        return False
    
    def _send_via_gmail_smtp(self, email, code, ip_address):
        """Send via Gmail SMTP (free)"""
        try:
            # Gmail SMTP settings
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            
            # Use environment variables or defaults
            sender_email = Config.FROM_EMAIL or "your-gmail@gmail.com"
            sender_password = Config.GMAIL_APP_PASSWORD or "your-app-password"
            
            if not sender_password or sender_password == "your-app-password":
                logger.warning("Gmail app password not configured")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🔐 Verification Code - {Config.APP_NAME}"
            msg['From'] = f"{Config.FROM_NAME} <{sender_email}>"
            msg['To'] = email
            
            # Email content
            text_content = f"""
🔐 VERIFICATION CODE - {Config.APP_NAME}

Your verification code is: {code}

This code will expire in 10 minutes.

Security Details:
• IP Address: {ip_address}
• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Request ID: {secrets.token_hex(8)}

If you didn't request this code, please ignore this email.

---
{Config.APP_NAME} Security System
            """
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">🔐 Verification Code</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">{Config.APP_NAME}</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                    <div style="background: white; padding: 30px; border-radius: 8px; text-align: center; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #333; margin: 0 0 20px 0; font-size: 28px;">{code}</h2>
                        <p style="color: #666; margin: 0; font-size: 16px;">Enter this code to complete your login</p>
                    </div>
                    
                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 15px; margin-bottom: 20px;">
                        <p style="margin: 0; color: #856404; font-size: 14px;">
                            ⏰ <strong>This code expires in 10 minutes</strong>
                        </p>
                    </div>
                    
                    <div style="background: #e9ecef; padding: 15px; border-radius: 6px; font-size: 12px; color: #6c757d;">
                        <p style="margin: 0 0 5px 0;"><strong>Security Details:</strong></p>
                        <p style="margin: 0 0 3px 0;">• IP Address: {ip_address}</p>
                        <p style="margin: 0 0 3px 0;">• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p style="margin: 0;">• Request ID: {secrets.token_hex(8)}</p>
                    </div>
                    
                    <p style="color: #6c757d; font-size: 12px; text-align: center; margin: 20px 0 0 0;">
                        If you didn't request this code, please ignore this email.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Attach parts
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Gmail SMTP error: {e}")
            return False
    
    def _send_via_outlook_smtp(self, email, code, ip_address):
        """Send via Outlook/Hotmail SMTP (free)"""
        try:
            # Outlook SMTP settings
            smtp_server = "smtp-mail.outlook.com"
            smtp_port = 587
            
            sender_email = Config.FROM_EMAIL or "your-email@outlook.com"
            sender_password = Config.OUTLOOK_PASSWORD or "your-password"
            
            if not sender_password or sender_password == "your-password":
                logger.warning("Outlook password not configured")
                return False
            
            # Create message (same as Gmail)
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🔐 Verification Code - {Config.APP_NAME}"
            msg['From'] = f"{Config.FROM_NAME} <{sender_email}>"
            msg['To'] = email
            
            # Use same content as Gmail
            text_content = f"""
🔐 VERIFICATION CODE - {Config.APP_NAME}

Your verification code is: {code}

This code will expire in 10 minutes.

Security Details:
• IP Address: {ip_address}
• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Request ID: {secrets.token_hex(8)}

If you didn't request this code, please ignore this email.

---
{Config.APP_NAME} Security System
            """
            
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(part1)
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Outlook SMTP error: {e}")
            return False
    
    def _send_via_telegram(self, email, code, ip_address):
        """Send via Telegram Bot (free)"""
        try:
            bot_token = Config.TELEGRAM_BOT_TOKEN
            chat_id = Config.TELEGRAM_CHAT_ID
            
            if not bot_token or not chat_id:
                logger.warning("Telegram bot not configured")
                return False
            
            message = f"""
🔐 *VERIFICATION CODE - {Config.APP_NAME}*

📧 *Email:* `{email}`
🔢 *Code:* `{code}`
⏰ *Expires:* 10 minutes
🌐 *IP:* `{ip_address}`
🕐 *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🆔 *Request ID:* `{secrets.token_hex(8)}`

_This code will expire in 10 minutes._
            """
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False
    
    def _send_via_discord(self, email, code, ip_address):
        """Send via Discord Webhook (free)"""
        try:
            webhook_url = Config.DISCORD_WEBHOOK_URL
            
            if not webhook_url:
                logger.warning("Discord webhook not configured")
                return False
            
            embed = {
                "title": f"🔐 Verification Code - {Config.APP_NAME}",
                "color": 0x00ff00,
                "fields": [
                    {"name": "📧 Email", "value": email, "inline": True},
                    {"name": "🔢 Code", "value": f"`{code}`", "inline": True},
                    {"name": "⏰ Expires", "value": "10 minutes", "inline": True},
                    {"name": "🌐 IP Address", "value": ip_address, "inline": True},
                    {"name": "🕐 Time", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "inline": True},
                    {"name": "🆔 Request ID", "value": f"`{secrets.token_hex(8)}`", "inline": True}
                ],
                "footer": {"text": f"{Config.APP_NAME} Security System"},
                "timestamp": datetime.now().isoformat()
            }
            
            data = {"embeds": [embed]}
            response = requests.post(webhook_url, json=data, timeout=10)
            return response.status_code == 204
            
        except Exception as e:
            logger.error(f"Discord webhook error: {e}")
            return False
    
    def _send_via_webhook_site(self, email, code, ip_address):
        """Send via webhook.site (free)"""
        try:
            webhook_url = Config.WEBHOOK_SITE_URL
            
            if not webhook_url:
                logger.warning("Webhook.site URL not configured")
                return False
            
            payload = {
                "email": email,
                "code": code,
                "ip_address": ip_address,
                "timestamp": datetime.now().isoformat(),
                "request_id": secrets.token_hex(8),
                "expires_in": "10 minutes",
                "app_name": Config.APP_NAME
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.status_code in [200, 201, 204]
            
        except Exception as e:
            logger.error(f"Webhook.site error: {e}")
            return False

# Global instance
free_email_manager = FreeEmailManager()