# 📍 WHERE EVERYTHING IS - VISUAL MAP

## 🎯 **ALL FEATURES IN ONE FILE: userbot.py**

---

## 📂 **FILE STRUCTURE**

```
/workspace/telegran/
├── userbot.py ⭐ MAIN FILE (656+ lines)
│   ├── CORE FEATURES (original)
│   │   ├── Auto-welcome
│   │   ├── Help response
│   │   ├── Rate limiting
│   │   └── Stealth features
│   │
│   └── ADVANCED FEATURES (NEW!)
│       ├── Account assessment
│       ├── Warm-up protocol
│       ├── Behavioral mimicry
│       ├── Member scraping
│       ├── Social scoring
│       ├── Engagement-first
│       ├── Adaptive limits
│       └── Success learning
│
├── config.json ⭐ CONFIG FILE
│   ├── Core settings (original)
│   └── "advanced" section (NEW!)
│
├── database.py (persistence)
├── flood_wait_handler.py (reliability)
├── message_validator.py (safety)
├── health_monitor.py (monitoring)
├── backup_manager.py (backups)
├── idempotency_manager.py (duplicates)
├── file_lock.py (concurrency)
└── security_manager.py (encryption)
```

---

## 🔍 **WHERE EACH FEATURE IS**

### **IN userbot.py:**

#### **Lines 1-35: Imports & Setup**
```python
- All necessary imports
- AccountStatus enum (NEW!)
- UserProfile dataclass (NEW!)
- Logging configuration
```

#### **Lines 36-75: __init__**
```python
- Database initialization
- Core feature setup
- ADVANCED features initialization (NEW!)
  * account_status
  * trust_score
  * user_profiles
  * behavioral counters
  * success tracking
```

#### **Lines 150-200: Account Assessment (NEW!)**
```python
assess_account_status()
- Calculates trust score
- Determines account maturity
- Adjusts limits automatically
```

#### **Lines 200-280: Warm-Up Protocol (NEW!)**
```python
warmup_protocol(days=7)
- 7-day trust building
- Simulates human activity
- Increases trust score gradually
```

#### **Lines 280-350: Behavioral Mimicry (NEW!)**
```python
simulate_reading()
simulate_profile_view()
simulate_reaction()
behavioral_mimicry_loop()
- Reads messages like human
- Views profiles naturally
- Reacts to content
- Continuous background activity
```

#### **Lines 350-450: Member Scraping (NEW!)**
```python
scrape_members(limit=500)
create_user_profile(user)
score_users(profiles)
- Scrapes target group
- Creates enhanced profiles
- Scores users 0-100
- Identifies influencers
```

#### **Lines 450-480: Engagement-First (NEW!)**
```python
engage_with_user(user_id)
- Views profile before messaging
- Reacts to their content
- Warm introduction strategy
```

#### **Lines 480-520: Adaptive Systems (NEW!)**
```python
get_adaptive_limit()
learn_from_success()
- Calculates optimal limits
- Learns from results
- Continuous improvement
```

#### **Lines 520-656: Core Functions**
```python
- Welcome handling (original)
- Help handling (original)
- Message sending (enhanced with features)
- Stats & monitoring (enhanced)
- Background tasks (expanded)
```

---

## ⚙️ **IN config.json:**

### **Structure:**
```json
{
  // CORE SETTINGS (original)
  "target_group": "cupidbotg",
  "enable_welcome": true,
  "enable_help": true,
  "welcome_messages": [...],
  "help_messages": [...],
  "stealth": {...},
  
  // ADVANCED SETTINGS (NEW!)
  "advanced": {
    "enable_warmup": false,
    "warmup_days": 7,
    "enable_scraping": false,
    "enable_behavioral_mimicry": false,
    "simulate_reading": false,
    "simulate_profile_views": false,
    "simulate_reactions": false,
    "enable_social_scoring": false,
    "target_influencers_first": false,
    "enable_engagement_first": false,
    "use_adaptive_limits": false,
    "learn_from_success": false,
    "ai_personalization": false
  }
}
```

---

## 🎯 **FEATURE LOCATIONS**

### **Feature 1: Account Assessment**
- **File:** userbot.py
- **Function:** `assess_account_status()`
- **Line:** ~150-200
- **Config:** Automatic (no config needed)
- **When:** On startup

### **Feature 2: Warm-Up Protocol**
- **File:** userbot.py
- **Function:** `warmup_protocol(days)`
- **Line:** ~200-280
- **Config:** `advanced.enable_warmup`
- **When:** On startup if new account

### **Feature 3: Behavioral Mimicry**
- **File:** userbot.py
- **Functions:** 
  - `simulate_reading()` (~280-310)
  - `simulate_profile_view()` (~310-340)
  - `simulate_reaction()` (~340-370)
  - `behavioral_mimicry_loop()` (~630-656)
- **Config:** 
  - `advanced.enable_behavioral_mimicry`
  - `advanced.simulate_reading`
  - `advanced.simulate_profile_views`
  - `advanced.simulate_reactions`
- **When:** Continuous background

### **Feature 4: Member Scraping**
- **File:** userbot.py
- **Function:** `scrape_members(limit)` (~350-400)
- **Line:** ~350-400
- **Config:** `advanced.enable_scraping`
- **When:** On startup (if enabled)

### **Feature 5: Social Scoring**
- **File:** userbot.py
- **Functions:**
  - `create_user_profile()` (~400-430)
  - `score_users()` (~430-470)
- **Line:** ~400-470
- **Config:** `advanced.enable_social_scoring`
- **When:** After scraping

### **Feature 6: Engagement-First**
- **File:** userbot.py
- **Function:** `engage_with_user()` (~450-480)
- **Line:** ~450-480
- **Config:** `advanced.enable_engagement_first`
- **When:** Before each message

### **Feature 7: Adaptive Limits**
- **File:** userbot.py
- **Function:** `get_adaptive_limit()` (~480-500)
- **Line:** ~480-500
- **Config:** `advanced.use_adaptive_limits`
- **When:** Every message check

### **Feature 8: Success Learning**
- **File:** userbot.py
- **Function:** `learn_from_success()` (~500-520)
- **Line:** ~500-520
- **Config:** `advanced.learn_from_success`
- **When:** After each message

### **Feature 9: Trust Score**
- **File:** userbot.py
- **Variable:** `self.trust_score`
- **Line:** Throughout (used everywhere)
- **Config:** Automatic
- **When:** Calculated on startup

### **Feature 10: Enhanced Profiles**
- **File:** userbot.py
- **Class:** `UserProfile` (dataclass)
- **Line:** ~25-45
- **Config:** Automatic when scraping
- **When:** During scraping

---

## 🚀 **HOW TO ENABLE FEATURES**

### **Step 1: Edit config.json**
```bash
nano /workspace/telegran/config.json
```

### **Step 2: Add Advanced Section**
Scroll to bottom, add before closing `}`:
```json
,
"advanced": {
  "enable_behavioral_mimicry": true,
  "simulate_reading": true,
  "use_adaptive_limits": true,
  "learn_from_success": true
}
```

### **Step 3: Save & Run**
```bash
python3 userbot.py
```

---

## 📊 **WHAT RUNS WHEN**

### **Startup Sequence:**
```
1. Load config.json
2. Initialize database
3. Connect to Telegram
4. Assess account status ⭐ NEW
5. Offer warm-up (if new) ⭐ NEW
6. Scrape members (if enabled) ⭐ NEW
7. Start core welcome/help
8. Start background tasks ⭐ ENHANCED
```

### **Background Tasks:**
```
CORE (original):
- Reset hourly counter
- Print stats
- Process pending welcomes
- Cleanup database
- Retry failed messages
- Health monitoring
- Automated backups

ADVANCED (NEW!):
- Behavioral mimicry loop
- Continuous activity simulation
- Success pattern tracking
```

### **Per Message:**
```
CORE (original):
1. Detect new member
2. Check if already welcomed
3. Apply rate limits
4. Random delay
5. Send message

ADVANCED (NEW!):
1. Check user profile (if scraped)
2. Check priority score
3. Engage first (if enabled)
4. Use adaptive limit
5. Optimal delay calculation
6. Send with personalization
7. Learn from result
```

---

## 🎓 **UNDERSTANDING THE CODE**

### **Key Classes:**

#### **AccountStatus (enum)**
```python
Line: ~28-32
Values: NEW, WARMING, ESTABLISHED, TRUSTED
Used by: assess_account_status()
```

#### **UserProfile (dataclass)**
```python
Line: ~34-50
Fields: id, username, scores, stats
Used by: scraping & targeting
```

#### **StealthUserbot (main class)**
```python
Line: ~52-656
Contains: ALL features (core + advanced)
```

### **Key Variables:**

#### **self.account_status**
- Type: AccountStatus enum
- Set: assess_account_status()
- Used: Throughout for decision making

#### **self.trust_score**
- Type: float (0.0-1.0)
- Set: assess_account_status()
- Used: Adaptive limits, all safety checks

#### **self.user_profiles**
- Type: Dict[int, UserProfile]
- Set: scrape_members()
- Used: Targeting, scoring, prioritization

#### **self.success_patterns**
- Type: Dict[str, List[float]]
- Set: learn_from_success()
- Used: Optimization, improvement

---

## 💡 **QUICK REFERENCE**

### **Want Account Assessment?**
- **Where:** `assess_account_status()`
- **Line:** ~150-200
- **Config:** Automatic
- **Enable:** Always on

### **Want Warm-Up?**
- **Where:** `warmup_protocol()`
- **Line:** ~200-280
- **Config:** `advanced.enable_warmup = true`
- **Enable:** Set in config.json

### **Want Mimicry?**
- **Where:** `behavioral_mimicry_loop()`
- **Line:** ~630-656
- **Config:** `advanced.enable_behavioral_mimicry = true`
- **Enable:** Set in config.json

### **Want Scraping?**
- **Where:** `scrape_members()`
- **Line:** ~350-400
- **Config:** `advanced.enable_scraping = true`
- **Enable:** Set in config.json

### **Want Everything?**
```json
"advanced": {
  "enable_warmup": true,
  "enable_scraping": true,
  "enable_behavioral_mimicry": true,
  "simulate_reading": true,
  "simulate_profile_views": true,
  "simulate_reactions": true,
  "enable_social_scoring": true,
  "target_influencers_first": true,
  "enable_engagement_first": true,
  "use_adaptive_limits": true,
  "learn_from_success": true
}
```

---

## ✅ **VERIFICATION**

### **Check Integration:**
```bash
# 1. Check file size
wc -l userbot.py
# Should be 656+ lines

# 2. Check for advanced features
grep "assess_account_status" userbot.py
grep "warmup_protocol" userbot.py
grep "scrape_members" userbot.py
grep "behavioral_mimicry" userbot.py

# 3. Compile check
python3 -m py_compile userbot.py
# Should succeed with no errors
```

### **Check Config:**
```bash
# Check for advanced section
cat config.json | grep "advanced"
# Should show advanced section
```

---

## 🎉 **SUMMARY**

**Everything is in ONE file:** `userbot.py`

**Simple to use:**
1. Edit `config.json`
2. Enable features you want
3. Run `python3 userbot.py`
4. Done!

**No separate tools needed!**
**All features integrated!**
**Production ready!**

---

**📍 YOU NOW KNOW EXACTLY WHERE EVERYTHING IS! 📍**
