using System;
using System.Collections.Generic;
using System.Net;

namespace ProxyAssessmentTool.Core.Models
{
    /// <summary>
    /// Application configuration model
    /// </summary>
    public class AppConfiguration
    {
        public string ConsentId { get; set; } = string.Empty;
        public ScopeConfiguration Scope { get; set; } = new();
        public DiscoveryConfiguration Discovery { get; set; } = new();
        public CanaryConfiguration Canary { get; set; } = new();
        public UsageConfiguration Usage { get; set; } = new();
        public ReputationConfiguration Reputation { get; set; } = new();
        public GeoConfiguration Geo { get; set; } = new();
        public SelectionConfiguration Selection { get; set; } = new();
        public SocialCompatConfiguration SocialCompat { get; set; } = new();
        public LeakageChecksConfiguration LeakageChecks { get; set; } = new();
        public UptimeConfiguration Uptime { get; set; } = new();
        public SecurityConfiguration Security { get; set; } = new();
        public PackagingConfiguration Packaging { get; set; } = new();
        public IntegrationsConfiguration Integrations { get; set; } = new();
        public ApiConfiguration Api { get; set; } = new();
    }

    public class ScopeConfiguration
    {
        public List<string> Cidrs { get; set; } = new();
        public List<CloudAccount> CloudAccounts { get; set; } = new();
        public List<string> DoNotScan { get; set; } = new();
        public bool EnforceStrictBoundaries { get; set; } = true;
    }

    public class CloudAccount
    {
        public string Provider { get; set; } = string.Empty; // aws, azure, gcp
        public string AccountId { get; set; } = string.Empty;
        public List<string> Regions { get; set; } = new();
        public Dictionary<string, string> Tags { get; set; } = new();
    }

    public class DiscoveryConfiguration
    {
        public int RateLimitPerCidrPerMin { get; set; } = 60;
        public bool Ipv6Enabled { get; set; } = true;
        public List<int> DefaultPorts { get; set; } = new() { 1080, 3128, 8080, 8000, 8001, 8888, 9050 };
        public int MaxConcurrentScans { get; set; } = 10;
        public int TimeoutSeconds { get; set; } = 5;
        public int MaxRetries { get; set; } = 2;
        public BackoffStrategy BackoffStrategy { get; set; } = BackoffStrategy.Exponential;
    }

    public enum BackoffStrategy
    {
        Linear,
        Exponential,
        Constant
    }

    public class CanaryConfiguration
    {
        public List<string> Endpoints { get; set; } = new();
        public string EchoPattern { get; set; } = "PROXY-TEST-{timestamp}";
        public int TimeoutSeconds { get; set; } = 10;
        public bool RequireTls { get; set; } = true;
    }

    public class UsageConfiguration
    {
        public int LookbackDays { get; set; } = 30;
        public UsageThresholds Thresholds { get; set; } = new();
        public List<string> TelemetrySources { get; set; } = new();
        public bool IncludeInternalTraffic { get; set; } = false;
    }

    public class UsageThresholds
    {
        public int UnusedMaxRequestsPerDay { get; set; } = 0;
        public int LowUsageMaxRequestsPerDay { get; set; } = 50;
        public int ModerateUsageMaxRequestsPerDay { get; set; } = 500;
        public int HighUsageMinRequestsPerDay { get; set; } = 5000;
    }

    public class ReputationConfiguration
    {
        public ReputationMode Mode { get; set; } = ReputationMode.Offline;
        public int AcceptOnlyFraudScore { get; set; } = 0;
        public string? VendorApiKey { get; set; }
        public string? VendorEndpoint { get; set; }
        public int CacheDurationHours { get; set; } = 24;
        public string OfflineModelPath { get; set; } = "models/fraud-detection.bin";
    }

    public enum ReputationMode
    {
        Offline,
        Vendor,
        Hybrid
    }

    public class GeoConfiguration
    {
        public string RequireCountryIso { get; set; } = "US";
        public bool EnrichStateCity { get; set; } = true;
        public List<string> MobileAsnAllowlist { get; set; } = new()
        {
            "AS22394", // Verizon
            "AS20057", // AT&T
            "AS21928", // T-Mobile
            "AS6181",  // Sprint
            "AS7018",  // AT&T Mobility
            "AS310",   // US Cellular
        };
        public string GeoIpDatabasePath { get; set; } = "data/GeoLite2-City.mmdb";
        public string AsnDatabasePath { get; set; } = "data/GeoLite2-ASN.mmdb";
    }

    public class SelectionConfiguration
    {
        public string RequireProtocol { get; set; } = "socks5";
        public bool RequireNoAuth { get; set; } = true;
        public bool RequireMobile { get; set; } = true;
        public bool RequireUsLocation { get; set; } = true;
        public int RequireFraudScore { get; set; } = 0;
    }

    public class SocialCompatConfiguration
    {
        public CompatibilityMode Mode { get; set; } = CompatibilityMode.Synthetic;
        public TlsRequirements TlsRequirements { get; set; } = new();
        public bool WebRtcStunChecks { get; set; } = true;
        public bool DnsThroughProxyRequired { get; set; } = true;
        public List<PlatformTestConfig> PlatformTests { get; set; } = new();
    }

    public enum CompatibilityMode
    {
        Synthetic,
        PlatformAuthorized,
        Both
    }

    public class TlsRequirements
    {
        public string MinVersion { get; set; } = "TLS1.2";
        public bool Http2Required { get; set; } = true;
        public bool Http3Required { get; set; } = true;
        public List<string> RequiredCipherSuites { get; set; } = new();
    }

    public class PlatformTestConfig
    {
        public string Platform { get; set; } = string.Empty;
        public bool Enabled { get; set; }
        public string? TestAccountId { get; set; }
        public string? ApprovalId { get; set; }
        public int RateLimitPerHour { get; set; } = 10;
    }

    public class LeakageChecksConfiguration
    {
        public LeakagePolicy DnsLeak { get; set; } = LeakagePolicy.Enforce;
        public LeakagePolicy WebRtcStun { get; set; } = LeakagePolicy.Warn;
        public Ipv6Policy Ipv6Policy { get; set; } = Ipv6Policy.AllowWithControls;
    }

    public enum LeakagePolicy
    {
        Ignore,
        Warn,
        Enforce
    }

    public enum Ipv6Policy
    {
        Disable,
        AllowWithControls,
        RequireDualStack
    }

    public class UptimeConfiguration
    {
        public double SloTarget30d { get; set; } = 99.5;
        public ProbeIntervals ProbeIntervals { get; set; } = new();
        public int MaxConsecutiveFailures { get; set; } = 3;
        public bool AlertOnDowntime { get; set; } = true;
    }

    public class ProbeIntervals
    {
        public TimeSpan Tcp { get; set; } = TimeSpan.FromSeconds(60);
        public TimeSpan Socks5Handshake { get; set; } = TimeSpan.FromMinutes(5);
        public TimeSpan Functional { get; set; } = TimeSpan.FromMinutes(15);
    }

    public class SecurityConfiguration
    {
        public List<string> RbacRoles { get; set; } = new() { "Viewer", "Operator", "Admin", "Auditor" };
        public bool SsoOidcEnabled { get; set; } = false;
        public string? SsoProvider { get; set; }
        public string? SsoClientId { get; set; }
        public string? SsoTenantId { get; set; }
        public PiiScrubbing PiiScrubbing { get; set; } = PiiScrubbing.Strict;
        public int SessionTimeoutMinutes { get; set; } = 30;
        public bool RequireMfa { get; set; } = false;
    }

    public enum PiiScrubbing
    {
        None,
        Basic,
        Strict
    }

    public class PackagingConfiguration
    {
        public string Output { get; set; } = "self-contained-exe";
        public bool CodeSigning { get; set; } = true;
        public AutoUpdateConfig AutoUpdate { get; set; } = new();
        public string? SigningCertificateThumbprint { get; set; }
    }

    public class AutoUpdateConfig
    {
        public bool Enabled { get; set; } = true;
        public bool SignatureRequired { get; set; } = true;
        public string UpdateUrl { get; set; } = string.Empty;
        public TimeSpan CheckInterval { get; set; } = TimeSpan.FromDays(1);
    }

    public class IntegrationsConfiguration
    {
        public SiemConfig Siem { get; set; } = new();
        public TicketingConfig Tickets { get; set; } = new();
        public WebhookConfig Webhooks { get; set; } = new();
    }

    public class SiemConfig
    {
        public string Format { get; set; } = "json-cef";
        public bool Enabled { get; set; } = false;
        public string? Endpoint { get; set; }
        public string? ApiKey { get; set; }
        public int BatchSize { get; set; } = 100;
    }

    public class TicketingConfig
    {
        public string System { get; set; } = "jira";
        public bool Enabled { get; set; } = false;
        public string? Endpoint { get; set; }
        public string? ApiKey { get; set; }
        public string? ProjectKey { get; set; }
        public Dictionary<string, string> FieldMappings { get; set; } = new();
    }

    public class WebhookConfig
    {
        public bool Enabled { get; set; } = false;
        public List<WebhookEndpoint> Endpoints { get; set; } = new();
        public int RetryCount { get; set; } = 3;
        public TimeSpan Timeout { get; set; } = TimeSpan.FromSeconds(30);
    }

    public class WebhookEndpoint
    {
        public string Name { get; set; } = string.Empty;
        public string Url { get; set; } = string.Empty;
        public string Secret { get; set; } = string.Empty;
        public List<string> Events { get; set; } = new();
        public bool Enabled { get; set; } = true;
    }

    public class ApiConfiguration
    {
        public bool LocalhostReadonly { get; set; } = true;
        public bool HeadlessCli { get; set; } = true;
        public int Port { get; set; } = 5000;
        public string BindAddress { get; set; } = "127.0.0.1";
        public bool RequireApiKey { get; set; } = true;
    }
}