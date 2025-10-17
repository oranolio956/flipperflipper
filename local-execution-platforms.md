# Local Execution Interview Platforms

## 🖥️ Platforms That Run Locally on Desktop

These solutions can be downloaded and run entirely on the local machine without requiring cloud infrastructure.

---

## 1. **VS Code + Live Share** (Most Practical)

### Installation & Setup
```bash
# Interviewer setup:
1. Download VS Code: https://code.visualstudio.com/
2. Install Live Share extension
3. Sign in with GitHub/Microsoft account
4. Click "Share" to start session

# Candidate setup:
1. Download VS Code (or use browser)
2. Join with shared link
```

### Features Running Locally:
- ✅ Full IDE runs on desktop
- ✅ Code execution on local machine
- ✅ Debugging capabilities
- ✅ Terminal access (if permitted)
- ✅ Local file system access

### How to Distribute:
```bash
# Create a portable VS Code package with extensions
# Windows example:
1. Download VS Code portable
2. Pre-install extensions
3. Create ZIP file
4. Share with candidates
```

---

## 2. **Standalone Electron Interview App**

### Create Your Own Desktop App:

**Project Structure:**
```
interview-desktop/
├── main.js           # Electron main process
├── renderer.js       # UI and collaboration logic  
├── package.json      # Dependencies
├── preload.js        # Security bridge
└── index.html        # Main UI
```

**main.js:**
```javascript
const { app, BrowserWindow, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let mainWindow;
let codeProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  mainWindow.loadFile('index.html');
}

// Handle code execution
ipcMain.handle('execute-code', async (event, code, language) => {
  return new Promise((resolve) => {
    let command, args;
    
    switch(language) {
      case 'python':
        command = 'python';
        args = ['-c', code];
        break;
      case 'javascript':
        command = 'node';
        args = ['-e', code];
        break;
      case 'java':
        // Would need compilation first
        command = 'java';
        args = [];
        break;
    }
    
    codeProcess = spawn(command, args);
    let output = '';
    
    codeProcess.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    codeProcess.stderr.on('data', (data) => {
      output += 'Error: ' + data.toString();
    });
    
    codeProcess.on('close', (code) => {
      resolve({ output, exitCode: code });
    });
  });
});

app.whenReady().then(createWindow);
```

**preload.js:**
```javascript
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  executeCode: (code, language) => ipcRenderer.invoke('execute-code', code, language)
});
```

**index.html:**
```html
<!DOCTYPE html>
<html>
<head>
  <title>Interview Platform</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
    #editor { width: 100%; height: 400px; border: 1px solid #ddd; }
    #output { background: #f4f4f4; padding: 10px; margin-top: 20px; }
  </style>
</head>
<body>
  <h1>Code Interview Platform</h1>
  
  <select id="language">
    <option value="javascript">JavaScript</option>
    <option value="python">Python</option>
    <option value="java">Java</option>
  </select>
  
  <textarea id="editor" placeholder="Write your code here..."></textarea>
  
  <button onclick="runCode()">Run Code</button>
  
  <div id="output"></div>
  
  <script>
    async function runCode() {
      const code = document.getElementById('editor').value;
      const language = document.getElementById('language').value;
      
      const result = await window.electronAPI.executeCode(code, language);
      document.getElementById('output').innerText = result.output;
    }
  </script>
</body>
</html>
```

**Building & Distribution:**
```bash
# Install dependencies
npm init -y
npm install electron electron-builder

# Package for distribution
npm run build-win    # Creates .exe installer
npm run build-mac    # Creates .dmg installer  
npm run build-linux  # Creates .AppImage
```

---

## 3. **Portable Code Runner Package**

### Create a portable interview environment:

**Package Contents:**
```
InterviewKit/
├── VSCodePortable/       # Portable VS Code
├── Python/               # Portable Python
├── Node/                 # Portable Node.js
├── Java/                 # Portable JDK
├── start-interview.bat   # Windows launcher
├── start-interview.sh    # Mac/Linux launcher
└── README.txt
```

**start-interview.bat (Windows):**
```batch
@echo off
echo Starting Interview Environment...

REM Set paths
set PATH=%~dp0Python;%~dp0Node;%~dp0Java\bin;%PATH%

REM Start VS Code with specific workspace
start "" "%~dp0VSCodePortable\Code.exe" "%~dp0workspace"

REM Start local collaboration server (optional)
cd "%~dp0"
node server.js
```

**server.js (Local collaboration server):**
```javascript
const express = require('express');
const http = require('http');
const socketIO = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = socketIO(server);

app.use(express.static('public'));

io.on('connection', (socket) => {
  console.log('User connected');
  
  socket.on('code-change', (data) => {
    socket.broadcast.emit('code-update', data);
  });
  
  socket.on('run-code', async (data) => {
    // Execute code locally
    const result = await executeCode(data.code, data.language);
    io.emit('execution-result', result);
  });
});

server.listen(3000, () => {
  console.log('Interview platform running on http://localhost:3000');
});
```

---

## 4. **Docker-Based Desktop Solution**

### Package everything in Docker:

**Dockerfile:**
```dockerfile
FROM ubuntu:22.04

# Install development tools
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    nodejs npm \
    openjdk-11-jdk \
    gcc g++ \
    git vim

# Install code-server (VS Code in browser)
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Copy interview platform files
COPY . /workspace

WORKDIR /workspace

# Expose port for web interface
EXPOSE 8080

# Start code-server
CMD ["code-server", "--bind-addr", "0.0.0.0:8080", "--auth", "none", "/workspace"]
```

**docker-compose.yml:**
```yaml
version: '3'
services:
  interview-platform:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./workspace:/workspace
    environment:
      - PASSWORD=interview123
```

**Distribution:**
```bash
# Package as single executable (Windows)
docker save interview-platform | gzip > interview-platform.tar.gz

# Create installer script
echo "docker load < interview-platform.tar.gz && docker-compose up" > run.sh
```

---

## 5. **Jupyter Notebook Package**

### For Python/Data Science Interviews:

**Setup Script:**
```python
# setup_interview.py
import subprocess
import os
import webbrowser

def setup_interview_env():
    # Create virtual environment
    subprocess.run(["python", "-m", "venv", "interview_env"])
    
    # Activate and install packages
    if os.name == 'nt':  # Windows
        activate = r"interview_env\Scripts\activate.bat && "
    else:  # Unix
        activate = "source interview_env/bin/activate && "
    
    # Install Jupyter and extensions
    subprocess.run(activate + "pip install jupyter jupyterlab jupyter-collaboration", shell=True)
    
    # Start Jupyter with collaboration
    subprocess.run(activate + "jupyter lab --collaborative", shell=True)

if __name__ == "__main__":
    setup_interview_env()
```

---

## 6. **All-in-One Installer Package**

### Create a complete installer with everything:

**Using NSIS (Windows):**
```nsis
!include "MUI2.nsh"

Name "Interview Platform"
OutFile "InterviewPlatform-Setup.exe"
InstallDir "$PROGRAMFILES\InterviewPlatform"

Section "Main Application"
  SetOutPath "$INSTDIR"
  
  ; Copy application files
  File /r "app\*.*"
  
  ; Install Python silently
  ExecWait '"$INSTDIR\python-installer.exe" /quiet'
  
  ; Install Node.js silently  
  ExecWait 'msiexec /i "$INSTDIR\node.msi" /quiet'
  
  ; Create shortcuts
  CreateShortcut "$DESKTOP\Interview Platform.lnk" "$INSTDIR\start.exe"
SectionEnd
```

---

## 🔐 Security Considerations for Local Execution

### Sandboxing Code Execution:
```javascript
// Use Docker for sandboxing
const { spawn } = require('child_process');

function executeInSandbox(code, language) {
  return new Promise((resolve) => {
    const docker = spawn('docker', [
      'run',
      '--rm',           // Remove container after execution
      '--network=none', // No network access
      '--memory=512m',  // Limit memory
      '--cpus=1',       // Limit CPU
      '-v', `${__dirname}/code:/code:ro`,  // Read-only volume
      `interview-${language}`,
      language, '/code/script'
    ]);
    
    // Handle output...
  });
}
```

---

## 📦 Distribution Methods

### 1. **USB Drive Package**
```
InterviewUSB/
├── Windows/
│   └── InterviewPlatform.exe
├── Mac/
│   └── InterviewPlatform.app
├── Linux/
│   └── InterviewPlatform.AppImage
└── README.txt
```

### 2. **Private Download Server**
```nginx
# Nginx config for secure download
location /download {
    auth_basic "Interview Platform";
    auth_basic_user_file /etc/nginx/.htpasswd;
    alias /var/www/downloads/;
}
```

### 3. **Temporary Access Codes**
```javascript
// Generate temporary download links
function generateDownloadLink() {
  const code = crypto.randomBytes(16).toString('hex');
  const expires = Date.now() + (24 * 60 * 60 * 1000); // 24 hours
  
  return {
    url: `https://download.company.com/interview/${code}`,
    expires: expires
  };
}
```

---

## ⚡ Quick Start Recommendation

**For immediate local execution needs:**

1. **Fastest**: Use VS Code + Live Share
2. **Most Control**: Build Electron app with sandboxed execution
3. **Most Portable**: Docker-based solution
4. **Simplest Distribution**: All-in-one installer

---

## 📋 Checklist for Desktop Deployment

- [ ] Code signing certificates obtained
- [ ] Sandboxing implemented for code execution
- [ ] Auto-update mechanism configured
- [ ] Uninstaller included
- [ ] Privacy policy and terms included
- [ ] Tested on all target OS versions
- [ ] Antivirus false-positive checks done
- [ ] Distribution method secured
- [ ] Support documentation prepared
- [ ] Rollback plan ready

---

*Remember: Desktop applications have significant security implications. Always use sandboxing for code execution and get proper legal/security review before deployment.*