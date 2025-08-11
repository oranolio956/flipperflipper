# 22. Requirements-to-Artifacts Traceability Matrix

## Overview

This matrix maps each numbered requirement to its implementation artifacts across UI screens, services, schemas, tests, logs/metrics, and documentation.

## Traceability Matrix

| Requirement | UI Components | Services/Modules | Schemas | Tests | Logs/Metrics | Docs |
|-------------|---------------|------------------|---------|-------|--------------|------|
| **1. Autonomous Discovery** | DiscoveryView, ScopeConsentView | DiscoveryEngine, ConsentLedger | ScopeConfiguration, DiscoveryConfiguration | DiscoveryEngineTests, ConsentValidationTests | discovery_started, discovery_completed, targets_scanned | 04-discovery-strategy.md |
| **2. Protocol Validation** | ValidationView, FindingsView | ProtocolFingerprinter, SafeValidator | Finding, ValidationResult | FingerprintTests, ValidationTests | validation_attempted, validation_result, protocol_detected | 05-protocol-fingerprinting-validation.md |
| **3. Usage Classification** | FindingsView (Usage column) | UsageClassifier, TelemetryAnalyzer | UsageMetrics, UsageClass | UsageClassifierTests, TelemetryParserTests | usage_analyzed, classification_result | 06-usage-classification.md |
| **4. SOCKS5 No-Auth Only** | ValidationView, FindingsView (filters) | SafeValidator, AuthMethodValidator | AuthMethod, Socks5Metadata | Socks5HandshakeTests, AuthFilterTests | auth_method_detected, eligibility_check | 05-protocol-fingerprinting-validation.md |
| **5. Mobile US Only** | FindingsView (Geo/ASN columns) | GeoAsnEnrichment, MobileDetector | GeoLocation, AsnInfo | GeoEnrichmentTests, MobileDetectionTests | geo_lookup, asn_lookup, mobile_check | 08-geo-asn-classification.md |
| **6. Fraud Score 0/10 Gate** | FindingsView (Fraud column) | ReputationAnalyzer, FraudScorer | ReputationScore, FraudIndicator | ReputationTests, FraudGateTests | fraud_score_check, reputation_lookup | 07-reputation-fraud-scoring.md |
| **7. Social Compatibility** | FindingsView (Compat column) | SocialCompatibilityAnalyzer | CompatibilityProfile | CompatibilityTests, SyntheticTests | compatibility_test_run, platform_test_result | 09-social-media-compatibility.md |
| **8. Uptime Monitoring** | FindingsView (Uptime %), UptimeView | UptimeMonitor, HealthChecker | UptimeHistory | UptimeMonitorTests, SLOTests | uptime_probe, slo_calculation | 11-uptime-monitoring.md |
| **9. Risk Scoring** | FindingsView (Risk column), DashboardView | RiskScorer, RiskAggregator | RiskScore, RiskFactor | RiskScoringTests, ThresholdTests | risk_calculated, severity_assigned | 12-risk-scoring.md |
| **10. Windows UI** | All Views, MainWindow | NavigationService, ThemeService | N/A | UIAutomationTests, AccessibilityTests | ui_interaction, navigation_event | 03-ux-ui-design-spec.md |
| **11. DNS/WebRTC Leaks** | FindingsView (Leakage status) | LeakageChecker, DnsLeakDetector | LeakageTestResults | LeakageTests, WebRtcTests | leak_test_performed, leak_detected | 10-leakage-compatibility.md |
| **12. Evidence Model** | FindingsView (Evidence links) | EvidenceStore, HashCalculator | EvidenceItem, Evidence | EvidenceIntegrityTests | evidence_stored, hash_calculated | 13-evidence-model.md |
| **13. Remediation** | RemediationView, ReportsView | RemediationGenerator | RemediationStep | RemediationTests | remediation_generated, ticket_created | 14-remediation-playbooks.md |
| **14. Notifications** | NotificationPanel, ReportsView | NotificationService, ReportGenerator | Report, NotificationConfig | NotificationTests | notification_sent, report_generated | 18-notification-reporting.md |
| **15. Configuration** | SettingsView | ConfigurationManager | AppConfiguration | ConfigValidationTests | config_loaded, config_changed | default.yaml |
| **16. Audit Trail** | AuditLogView (Admin only) | AuditLogger | AuditRecord | AuditLogTests | audit_event_logged | 02-architecture-blueprint.md |
| **17. RBAC/SSO** | LoginView, UserMenu | AuthenticationService | Role, Permission | AuthTests, RBACTests | login_attempt, role_check | 20-security-privacy.md |
| **18. Air-gapped Mode** | SettingsView (Offline toggle) | OfflineManager | OfflineConfig | OfflineModeTests | offline_mode_enabled | 20-security-privacy.md |
| **19. SIEM Integration** | SettingsView (Integrations) | SiemExporter | SiemConfig | IntegrationTests | siem_export, event_forwarded | 21-integrations.md |
| **20. API/CLI** | N/A (headless) | ApiServer, CliHandler | ApiConfiguration | ApiTests, CliTests | api_request, cli_command | 21-integrations.md |

## Detailed Component Mappings

### UI Screen Details

#### DashboardView
- **Requirements**: 9 (Risk overview), 10 (Windows UI)
- **Components**: SummaryCards, RiskChart, GeoMap, ActivityTimeline
- **Data Sources**: FindingsRepository, MetricsAggregator
- **User Actions**: Navigate to details, refresh data, export summary

#### ScopeConsentView
- **Requirements**: 1 (Discovery scope)
- **Components**: ConsentManager, NetworkList, DoNotScanList
- **Data Sources**: ConsentLedger, ScopeConfiguration
- **User Actions**: Add/remove networks, update consent, view history

#### DiscoveryView
- **Requirements**: 1 (Autonomous discovery)
- **Components**: ScanConfigurator, ProgressBar, LiveResults
- **Data Sources**: DiscoveryEngine, RateLimiter
- **User Actions**: Start/stop scan, configure parameters, emergency stop

#### ValidationView
- **Requirements**: 2 (Validation), 4 (SOCKS5 no-auth)
- **Components**: ValidationQueue, ResultsGrid, DetailPanel
- **Data Sources**: SafeValidator, ProtocolFingerprinter
- **User Actions**: View results, retry validation, export transcripts

#### FindingsView
- **Requirements**: 3-9, 11-12 (All enrichment data)
- **Components**: FilterBar, ResultsGrid, DetailView, BulkActions
- **Data Sources**: FindingsRepository, all enrichment services
- **User Actions**: Filter, sort, export, generate reports, view evidence

### Service Module Details

#### DiscoveryEngine
```csharp
public interface IDiscoveryEngine
{
    Task<DiscoveryResult> DiscoverAsync(DiscoveryScope scope, CancellationToken ct);
    Task<bool> IsInScopeAsync(IPAddress address);
    void ConfigureRateLimiting(RateLimitConfig config);
}
```
- **Tests**: Unit (scope validation), Integration (network scanning), Load (concurrent scans)
- **Metrics**: targets_scanned, scan_duration, errors_encountered

#### SafeValidator
```csharp
public interface ISafeValidator
{
    Task<ValidationResult> ValidateAsync(ProxyCandidate candidate, CanaryEndpoint canary);
    Task<bool> TestConnectivityAsync(ProxyCandidate candidate);
    Task<AuthMethod[]> GetSupportedAuthMethodsAsync(ProxyCandidate candidate);
}
```
- **Tests**: Unit (protocol parsing), Integration (canary connection), Safety (no external relays)
- **Metrics**: validations_performed, canary_connections, auth_methods_detected

### Schema Details

#### Finding (Primary Entity)
```csharp
public class Finding
{
    public string Id { get; set; }
    public IPAddress IpAddress { get; set; }
    public int Port { get; set; }
    public ProxyProtocol Protocol { get; set; }
    public AuthMethod SelectedAuthMethod { get; set; }
    public double FraudScore { get; set; }
    public string CountryCode { get; set; }
    public bool IsMobile { get; set; }
    public UsageClass UsageClass { get; set; }
    public double RiskScore { get; set; }
    public bool IsEligible { get; set; }
    // ... additional properties
}
```

### Test Coverage

#### Unit Tests
- **Coverage Target**: 80%
- **Key Areas**: Business logic, eligibility gates, parsers, validators
- **Framework**: xUnit, Moq, FluentAssertions

#### Integration Tests
- **Coverage Target**: 60%
- **Key Areas**: Service interactions, database operations, API calls
- **Framework**: TestContainers, WireMock

#### E2E Tests
- **Coverage Target**: Critical paths
- **Key Areas**: Full discovery → validation → enrichment → reporting flow
- **Framework**: SpecFlow, Selenium

#### Safety Tests
- **Key Validations**:
  - No external network connections beyond canaries
  - Consent enforcement on every operation
  - Rate limiting effectiveness
  - Do-not-scan list compliance

### Logging & Metrics

#### Structured Logging
```csharp
_logger.LogInformation("Proxy validated", new
{
    ProxyId = finding.Id,
    Protocol = finding.Protocol,
    AuthMethod = finding.SelectedAuthMethod,
    IsEligible = finding.IsEligible,
    ValidationDuration = duration,
    ConsentId = consentId
});
```

#### Key Metrics
- **discovery_coverage**: % of authorized IPs scanned
- **validation_success_rate**: Successful validations / attempts
- **eligibility_rate**: Eligible proxies / total validated
- **fraud_gate_effectiveness**: Proxies blocked by fraud score
- **geo_compliance**: US mobile proxies / total
- **uptime_slo**: % meeting uptime targets
- **remediation_completion**: Completed / generated

### Documentation Coverage

Each requirement maps to detailed documentation:
1. Problem framing (01-problem-framing.md)
2. Architecture (02-architecture-blueprint.md)
3. UI/UX specifications (03-ux-ui-design-spec.md)
4. Implementation guides (04-21-*.md)
5. Configuration reference (default.yaml)
6. API documentation (generated from code)
7. Operational runbook (19-operational-runbook.md)

## Compliance Verification

### Acceptance Criteria Mapping

| Criterion | Implementation | Verification Method |
|-----------|----------------|-------------------|
| Consent required for all scans | ConsentLedger.ValidateConsentAsync() | Audit log review, integration tests |
| SOCKS5 no-auth only eligible | AuthMethodValidator.IsEligible() | Unit tests, findings query |
| Fraud score exactly 0 | ReputationAnalyzer.MeetsEligibility() | Gate tests, metrics |
| US mobile only | GeoAsnEnrichment.IsUsMobile() | Enrichment tests, data validation |
| No external relay testing | SafeValidator with canary only | Network monitoring, safety tests |
| Evidence chain integrity | EvidenceStore.VerifyHash() | Integrity tests, audit |

### Quality Gates

1. **Pre-Release**
   - All tests passing
   - Code coverage met
   - Security scan clean
   - Documentation complete

2. **Production Readiness**
   - Performance benchmarks met
   - Accessibility validated
   - Compliance verified
   - Operational runbook tested