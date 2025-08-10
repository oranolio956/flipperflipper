# ProxyAssessmentTool - Migration Notes

## Overview

This document describes the breaking changes and migration steps required after implementing the comprehensive bug fixes and security improvements in ProxyAssessmentTool v1.1.

## Breaking Changes

### 1. Eligibility Evaluation API Changes

**Old API**:
```csharp
finding.CheckEligibility();
if (finding.IsEligible) { ... }
```

**New API**:
```csharp
var fraudScore = new FraudScore(finding.FraudScore);
var snapshot = EligibilityEvaluator.CreateSnapshot(finding, fraudScore);
var isEligible = EligibilityEvaluator.IsEligible(snapshot);
```

**Migration Steps**:
1. Replace all calls to `Finding.CheckEligibility()` with the new `EligibilityEvaluator` pattern
2. Use `FraudScore` value type instead of raw doubles for fraud scores
3. The eligibility check is now immutable and thread-safe

### 2. Fraud Score Type Changes

**Old**:
```csharp
double fraudScore = 0.0;
if (fraudScore == 0) { ... }
```

**New**:
```csharp
var fraudScore = new FraudScore(0.0m);
if (fraudScore.Value == 0) { ... }
```

**Migration Steps**:
1. Replace all `double` fraud scores with `FraudScore` value type
2. Use `.Value` property to get the normalized integer value
3. Remove all floating-point equality comparisons

### 3. Application Startup Pattern

**Old**:
```csharp
protected override async void OnStartup(StartupEventArgs e)
{
    // Async startup logic
}
```

**New**:
```csharp
protected override void OnStartup(StartupEventArgs e)
{
    Task.Run(async () =>
    {
        try
        {
            await InitializeAsync(e);
        }
        catch (Exception ex)
        {
            await Dispatcher.InvokeAsync(() => HandleError(ex));
        }
    });
}
```

**Migration Steps**:
1. Remove all `async void` methods except UI event handlers
2. Wrap async initialization in `Task.Run`
3. Add proper exception handling with dispatcher invocation

### 4. Input Validation Requirements

**Old**: Direct use of user input
```csharp
var cidr = userInput;
IPNetwork.Parse(cidr);
```

**New**: Mandatory validation
```csharp
var validation = CidrValidator.Validate(userInput);
if (!validation.IsValid)
{
    ShowError(validation.ErrorMessage);
    return;
}
var cidr = userInput;
```

**Migration Steps**:
1. Add validation calls for all user inputs (CIDR, hostname, port, file path)
2. Display user-friendly error messages from `ValidationResult`
3. Remove any direct parsing without validation

### 5. Session Management

**Old**: Simple authentication state
```csharp
bool isAuthenticated = true;
```

**New**: Full session management with MFA
```csharp
var session = await sessionManager.CreateSessionAsync(user);
// Check MFA requirement
if (mfaPolicy.RequiresMfa(action))
{
    var mfaResult = await mfaProvider.ChallengeAsync(context);
    // Handle MFA
}
```

**Migration Steps**:
1. Replace authentication flags with `SessionManager`
2. Add MFA checks for sensitive operations
3. Implement session timeout and lock screen

### 6. Connection Pooling

**Old**: Direct socket/HTTP creation
```csharp
var client = new HttpClient();
var socket = new Socket(...);
```

**New**: Pooled connections
```csharp
var client = connectionPoolManager.HttpClient;
using var socksConnection = await connectionPoolManager.LeaseSocksConnectionAsync(endpoint);
```

**Migration Steps**:
1. Replace all `HttpClient` instantiations with pooled instance
2. Use connection pool for SOCKS connections
3. Remove manual socket disposal (handled by pool)

### 7. UI Data Binding for Large Datasets

**Old**: Direct binding
```csharp
dataGrid.ItemsSource = findings;
```

**New**: Paginated/virtualized binding
```csharp
var pagedView = new PagedCollectionView<Finding>(findings, pageSize: 200);
dataGrid.ItemsSource = pagedView;
// Enable virtualization in XAML
```

**Migration Steps**:
1. Replace direct collection binding with `PagedCollectionView`
2. Enable virtualization in all DataGrid/ListView controls
3. Add pagination controls to UI

## Configuration Changes

### New Configuration Keys

```yaml
# Session management
security:
  session:
    inactivity_timeout_minutes: 15
    absolute_timeout_hours: 8
    require_mfa_on_unlock: true

# Connection pooling
performance:
  connection_pool:
    max_connections_per_server: 100
    connection_lifetime_minutes: 2
    idle_timeout_seconds: 90

# MFA settings
mfa:
  providers:
    - windows_hello
    - totp
  totp:
    time_step_seconds: 30
    code_length: 6
    skew_tolerance: 1
```

### Deprecated Configuration Keys

- `authentication.simple_mode` - Replaced by full session management
- `network.create_new_connections` - Always uses connection pooling now
- `ui.max_displayed_items` - Replaced by pagination settings

## Operational Changes

### 1. New Dependencies

Add these NuGet packages to existing projects:
- `System.Net.IPNetwork` (2.5.0+) - For CIDR validation
- `FsCheck.Xunit` (2.16.0+) - For property-based tests (test projects only)

### 2. Analyzer Configuration

The new `.editorconfig` and `Directory.Build.props` files enforce:
- Nullable reference types enabled
- Security analyzers treating warnings as errors
- Required XML documentation for public APIs

To suppress specific warnings (with justification):
```xml
<PropertyGroup>
  <NoWarn>$(NoWarn);CA1234</NoWarn> <!-- Justification here -->
</PropertyGroup>
```

### 3. Build Requirements

- .NET SDK 8.0.100 or higher
- Visual Studio 2022 17.8+ or VS Code with C# extension
- Windows SDK 10.0.22621.0+ for Windows Hello support

### 4. Performance Budgets

New performance requirements enforced by tests:
- Eligibility evaluation: < 1μs average latency
- UI frame budget: 16ms (60 FPS)
- Connection pool hit rate: > 80%
- Memory allocation per finding: < 1KB

### 5. Security Requirements

- All cryptographic operations use `RandomNumberGenerator.GetBytes()`
- Session tokens include HMAC for tamper detection
- MFA required for: scope changes, scan start, evidence export
- Audit logs cannot be modified after creation

## Rollback Plan

If issues arise after migration:

1. **Database**: No schema changes, rollback safe
2. **Configuration**: Keep backup of old config files
3. **Code**: Tag release before migration for easy revert
4. **Sessions**: Will require all users to re-authenticate

## Migration Checklist

- [ ] Update all `Finding.CheckEligibility()` calls to use `EligibilityEvaluator`
- [ ] Replace floating-point fraud scores with `FraudScore` value type
- [ ] Remove all `async void` methods (except event handlers)
- [ ] Add input validation to all user input points
- [ ] Implement session management for authentication
- [ ] Add MFA checks for sensitive operations
- [ ] Replace direct HTTP/socket creation with connection pools
- [ ] Update UI bindings to use pagination/virtualization
- [ ] Update configuration files with new keys
- [ ] Run all tests with new performance assertions
- [ ] Review and fix all analyzer warnings
- [ ] Update deployment scripts for new dependencies
- [ ] Train operators on new security features

## Support

For migration assistance:
- Review the updated API documentation
- Check test cases for usage examples
- Enable debug logging during migration
- Monitor performance metrics after deployment