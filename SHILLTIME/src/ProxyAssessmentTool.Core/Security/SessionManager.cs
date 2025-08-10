using System;
using System.Collections.Concurrent;
using System.Security.Claims;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using System.Collections.Generic; // Added missing import
using System.Linq; // Added missing import

namespace ProxyAssessmentTool.Core.Security
{
    /// <summary>
    /// Desktop session manager with sliding expiration and security features
    /// </summary>
    public sealed class SessionManager : IDisposable
    {
        private readonly ConcurrentDictionary<string, UserSession> _sessions = new();
        private readonly ILogger<SessionManager> _logger;
        private readonly SessionOptions _options;
        private readonly Timer _cleanupTimer;
        private readonly CryptoService _cryptoService;
        private bool _disposed;

        public SessionManager(ILogger<SessionManager> logger, SessionOptions options)
        {
            _logger = logger;
            _options = options;
            _cryptoService = new CryptoService();
            
            // Start cleanup timer
            _cleanupTimer = new Timer(
                CleanupExpiredSessions,
                null,
                TimeSpan.FromMinutes(1),
                TimeSpan.FromMinutes(1));
        }

        /// <summary>
        /// Creates a new session for a user
        /// </summary>
        public async Task<SessionToken> CreateSessionAsync(ClaimsPrincipal user, CancellationToken cancellationToken = default)
        {
            if (user?.Identity?.IsAuthenticated != true)
                throw new InvalidOperationException("User must be authenticated to create a session");

            var userId = user.FindFirst(ClaimTypes.NameIdentifier)?.Value 
                        ?? throw new InvalidOperationException("User ID claim not found");

            // Invalidate any existing session
            await InvalidateSessionAsync(userId, cancellationToken);

            var sessionId = _cryptoService.GenerateSecureToken();
            var session = new UserSession(
                SessionId: sessionId,
                UserId: userId,
                Principal: user,
                CreatedAt: DateTime.UtcNow,
                LastActivityAt: DateTime.UtcNow,
                ExpiresAt: DateTime.UtcNow.Add(_options.AbsoluteTimeout),
                IsLocked: false,
                Metadata: new()
            );

            // Compute session hash for tamper detection
            var sessionHash = ComputeSessionHash(session);
            session = session with { Hash = sessionHash };

            if (!_sessions.TryAdd(sessionId, session))
            {
                throw new InvalidOperationException("Failed to create session");
            }

            _logger.LogInformation("Created session {SessionId} for user {UserId}", sessionId, userId);

            return new SessionToken(sessionId, session.ExpiresAt);
        }

        /// <summary>
        /// Gets a session and updates activity time
        /// </summary>
        public SessionValidationResult ValidateSession(string sessionId)
        {
            if (string.IsNullOrWhiteSpace(sessionId))
                return SessionValidationResult.Invalid("Session ID is required");

            if (!_sessions.TryGetValue(sessionId, out var session))
                return SessionValidationResult.Invalid("Session not found");

            var now = DateTime.UtcNow;

            // Check absolute expiration
            if (now > session.ExpiresAt)
            {
                _sessions.TryRemove(sessionId, out _);
                _logger.LogInformation("Session {SessionId} expired (absolute)", sessionId);
                return SessionValidationResult.Expired();
            }

            // Check inactivity timeout
            if (now - session.LastActivityAt > _options.InactivityTimeout)
            {
                // Lock the session instead of invalidating
                var lockedSession = session with { IsLocked = true };
                _sessions.TryUpdate(sessionId, lockedSession, session);
                _logger.LogInformation("Session {SessionId} locked due to inactivity", sessionId);
                return SessionValidationResult.Locked();
            }

            // Verify session integrity
            var expectedHash = ComputeSessionHash(session);
            if (!CryptoService.ConstantTimeEquals(session.Hash, expectedHash))
            {
                _sessions.TryRemove(sessionId, out _);
                _logger.LogWarning("Session {SessionId} failed integrity check", sessionId);
                return SessionValidationResult.Invalid("Session integrity check failed");
            }

            // Update activity time (sliding expiration)
            var updatedSession = session with { LastActivityAt = now };
            var newHash = ComputeSessionHash(updatedSession);
            updatedSession = updatedSession with { Hash = newHash };
            
            _sessions.TryUpdate(sessionId, updatedSession, session);

            return SessionValidationResult.Valid(updatedSession.Principal);
        }

        /// <summary>
        /// Unlocks a locked session after re-authentication
        /// </summary>
        public async Task<bool> UnlockSessionAsync(string sessionId, string userId, CancellationToken cancellationToken = default)
        {
            if (!_sessions.TryGetValue(sessionId, out var session))
                return false;

            if (session.UserId != userId)
            {
                _logger.LogWarning("Unlock attempt for session {SessionId} with wrong user ID", sessionId);
                return false;
            }

            if (!session.IsLocked)
                return true; // Already unlocked

            var unlockedSession = session with 
            { 
                IsLocked = false,
                LastActivityAt = DateTime.UtcNow
            };
            
            var newHash = ComputeSessionHash(unlockedSession);
            unlockedSession = unlockedSession with { Hash = newHash };

            if (_sessions.TryUpdate(sessionId, unlockedSession, session))
            {
                _logger.LogInformation("Session {SessionId} unlocked for user {UserId}", sessionId, userId);
                await Task.CompletedTask; // Async for future extensions
                return true;
            }

            return false;
        }

        /// <summary>
        /// Extends session expiration time
        /// </summary>
        public bool ExtendSession(string sessionId, TimeSpan extension)
        {
            if (!_sessions.TryGetValue(sessionId, out var session))
                return false;

            var newExpiry = DateTime.UtcNow.Add(extension);
            if (newExpiry > DateTime.UtcNow.Add(_options.AbsoluteTimeout))
                newExpiry = DateTime.UtcNow.Add(_options.AbsoluteTimeout);

            var extendedSession = session with { ExpiresAt = newExpiry };
            var newHash = ComputeSessionHash(extendedSession);
            extendedSession = extendedSession with { Hash = newHash };

            return _sessions.TryUpdate(sessionId, extendedSession, session);
        }

        /// <summary>
        /// Invalidates a session
        /// </summary>
        public async Task InvalidateSessionAsync(string userId, CancellationToken cancellationToken = default)
        {
            var sessionsToRemove = _sessions
                .Where(kvp => kvp.Value.UserId == userId)
                .Select(kvp => kvp.Key)
                .ToList();

            foreach (var sessionId in sessionsToRemove)
            {
                if (_sessions.TryRemove(sessionId, out _))
                {
                    _logger.LogInformation("Invalidated session {SessionId} for user {UserId}", sessionId, userId);
                }
            }

            await Task.CompletedTask; // Async for future extensions
        }

        /// <summary>
        /// Gets session metadata
        /// </summary>
        public bool TryGetSessionMetadata(string sessionId, out SessionMetadata metadata)
        {
            metadata = default!;
            
            if (!_sessions.TryGetValue(sessionId, out var session))
                return false;

            metadata = new SessionMetadata(
                SessionId: session.SessionId,
                UserId: session.UserId,
                CreatedAt: session.CreatedAt,
                LastActivityAt: session.LastActivityAt,
                ExpiresAt: session.ExpiresAt,
                IsLocked: session.IsLocked
            );

            return true;
        }

        /// <summary>
        /// Stores data in session
        /// </summary>
        public bool StoreSessionData(string sessionId, string key, object value)
        {
            if (!_sessions.TryGetValue(sessionId, out var session))
                return false;

            session.Metadata[key] = value;
            
            // Update hash
            var newHash = ComputeSessionHash(session);
            var updatedSession = session with { Hash = newHash };
            
            return _sessions.TryUpdate(sessionId, updatedSession, session);
        }

        /// <summary>
        /// Retrieves data from session
        /// </summary>
        public bool TryGetSessionData<T>(string sessionId, string key, out T? value)
        {
            value = default;
            
            if (!_sessions.TryGetValue(sessionId, out var session))
                return false;

            if (session.Metadata.TryGetValue(key, out var obj) && obj is T typedValue)
            {
                value = typedValue;
                return true;
            }

            return false;
        }

        private void CleanupExpiredSessions(object? state)
        {
            try
            {
                var now = DateTime.UtcNow;
                var expiredSessions = _sessions
                    .Where(kvp => now > kvp.Value.ExpiresAt)
                    .Select(kvp => kvp.Key)
                    .ToList();

                foreach (var sessionId in expiredSessions)
                {
                    if (_sessions.TryRemove(sessionId, out _))
                    {
                        _logger.LogDebug("Cleaned up expired session {SessionId}", sessionId);
                    }
                }

                if (expiredSessions.Count > 0)
                {
                    _logger.LogInformation("Cleaned up {Count} expired sessions", expiredSessions.Count);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during session cleanup");
            }
        }

        private byte[] ComputeSessionHash(UserSession session)
        {
            // Create a canonical representation for hashing
            var data = $"{session.SessionId}|{session.UserId}|{session.CreatedAt:O}|{session.LastActivityAt:O}|{session.ExpiresAt:O}|{session.IsLocked}";
            var bytes = System.Text.Encoding.UTF8.GetBytes(data);
            return _cryptoService.ComputeHmac(bytes);
        }

        public void Dispose()
        {
            if (_disposed)
                return;

            _cleanupTimer?.Dispose();
            _cryptoService?.Dispose();
            _sessions.Clear();
            
            _disposed = true;
        }

        private sealed record UserSession(
            string SessionId,
            string UserId,
            ClaimsPrincipal Principal,
            DateTime CreatedAt,
            DateTime LastActivityAt,
            DateTime ExpiresAt,
            bool IsLocked,
            Dictionary<string, object> Metadata,
            byte[] Hash = null!);
    }

    /// <summary>
    /// Session configuration options
    /// </summary>
    public sealed class SessionOptions
    {
        public TimeSpan InactivityTimeout { get; set; } = TimeSpan.FromMinutes(15);
        public TimeSpan AbsoluteTimeout { get; set; } = TimeSpan.FromHours(8);
        public bool RequireMfaOnUnlock { get; set; } = true;
        public bool EnableSessionLogging { get; set; } = true;
    }

    /// <summary>
    /// Session token returned to clients
    /// </summary>
    public sealed record SessionToken(string SessionId, DateTime ExpiresAt);

    /// <summary>
    /// Result of session validation
    /// </summary>
    public sealed class SessionValidationResult
    {
        public bool IsValid { get; }
        public bool IsLocked { get; }
        public bool IsExpired { get; }
        public string? Message { get; }
        public ClaimsPrincipal? Principal { get; }

        private SessionValidationResult(bool isValid, bool isLocked, bool isExpired, string? message, ClaimsPrincipal? principal)
        {
            IsValid = isValid;
            IsLocked = isLocked;
            IsExpired = isExpired;
            Message = message;
            Principal = principal;
        }

        public static SessionValidationResult Valid(ClaimsPrincipal principal) =>
            new(true, false, false, null, principal);

        public static SessionValidationResult Invalid(string message) =>
            new(false, false, false, message, null);

        public static SessionValidationResult Locked() =>
            new(false, true, false, "Session is locked due to inactivity", null);

        public static SessionValidationResult Expired() =>
            new(false, false, true, "Session has expired", null);
    }

    /// <summary>
    /// Session metadata for monitoring
    /// </summary>
    public sealed record SessionMetadata(
        string SessionId,
        string UserId,
        DateTime CreatedAt,
        DateTime LastActivityAt,
        DateTime ExpiresAt,
        bool IsLocked);

    /// <summary>
    /// Session events for audit logging
    /// </summary>
    public enum SessionEvent
    {
        Created,
        Validated,
        Extended,
        Locked,
        Unlocked,
        Invalidated,
        Expired
    }

    /// <summary>
    /// Session audit entry
    /// </summary>
    public sealed record SessionAuditEntry(
        string SessionId,
        string UserId,
        SessionEvent Event,
        DateTime Timestamp,
        string? IpAddress,
        Dictionary<string, object>? Metadata);
}