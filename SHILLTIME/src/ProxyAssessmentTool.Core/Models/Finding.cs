using System;
using System.Collections.Generic;
using System.Net;
using Newtonsoft.Json;

namespace ProxyAssessmentTool.Core.Models
{
    /// <summary>
    /// Represents a discovered proxy with all enrichment data
    /// </summary>
    public class Finding
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public DateTime DiscoveredAt { get; set; } = DateTime.UtcNow;
        public DateTime LastUpdated { get; set; } = DateTime.UtcNow;
        
        // Basic proxy information
        public IPAddress IpAddress { get; set; } = IPAddress.None;
        public int Port { get; set; }
        public ProxyProtocol Protocol { get; set; }
        public List<AuthMethod> AuthMethods { get; set; } = new();
        public AuthMethod SelectedAuthMethod { get; set; }
        
        // Validation results
        public ValidationStatus ValidationStatus { get; set; }
        public string? ValidationError { get; set; }
        public DateTime? LastValidated { get; set; }
        public string? CanaryEndpoint { get; set; }
        
        // Reputation data
        public double FraudScore { get; set; }
        public List<FraudIndicator> FraudIndicators { get; set; } = new();
        public string? ReputationSource { get; set; }
        public DateTime? ReputationCheckedAt { get; set; }
        
        // Geolocation data
        public string? CountryCode { get; set; }
        public string? CountryName { get; set; }
        public string? State { get; set; }
        public string? City { get; set; }
        public double? Latitude { get; set; }
        public double? Longitude { get; set; }
        public string? TimeZone { get; set; }
        
        // ASN and network data
        public int? Asn { get; set; }
        public string? AsnOrganization { get; set; }
        public bool IsMobile { get; set; }
        public string? NetworkType { get; set; }
        public string? Isp { get; set; }
        
        // Usage classification
        public UsageClass UsageClass { get; set; }
        public UsageMetrics? UsageMetrics { get; set; }
        public DateTime? UsageAnalyzedAt { get; set; }
        
        // Social media compatibility
        public CompatibilityProfile? SocialCompatibility { get; set; }
        public DateTime? CompatibilityTestedAt { get; set; }
        
        // Leakage test results
        public LeakageTestResults? LeakageTests { get; set; }
        
        // Uptime monitoring
        public double UptimePercentage { get; set; }
        public DateTime? LastSeenOnline { get; set; }
        public int ConsecutiveFailures { get; set; }
        
        // Risk assessment
        public double RiskScore { get; set; }
        public RiskLevel RiskLevel { get; set; }
        public List<RiskFactor> RiskFactors { get; set; } = new();
        
        // Eligibility determination
        public bool IsEligible { get; set; }
        public List<string> EligibilityFailureReasons { get; set; } = new();
        
        // Evidence and audit
        public string EvidenceHash { get; set; } = string.Empty;
        public List<EvidenceItem> Evidence { get; set; } = new();
        public string ConsentId { get; set; } = string.Empty;
        
        // Remediation
        public RemediationStatus RemediationStatus { get; set; }
        public List<RemediationStep> RemediationSteps { get; set; } = new();
        public string? TicketId { get; set; }
        
        // Check eligibility based on strict criteria
        public void CheckEligibility()
        {
            EligibilityFailureReasons.Clear();
            
            if (Protocol != ProxyProtocol.Socks5)
                EligibilityFailureReasons.Add($"Protocol is {Protocol}, not SOCKS5");
                
            if (SelectedAuthMethod != AuthMethod.NoAuth)
                EligibilityFailureReasons.Add($"Auth method is {SelectedAuthMethod}, not NoAuth");
                
            if (FraudScore != 0)
                EligibilityFailureReasons.Add($"Fraud score is {FraudScore}, not 0");
                
            if (CountryCode != "US")
                EligibilityFailureReasons.Add($"Country is {CountryCode}, not US");
                
            if (!IsMobile)
                EligibilityFailureReasons.Add("Network is not mobile");
                
            IsEligible = EligibilityFailureReasons.Count == 0;
        }
    }
    
    public enum ProxyProtocol
    {
        Unknown,
        Http,
        Https,
        Socks4,
        Socks4a,
        Socks5,
        Transparent,
        Reverse
    }
    
    public enum AuthMethod
    {
        Unknown = -1,
        NoAuth = 0x00,
        GssApi = 0x01,
        UsernamePassword = 0x02,
        NoAcceptableMethods = 0xFF
    }
    
    public enum ValidationStatus
    {
        NotValidated,
        Validating,
        Valid,
        Invalid,
        Error,
        Timeout
    }
    
    public enum UsageClass
    {
        Unknown,
        Unused,
        LowUsage,
        ModerateUsage,
        HighUsage,
        Active
    }
    
    public enum RiskLevel
    {
        Critical,
        High,
        Medium,
        Low,
        Informational
    }
    
    public enum RemediationStatus
    {
        NotStarted,
        InProgress,
        Completed,
        Failed,
        Deferred
    }
}