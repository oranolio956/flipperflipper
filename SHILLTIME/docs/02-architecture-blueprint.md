# 2. Architecture Blueprint (Windows-Specific)

## 2.1 High-Level Architecture

The ProxyAssessmentTool follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    WPF UI Layer (MVVM)                      │
│  Views │ ViewModels │ Converters │ Controls │ Behaviors    │
├─────────────────────────────────────────────────────────────┤
│                 Application Core (Orchestrator)              │
│  Message Bus │ Config │ Consent │ Audit │ Evidence Store   │
├─────────────────────────────────────────────────────────────┤
│                     Service Modules                          │
│ Discovery │ Fingerprint │ Validate │ Usage │ Reputation    │
│ Geo/ASN │ Social │ Uptime │ Risk │ Report │ Remediation   │
├─────────────────────────────────────────────────────────────┤
│                      Data Layer                              │
│  SQLite │ DPAPI │ File System │ Event Log │ Named Pipes    │
└─────────────────────────────────────────────────────────────┘
```

## 2.2 Component Details

### 2.2.1 UI Layer (WPF)

**Views**
- MainWindow.xaml: Primary application window with navigation
- DashboardView.xaml: Overview and metrics
- ScopeConsentView.xaml: Authorization management
- DiscoveryView.xaml: Network scanning interface
- ValidationView.xaml: Proxy verification results
- FindingsView.xaml: Detailed proxy listings
- ReportsView.xaml: Report generation and export
- SettingsView.xaml: Configuration management

**ViewModels (MVVM)**
- BaseViewModel: Common functionality, INotifyPropertyChanged
- MainViewModel: Navigation and global state
- DashboardViewModel: Metrics aggregation
- DiscoveryViewModel: Scan orchestration
- FindingsViewModel: Result filtering and display

**Key Features**
- Fluent Design System aesthetics
- Light/Dark theme support
- WCAG 2.2 AA accessibility
- Keyboard navigation (Tab, arrows, shortcuts)
- High DPI support
- Touch-friendly controls

### 2.2.2 Application Core

**Orchestrator Service**
```csharp
public interface IOrchestrator
{
    Task<ScanResult> ExecuteScanAsync(ScanRequest request, CancellationToken ct);
    Task<ValidationResult> ValidateProxyAsync(ProxyCandidate candidate, CancellationToken ct);
    Task<EligibilityResult> CheckEligibilityAsync(Finding finding);
    Task<RemediationPlan> GenerateRemediationAsync(Finding finding);
}
```

**Message Bus**
- Event-driven communication between modules
- Pub/Sub pattern for loose coupling
- Priority queuing for critical events

**Configuration Manager**
```csharp
public interface IConfigurationManager
{
    AppConfiguration Load(string path);
    void Validate(AppConfiguration config);
    void SaveSecure(AppConfiguration config);
    event EventHandler<ConfigurationChangedEventArgs> ConfigurationChanged;
}
```

**Consent Ledger**
```csharp
public interface IConsentLedger
{
    Task<ConsentRecord> RecordConsentAsync(ConsentRequest request);
    Task<bool> ValidateConsentAsync(string consentId, IPAddress target);
    Task<ConsentAudit[]> GetAuditTrailAsync(string consentId);
    Task RevokeConsentAsync(string consentId, string reason);
}
```

**Audit Logger**
```csharp
public interface IAuditLogger
{
    Task LogSecurityEventAsync(SecurityEvent evt);
    Task LogOperationAsync(Operation op, OperationResult result);
    Task LogConfigChangeAsync(ConfigChange change);
    Task<AuditRecord[]> QueryAuditLogAsync(AuditQuery query);
}
```

### 2.2.3 Service Modules

**Discovery Engine**
```csharp
public interface IDiscoveryEngine
{
    Task<DiscoveryResult> DiscoverAsync(DiscoveryScope scope, CancellationToken ct);
    Task<bool> IsInScopeAsync(IPAddress address);
    void ConfigureRateLimiting(RateLimitConfig config);
}
```

**Protocol Fingerprinter**
```csharp
public interface IProtocolFingerprinter
{
    Task<FingerprintResult> IdentifyProtocolAsync(IPEndPoint endpoint);
    Task<Socks5Metadata> GetSocks5DetailsAsync(IPEndPoint endpoint);
    bool SupportsNoAuth(Socks5Metadata metadata);
}
```

**Safe Validator**
```csharp
public interface ISafeValidator
{
    Task<ValidationResult> ValidateAsync(ProxyCandidate candidate, CanaryEndpoint canary);
    Task<bool> TestConnectivityAsync(ProxyCandidate candidate);
    Task<AuthMethod[]> GetSupportedAuthMethodsAsync(ProxyCandidate candidate);
}
```

**Usage Classifier**
```csharp
public interface IUsageClassifier
{
    Task<UsageMetrics> AnalyzeUsageAsync(IPAddress proxy, TimeSpan lookback);
    Task<UsageClass> ClassifyAsync(UsageMetrics metrics);
    Task<TelemetrySource[]> GetAvailableSourcesAsync();
}
```

**Reputation Analyzer**
```csharp
public interface IReputationAnalyzer
{
    Task<ReputationScore> GetScoreAsync(IPAddress address);
    Task<FraudIndicators> GetFraudIndicatorsAsync(IPAddress address);
    bool MeetsEligibilityCriteria(ReputationScore score); // score == 0
}
```

**Geo/ASN Enrichment**
```csharp
public interface IGeoAsnEnrichment
{
    Task<GeoLocation> GetLocationAsync(IPAddress address);
    Task<AsnInfo> GetAsnInfoAsync(IPAddress address);
    bool IsMobileNetwork(AsnInfo asn);
    bool IsUnitedStates(GeoLocation location);
}
```

### 2.2.4 Data Layer

**SQLite Schema**
```sql
-- Main findings table
CREATE TABLE findings (
    id TEXT PRIMARY KEY,
    discovered_at TIMESTAMP NOT NULL,
    ip_address TEXT NOT NULL,
    port INTEGER NOT NULL,
    protocol TEXT NOT NULL,
    auth_methods TEXT,
    fraud_score REAL,
    country_code TEXT,
    state TEXT,
    city TEXT,
    asn INTEGER,
    is_mobile BOOLEAN,
    usage_class TEXT,
    risk_score REAL,
    evidence_hash TEXT NOT NULL,
    UNIQUE(ip_address, port)
);

-- Audit log
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT,
    result TEXT,
    details TEXT,
    consent_id TEXT
);

-- Uptime tracking
CREATE TABLE uptime_history (
    proxy_id TEXT NOT NULL,
    checked_at TIMESTAMP NOT NULL,
    status TEXT NOT NULL,
    response_time_ms INTEGER,
    error_details TEXT,
    FOREIGN KEY (proxy_id) REFERENCES findings(id)
);

-- Evidence store
CREATE TABLE evidence (
    hash TEXT PRIMARY KEY,
    finding_id TEXT NOT NULL,
    type TEXT NOT NULL,
    data BLOB NOT NULL,
    created_at TIMESTAMP NOT NULL,
    integrity_hash TEXT NOT NULL,
    FOREIGN KEY (finding_id) REFERENCES findings(id)
);
```

**Encryption**
- SQLite database encrypted using SQLCipher
- Secrets protected with Windows DPAPI
- Evidence files encrypted with AES-256-GCM
- Key rotation every 90 days

## 2.3 Data Flow

### 2.3.1 Discovery Flow
```
User Input → Consent Validation → Scope Definition → 
Discovery Engine → Rate Limiting → Target Enumeration →
Port Scanning → Protocol Detection → Candidate Queue
```

### 2.3.2 Validation Flow
```
Candidate Queue → Fingerprinting → SOCKS5 Check →
Auth Method Detection → No-Auth Gate → Canary Connection →
Echo Validation → Result Recording
```

### 2.3.3 Enrichment Flow
```
Validated Proxy → Usage Analysis → Reputation Check →
Fraud Score Gate (==0) → Geo Lookup → US Check →
ASN Analysis → Mobile Check → Social Compat →
Uptime Monitoring → Risk Scoring
```

### 2.3.4 Eligibility Decision
```
All Data → Eligibility Gates:
  - Protocol == SOCKS5
  - Auth == No-Auth (0x00)
  - Fraud Score == 0
  - Country == US
  - Is Mobile == True
→ Final Classification (Eligible/Remediation-Only)
```

## 2.4 Deployment Architecture

### 2.4.1 Standalone Mode
```
ProxyAssessmentTool.exe
├── UI Process (User Context)
├── Core Services (In-Process)
├── SQLite Database (User AppData)
└── Logs (User AppData)
```

### 2.4.2 Service Mode
```
ProxyAssessmentService (Windows Service)
├── Background Scanner
├── API Server (localhost:5000)
├── Named Pipe Server
└── Scheduled Tasks

ProxyAssessmentTool.exe (UI)
├── Service Client
├── Named Pipe Client
└── Read-Only Database Access
```

### 2.4.3 File Locations
```
%ProgramFiles%\ProxyAssessmentTool\
├── ProxyAssessmentTool.exe
├── *.dll (dependencies)
├── GeoIP2-City.mmdb
├── mobile-asns.json
└── config\
    └── default.yaml

%AppData%\ProxyAssessmentTool\
├── config.yaml (user overrides)
├── proxy-assessment.db
├── evidence\
│   └── {hash}\
└── logs\
    └── proxy-assessment-{date}.log

%ProgramData%\ProxyAssessmentTool\ (Service Mode)
├── service-config.yaml
├── service.db
└── service-logs\
```

## 2.5 Security Architecture

### 2.5.1 Authentication & Authorization
```csharp
public interface IAuthenticationService
{
    Task<AuthResult> AuthenticateAsync(Credentials credentials);
    Task<bool> AuthorizeAsync(ClaimsPrincipal principal, Permission permission);
    Task<SsoResult> AuthenticateViaSSO(SsoProvider provider);
}

public enum Role
{
    Viewer,      // Read-only access
    Operator,    // Run scans, view results
    Admin,       // Full configuration access
    Auditor      // Audit log access only
}
```

### 2.5.2 Secrets Management
- Windows DPAPI for local secrets
- Certificate-based encryption for exports
- No hardcoded credentials
- Secure credential prompting when needed

### 2.5.3 Network Security
- TLS 1.2+ for all HTTPS connections
- Certificate pinning for known services
- Proxy connections via SOCKS5 only to canaries
- No direct internet connections in air-gapped mode

## 2.6 Performance Specifications

### 2.6.1 Scalability Targets
- Handle 10,000+ targets without UI freeze
- Process 1,000 proxies/minute (discovery)
- Validate 100 proxies/minute (with canary)
- Store 1M findings with <1s query time

### 2.6.2 Resource Limits
- Memory: <2GB for typical operation
- CPU: <25% average on 4-core system
- Disk: <10GB for 90-day retention
- Network: Respect configured rate limits

### 2.6.3 Optimization Strategies
- Async/await throughout
- Parallel processing with configurable concurrency
- Database indexing on key fields
- Lazy loading for large datasets
- Background task queuing

## 2.7 Gotchas & Pitfalls

### 2.7.1 Common Issues
1. **Windows Defender**: May flag network scanning
   - Solution: Code signing, reputation building

2. **Corporate Proxies**: May interfere with detection
   - Solution: Proxy-aware networking, bypass options

3. **UAC Prompts**: Service installation requires elevation
   - Solution: Clear documentation, manifest marking

4. **Database Locking**: SQLite concurrency limits
   - Solution: Write-ahead logging, connection pooling

5. **Memory Leaks**: Event handler subscriptions
   - Solution: Weak references, proper disposal

### 2.7.2 Technical Gotchas
1. **SOCKS5 Variations**: Implementations differ
   - Solution: Strict RFC 1928 compliance, quirks mode

2. **Mobile Network Detection**: CGNAT complicates detection
   - Solution: Multiple signals (ASN + rDNS + WHOIS)

3. **Geo Accuracy**: VPNs/proxies affect geolocation
   - Solution: Multi-source correlation, confidence scores

4. **Rate Limiting**: Target networks may block
   - Solution: Adaptive throttling, backoff algorithms

## 2.8 Quality Checks

### 2.8.1 Startup Checks
```csharp
public class StartupValidator
{
    public async Task<ValidationResult> ValidateAsync()
    {
        var checks = new[]
        {
            CheckDatabaseIntegrity(),
            CheckCanaryReachability(),
            CheckGeoIpDatabase(),
            CheckAsnList(),
            CheckConfigValidity(),
            CheckAuditLogWriteable(),
            CheckDiskSpace(),
            CheckNetworkConnectivity()
        };
        
        return await Task.WhenAll(checks);
    }
}
```

### 2.8.2 Runtime Monitoring
- Health endpoint: /health (localhost only)
- Metrics collection: Performance counters
- Error tracking: Structured logging
- Resource monitoring: Memory/CPU alerts

### 2.8.3 Data Quality
- Finding deduplication
- Evidence integrity verification
- Audit log tamper detection
- Configuration validation