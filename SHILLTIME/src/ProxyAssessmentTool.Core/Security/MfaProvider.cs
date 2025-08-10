using System;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using System.Collections.Generic;
using System.Linq;
using System.Collections.Concurrent;
using System.Collections;

namespace ProxyAssessmentTool.Core.Security
{
    /// <summary>
    /// Multi-factor authentication provider interface
    /// </summary>
    public interface IMfaProvider
    {
        string Name { get; }
        bool IsAvailable { get; }
        Task<MfaResult> ChallengeAsync(MfaContext context, CancellationToken cancellationToken = default);
        Task<bool> ValidateAsync(string response, MfaContext context, CancellationToken cancellationToken = default);
    }

    /// <summary>
    /// Context for MFA operations
    /// </summary>
    public sealed record MfaContext(
        string UserId,
        string Action,
        string SessionId,
        DateTime RequestedAt,
        Dictionary<string, object> Metadata)
    {
        public MfaContext(string userId, string action) 
            : this(userId, action, CryptoHelper.GenerateNonce(), DateTime.UtcNow, new()) { }
    }

    /// <summary>
    /// Result of an MFA challenge
    /// </summary>
    public sealed record MfaResult(
        bool Success,
        string? ChallengeId,
        string? Message,
        TimeSpan? ValidFor,
        Dictionary<string, object> Data)
    {
        public static MfaResult CreateSuccess(string challengeId, TimeSpan validFor) =>
            new(true, challengeId, null, validFor, new());

        public static MfaResult CreateFailure(string message) =>
            new(false, null, message, null, new());
    }

    /// <summary>
    /// Time-based One-Time Password (TOTP) provider - RFC 6238
    /// </summary>
    public sealed class TotpProvider : IMfaProvider
    {
        private readonly ILogger<TotpProvider> _logger;
        private readonly ITotpSecretStore _secretStore;
        private readonly TimeSpan _timeStep;
        private readonly int _codeLength;
        private readonly int _timeSkewTolerance;

        public string Name => "TOTP";
        public bool IsAvailable => true;

        public TotpProvider(ILogger<TotpProvider> logger, ITotpSecretStore secretStore)
        {
            _logger = logger;
            _secretStore = secretStore;
            _timeStep = TimeSpan.FromSeconds(30);
            _codeLength = 6;
            _timeSkewTolerance = 1; // Allow ±1 time window
        }

        public async Task<MfaResult> ChallengeAsync(MfaContext context, CancellationToken cancellationToken)
        {
            try
            {
                var secret = await _secretStore.GetSecretAsync(context.UserId, cancellationToken);
                if (secret == null)
                {
                    return MfaResult.CreateFailure("TOTP not configured for user");
                }

                var challengeId = CryptoHelper.GenerateNonce();
                return MfaResult.CreateSuccess(challengeId, _timeStep);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "TOTP challenge failed for user {UserId}", context.UserId);
                return MfaResult.CreateFailure("Failed to create TOTP challenge");
            }
        }

        public async Task<bool> ValidateAsync(string response, MfaContext context, CancellationToken cancellationToken)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(response) || response.Length != _codeLength)
                    return false;

                var secret = await _secretStore.GetSecretAsync(context.UserId, cancellationToken);
                if (secret == null)
                    return false;

                var currentTime = DateTimeOffset.UtcNow;
                
                // Check current and adjacent time windows for skew tolerance
                for (int i = -_timeSkewTolerance; i <= _timeSkewTolerance; i++)
                {
                    var timeOffset = currentTime.AddSeconds(i * _timeStep.TotalSeconds);
                    var expectedCode = GenerateCode(secret, timeOffset);
                    
                    if (CryptoHelper.ConstantTimeEquals(response, expectedCode))
                    {
                        _logger.LogInformation("TOTP validation successful for user {UserId}", context.UserId);
                        return true;
                    }
                }

                _logger.LogWarning("TOTP validation failed for user {UserId}", context.UserId);
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "TOTP validation error for user {UserId}", context.UserId);
                return false;
            }
        }

        private string GenerateCode(byte[] secret, DateTimeOffset time)
        {
            var counter = (long)(time.ToUnixTimeSeconds() / _timeStep.TotalSeconds);
            var counterBytes = BitConverter.GetBytes(counter);
            
            if (BitConverter.IsLittleEndian)
                Array.Reverse(counterBytes);

            using var hmac = new HMACSHA1(secret);
            var hash = hmac.ComputeHash(counterBytes);

            var offset = hash[^1] & 0x0F;
            var code = (hash[offset] & 0x7F) << 24
                     | (hash[offset + 1] & 0xFF) << 16
                     | (hash[offset + 2] & 0xFF) << 8
                     | (hash[offset + 3] & 0xFF);

            var modulo = (int)Math.Pow(10, _codeLength);
            return (code % modulo).ToString($"D{_codeLength}");
        }

        public static string GenerateSecret(int length = 32)
        {
            var bytes = CryptoHelper.GetRandomBytes(length);
            return Base32Encode(bytes);
        }

        private static string Base32Encode(byte[] data)
        {
            const string alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
            var result = new StringBuilder();
            
            for (int offset = 0; offset < data.Length;)
            {
                int numCharsToOutput = GetNextGroup(data, ref offset, out byte a, out byte b, out byte c, out byte d, out byte e, out byte f, out byte g, out byte h);

                result.Append((numCharsToOutput >= 1) ? alphabet[a] : '=');
                result.Append((numCharsToOutput >= 2) ? alphabet[b] : '=');
                result.Append((numCharsToOutput >= 3) ? alphabet[c] : '=');
                result.Append((numCharsToOutput >= 4) ? alphabet[d] : '=');
                result.Append((numCharsToOutput >= 5) ? alphabet[e] : '=');
                result.Append((numCharsToOutput >= 6) ? alphabet[f] : '=');
                result.Append((numCharsToOutput >= 7) ? alphabet[g] : '=');
                result.Append((numCharsToOutput >= 8) ? alphabet[h] : '=');
            }

            return result.ToString();
        }

        private static int GetNextGroup(byte[] data, ref int offset, out byte a, out byte b, out byte c, out byte d, out byte e, out byte f, out byte g, out byte h)
        {
            uint b1 = (offset < data.Length) ? data[offset++] : 0U;
            uint b2 = (offset < data.Length) ? data[offset++] : 0U;
            uint b3 = (offset < data.Length) ? data[offset++] : 0U;
            uint b4 = (offset < data.Length) ? data[offset++] : 0U;
            uint b5 = (offset < data.Length) ? data[offset++] : 0U;

            a = (byte)((b1 & 0xF8) >> 3);
            b = (byte)(((b1 & 0x07) << 2) | ((b2 & 0xC0) >> 6));
            c = (byte)((b2 & 0x3E) >> 1);
            d = (byte)(((b2 & 0x01) << 4) | ((b3 & 0xF0) >> 4));
            e = (byte)(((b3 & 0x0F) << 1) | ((b4 & 0x80) >> 7));
            f = (byte)((b4 & 0x7C) >> 2);
            g = (byte)(((b4 & 0x03) << 3) | ((b5 & 0xE0) >> 5));
            h = (byte)(b5 & 0x1F);

            return (offset - 5) switch
            {
                var x when x == data.Length => 1,
                var x when x == data.Length - 1 => 3,
                var x when x == data.Length - 2 => 4,
                var x when x == data.Length - 3 => 6,
                var x when x == data.Length - 4 => 7,
                _ => 8,
            };
        }
    }

    /// <summary>
    /// Windows Hello MFA provider (stub - requires Windows-specific implementation)
    /// </summary>
    public sealed class WindowsHelloProvider : IMfaProvider
    {
        private readonly ILogger<WindowsHelloProvider> _logger;

        public string Name => "Windows Hello";
        
        // This would check actual Windows Hello availability
        public bool IsAvailable => Environment.OSVersion.Platform == PlatformID.Win32NT 
                                  && Environment.OSVersion.Version.Major >= 10;

        public WindowsHelloProvider(ILogger<WindowsHelloProvider> logger)
        {
            _logger = logger;
        }

        public async Task<MfaResult> ChallengeAsync(MfaContext context, CancellationToken cancellationToken)
        {
            // In production, this would use Windows.Security.Credentials.UI
            // For now, return a simulated result
            await Task.Delay(100, cancellationToken);
            
            if (!IsAvailable)
            {
                return MfaResult.CreateFailure("Windows Hello is not available on this system");
            }

            var challengeId = CryptoHelper.GenerateNonce();
            return MfaResult.CreateSuccess(challengeId, TimeSpan.FromMinutes(5));
        }

        public async Task<bool> ValidateAsync(string response, MfaContext context, CancellationToken cancellationToken)
        {
            // In production, this would validate the Windows Hello response
            await Task.Delay(100, cancellationToken);
            return !string.IsNullOrEmpty(response);
        }
    }

    /// <summary>
    /// Storage interface for TOTP secrets
    /// </summary>
    public interface ITotpSecretStore
    {
        Task<byte[]?> GetSecretAsync(string userId, CancellationToken cancellationToken = default);
        Task SetSecretAsync(string userId, byte[] secret, CancellationToken cancellationToken = default);
        Task RemoveSecretAsync(string userId, CancellationToken cancellationToken = default);
    }

    /// <summary>
    /// MFA policy enforcement
    /// </summary>
    public sealed class MfaPolicy
    {
        private readonly HashSet<string> _protectedActions;
        private readonly TimeSpan _assertionLifetime;

        public MfaPolicy()
        {
            _protectedActions = new(StringComparer.OrdinalIgnoreCase)
            {
                "StartScan",
                "ModifyScope",
                "ExportEvidence",
                "ModifySecrets",
                "DeleteFindings",
                "ModifyConfiguration"
            };
            _assertionLifetime = TimeSpan.FromMinutes(15);
        }

        public bool RequiresMfa(string action) => _protectedActions.Contains(action);

        public TimeSpan AssertionLifetime => _assertionLifetime;

        public void AddProtectedAction(string action) => _protectedActions.Add(action);

        public void RemoveProtectedAction(string action) => _protectedActions.Remove(action);

        public IReadOnlySet<string> ProtectedActions => _protectedActions;
    }

    /// <summary>
    /// MFA assertion cache for short-lived validations
    /// </summary>
    public sealed class MfaAssertionCache
    {
        private readonly Dictionary<string, MfaAssertion> _assertions = new();
        private readonly ReaderWriterLockSlim _lock = new();
        private readonly ILogger<MfaAssertionCache> _logger;

        public MfaAssertionCache(ILogger<MfaAssertionCache> logger)
        {
            _logger = logger;
        }

        public void StoreAssertion(string userId, string action, TimeSpan validFor)
        {
            var assertion = new MfaAssertion(
                UserId: userId,
                Action: action,
                Nonce: CryptoHelper.GenerateNonce(),
                CreatedAt: DateTime.UtcNow,
                ExpiresAt: DateTime.UtcNow.Add(validFor)
            );

            _lock.EnterWriteLock();
            try
            {
                var key = GetKey(userId, action);
                _assertions[key] = assertion;
                _logger.LogDebug("Stored MFA assertion for {UserId}/{Action}", userId, action);
            }
            finally
            {
                _lock.ExitWriteLock();
            }
        }

        public bool ValidateAssertion(string userId, string action)
        {
            _lock.EnterReadLock();
            try
            {
                var key = GetKey(userId, action);
                if (!_assertions.TryGetValue(key, out var assertion))
                    return false;

                if (assertion.ExpiresAt < DateTime.UtcNow)
                {
                    _logger.LogDebug("MFA assertion expired for {UserId}/{Action}", userId, action);
                    return false;
                }

                return true;
            }
            finally
            {
                _lock.ExitReadLock();
            }
        }

        public void ClearExpired()
        {
            _lock.EnterWriteLock();
            try
            {
                var now = DateTime.UtcNow;
                var expired = _assertions.Where(kvp => kvp.Value.ExpiresAt < now).ToList();
                
                foreach (var kvp in expired)
                {
                    _assertions.Remove(kvp.Key);
                }

                if (expired.Count > 0)
                    _logger.LogDebug("Cleared {Count} expired MFA assertions", expired.Count);
            }
            finally
            {
                _lock.ExitWriteLock();
            }
        }

        private static string GetKey(string userId, string action) => $"{userId}:{action}";

        private sealed record MfaAssertion(
            string UserId,
            string Action,
            string Nonce,
            DateTime CreatedAt,
            DateTime ExpiresAt);
    }
}