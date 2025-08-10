# 5. Protocol Fingerprinting & Safe Validation

## 5.1 Overview

The fingerprinting module identifies proxy protocols and validates them safely using owner-controlled canary endpoints. Only SOCKS5 proxies with no authentication (method 0x00) are eligible for final selection.

## 5.2 Protocol Detection Strategy

### 5.2.1 Multi-Stage Fingerprinting

```csharp
public class ProtocolFingerprinter
{
    public async Task<FingerprintResult> IdentifyProtocolAsync(IPEndPoint endpoint)
    {
        // Stage 1: Banner grab
        var banner = await GrabBannerAsync(endpoint);
        if (banner != null)
        {
            var bannerMatch = IdentifyFromBanner(banner);
            if (bannerMatch != ProxyProtocol.Unknown)
                return new FingerprintResult { Protocol = bannerMatch, Confidence = 0.8 };
        }
        
        // Stage 2: Protocol-specific probes
        var probeResults = await Task.WhenAll(
            ProbeSocks5Async(endpoint),
            ProbeSocks4Async(endpoint),
            ProbeHttpAsync(endpoint),
            ProbeHttpConnectAsync(endpoint)
        );
        
        // Stage 3: Select highest confidence result
        return probeResults
            .Where(r => r.Success)
            .OrderByDescending(r => r.Confidence)
            .FirstOrDefault() ?? new FingerprintResult { Protocol = ProxyProtocol.Unknown };
    }
}
```

### 5.2.2 SOCKS5 Detection (RFC 1928)

**Handshake Flow**
```
Client → Server: Version(05) + NMethods + Methods[]
Server → Client: Version(05) + Selected Method

If Method == 0x00 (No Auth):
    Proceed to command phase
Else:
    Reject (not eligible)
```

**Implementation**
```csharp
public async Task<Socks5ProbeResult> ProbeSocks5Async(IPEndPoint endpoint)
{
    using var client = new TcpClient();
    await client.ConnectAsync(endpoint.Address, endpoint.Port);
    using var stream = client.GetStream();
    
    // SOCKS5 greeting: Version + NMethods + Methods
    var greeting = new byte[] 
    { 
        0x05,  // Version 5
        0x02,  // 2 methods
        0x00,  // No authentication
        0x02   // Username/password (for detection)
    };
    
    await stream.WriteAsync(greeting);
    
    // Read server response
    var response = new byte[2];
    var bytesRead = await stream.ReadAsync(response);
    
    if (bytesRead == 2 && response[0] == 0x05)
    {
        return new Socks5ProbeResult
        {
            Success = true,
            Version = response[0],
            SelectedMethod = (AuthMethod)response[1],
            SupportsNoAuth = response[1] == 0x00,
            Confidence = 1.0
        };
    }
    
    return new Socks5ProbeResult { Success = false };
}
```

### 5.2.3 SOCKS4/4a Detection

```csharp
public async Task<Socks4ProbeResult> ProbeSocks4Async(IPEndPoint endpoint)
{
    // SOCKS4 CONNECT request structure
    var request = new List<byte>();
    request.Add(0x04);              // Version
    request.Add(0x01);              // CONNECT command
    request.AddRange(BitConverter.GetBytes((ushort)80)); // Dest port
    request.AddRange(new byte[] { 127, 0, 0, 1 });      // Dest IP
    request.Add(0x00);              // Null-terminated user ID
    
    // Send and analyze response
    // Note: SOCKS4 is not eligible but detected for visibility
}
```

### 5.2.4 HTTP Proxy Detection

```csharp
public async Task<HttpProbeResult> ProbeHttpAsync(IPEndPoint endpoint)
{
    var request = "GET http://canary.internal/test HTTP/1.1\r\n" +
                  "Host: canary.internal\r\n" +
                  "User-Agent: ProxyAssessmentTool/1.0\r\n" +
                  "Connection: close\r\n\r\n";
    
    var response = await SendAndReceiveAsync(endpoint, request);
    
    // Check for proxy response patterns
    if (response.Contains("HTTP/1.") && 
        (response.Contains("Via:") || 
         response.Contains("X-Forwarded-") ||
         response.Contains("Proxy-")))
    {
        return new HttpProbeResult 
        { 
            Success = true, 
            IsProxy = true,
            Protocol = ProxyProtocol.Http 
        };
    }
}
```

## 5.3 Safe Validation Process

### 5.3.1 Canary Endpoint Configuration

```yaml
canary:
  endpoints:
    - "canary1.internal.local:443"   # HTTPS echo service
    - "canary2.internal.local:8080"  # HTTP echo service
    - "canary3.internal.local:9000"  # TCP echo service
  echo_pattern: "PROXY-TEST-{timestamp}-{nonce}"
  validation_timeout: 10s
  require_exact_echo: true
```

### 5.3.2 SOCKS5 Validation Workflow

```csharp
public async Task<ValidationResult> ValidateSocks5ProxyAsync(
    ProxyCandidate candidate, 
    CanaryEndpoint canary)
{
    // Step 1: Establish SOCKS5 connection
    var socks5Client = new Socks5Client(candidate.IpAddress, candidate.Port);
    
    // Step 2: Authenticate (must be no-auth)
    var authResult = await socks5Client.AuthenticateAsync(AuthMethod.NoAuth);
    if (!authResult.Success || authResult.Method != AuthMethod.NoAuth)
    {
        return new ValidationResult
        {
            Valid = false,
            Reason = $"Authentication failed or wrong method: {authResult.Method}",
            EligibilityImpact = "Not eligible - requires authentication"
        };
    }
    
    // Step 3: CONNECT to canary
    var connectResult = await socks5Client.ConnectAsync(
        canary.Host, 
        canary.Port,
        _config.ValidationTimeout
    );
    
    if (!connectResult.Success)
    {
        return new ValidationResult
        {
            Valid = false,
            Reason = connectResult.Error,
            RetryRecommended = IsRetryableError(connectResult.Error)
        };
    }
    
    // Step 4: Echo test
    var testData = GenerateEchoPattern();
    var echoResult = await PerformEchoTestAsync(socks5Client.Stream, testData);
    
    return new ValidationResult
    {
        Valid = echoResult.Success,
        Latency = echoResult.RoundTripTime,
        CanaryEndpoint = canary.ToString(),
        ValidationTranscript = echoResult.Transcript
    };
}
```

### 5.3.3 Echo Test Implementation

```csharp
public class EchoValidator
{
    public async Task<EchoResult> PerformEchoTestAsync(
        Stream proxyStream, 
        string testPattern)
    {
        var stopwatch = Stopwatch.StartNew();
        var transcript = new StringBuilder();
        
        try
        {
            // Send test pattern
            var sendData = Encoding.UTF8.GetBytes(testPattern);
            transcript.AppendLine($"SEND: {testPattern}");
            await proxyStream.WriteAsync(sendData);
            
            // Read echo response
            var buffer = new byte[1024];
            var received = await proxyStream.ReadAsync(buffer);
            var response = Encoding.UTF8.GetString(buffer, 0, received);
            transcript.AppendLine($"RECV: {response}");
            
            stopwatch.Stop();
            
            // Validate echo
            var success = response.Trim() == testPattern.Trim();
            
            return new EchoResult
            {
                Success = success,
                RoundTripTime = stopwatch.Elapsed,
                Transcript = transcript.ToString(),
                BytesSent = sendData.Length,
                BytesReceived = received
            };
        }
        catch (Exception ex)
        {
            transcript.AppendLine($"ERROR: {ex.Message}");
            return new EchoResult
            {
                Success = false,
                Error = ex.Message,
                Transcript = transcript.ToString()
            };
        }
    }
}
```

## 5.4 Authentication Method Handling

### 5.4.1 SOCKS5 Auth Methods

```csharp
public enum Socks5AuthMethod : byte
{
    NoAuth = 0x00,              // ✓ ELIGIBLE
    GssApi = 0x01,              // ✗ Not eligible
    UsernamePassword = 0x02,    // ✗ Not eligible  
    ChallengeResponse = 0x03,   // ✗ Not eligible
    // 0x04-0x7F: IANA assigned
    // 0x80-0xFE: Private methods
    NoAcceptableMethods = 0xFF  // ✗ Connection refused
}
```

### 5.4.2 Eligibility Enforcement

```csharp
public class AuthMethodValidator
{
    public bool IsEligibleAuthMethod(Socks5AuthMethod method)
    {
        // ONLY no-auth is eligible
        return method == Socks5AuthMethod.NoAuth;
    }
    
    public string GetIneligibilityReason(Socks5AuthMethod method)
    {
        return method switch
        {
            Socks5AuthMethod.GssApi => "GSS-API authentication required",
            Socks5AuthMethod.UsernamePassword => "Username/password required",
            Socks5AuthMethod.NoAcceptableMethods => "No acceptable auth methods",
            _ => $"Authentication method {method:X2} required"
        };
    }
}
```

## 5.5 False Positive Mitigation

### 5.5.1 Multi-Attempt Validation

```csharp
public async Task<ValidationResult> ValidateWithRetryAsync(
    ProxyCandidate candidate,
    int maxAttempts = 3)
{
    var attempts = new List<ValidationAttempt>();
    
    for (int i = 0; i < maxAttempts; i++)
    {
        if (i > 0)
        {
            // Add jitter between attempts
            await Task.Delay(TimeSpan.FromMilliseconds(
                _random.Next(100, 500) * i
            ));
        }
        
        var attempt = await AttemptValidationAsync(candidate);
        attempts.Add(attempt);
        
        if (attempt.Success)
        {
            // Require 2 successes for high confidence
            var successCount = attempts.Count(a => a.Success);
            if (successCount >= 2)
            {
                return new ValidationResult 
                { 
                    Valid = true,
                    Confidence = (double)successCount / attempts.Count,
                    Attempts = attempts 
                };
            }
        }
    }
    
    return new ValidationResult 
    { 
        Valid = false,
        Attempts = attempts 
    };
}
```

### 5.5.2 Cross-Canary Validation

```csharp
public async Task<CrossValidationResult> CrossValidateAsync(
    ProxyCandidate candidate)
{
    var canaries = _config.Canary.Endpoints;
    var results = new ConcurrentBag<ValidationResult>();
    
    await Parallel.ForEachAsync(canaries, async (canary, ct) =>
    {
        var result = await ValidateAgainstCanaryAsync(candidate, canary);
        results.Add(result);
    });
    
    // Require majority success
    var successCount = results.Count(r => r.Valid);
    var successRate = (double)successCount / canaries.Count;
    
    return new CrossValidationResult
    {
        Valid = successRate >= 0.66, // 2/3 majority
        SuccessRate = successRate,
        IndividualResults = results.ToList()
    };
}
```

## 5.6 Validation Logging

### 5.6.1 Detailed Transcripts

```csharp
public class ValidationTranscript
{
    public DateTime StartTime { get; set; }
    public DateTime EndTime { get; set; }
    public IPEndPoint ProxyEndpoint { get; set; }
    public IPEndPoint CanaryEndpoint { get; set; }
    public List<NetworkEvent> Events { get; set; } = new();
    
    public void LogEvent(NetworkEventType type, byte[] data, string description)
    {
        Events.Add(new NetworkEvent
        {
            Timestamp = DateTime.UtcNow,
            Type = type,
            Data = BitConverter.ToString(data),
            Description = description,
            Direction = type.ToString().Contains("Send") ? "→" : "←"
        });
    }
    
    public string GenerateReport()
    {
        var sb = new StringBuilder();
        sb.AppendLine($"Validation Transcript for {ProxyEndpoint}");
        sb.AppendLine($"Duration: {EndTime - StartTime:ss\\.fff}s");
        sb.AppendLine("Events:");
        
        foreach (var evt in Events)
        {
            sb.AppendLine($"{evt.Timestamp:HH:mm:ss.fff} {evt.Direction} {evt.Type}: {evt.Description}");
            if (_config.IncludeRawData)
                sb.AppendLine($"  Data: {evt.Data}");
        }
        
        return sb.ToString();
    }
}
```

## 5.7 Performance Optimization

### 5.7.1 Connection Pooling

```csharp
public class ProxyConnectionPool
{
    private readonly ConcurrentDictionary<IPEndPoint, ConnectionPool> _pools = new();
    
    public async Task<PooledConnection> GetConnectionAsync(IPEndPoint proxy)
    {
        var pool = _pools.GetOrAdd(proxy, _ => new ConnectionPool(proxy, _config));
        return await pool.GetConnectionAsync();
    }
    
    public class ConnectionPool
    {
        private readonly Queue<PooledConnection> _available = new();
        private readonly SemaphoreSlim _semaphore;
        
        public async Task<PooledConnection> GetConnectionAsync()
        {
            await _semaphore.WaitAsync();
            
            if (_available.TryDequeue(out var connection) && connection.IsAlive)
            {
                return connection;
            }
            
            return await CreateNewConnectionAsync();
        }
    }
}
```

## 5.8 Gotchas & Pitfalls

### 5.8.1 Protocol Variations

1. **SOCKS5 Extensions**
   - Some implementations support non-standard auth methods
   - Solution: Strict RFC 1928 compliance

2. **Broken Implementations**
   - Partial SOCKS5 support
   - Solution: Comprehensive error handling

3. **Dual-Stack Confusion**
   - IPv4/IPv6 handling differences
   - Solution: Test both protocols

### 5.8.2 Network Issues

1. **Firewall Interference**
   - Stateful firewalls may block return traffic
   - Solution: Use established connections

2. **NAT Timeouts**
   - Connections dropped after inactivity
   - Solution: Keepalive mechanisms

3. **MTU Issues**
   - Large packets fragmented
   - Solution: Conservative packet sizes

## 5.9 Quality Checks

### 5.9.1 Validation Metrics

```csharp
public class ValidationMetrics
{
    public int TotalValidations { get; set; }
    public int SuccessfulValidations { get; set; }
    public int FailedValidations { get; set; }
    public int TimeoutValidations { get; set; }
    public Dictionary<string, int> ErrorCounts { get; set; }
    public TimeSpan AverageValidationTime { get; set; }
    public double SuccessRate => (double)SuccessfulValidations / TotalValidations;
}
```

### 5.9.2 Consistency Checks

- **Deterministic Results**: Same proxy → same result
- **Canary Health**: Monitor canary availability
- **Latency Baseline**: Track normal response times
- **Error Patterns**: Identify systematic issues