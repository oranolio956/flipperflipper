# ProxyAssessmentTool - Quick Start Guide

## Prerequisites

1. **Windows 10/11** (64-bit)
2. **.NET 8 SDK** (for building from source)
3. **Administrator privileges** (for service mode only)

## Installation

### Option 1: Pre-built Executable

1. Download `ProxyAssessmentTool.exe` from releases
2. Place in desired directory
3. Run the executable

### Option 2: Build from Source

```powershell
# Clone the repository
git clone <repository-url>
cd SHILLTIME

# Build the application
.\build.ps1 -Clean -Package

# The executable will be in dist/exe/
```

## First Run Setup

### 1. Launch the Application

Double-click `ProxyAssessmentTool.exe` or run from command line:

```cmd
ProxyAssessmentTool.exe
```

### 2. Complete Onboarding Wizard

**Step 1: Welcome**
- Review safety reminder
- Acknowledge consent requirements

**Step 2: Consent Setup**
- Enter your consent ID (e.g., "SEC-2024-001")
- Define initial scope:
  ```yaml
  # Example authorized networks
  - 10.0.0.0/16      # Corporate network
  - 172.16.0.0/12    # Lab environment
  - 192.168.1.0/24   # Test network
  ```
- Set do-not-scan list:
  ```yaml
  # Critical infrastructure to exclude
  - 10.0.0.1         # Core router
  - 10.0.0.0/29      # Management subnet
  ```

**Step 3: Configuration**
- Choose theme (Light/Dark/System)
- Configure canary endpoints:
  ```yaml
  - canary1.internal.local:443
  - canary2.internal.local:8080
  ```

## Basic Usage

### 1. Perform Discovery Scan

1. Navigate to **Discovery** in the left menu
2. Select target networks from authorized scope
3. Configure scan parameters:
   - Port range: Use defaults (proxy ports)
   - Rate limit: 60 requests/min (default)
   - Scan window: Business hours only
4. Click **Start Scan**
5. Monitor progress in real-time

### 2. Review Findings

1. Navigate to **Findings**
2. Apply filters to focus on eligible proxies:
   - Protocol: SOCKS5
   - Auth: No-Auth
   - Fraud Score: 0
   - Country: US
   - Mobile: Yes
3. View detailed information for each proxy
4. Export results as needed

### 3. Generate Reports

1. Navigate to **Reports**
2. Select report template:
   - Executive Summary
   - Technical Details
   - Remediation Plan
3. Choose date range
4. Click **Generate**
5. Download or email report

## Authorized Lab Testing

### Setting Up Test Environment

1. **Deploy Test Proxies**
   ```bash
   # SOCKS5 no-auth (ELIGIBLE)
   docker run -d -p 1080:1080 serjs/go-socks5-proxy

   # SOCKS5 with auth (NOT ELIGIBLE)
   docker run -d -p 1081:1080 -e PROXY_USER=user -e PROXY_PASS=pass serjs/go-socks5-proxy

   # HTTP proxy (NOT ELIGIBLE)
   docker run -d -p 3128:3128 datadog/squid
   ```

2. **Configure Canary Endpoints**
   ```bash
   # Simple echo server
   docker run -d -p 8080:8080 hashicorp/http-echo -text="PROXY-TEST-ECHO"
   ```

3. **Run Test Scan**
   - Add test subnet to authorized scope
   - Configure do-not-scan for production
   - Run discovery with test configuration

### Expected Results

| Proxy Type | Port | Expected Result |
|------------|------|-----------------|
| SOCKS5 no-auth | 1080 | ✓ Eligible (if US mobile + fraud=0) |
| SOCKS5 with auth | 1081 | ✗ Remediation only (auth required) |
| HTTP proxy | 3128 | ✗ Remediation only (not SOCKS5) |

## Configuration Reference

### Key Settings

```yaml
# Strict eligibility gates (cannot be disabled)
selection:
  require_protocol: "socks5"
  require_no_auth: true
  require_mobile: true
  require_us_location: true
  require_fraud_score: 0

# Discovery settings
discovery:
  rate_limit_per_cidr_per_min: 60
  timeout_seconds: 5
  max_concurrent_scans: 10

# Usage classification thresholds
usage:
  thresholds:
    unused_max_requests_per_day: 0
    low_usage_max_requests_per_day: 50
```

### Advanced Options

See `config/default.yaml` for all configuration options.

## Troubleshooting

### Common Issues

1. **"No consent ID configured"**
   - Solution: Complete onboarding wizard or edit config.yaml

2. **"Canary endpoints unreachable"**
   - Solution: Verify canary services are running
   - Check network connectivity
   - Update canary configuration

3. **"All proxies marked ineligible"**
   - This is expected if proxies don't meet ALL criteria
   - Check individual failure reasons in Findings view

4. **"Rate limit exceeded"**
   - Solution: Reduce concurrent scans
   - Increase rate limit delays
   - Use scan windows

### Logs and Diagnostics

Logs are stored in:
```
%APPDATA%\ProxyAssessmentTool\Logs\proxy-assessment-YYYY-MM-DD.log
```

Enable debug logging:
```yaml
logging:
  minimum_level: "Debug"
```

## Security Notes

1. **Consent is mandatory** - No scanning without valid consent ID
2. **Canary-only validation** - No external relay testing
3. **Strict eligibility** - Gates cannot be bypassed
4. **Audit trail** - All operations logged

## Getting Help

1. Check documentation in `/docs` folder
2. Review Requirements Traceability Matrix
3. Consult operational runbook
4. Contact security engineering team

## Quick Commands

### Command Line Usage

```cmd
# Run with custom config
ProxyAssessmentTool.exe --config custom.yaml

# Run in service mode
ProxyAssessmentTool.exe --service install
ProxyAssessmentTool.exe --service start

# API access (localhost only)
curl http://localhost:5000/api/findings
```

### PowerShell Integration

```powershell
# Get eligible findings
$findings = Invoke-RestMethod -Uri "http://localhost:5000/api/findings?eligible=true"

# Export to CSV
$findings | Export-Csv -Path "eligible-proxies.csv" -NoTypeInformation
```

---

**IMPORTANT SAFETY REMINDER**: This tool is for consent-based assessment of your own or explicitly authorized assets only. Do not use it to discover or assess third-party systems without written permission. Do not relay traffic through discovered proxies to external destinations.