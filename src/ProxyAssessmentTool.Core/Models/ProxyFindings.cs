using System;
using System.Collections.Generic;
using System.Net;

namespace ProxyAssessmentTool.Core.Models
{
    public class ProxyFinding
    {
        public Guid Id { get; set; } = Guid.NewGuid();
        public DateTime DiscoveredAt { get; set; } = DateTime.UtcNow;
        public DateTime LastCheckedAt { get; set; } = DateTime.UtcNow;
        
        // Core Properties
        public IPAddress IpAddress { get; set; }
        public int Port { get; set; }
        public ProxyProtocol Protocol { get; set; }
        public ProxyAuthMethod AuthMethod { get; set; }
        
        // Eligibility Criteria
        public int FraudScore { get; set; }
        public string CountryCode { get; set; }
        public string CityName { get; set; }
        public string StateCode { get; set; }
        public int ASN { get; set; }
        public string ISPName { get; set; }
        public bool IsMobileCarrier { get; set; }
        public MobileCarrierType? CarrierType { get; set; }
        
        // Usage Analysis
        public ProxyUsageLevel UsageLevel { get; set; }
        public DateTime? LastSeenActive { get; set; }
        public int ConnectionCount { get; set; }
        public long BytesTransferred { get; set; }
        
        // Social Platform Compatibility
        public Dictionary<SocialPlatform, PlatformCompatibility> PlatformTests { get; set; } = new();
        
        // Uptime Tracking
        public double UptimePercentage { get; set; }
        public TimeSpan TotalUptime { get; set; }
        public TimeSpan TotalDowntime { get; set; }
        public List<UptimeIncident> UptimeIncidents { get; set; } = new();
        
        // Leakage Tests
        public bool HasDnsLeak { get; set; }
        public bool HasWebRtcLeak { get; set; }
        public bool HasIPv6Leak { get; set; }
        public string RealIpAddress { get; set; }
        
        // Risk Assessment
        public RiskLevel RiskLevel { get; set; }
        public double RiskScore { get; set; }
        public List<string> RiskFactors { get; set; } = new();
        
        // Evidence
        public List<ValidationEvidence> Evidence { get; set; } = new();
        
        // Metadata
        public Dictionary<string, object> Metadata { get; set; } = new();
        public List<string> Tags { get; set; } = new();
        
        // Eligibility Result
        public bool IsEligible => CheckEligibility();
        public List<string> IneligibilityReasons { get; set; } = new();
        
        private bool CheckEligibility()
        {
            IneligibilityReasons.Clear();
            
            if (Protocol != ProxyProtocol.SOCKS5)
                IneligibilityReasons.Add($"Protocol {Protocol} is not SOCKS5");
                
            if (AuthMethod != ProxyAuthMethod.NoAuth)
                IneligibilityReasons.Add($"Authentication required: {AuthMethod}");
                
            if (FraudScore != 0)
                IneligibilityReasons.Add($"Fraud score {FraudScore} exceeds threshold (0)");
                
            if (CountryCode != "US")
                IneligibilityReasons.Add($"Country {CountryCode} is not US");
                
            if (!IsMobileCarrier)
                IneligibilityReasons.Add("Not a mobile carrier ASN");
                
            if (UsageLevel != ProxyUsageLevel.Unused && UsageLevel != ProxyUsageLevel.Low)
                IneligibilityReasons.Add($"Usage level {UsageLevel} exceeds threshold");
                
            return IneligibilityReasons.Count == 0;
        }
    }
    
    public enum ProxyProtocol
    {
        HTTP,
        HTTPS,
        SOCKS4,
        SOCKS5
    }
    
    public enum ProxyAuthMethod
    {
        NoAuth,
        UserPass,
        IPAuth,
        Certificate,
        Unknown
    }
    
    public enum ProxyUsageLevel
    {
        Unused,
        Low,
        Medium,
        High,
        Saturated
    }
    
    public enum SocialPlatform
    {
        Twitter,
        Instagram,
        TikTok,
        Reddit,
        Facebook,
        LinkedIn,
        YouTube,
        Snapchat
    }
    
    public enum MobileCarrierType
    {
        Verizon,
        ATT,
        TMobile,
        Sprint,
        USCellular,
        Cricket,
        MetroPCS,
        Boost,
        Other
    }
    
    public enum RiskLevel
    {
        Low,
        Medium,
        High,
        Critical
    }
    
    public class PlatformCompatibility
    {
        public SocialPlatform Platform { get; set; }
        public bool IsCompatible { get; set; }
        public DateTime TestedAt { get; set; }
        public string TestResult { get; set; }
        public Dictionary<string, object> TestDetails { get; set; } = new();
    }
    
    public class UptimeIncident
    {
        public DateTime StartTime { get; set; }
        public DateTime? EndTime { get; set; }
        public TimeSpan Duration => EndTime?.Subtract(StartTime) ?? DateTime.UtcNow.Subtract(StartTime);
        public string Type { get; set; } // "Outage", "Degraded", "Maintenance"
        public string Description { get; set; }
    }
    
    public class ValidationEvidence
    {
        public DateTime Timestamp { get; set; }
        public string Type { get; set; }
        public string Description { get; set; }
        public Dictionary<string, object> Data { get; set; } = new();
        public byte[] RawData { get; set; }
    }
    
    // Mobile Carrier ASN Database
    public static class MobileCarrierASNs
    {
        public static readonly Dictionary<int, MobileCarrierType> USMobileASNs = new()
        {
            // Verizon
            { 6167, MobileCarrierType.Verizon },
            { 22394, MobileCarrierType.Verizon },
            { 2828, MobileCarrierType.Verizon },
            
            // AT&T
            { 7018, MobileCarrierType.ATT },
            { 20057, MobileCarrierType.ATT },
            { 7132, MobileCarrierType.ATT },
            
            // T-Mobile
            { 21928, MobileCarrierType.TMobile },
            { 22140, MobileCarrierType.TMobile },
            
            // Sprint (now T-Mobile)
            { 10507, MobileCarrierType.Sprint },
            { 1239, MobileCarrierType.Sprint },
            
            // US Cellular
            { 6430, MobileCarrierType.USCellular },
            
            // Cricket (AT&T subsidiary)
            { 11426, MobileCarrierType.Cricket },
            
            // MetroPCS (T-Mobile subsidiary)
            { 30619, MobileCarrierType.MetroPCS },
            
            // Boost Mobile
            { 14979, MobileCarrierType.Boost }
        };
        
        public static bool IsUSMobileCarrier(int asn, out MobileCarrierType? carrier)
        {
            return USMobileASNs.TryGetValue(asn, out carrier.Value);
        }
    }
}