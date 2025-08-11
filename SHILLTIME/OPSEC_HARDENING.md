# ProxyAssessmentTool - OPSEC Hardening Guide

## Overview

This guide provides comprehensive operational security (OPSEC) guidance for deploying and operating the ProxyAssessmentTool in production environments. All recommendations align with security best practices and regulatory requirements.

## Multi-Factor Authentication (MFA)

### Configuration

**Required for all sensitive operations:**
- Scope configuration changes
- Scan initiation
- Evidence/report export
- Security settings modification
- Finding deletion

**MFA Providers:**

1. **Windows Hello (Recommended)**
   - Biometric or PIN-based
   - Hardware-backed security
   - No additional infrastructure

2. **TOTP (Time-based One-Time Password)**
   - RFC 6238 compliant
   - 30-second time window
   - ±1 window tolerance for clock skew

### Implementation

```yaml
mfa:
  enabled: true
  required_actions:
    - StartScan
    - ModifyScope
    - ExportEvidence
    - ModifySecrets
    - DeleteFindings
    - ModifyConfiguration
  providers:
    primary: windows_hello
    fallback: totp
  assertion_lifetime_minutes: 15
```

### Best Practices

1. **Enrollment**
   - Require MFA enrollment on first login
   - Provide backup codes for TOTP
   - Test MFA before enforcing

2. **Recovery**
   - Implement secure recovery process
   - Require manager approval for MFA reset
   - Log all recovery attempts

3. **Monitoring**
   - Alert on repeated MFA failures
   - Track MFA bypass attempts
   - Regular MFA functionality testing

## Session Management

### Configuration

```yaml
security:
  session:
    inactivity_timeout_minutes: 15
    absolute_timeout_hours: 8
    require_mfa_on_unlock: true
    concurrent_sessions_allowed: false
    bind_to_ip: true
```

### Security Features

1. **Sliding Expiration**
   - 15-minute inactivity timeout
   - Activity extends session
   - Absolute 8-hour maximum

2. **Session Locking**
   - Automatic lock on inactivity
   - Screen lock with blur effect
   - MFA required to unlock

3. **Tamper Detection**
   - HMAC integrity verification
   - Session state validation
   - Automatic invalidation on tampering

### Implementation Details

```csharp
// Session creation with security context
var session = await sessionManager.CreateSessionAsync(user);
session.BindToIp(request.IpAddress);
session.RequireMfaForSensitiveOps = true;

// Activity tracking
sessionManager.ValidateSession(sessionId); // Updates last activity

// Secure session storage
- Sessions stored in memory only
- No persistent session storage
- Encrypted session tokens
```

## Cryptographic Operations

### Random Number Generation

**Always use cryptographically secure RNG:**

```csharp
// CORRECT
byte[] nonce = RandomNumberGenerator.GetBytes(32);
string token = Convert.ToBase64String(nonce);

// INCORRECT - Never use these
Random random = new Random(); // Predictable
Guid.NewGuid(); // Not cryptographically secure for tokens
```

### Key Management

1. **Key Storage**
   ```csharp
   // Use Windows DPAPI for local secrets
   byte[] encrypted = ProtectedData.Protect(
       sensitiveData,
       entropy,
       DataProtectionScope.CurrentUser
   );
   ```

2. **Key Rotation**
   - Automatic rotation every 30 days
   - Graceful handling of old keys
   - Audit trail for key changes

3. **Key Derivation**
   ```csharp
   // PBKDF2 with strong parameters
   var key = CryptoService.DeriveKey(
       password: userInput,
       salt: salt,
       iterations: 100_000,
       keyLength: 32
   );
   ```

### Secure Token Generation

```csharp
public string GenerateSecureToken()
{
    // 256-bit entropy
    var bytes = RandomNumberGenerator.GetBytes(32);
    
    // URL-safe encoding
    return Convert.ToBase64String(bytes)
        .TrimEnd('=')
        .Replace('+', '-')
        .Replace('/', '_');
}
```

## Secrets Management

### Application Secrets

1. **Never store in code or config files**
   ```xml
   <!-- WRONG -->
   <add key="ApiKey" value="sk_live_abcd1234" />
   
   <!-- RIGHT -->
   <add key="ApiKey" value="" /> <!-- Set via environment or secure store -->
   ```

2. **Use platform secret stores**
   - Windows: Credential Manager
   - Azure: Key Vault
   - AWS: Secrets Manager

3. **Runtime injection**
   ```csharp
   public class SecureConfiguration
   {
       private readonly ISecretStore _secrets;
       
       public string GetApiKey()
       {
           return _secrets.GetSecretAsync("api-key").Result;
       }
   }
   ```

### Database Encryption

```csharp
// SQLCipher configuration
var connectionString = new SqliteConnectionStringBuilder
{
    DataSource = "assessments.db",
    Mode = SqliteOpenMode.ReadWriteCreate,
    Password = derivedKey // From secure key derivation
}.ToString();

// Enable encryption
connection.Execute("PRAGMA cipher_compatibility = 4");
connection.Execute("PRAGMA kdf_iter = 256000");
```

## Audit Logging

### Required Audit Events

1. **Authentication**
   - Login attempts (success/failure)
   - MFA challenges
   - Session creation/termination
   - Password changes

2. **Authorization**
   - Privilege escalation attempts
   - Access denials
   - Role changes

3. **Data Access**
   - Finding views/exports
   - Report generation
   - Configuration changes
   - Scope modifications

4. **Security Events**
   - Failed validations
   - Suspicious patterns
   - Security exceptions

### Audit Log Format

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "eventId": "AUTH_LOGIN_SUCCESS",
  "userId": "user123",
  "sessionId": "sess_abc123",
  "ipAddress": "10.0.0.50",
  "userAgent": "ProxyAssessmentTool/1.1",
  "action": "Login",
  "result": "Success",
  "metadata": {
    "mfaUsed": true,
    "mfaProvider": "windows_hello"
  },
  "integrity": "hmac_sha256_signature"
}
```

### Log Protection

1. **Immutability**
   - Write-once storage
   - No update/delete operations
   - Cryptographic integrity

2. **Retention**
   - Minimum 90 days
   - Automated archival
   - Secure deletion

3. **Monitoring**
   - Real-time alerts
   - Anomaly detection
   - Regular reviews

## Network Security

### TLS Configuration

```csharp
var handler = new SocketsHttpHandler
{
    SslOptions = new SslClientAuthenticationOptions
    {
        EnabledSslProtocols = SslProtocols.Tls12 | SslProtocols.Tls13,
        CertificateRevocationCheckMode = X509RevocationMode.Online,
        RemoteCertificateValidationCallback = ValidateCertificate
    }
};
```

### Certificate Validation

```csharp
private bool ValidateCertificate(
    object sender,
    X509Certificate? certificate,
    X509Chain? chain,
    SslPolicyErrors sslPolicyErrors)
{
    // Implement certificate pinning for known endpoints
    if (IsKnownEndpoint(sender))
    {
        return ValidatePinnedCertificate(certificate);
    }
    
    // Standard validation for others
    return sslPolicyErrors == SslPolicyErrors.None;
}
```

## Deployment Security

### Build Process

1. **Code Signing**
   ```powershell
   signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /n "Your Company" ProxyAssessmentTool.exe
   ```

2. **Dependency Verification**
   - Check NuGet package signatures
   - Verify checksums
   - No unsigned dependencies

3. **Build Environment**
   - Isolated build servers
   - No internet access during build
   - Audit all build tools

### Runtime Protections

1. **ASLR and DEP**
   ```xml
   <PropertyGroup>
     <HighEntropyVA>true</HighEntropyVA>
     <NXCOMPAT>true</NXCOMPAT>
   </PropertyGroup>
   ```

2. **Runtime Checks**
   - Integrity verification on startup
   - Anti-debugging measures
   - Resource tampering detection

## Incident Response

### Detection

1. **Indicators of Compromise**
   - Unexpected network connections
   - Modified binaries
   - Unusual process behavior
   - Suspicious audit logs

2. **Monitoring**
   ```csharp
   // Built-in security monitoring
   public class SecurityMonitor
   {
       public void DetectAnomalies()
       {
           CheckForDebugger();
           ValidateBinaryIntegrity();
           MonitorNetworkConnections();
           AnalyzeAuditPatterns();
       }
   }
   ```

### Response Plan

1. **Immediate Actions**
   - Isolate affected system
   - Preserve evidence
   - Notify security team
   - Begin forensics

2. **Investigation**
   - Review audit logs
   - Analyze memory dumps
   - Check file integrity
   - Network traffic analysis

3. **Recovery**
   - Clean installation
   - Restore from backup
   - Reset all credentials
   - Enhanced monitoring

## Security Checklist

### Pre-Deployment

- [ ] Enable all security analyzers
- [ ] Run security scan on code
- [ ] Verify all dependencies
- [ ] Configure MFA providers
- [ ] Set up audit logging
- [ ] Implement key management
- [ ] Configure session policies
- [ ] Enable TLS 1.2+ only
- [ ] Sign all executables
- [ ] Document security procedures

### Operational

- [ ] Regular security updates
- [ ] Monitor audit logs daily
- [ ] Test MFA monthly
- [ ] Rotate keys on schedule
- [ ] Review access quarterly
- [ ] Conduct security drills
- [ ] Update threat model
- [ ] Patch dependencies
- [ ] Backup audit logs
- [ ] Incident response ready

### Compliance

- [ ] Meet regulatory requirements
- [ ] Document security controls
- [ ] Regular assessments
- [ ] Maintain evidence chain
- [ ] Privacy compliance
- [ ] Data retention policies
- [ ] Access reviews
- [ ] Training records
- [ ] Audit readiness
- [ ] Control effectiveness

## Conclusion

Security is not a one-time configuration but an ongoing process. This guide provides the foundation for secure operations, but must be adapted to your specific environment and threat model. Regular reviews and updates are essential to maintain security posture.