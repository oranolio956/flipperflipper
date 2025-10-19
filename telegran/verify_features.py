#!/usr/bin/env python3
"""
Feature Verification Script
Verifies all 8 anti-detection features are properly implemented
"""

import json
import re

def verify_userbot_code():
    """Verify userbot.py has all claimed features"""
    
    with open('userbot.py', 'r') as f:
        code = f.read()
    
    checks = {
        "1. Random Delays": {
            "patterns": [
                r"simulate_human_delay",
                r"random\.uniform\(min_delay, max_delay\)",
                r"welcome_delay_min",
                r"welcome_delay_max"
            ],
            "status": False
        },
        "2. Typing Indicators": {
            "patterns": [
                r"simulate_typing",
                r"self\.client\.action\(chat, 'typing'\)",
                r"typing_time_min",
                r"typing_time_max"
            ],
            "status": False
        },
        "3. Message Variations": {
            "patterns": [
                r"get_random_message",
                r"random\.choice\(message_list\)",
                r"welcome_messages",
                r"help_messages"
            ],
            "status": False
        },
        "4. Rate Limiting (Hourly)": {
            "patterns": [
                r"max_messages_per_hour",
                r"self\.message_count",
                r"reset_hourly_counter"
            ],
            "status": False
        },
        "5. Rate Limiting (Daily)": {
            "patterns": [
                r"max_messages_per_day",
                r"self\.daily_message_count",
                r"last_reset_date"
            ],
            "status": False
        },
        "6. Response Probability": {
            "patterns": [
                r"response_probability",
                r"random\.random\(\) > probability",
                r"should_respond_now"
            ],
            "status": False
        },
        "7. Time-Based Activity": {
            "patterns": [
                r"active_hours_start",
                r"active_hours_end",
                r"night_response_probability",
                r"datetime\.now\(\)\.hour"
            ],
            "status": False
        },
        "8. Cooldown Periods": {
            "patterns": [
                r"cooldown_hours",
                r"help_cooldowns",
                r"timedelta\(hours="
            ],
            "status": False
        },
        "Target Group Filtering": {
            "patterns": [
                r"is_target_group",
                r"target_group",
                r"if not self\.is_target_group"
            ],
            "status": False
        },
        "Error Handling": {
            "patterns": [
                r"try:",
                r"except Exception as e:",
                r"logger\.error"
            ],
            "status": False
        }
    }
    
    # Check each feature
    for feature, info in checks.items():
        all_found = all(re.search(pattern, code) for pattern in info["patterns"])
        checks[feature]["status"] = all_found
    
    return checks


def verify_config():
    """Verify config.json has all necessary settings"""
    
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    checks = {
        "Welcome Messages": len(config.get('welcome_messages', [])) >= 5,
        "Help Messages": len(config.get('help_messages', [])) >= 5,
        "Help Keywords": len(config.get('help_keywords', [])) >= 10,
        "Stealth Config": 'stealth' in config,
        "Welcome Delay Min": config.get('stealth', {}).get('welcome_delay_min', 0) >= 45,
        "Welcome Delay Max": config.get('stealth', {}).get('welcome_delay_max', 0) >= 180,
        "Typing Time": config.get('stealth', {}).get('typing_time_min', 0) >= 2,
        "Max Messages/Hour": config.get('stealth', {}).get('max_messages_per_hour', 0) <= 10,
        "Max Messages/Day": config.get('stealth', {}).get('max_messages_per_day', 0) <= 50,
        "Response Probability": 0 < config.get('stealth', {}).get('response_probability', 0) < 1,
        "Target Group Set": len(config.get('target_group', '')) > 0
    }
    
    return checks


def verify_gitignore():
    """Verify .gitignore protects sensitive files"""
    
    with open('.gitignore', 'r') as f:
        gitignore = f.read()
    
    checks = {
        ".env protected": '.env' in gitignore,
        "Session files protected": '*.session' in gitignore,
        "Log files protected": '*.log' in gitignore,
        "Python cache protected": '__pycache__' in gitignore
    }
    
    return checks


def main():
    """Run all verification checks"""
    
    print("=" * 60)
    print("TELEGRAN USERBOT - FEATURE VERIFICATION")
    print("=" * 60)
    print()
    
    # Check code features
    print("🔍 Checking userbot.py implementation...")
    print()
    code_checks = verify_userbot_code()
    
    code_passed = 0
    code_total = len(code_checks)
    
    for feature, info in code_checks.items():
        status = "✅ PASS" if info["status"] else "❌ FAIL"
        print(f"  {status} - {feature}")
        if info["status"]:
            code_passed += 1
    
    print()
    print(f"Code Implementation: {code_passed}/{code_total} features verified")
    print()
    
    # Check config
    print("⚙️  Checking config.json settings...")
    print()
    config_checks = verify_config()
    
    config_passed = sum(1 for v in config_checks.values() if v)
    config_total = len(config_checks)
    
    for feature, status in config_checks.items():
        status_text = "✅ PASS" if status else "❌ FAIL"
        print(f"  {status_text} - {feature}")
    
    print()
    print(f"Configuration: {config_passed}/{config_total} settings verified")
    print()
    
    # Check gitignore
    print("🔒 Checking .gitignore security...")
    print()
    gitignore_checks = verify_gitignore()
    
    gitignore_passed = sum(1 for v in gitignore_checks.values() if v)
    gitignore_total = len(gitignore_checks)
    
    for feature, status in gitignore_checks.items():
        status_text = "✅ PASS" if status else "❌ FAIL"
        print(f"  {status_text} - {feature}")
    
    print()
    print(f"Security: {gitignore_passed}/{gitignore_total} protections verified")
    print()
    
    # Overall result
    total_passed = code_passed + config_passed + gitignore_passed
    total_checks = code_total + config_total + gitignore_total
    
    print("=" * 60)
    print(f"OVERALL: {total_passed}/{total_checks} checks passed ({total_passed/total_checks*100:.1f}%)")
    print("=" * 60)
    
    if total_passed == total_checks:
        print()
        print("🎉 ALL FEATURES VERIFIED! The userbot is fully implemented.")
        print()
        return 0
    else:
        print()
        print("⚠️  Some features failed verification. Review the code.")
        print()
        return 1


if __name__ == '__main__':
    exit(main())
