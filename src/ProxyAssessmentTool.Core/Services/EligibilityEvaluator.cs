using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using ProxyAssessmentTool.Core.Models;

namespace ProxyAssessmentTool.Core.Services
{
    /// <summary>
    /// Thread-safe, pure eligibility evaluator with strict validation rules
    /// </summary>
    public interface IEligibilityEvaluator
    {
        EligibilityResult Evaluate(ProxyFinding finding);
        EligibilityResult EvaluateBatch(IEnumerable<ProxyFinding> findings);
        EligibilityConfiguration GetConfiguration();
        void UpdateConfiguration(EligibilityConfiguration config);
    }
    
    public class EligibilityEvaluator : IEligibilityEvaluator
    {
        private readonly ReaderWriterLockSlim _configLock = new();
        private EligibilityConfiguration _config;
        
        public EligibilityEvaluator(EligibilityConfiguration config = null)
        {
            _config = config ?? EligibilityConfiguration.Default;
        }
        
        public EligibilityResult Evaluate(ProxyFinding finding)
        {
            if (finding == null)
                throw new ArgumentNullException(nameof(finding));
                
            _configLock.EnterReadLock();
            try
            {
                var result = new EligibilityResult
                {
                    Finding = finding,
                    EvaluatedAt = DateTime.UtcNow,
                    Configuration = _config.Clone()
                };
                
                // Protocol Check - SOCKS5 only
                if (finding.Protocol != ProxyProtocol.SOCKS5)
                {
                    result.FailureReasons.Add(new EligibilityFailure
                    {
                        Rule = "Protocol",
                        Expected = "SOCKS5",
                        Actual = finding.Protocol.ToString(),
                        Severity = FailureSeverity.Critical
                    });
                }
                
                // Authentication Check - No auth only
                if (finding.AuthMethod != ProxyAuthMethod.NoAuth)
                {
                    result.FailureReasons.Add(new EligibilityFailure
                    {
                        Rule = "Authentication",
                        Expected = "NoAuth",
                        Actual = finding.AuthMethod.ToString(),
                        Severity = FailureSeverity.Critical
                    });
                }
                
                // Fraud Score Gate - Must be exactly 0
                if (finding.FraudScore != 0)
                {
                    result.FailureReasons.Add(new EligibilityFailure
                    {
                        Rule = "FraudScore",
                        Expected = "0",
                        Actual = finding.FraudScore.ToString(),
                        Severity = FailureSeverity.Critical,
                        Details = $"Fraud score {finding.FraudScore} exceeds maximum allowed (0)"
                    });
                }
                
                // Geographic Filter - US only
                if (finding.CountryCode != "US")
                {
                    result.FailureReasons.Add(new EligibilityFailure
                    {
                        Rule = "Geography",
                        Expected = "US",
                        Actual = finding.CountryCode ?? "Unknown",
                        Severity = FailureSeverity.Critical,
                        Details = $"Country {finding.CountryCode} is not in allowed list"
                    });
                }
                
                // Mobile Carrier Check
                if (!finding.IsMobileCarrier)
                {
                    result.FailureReasons.Add(new EligibilityFailure
                    {
                        Rule = "MobileCarrier",
                        Expected = "True",
                        Actual = "False",
                        Severity = FailureSeverity.Critical,
                        Details = $"ASN {finding.ASN} is not a recognized US mobile carrier"
                    });
                }
                else if (!_config.AllowedCarriers.Contains(finding.CarrierType.Value))
                {
                    result.FailureReasons.Add(new EligibilityFailure
                    {
                        Rule = "CarrierType",
                        Expected = string.Join(", ", _config.AllowedCarriers),
                        Actual = finding.CarrierType.ToString(),
                        Severity = FailureSeverity.High
                    });
                }
                
                // Usage Level Check
                if (finding.UsageLevel != ProxyUsageLevel.Unused && 
                    finding.UsageLevel != ProxyUsageLevel.Low)
                {
                    result.FailureReasons.Add(new EligibilityFailure
                    {
                        Rule = "UsageLevel",
                        Expected = "Unused or Low",
                        Actual = finding.UsageLevel.ToString(),
                        Severity = FailureSeverity.High,
                        Details = $"Usage level {finding.UsageLevel} exceeds threshold"
                    });
                }
                
                // Leakage Checks
                if (finding.HasDnsLeak || finding.HasWebRtcLeak || finding.HasIPv6Leak)
                {
                    var leaks = new List<string>();
                    if (finding.HasDnsLeak) leaks.Add("DNS");
                    if (finding.HasWebRtcLeak) leaks.Add("WebRTC");
                    if (finding.HasIPv6Leak) leaks.Add("IPv6");
                    
                    result.FailureReasons.Add(new EligibilityFailure
                    {
                        Rule = "LeakageTest",
                        Expected = "No leaks",
                        Actual = string.Join(", ", leaks),
                        Severity = FailureSeverity.High,
                        Details = $"Proxy has {string.Join(", ", leaks)} leak(s)"
                    });
                }
                
                // Social Platform Compatibility (if configured)
                if (_config.RequiredPlatforms.Any())
                {
                    var incompatiblePlatforms = _config.RequiredPlatforms
                        .Where(p => !finding.PlatformTests.ContainsKey(p) || 
                                   !finding.PlatformTests[p].IsCompatible)
                        .ToList();
                        
                    if (incompatiblePlatforms.Any())
                    {
                        result.FailureReasons.Add(new EligibilityFailure
                        {
                            Rule = "SocialCompatibility",
                            Expected = "All platforms compatible",
                            Actual = $"{incompatiblePlatforms.Count} incompatible",
                            Severity = FailureSeverity.Medium,
                            Details = $"Incompatible with: {string.Join(", ", incompatiblePlatforms)}"
                        });
                    }
                }
                
                // Uptime Check
                if (finding.UptimePercentage < _config.MinimumUptimePercentage)
                {
                    result.FailureReasons.Add(new EligibilityFailure
                    {
                        Rule = "Uptime",
                        Expected = $">= {_config.MinimumUptimePercentage}%",
                        Actual = $"{finding.UptimePercentage:F2}%",
                        Severity = FailureSeverity.Medium
                    });
                }
                
                // Calculate eligibility
                result.IsEligible = !result.FailureReasons.Any(f => f.Severity == FailureSeverity.Critical);
                result.EligibilityScore = CalculateScore(result);
                
                return result;
            }
            finally
            {
                _configLock.ExitReadLock();
            }
        }
        
        public EligibilityResult EvaluateBatch(IEnumerable<ProxyFinding> findings)
        {
            var batchResult = new EligibilityResult
            {
                EvaluatedAt = DateTime.UtcNow,
                IsBatch = true
            };
            
            var results = findings.Select(Evaluate).ToList();
            batchResult.BatchResults = results;
            batchResult.IsEligible = results.Any(r => r.IsEligible);
            batchResult.EligibilityScore = results.Any() ? 
                results.Average(r => r.EligibilityScore) : 0;
                
            return batchResult;
        }
        
        public EligibilityConfiguration GetConfiguration()
        {
            _configLock.EnterReadLock();
            try
            {
                return _config.Clone();
            }
            finally
            {
                _configLock.ExitReadLock();
            }
        }
        
        public void UpdateConfiguration(EligibilityConfiguration config)
        {
            if (config == null)
                throw new ArgumentNullException(nameof(config));
                
            _configLock.EnterWriteLock();
            try
            {
                _config = config.Clone();
            }
            finally
            {
                _configLock.ExitWriteLock();
            }
        }
        
        private double CalculateScore(EligibilityResult result)
        {
            if (result.FailureReasons.Any(f => f.Severity == FailureSeverity.Critical))
                return 0;
                
            var score = 100.0;
            
            foreach (var failure in result.FailureReasons)
            {
                score -= failure.Severity switch
                {
                    FailureSeverity.High => 20,
                    FailureSeverity.Medium => 10,
                    FailureSeverity.Low => 5,
                    _ => 0
                };
            }
            
            return Math.Max(0, score);
        }
    }
    
    public class EligibilityConfiguration
    {
        public int MaxFraudScore { get; set; } = 0;
        public HashSet<string> AllowedCountries { get; set; } = new() { "US" };
        public HashSet<MobileCarrierType> AllowedCarriers { get; set; } = new()
        {
            MobileCarrierType.Verizon,
            MobileCarrierType.ATT,
            MobileCarrierType.TMobile,
            MobileCarrierType.Sprint,
            MobileCarrierType.USCellular,
            MobileCarrierType.Cricket,
            MobileCarrierType.MetroPCS,
            MobileCarrierType.Boost
        };
        public HashSet<ProxyUsageLevel> AllowedUsageLevels { get; set; } = new()
        {
            ProxyUsageLevel.Unused,
            ProxyUsageLevel.Low
        };
        public HashSet<SocialPlatform> RequiredPlatforms { get; set; } = new()
        {
            SocialPlatform.Twitter,
            SocialPlatform.Instagram,
            SocialPlatform.TikTok,
            SocialPlatform.Reddit
        };
        public double MinimumUptimePercentage { get; set; } = 95.0;
        public bool RequireNoLeaks { get; set; } = true;
        
        public static EligibilityConfiguration Default => new();
        
        public EligibilityConfiguration Clone()
        {
            return new EligibilityConfiguration
            {
                MaxFraudScore = MaxFraudScore,
                AllowedCountries = new HashSet<string>(AllowedCountries),
                AllowedCarriers = new HashSet<MobileCarrierType>(AllowedCarriers),
                AllowedUsageLevels = new HashSet<ProxyUsageLevel>(AllowedUsageLevels),
                RequiredPlatforms = new HashSet<SocialPlatform>(RequiredPlatforms),
                MinimumUptimePercentage = MinimumUptimePercentage,
                RequireNoLeaks = RequireNoLeaks
            };
        }
    }
    
    public class EligibilityResult
    {
        public ProxyFinding Finding { get; set; }
        public bool IsEligible { get; set; }
        public double EligibilityScore { get; set; }
        public List<EligibilityFailure> FailureReasons { get; set; } = new();
        public DateTime EvaluatedAt { get; set; }
        public EligibilityConfiguration Configuration { get; set; }
        public bool IsBatch { get; set; }
        public List<EligibilityResult> BatchResults { get; set; }
    }
    
    public class EligibilityFailure
    {
        public string Rule { get; set; }
        public string Expected { get; set; }
        public string Actual { get; set; }
        public FailureSeverity Severity { get; set; }
        public string Details { get; set; }
    }
    
    public enum FailureSeverity
    {
        Low,
        Medium,
        High,
        Critical
    }
}