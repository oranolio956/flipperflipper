# 4. Autonomous Discovery Strategy

## 4.1 Overview

The discovery module implements a consent-based, passive-first approach to identify potential proxy services within authorized networks. No public lists or internet-wide scanning is performed.

## 4.2 Authorized Scan Set

### 4.2.1 Scope Definition

**CIDR Blocks**
- Private RFC 1918 ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Public IP ranges with explicit authorization
- IPv6 ranges when enabled

**Cloud Accounts**
```yaml
cloud_accounts:
  - provider: "aws"
    account_id: "123456789012"
    regions: ["us-east-1", "us-west-2"]
    vpc_ids: ["vpc-12345678"]
  - provider: "azure"
    subscription_id: "00000000-0000-0000-0000-000000000000"
    resource_groups: ["rg-prod", "rg-dev"]
  - provider: "gcp"
    project_id: "my-project-123"
    regions: ["us-central1"]
```

**Internal DNS Integration**
- Query internal DNS for proxy-related records
- Look for patterns: proxy*, prx*, gateway*, relay*
- Resolve to IPs and add to scan queue

**Load Balancer VIPs**
- Enumerate LB configurations
- Check backend pools for proxy services
- Include health check endpoints

**Device Inventories**
- Import from CMDB/asset management
- Filter by device type/role
- Include network appliances

### 4.2.2 Do-Not-Scan Lists

**Critical Infrastructure**
```yaml
do_not_scan:
  - "10.0.0.1"          # Core router
  - "10.0.0.0/29"       # Management subnet
  - "192.168.1.0/24"    # Production databases
  - "dns.internal.com"  # Critical DNS servers
```

**Validation Rules**
- Reject RFC 1918 without consent
- Block well-known public services
- Prevent scanning of own infrastructure

## 4.3 Passive Discovery Methods

### 4.3.1 Telemetry Analysis

**NetFlow/IPFIX**
```csharp
public class NetFlowAnalyzer
{
    public async Task<List<ProxyCandidate>> AnalyzeFlowsAsync(TimeSpan lookback)
    {
        var flows = await _flowCollector.GetFlowsAsync(lookback);
        
        var candidates = flows
            .Where(f => IsProxyPort(f.DestPort))
            .Where(f => f.BytesTransferred > MinProxyTrafficThreshold)
            .GroupBy(f => new { f.DestIP, f.DestPort })
            .Where(g => g.Count() > MinFlowCount)
            .Select(g => new ProxyCandidate
            {
                IpAddress = g.Key.DestIP,
                Port = g.Key.DestPort,
                DiscoverySource = "NetFlow",
                Confidence = CalculateConfidence(g)
            });
            
        return candidates.ToList();
    }
}
```

**VPC Flow Logs**
- Parse cloud provider flow logs
- Identify proxy-pattern traffic
- Correlate with security groups

**Proxy Access Logs**
- Parse existing proxy logs
- Extract upstream proxy references
- Identify chained proxy configurations

**WAF/LB Logs**
- Analyze X-Forwarded-For headers
- Detect proxy chains
- Identify misconfigured forwards

### 4.3.2 Configuration Mining

**Cloud APIs**
```csharp
public async Task<List<ProxyCandidate>> DiscoverCloudProxiesAsync()
{
    var candidates = new List<ProxyCandidate>();
    
    // AWS
    var ec2Instances = await _awsClient.DescribeInstancesAsync();
    candidates.AddRange(FindProxyInstances(ec2Instances));
    
    // Azure
    var vms = await _azureClient.ListVirtualMachinesAsync();
    candidates.AddRange(FindProxyVMs(vms));
    
    // GCP
    var instances = await _gcpClient.ListInstancesAsync();
    candidates.AddRange(FindProxyInstances(instances));
    
    return candidates;
}
```

**Container Registries**
- Scan for proxy-related images
- Check running containers
- Analyze exposed ports

**Service Mesh**
- Query Istio/Linkerd configs
- Identify sidecar proxies
- Check egress gateways

## 4.4 Active Discovery Methods

### 4.4.1 Conservative Port Scanning

**Target Ports**
```csharp
public static readonly int[] ProxyPorts = new[]
{
    1080,   // SOCKS
    1081,   // SOCKS alternate
    3128,   // Squid default
    8080,   // HTTP proxy
    8118,   // Privoxy
    8123,   // Polipo
    8888,   // Common proxy
    9050,   // Tor SOCKS
    9150,   // Tor Browser
    // Dynamic range
    8000, 8001, 8002, 8003, 8004, 8005,
    8081, 8082, 8083, 8084, 8085, 8086,
    8087, 8088, 8089, 8090, 8091, 8092
};
```

**Scan Strategy**
```csharp
public async Task<ScanResult> ScanSubnetAsync(IPNetwork subnet, CancellationToken ct)
{
    var rateLimiter = new SlidingWindowRateLimiter(
        _config.RateLimitPerCidrPerMin,
        TimeSpan.FromMinutes(1)
    );
    
    var scanner = new ParallelScanner(_config.MaxConcurrentScans);
    var results = new ConcurrentBag<PortScanResult>();
    
    await scanner.ScanAsync(subnet.ListIPAddresses(), async (ip) =>
    {
        await rateLimiter.WaitAsync(ct);
        
        foreach (var port in ProxyPorts)
        {
            if (await IsPortOpenAsync(ip, port, _config.TimeoutSeconds))
            {
                results.Add(new PortScanResult { IP = ip, Port = port });
            }
        }
    }, ct);
    
    return new ScanResult { OpenPorts = results.ToList() };
}
```

### 4.4.2 Smart Target Selection

**Prioritization Algorithm**
1. Known proxy subnets (from inventory)
2. High-traffic endpoints (from flow analysis)
3. Cloud compute instances
4. DMZ/perimeter networks
5. Development/test environments

**Exclusion Rules**
- Skip if in do-not-scan list
- Skip if recently scanned
- Skip if marked as critical
- Skip if rate limit exceeded

## 4.5 Discovery Scheduling

### 4.5.1 Scan Windows

```csharp
public class ScanScheduler
{
    public bool IsInScanWindow(DateTime utcNow)
    {
        var localTime = TimeZoneInfo.ConvertTimeFromUtc(utcNow, _timezone);
        var dayOfWeek = localTime.DayOfWeek;
        var timeOfDay = localTime.TimeOfDay;
        
        // Business hours only
        if (_config.BusinessHoursOnly)
        {
            if (dayOfWeek == DayOfWeek.Saturday || dayOfWeek == DayOfWeek.Sunday)
                return false;
                
            if (timeOfDay < TimeSpan.FromHours(8) || timeOfDay > TimeSpan.FromHours(18))
                return false;
        }
        
        // Maintenance windows
        foreach (var window in _config.MaintenanceWindows)
        {
            if (window.IsActive(localTime))
                return false;
        }
        
        return true;
    }
}
```

### 4.5.2 Progressive Scanning

**Phase 1: Passive Only** (Days 1-7)
- Telemetry analysis
- Configuration discovery
- No active probing

**Phase 2: Limited Active** (Days 8-14)
- Top 10% of candidates
- Conservative rate limits
- Monitor for complaints

**Phase 3: Full Active** (Day 15+)
- All authorized targets
- Normal rate limits
- Continuous discovery

## 4.6 Rate Limiting & Backpressure

### 4.6.1 Multi-Level Rate Limiting

```csharp
public class HierarchicalRateLimiter
{
    private readonly RateLimiter _globalLimiter;
    private readonly Dictionary<string, RateLimiter> _perCidrLimiters;
    private readonly Dictionary<IPAddress, RateLimiter> _perHostLimiters;
    
    public async Task<bool> TryAcquireAsync(IPAddress target)
    {
        // Global limit
        if (!await _globalLimiter.TryAcquireAsync())
            return false;
            
        // Per-CIDR limit
        var cidr = GetCidr(target);
        if (!await _perCidrLimiters[cidr].TryAcquireAsync())
            return false;
            
        // Per-host limit
        if (!await _perHostLimiters[target].TryAcquireAsync())
            return false;
            
        return true;
    }
}
```

### 4.6.2 Backoff Strategies

**Exponential Backoff**
```csharp
public TimeSpan CalculateBackoff(int attemptNumber)
{
    var baseDelay = TimeSpan.FromSeconds(1);
    var maxDelay = TimeSpan.FromMinutes(5);
    var jitter = TimeSpan.FromMilliseconds(_random.Next(0, 1000));
    
    var exponentialDelay = TimeSpan.FromMilliseconds(
        baseDelay.TotalMilliseconds * Math.Pow(2, attemptNumber)
    );
    
    var actualDelay = exponentialDelay + jitter;
    return actualDelay > maxDelay ? maxDelay : actualDelay;
}
```

## 4.7 Emergency Controls

### 4.7.1 Kill Switch

```csharp
public class EmergencyStop
{
    private volatile bool _stopRequested;
    
    public void Stop(string reason)
    {
        _stopRequested = true;
        _auditLogger.LogEmergencyStop(reason);
        _notifier.NotifyEmergencyStop(reason);
        
        // Cancel all active scans
        _scanCancellation.Cancel();
        
        // Flush partial results
        _resultStore.FlushPending();
    }
}
```

### 4.7.2 Circuit Breaker

```csharp
public class ScanCircuitBreaker
{
    private int _consecutiveFailures;
    private DateTime _lastFailureTime;
    
    public bool IsOpen => _consecutiveFailures >= _config.FailureThreshold &&
                          DateTime.UtcNow - _lastFailureTime < _config.CooldownPeriod;
    
    public void RecordSuccess() => _consecutiveFailures = 0;
    
    public void RecordFailure()
    {
        _consecutiveFailures++;
        _lastFailureTime = DateTime.UtcNow;
    }
}
```

## 4.8 Gotchas & Pitfalls

### 4.8.1 Common Issues

1. **False Positives**
   - Non-proxy services on proxy ports
   - Solution: Protocol fingerprinting validation

2. **Network Congestion**
   - Scanning impacts production traffic
   - Solution: Adaptive rate limiting

3. **IDS/IPS Triggers**
   - Security tools flag scanning
   - Solution: Whitelist scanning source

4. **Dynamic Infrastructure**
   - Containers/VMs changing IPs
   - Solution: Service discovery integration

### 4.8.2 Technical Gotchas

1. **CGNAT Addresses**
   - Carrier-grade NAT in mobile networks
   - Solution: Correlate with ASN data

2. **Anycast IPs**
   - Same IP in multiple locations
   - Solution: Geographic correlation

3. **IPv6 Complexity**
   - Huge address space
   - Solution: Smart targeting, DNS mining

## 4.9 Quality Checks

### 4.9.1 Coverage Metrics

```csharp
public class CoverageAnalyzer
{
    public CoverageReport AnalyzeCoverage()
    {
        return new CoverageReport
        {
            TotalAuthorizedIPs = CountAuthorizedIPs(),
            TotalScannedIPs = CountScannedIPs(),
            CoveragePercentage = CalculateCoveragePercentage(),
            UnscannedSubnets = GetUnscannedSubnets(),
            LastScanTimes = GetLastScanTimes()
        };
    }
}
```

### 4.9.2 Discovery Quality

- **Duplicate Detection**: Merge identical findings
- **Stale Entry Removal**: Age out old discoveries
- **Confidence Scoring**: Weight by discovery method
- **Correlation**: Cross-reference multiple sources