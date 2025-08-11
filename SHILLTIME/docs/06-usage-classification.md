# 6. Usage Classification (Unused/Low-Usage Determination)

## 6.1 Overview

The usage classification module analyzes owner-side telemetry to determine if a proxy is unused, low-usage, or actively used. This analysis relies exclusively on data sources the owner controls - no external probing or traffic generation.

## 6.2 Telemetry Sources

### 6.2.1 Proxy Access Logs

**Log Formats Supported**
```csharp
public interface ILogParser
{
    Task<List<ProxyLogEntry>> ParseLogsAsync(Stream logStream, TimeSpan lookback);
}

public class SquidLogParser : ILogParser
{
    // Format: timestamp elapsed client action/code size method uri
    // Example: 1638360000.123 234 10.0.0.5 TCP_MISS/200 1234 GET http://example.com
}

public class NginxLogParser : ILogParser
{
    // Format: $remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent
}

public class HaProxyLogParser : ILogParser
{
    // Format: client_ip:client_port [date] frontend backend/server response_time status bytes
}
```

**Log Analysis Pipeline**
```csharp
public class ProxyLogAnalyzer
{
    public async Task<UsageMetrics> AnalyzeLogsAsync(
        IPAddress proxyIp, 
        int proxyPort,
        TimeSpan lookback)
    {
        var logs = await CollectLogsAsync(proxyIp, proxyPort, lookback);
        
        return new UsageMetrics
        {
            LookbackPeriod = lookback,
            TotalRequests = logs.Count,
            UniqueClients = logs.Select(l => l.ClientIp).Distinct().Count(),
            AverageRequestsPerDay = logs.Count / lookback.TotalDays,
            PeakRequestsPerHour = CalculatePeakHour(logs),
            LastActivityTime = logs.Max(l => l.Timestamp),
            RequestsByHour = GroupByHour(logs),
            TopUserAgents = GetTopUserAgents(logs, 10),
            BandwidthUsedGB = logs.Sum(l => l.ResponseBytes) / 1_073_741_824.0
        };
    }
}
```

### 6.2.2 NetFlow/IPFIX Analysis

**Flow Record Processing**
```csharp
public class NetFlowUsageAnalyzer
{
    public async Task<FlowMetrics> AnalyzeFlowsAsync(
        IPAddress proxyIp,
        int proxyPort,
        TimeSpan lookback)
    {
        var flows = await _flowCollector.QueryFlowsAsync(
            filter: f => f.DestIp == proxyIp && f.DestPort == proxyPort,
            timeRange: lookback
        );
        
        var metrics = new FlowMetrics
        {
            TotalFlows = flows.Count,
            UniqueSourceIPs = flows.Select(f => f.SourceIp).Distinct().Count(),
            TotalBytes = flows.Sum(f => f.Bytes),
            TotalPackets = flows.Sum(f => f.Packets),
            AverageFlowDuration = TimeSpan.FromSeconds(
                flows.Average(f => f.DurationSeconds)
            ),
            ProtocolDistribution = flows.GroupBy(f => f.Protocol)
                .ToDictionary(g => g.Key, g => g.Count())
        };
        
        return metrics;
    }
}
```

### 6.2.3 VPC Flow Logs

**AWS VPC Flow Logs**
```csharp
public class AwsFlowLogAnalyzer
{
    public async Task<VpcFlowMetrics> AnalyzeVpcFlowsAsync(
        string vpcId,
        IPAddress proxyIp,
        TimeSpan lookback)
    {
        var query = $@"
            SELECT srcaddr, dstaddr, dstport, protocol, bytes, packets, start_time
            FROM vpc_flow_logs
            WHERE vpc_id = '{vpcId}'
              AND dstaddr = '{proxyIp}'
              AND dstport IN (1080, 3128, 8080)
              AND start_time > NOW() - INTERVAL '{lookback.TotalDays}' DAY
        ";
        
        var results = await _cloudWatchLogs.QueryAsync(query);
        return ProcessVpcFlowResults(results);
    }
}
```

**Azure NSG Flow Logs**
```csharp
public class AzureNsgFlowAnalyzer
{
    public async Task<NsgFlowMetrics> AnalyzeNsgFlowsAsync(
        string resourceGroup,
        IPAddress proxyIp,
        TimeSpan lookback)
    {
        var flows = await _storageClient.GetNsgFlowLogsAsync(
            resourceGroup,
            startTime: DateTime.UtcNow - lookback
        );
        
        return ProcessNsgFlows(flows, proxyIp);
    }
}
```

### 6.2.4 Container/Kubernetes Logs

**Container Traffic Analysis**
```csharp
public class ContainerUsageAnalyzer
{
    public async Task<ContainerMetrics> AnalyzeContainerTrafficAsync(
        string containerId,
        TimeSpan lookback)
    {
        // eBPF-based traffic monitoring
        var ebpfData = await _ebpfCollector.GetContainerNetworkDataAsync(
            containerId,
            lookback
        );
        
        // Sidecar proxy logs (Envoy/Istio)
        var sidecarLogs = await _meshTelemetry.GetProxyLogsAsync(
            containerId,
            lookback
        );
        
        return CombineMetrics(ebpfData, sidecarLogs);
    }
}
```

## 6.3 Usage Classification Algorithm

### 6.3.1 Classification Thresholds

```yaml
usage:
  thresholds:
    unused_max_requests_per_day: 0
    low_usage_max_requests_per_day: 50
    moderate_usage_max_requests_per_day: 500
    high_usage_min_requests_per_day: 5000
```

### 6.3.2 Multi-Signal Classification

```csharp
public class UsageClassifier
{
    public async Task<UsageClass> ClassifyUsageAsync(
        IPAddress proxyIp,
        int proxyPort,
        TimeSpan lookback)
    {
        // Collect from all available sources
        var signals = await Task.WhenAll(
            GetProxyLogSignalAsync(proxyIp, proxyPort, lookback),
            GetNetFlowSignalAsync(proxyIp, proxyPort, lookback),
            GetVpcFlowSignalAsync(proxyIp, lookback),
            GetSiemSignalAsync(proxyIp, proxyPort, lookback)
        );
        
        // Weight signals by reliability
        var weightedMetrics = signals
            .Where(s => s != null)
            .Select(s => new WeightedSignal
            {
                Signal = s,
                Weight = GetSignalWeight(s.Source),
                Confidence = s.Confidence
            });
        
        // Aggregate metrics
        var aggregated = AggregateMetrics(weightedMetrics);
        
        // Apply classification rules
        return ClassifyByThresholds(aggregated);
    }
    
    private UsageClass ClassifyByThresholds(AggregatedMetrics metrics)
    {
        var avgRequestsPerDay = metrics.AverageRequestsPerDay;
        
        if (avgRequestsPerDay <= _config.UnusedMaxRequestsPerDay)
            return UsageClass.Unused;
            
        if (avgRequestsPerDay <= _config.LowUsageMaxRequestsPerDay)
            return UsageClass.LowUsage;
            
        if (avgRequestsPerDay <= _config.ModerateUsageMaxRequestsPerDay)
            return UsageClass.ModerateUsage;
            
        if (avgRequestsPerDay >= _config.HighUsageMinRequestsPerDay)
            return UsageClass.HighUsage;
            
        return UsageClass.Active;
    }
}
```

### 6.3.3 Confidence Scoring

```csharp
public class UsageConfidenceCalculator
{
    public double CalculateConfidence(UsageClassification classification)
    {
        var factors = new List<ConfidenceFactor>
        {
            new() { Name = "DataCompleteness", Score = GetDataCompleteness(classification) },
            new() { Name = "SourceDiversity", Score = GetSourceDiversity(classification) },
            new() { Name = "TimeCoverage", Score = GetTimeCoverage(classification) },
            new() { Name = "ConsistencyAcrossSources", Score = GetConsistency(classification) }
        };
        
        // Weighted average
        return factors.Sum(f => f.Score * f.Weight) / factors.Sum(f => f.Weight);
    }
    
    private double GetDataCompleteness(UsageClassification classification)
    {
        var totalHours = classification.LookbackPeriod.TotalHours;
        var hoursWithData = classification.HoursWithTelemetry;
        return Math.Min(hoursWithData / totalHours, 1.0);
    }
}
```

## 6.4 Temporal Analysis

### 6.4.1 Time-Based Patterns

```csharp
public class TemporalUsageAnalyzer
{
    public TemporalPattern AnalyzeTemporalPatterns(List<TimestampedRequest> requests)
    {
        return new TemporalPattern
        {
            HourlyDistribution = CalculateHourlyDistribution(requests),
            DailyDistribution = CalculateDailyDistribution(requests),
            WeeklyPattern = CalculateWeeklyPattern(requests),
            PeakHours = IdentifyPeakHours(requests),
            QuietPeriods = IdentifyQuietPeriods(requests),
            Seasonality = DetectSeasonality(requests),
            Trend = CalculateTrend(requests)
        };
    }
    
    private Dictionary<int, double> CalculateHourlyDistribution(
        List<TimestampedRequest> requests)
    {
        return requests
            .GroupBy(r => r.Timestamp.Hour)
            .ToDictionary(
                g => g.Key,
                g => (double)g.Count() / requests.Count
            );
    }
}
```

### 6.4.2 Anomaly Detection

```csharp
public class UsageAnomalyDetector
{
    public List<UsageAnomaly> DetectAnomalies(UsageTimeSeries timeSeries)
    {
        var anomalies = new List<UsageAnomaly>();
        
        // Spike detection
        var spikes = DetectSpikes(timeSeries, threshold: 3.0); // 3 std devs
        anomalies.AddRange(spikes);
        
        // Unusual patterns
        var patterns = DetectUnusualPatterns(timeSeries);
        anomalies.AddRange(patterns);
        
        // Sudden drops
        var drops = DetectSuddenDrops(timeSeries);
        anomalies.AddRange(drops);
        
        return anomalies;
    }
}
```

## 6.5 Client Analysis

### 6.5.1 Client Profiling

```csharp
public class ClientProfiler
{
    public ClientProfile ProfileClients(List<ProxyLogEntry> logs)
    {
        var clientGroups = logs.GroupBy(l => l.ClientIp);
        
        return new ClientProfile
        {
            TotalUniqueClients = clientGroups.Count(),
            ClientDistribution = clientGroups
                .Select(g => new ClientInfo
                {
                    ClientIp = g.Key,
                    RequestCount = g.Count(),
                    FirstSeen = g.Min(l => l.Timestamp),
                    LastSeen = g.Max(l => l.Timestamp),
                    TopDestinations = g.GroupBy(l => l.DestinationHost)
                        .OrderByDescending(h => h.Count())
                        .Take(10)
                        .Select(h => h.Key)
                        .ToList(),
                    IsInternal = IsInternalIp(g.Key),
                    UserAgent = g.Select(l => l.UserAgent).FirstOrDefault()
                })
                .ToList(),
            InternalVsExternalRatio = CalculateInternalRatio(clientGroups)
        };
    }
}
```

### 6.5.2 Deduplication

```csharp
public class NatDeduplicator
{
    public DeduplicatedMetrics DeduplicateNatClients(UsageMetrics metrics)
    {
        // Group by similar patterns to identify NAT'd clients
        var patterns = metrics.ClientPatterns
            .GroupBy(p => new
            {
                p.UserAgent,
                p.RequestPattern,
                TimeWindow = RoundToHour(p.Timestamp)
            });
        
        // Estimate actual client count
        var estimatedClients = patterns.Count();
        var deduplicationRatio = (double)estimatedClients / metrics.UniqueClients;
        
        return new DeduplicatedMetrics
        {
            OriginalClientCount = metrics.UniqueClients,
            EstimatedActualClients = estimatedClients,
            DeduplicationRatio = deduplicationRatio,
            Confidence = CalculateDeduplicationConfidence(patterns)
        };
    }
}
```

## 6.6 Evidence Collection

### 6.6.1 Telemetry Evidence

```csharp
public class UsageEvidenceCollector
{
    public async Task<UsageEvidence> CollectEvidenceAsync(
        Finding finding,
        UsageClassification classification)
    {
        var evidence = new UsageEvidence
        {
            FindingId = finding.Id,
            ClassificationTime = DateTime.UtcNow,
            LookbackPeriod = classification.LookbackPeriod,
            DataSources = classification.Sources.Select(s => s.Name).ToList()
        };
        
        // Collect sample logs
        evidence.SampleLogs = await CollectSampleLogsAsync(
            finding.IpAddress,
            finding.Port,
            maxSamples: 100
        );
        
        // Collect aggregated metrics
        evidence.AggregatedMetrics = classification.Metrics;
        
        // Generate summary report
        evidence.SummaryReport = GenerateSummaryReport(classification);
        
        // Calculate hash for integrity
        evidence.Hash = CalculateEvidenceHash(evidence);
        
        return evidence;
    }
}
```

## 6.7 Gotchas & Pitfalls

### 6.7.1 Data Quality Issues

1. **Incomplete Logs**
   - Log rotation may lose data
   - Solution: Multiple lookback windows

2. **Clock Skew**
   - Inconsistent timestamps across sources
   - Solution: Time normalization

3. **Log Format Changes**
   - Updates break parsers
   - Solution: Version detection, flexible parsing

4. **Sampling Bias**
   - Some sources sample traffic
   - Solution: Adjust for sampling rates

### 6.7.2 Technical Challenges

1. **NAT/CGNAT**
   - Multiple clients appear as one
   - Solution: Pattern-based deduplication

2. **Load Balancer Logs**
   - May hide actual client IPs
   - Solution: X-Forwarded-For analysis

3. **Encrypted Traffic**
   - Can't inspect payload
   - Solution: Metadata analysis only

4. **High Volume**
   - TB of logs to process
   - Solution: Streaming analytics

## 6.8 Quality Checks

### 6.8.1 Data Validation

```csharp
public class UsageDataValidator
{
    public ValidationResult ValidateUsageData(UsageMetrics metrics)
    {
        var checks = new List<ValidationCheck>
        {
            ValidateTimeRange(metrics),
            ValidateDataCompleteness(metrics),
            ValidateMetricConsistency(metrics),
            ValidateThresholdReasonability(metrics)
        };
        
        return new ValidationResult
        {
            IsValid = checks.All(c => c.Passed),
            FailedChecks = checks.Where(c => !c.Passed).ToList(),
            Warnings = GenerateWarnings(metrics)
        };
    }
}
```

### 6.8.2 Classification Accuracy

- **Cross-validation**: Compare multiple time windows
- **Source correlation**: Ensure sources agree
- **Trend analysis**: Look for classification stability
- **Manual sampling**: Spot-check classifications