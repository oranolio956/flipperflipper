# ProxyAssessmentTool - Windows Desktop Security Assessment Application

**IMPORTANT SAFETY REMINDER**: This guidance is solely for consent-based assessment of your own or explicitly authorized assets. Do not use it to discover or assess third-party systems without written permission. Do not generate or run code that relays traffic through discovered proxies to external destinations.

## Quick Start - Installation

**Easy Install**: Simply run **`INSTALL_ProxyAssessmentTool.bat`** as Administrator

The installer will automatically:
- ✅ Assemble the application from parts
- ✅ Install to Program Files
- ✅ Create desktop and Start Menu shortcuts
- ✅ Set up required directories
- ✅ Provide an uninstaller

## Overview

A Windows desktop application for autonomous discovery and assessment of potentially misconfigured proxy services within owned or explicitly authorized assets. The tool enforces strict eligibility criteria and provides comprehensive remediation guidance.

## Key Features

1. **Autonomous Discovery**: Consent-based scanning of authorized networks only
2. **Protocol Support**: SOCKS5 (no-auth only), HTTP, transparent proxies (visibility only)
3. **Strict Eligibility Gates**:
   - Protocol: SOCKS5 only
   - Authentication: No authentication required (0x00)
   - Reputation: Fraud score exactly 0/10
   - Geography: United States only with state/city enrichment
   - Network Type: Mobile (U.S. carrier networks only)
4. **Usage Classification**: Owner-side telemetry analysis
5. **Social Media Compatibility**: Synthetic testing by default
6. **Leakage Detection**: DNS and WebRTC leak checks
7. **Uptime Monitoring**: SLO-based health tracking
8. **Risk Scoring**: Weighted severity assessment
9. **Remediation**: Detailed playbooks and notifications

## Architecture

### Layers

1. **UI Layer** (WPF)
   - Fluent-inspired design with light/dark themes
   - MVVM pattern with data binding
   - Accessibility (WCAG 2.2 AA) compliance

2. **Application Core**
   - Orchestrator with message bus
   - Configuration management
   - Consent ledger
   - Audit logging
   - Evidence store

3. **Service Modules**
   - Inventory Provider
   - Discovery Engine
   - Protocol Fingerprinter
   - Safe Validator
   - Usage Classifier
   - Reputation/Fraud Analyzer
   - Geo/ASN Enrichment
   - Social Compatibility Analyzer
   - Uptime Monitor
   - Risk Scorer
   - Report Generator

4. **Data Layer**
   - SQLite with encrypted storage
   - Write-once evidence model
   - Append-only audit trail

5. **Security**
   - Windows DPAPI for secrets
   - RBAC with optional SSO
   - Code signing
   - Tamper-evident logs

## Installation

### Prerequisites

- Windows 10/11 (64-bit)
- .NET 8.0 Runtime
- Administrator privileges (for service installation only)

### Deployment Options

1. **Self-contained EXE**: Single executable with all dependencies
2. **MSIX Package**: Windows Store compatible package
3. **Service Mode**: Background scanning with UI frontend

## Configuration

The application uses a YAML configuration file with strict defaults. See `config/default.yaml` for the complete schema.

## Usage

1. **Initial Setup**
   - Launch application
   - Complete onboarding wizard
   - Provide consent ID and scope
   - Configure do-not-scan lists

2. **Discovery**
   - Define authorized networks (CIDRs, cloud accounts)
   - Set rate limits and scan windows
   - Run discovery with emergency stop available

3. **Validation**
   - Automatic protocol fingerprinting
   - Safe validation against owner canaries
   - No external relay testing

4. **Analysis**
   - Usage classification from owner telemetry
   - Reputation scoring (0/10 gate)
   - Geo/mobile network verification
   - Compatibility testing

5. **Reporting**
   - Executive and technical reports
   - Evidence packages
   - Remediation guidance
   - Automated notifications

## Security Model

- **Consent-based**: All operations require explicit authorization
- **Owner-only**: No third-party system assessment
- **Privacy-first**: Minimal data collection, PII scrubbing
- **Air-gapped capable**: Offline operation with signed updates
- **Audit trail**: Complete forensic logging

## Testing

Comprehensive test suite including:
- Unit tests for all modules
- Integration tests with synthetic lab
- End-to-end workflow validation
- Safety tests (no external relays)
- Load and performance tests

## License

Proprietary - Internal Use Only

## Support

For questions or issues, contact the security engineering team.