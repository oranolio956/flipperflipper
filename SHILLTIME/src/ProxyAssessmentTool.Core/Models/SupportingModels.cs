using System;
using System.Collections.Generic;

namespace ProxyAssessmentTool.Core.Models
{
    /// <summary>
    /// Fraud indicator details
    /// </summary>
    public class FraudIndicator
    {
        public string Type { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public double Severity { get; set; }
        public string Source { get; set; } = string.Empty;
    }

    /// <summary>
    /// Usage metrics for classification
    /// </summary>
    public class UsageMetrics
    {
        public TimeSpan LookbackPeriod { get; set; }
        public long TotalRequests { get; set; }
        public long UniqueClients { get; set; }
        public double AverageRequestsPerDay { get; set; }
        public double PeakRequestsPerHour { get; set; }
        public DateTime? LastActivityTime { get; set; }
        public Dictionary<string, long> RequestsByHour { get; set; } = new();
        public List<string> TopUserAgents { get; set; } = new();
        public double BandwidthUsedGB { get; set; }
    }

    /// <summary>
    /// Social media compatibility profile
    /// </summary>
    public class CompatibilityProfile
    {
        public CompatibilityTestMode TestMode { get; set; }
        public bool SyntheticTestsPassed { get; set; }
        public Dictionary<string, PlatformCompatibility> PlatformResults { get; set; } = new();
        public TlsCapabilities TlsCapabilities { get; set; } = new();
        public HttpCapabilities HttpCapabilities { get; set; } = new();
        public bool SupportsWebSockets { get; set; }
        public bool SupportsCookies { get; set; }
        public bool SupportsJavaScript { get; set; }
        public List<string> CompatibilityIssues { get; set; } = new();
    }

    public enum CompatibilityTestMode
    {
        Synthetic,
        PlatformAuthorized,
        Mixed
    }

    public class PlatformCompatibility
    {
        public string Platform { get; set; } = string.Empty;
        public bool Compatible { get; set; }
        public List<string> Issues { get; set; } = new();
        public DateTime TestedAt { get; set; }
    }

    public class TlsCapabilities
    {
        public List<string> SupportedVersions { get; set; } = new();
        public List<string> SupportedCipherSuites { get; set; } = new();
        public bool SupportsHttp2 { get; set; }
        public bool SupportsHttp3 { get; set; }
        public bool SupportsAlpn { get; set; }
    }

    public class HttpCapabilities
    {
        public int MaxHeaderSize { get; set; }
        public int MaxCookieSize { get; set; }
        public bool SupportsCompression { get; set; }
        public bool SupportsChunkedTransfer { get; set; }
        public List<string> SupportedMethods { get; set; } = new();
    }

    /// <summary>
    /// Leakage test results
    /// </summary>
    public class LeakageTestResults
    {
        public DnsLeakageResult DnsLeakage { get; set; } = new();
        public WebRtcLeakageResult WebRtcLeakage { get; set; } = new();
        public IpLeakageResult IpLeakage { get; set; } = new();
        public DateTime TestedAt { get; set; }
    }

    public class DnsLeakageResult
    {
        public bool Leaked { get; set; }
        public List<string> LeakedDnsServers { get; set; } = new();
        public string DnsResolutionMethod { get; set; } = string.Empty;
        public bool RemoteDnsSupported { get; set; }
    }

    public class WebRtcLeakageResult
    {
        public bool Leaked { get; set; }
        public List<string> LocalIpAddresses { get; set; } = new();
        public List<string> PublicIpAddresses { get; set; } = new();
        public bool StunBlocked { get; set; }
    }

    public class IpLeakageResult
    {
        public bool Ipv4Leaked { get; set; }
        public bool Ipv6Leaked { get; set; }
        public string? LeakedIpv4 { get; set; }
        public string? LeakedIpv6 { get; set; }
    }

    /// <summary>
    /// Risk assessment factor
    /// </summary>
    public class RiskFactor
    {
        public string Category { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public double Weight { get; set; }
        public double Score { get; set; }
        public RiskLevel Severity { get; set; }
    }

    /// <summary>
    /// Evidence item for audit trail
    /// </summary>
    public class EvidenceItem
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string Type { get; set; } = string.Empty;
        public DateTime CollectedAt { get; set; }
        public string Hash { get; set; } = string.Empty;
        public long SizeBytes { get; set; }
        public string StoragePath { get; set; } = string.Empty;
        public Dictionary<string, string> Metadata { get; set; } = new();
    }

    /// <summary>
    /// Remediation step details
    /// </summary>
    public class RemediationStep
    {
        public int Order { get; set; }
        public string Title { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public string Category { get; set; } = string.Empty;
        public RemediationPriority Priority { get; set; }
        public string? ScriptPath { get; set; }
        public Dictionary<string, string> Parameters { get; set; } = new();
        public bool IsCompleted { get; set; }
        public DateTime? CompletedAt { get; set; }
    }

    public enum RemediationPriority
    {
        Critical,
        High,
        Medium,
        Low
    }
}