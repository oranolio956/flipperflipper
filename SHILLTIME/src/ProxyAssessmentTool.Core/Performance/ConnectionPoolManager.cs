using System;
using System.Collections.Concurrent;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using System.Collections.Generic; // Added for List
using System.Linq; // Added for Sum
using System.Threading.Tasks; // Added for Interlocked
using System.Net.Security; // Added for DecompressionMethods

namespace ProxyAssessmentTool.Core.Performance
{
    /// <summary>
    /// Manages connection pooling for HTTP and SOCKS connections
    /// </summary>
    public sealed class ConnectionPoolManager : IDisposable
    {
        private readonly HttpClient _httpClient;
        private readonly SocketsHttpHandler _socketsHandler;
        private readonly SocksConnectionPool _socksPool;
        private readonly ILogger<ConnectionPoolManager> _logger;
        private readonly ConnectionPoolOptions _options;
        private bool _disposed;

        public ConnectionPoolManager(
            ILogger<ConnectionPoolManager> logger,
            IOptions<ConnectionPoolOptions> options)
        {
            _logger = logger;
            _options = options.Value;

            // Configure SocketsHttpHandler for connection pooling
            _socketsHandler = new SocketsHttpHandler
            {
                PooledConnectionLifetime = _options.PooledConnectionLifetime,
                PooledConnectionIdleTimeout = _options.PooledConnectionIdleTimeout,
                MaxConnectionsPerServer = _options.MaxConnectionsPerServer,
                ConnectTimeout = _options.ConnectTimeout,
                EnableMultipleHttp2Connections = true,
                
                // Enable connection reuse
                UseProxy = false,
                AllowAutoRedirect = false,
                AutomaticDecompression = DecompressionMethods.None,
            };

            _httpClient = new HttpClient(_socketsHandler, disposeHandler: false)
            {
                Timeout = _options.RequestTimeout
            };

            _socksPool = new SocksConnectionPool(logger, _options);
        }

        /// <summary>
        /// Gets the shared HttpClient instance with connection pooling
        /// </summary>
        public HttpClient HttpClient => _httpClient;

        /// <summary>
        /// Leases a SOCKS connection from the pool
        /// </summary>
        public async Task<PooledSocksConnection> LeaseSocksConnectionAsync(
            IPEndPoint endpoint,
            CancellationToken cancellationToken = default)
        {
            ThrowIfDisposed();
            return await _socksPool.LeaseConnectionAsync(endpoint, cancellationToken);
        }

        /// <summary>
        /// Gets pool statistics for monitoring
        /// </summary>
        public ConnectionPoolStatistics GetStatistics()
        {
            return new ConnectionPoolStatistics(
                HttpConnectionsActive: GetHttpActiveConnections(),
                HttpConnectionsIdle: GetHttpIdleConnections(),
                SocksConnectionsActive: _socksPool.ActiveConnections,
                SocksConnectionsIdle: _socksPool.IdleConnections,
                SocksConnectionsCreated: _socksPool.TotalConnectionsCreated,
                SocksConnectionsDisposed: _socksPool.TotalConnectionsDisposed,
                SocksPoolHits: _socksPool.PoolHits,
                SocksPoolMisses: _socksPool.PoolMisses
            );
        }

        private int GetHttpActiveConnections()
        {
            // This is an approximation - SocketsHttpHandler doesn't expose exact counts
            return 0; // Would need reflection or custom diagnostics
        }

        private int GetHttpIdleConnections()
        {
            // This is an approximation - SocketsHttpHandler doesn't expose exact counts
            return 0; // Would need reflection or custom diagnostics
        }

        private void ThrowIfDisposed()
        {
            if (_disposed)
                throw new ObjectDisposedException(nameof(ConnectionPoolManager));
        }

        public void Dispose()
        {
            if (_disposed)
                return;

            _httpClient?.Dispose();
            _socketsHandler?.Dispose();
            _socksPool?.Dispose();

            _disposed = true;
        }
    }

    /// <summary>
    /// SOCKS connection pool implementation
    /// </summary>
    internal sealed class SocksConnectionPool : IDisposable
    {
        private readonly ConcurrentDictionary<string, ConnectionPool> _pools = new();
        private readonly ILogger _logger;
        private readonly ConnectionPoolOptions _options;
        private readonly Timer _cleanupTimer;
        private long _totalConnectionsCreated;
        private long _totalConnectionsDisposed;
        private long _poolHits;
        private long _poolMisses;
        private bool _disposed;

        public int ActiveConnections => _pools.Values.Sum(p => p.ActiveCount);
        public int IdleConnections => _pools.Values.Sum(p => p.IdleCount);
        public long TotalConnectionsCreated => Interlocked.Read(ref _totalConnectionsCreated);
        public long TotalConnectionsDisposed => Interlocked.Read(ref _totalConnectionsDisposed);
        public long PoolHits => Interlocked.Read(ref _poolHits);
        public long PoolMisses => Interlocked.Read(ref _poolMisses);

        public SocksConnectionPool(ILogger logger, ConnectionPoolOptions options)
        {
            _logger = logger;
            _options = options;
            
            // Start cleanup timer
            _cleanupTimer = new Timer(
                CleanupIdleConnections,
                null,
                TimeSpan.FromSeconds(30),
                TimeSpan.FromSeconds(30));
        }

        public async Task<PooledSocksConnection> LeaseConnectionAsync(
            IPEndPoint endpoint,
            CancellationToken cancellationToken)
        {
            var poolKey = GetPoolKey(endpoint);
            var pool = _pools.GetOrAdd(poolKey, _ => new ConnectionPool(endpoint, _options));

            // Try to get existing connection
            if (pool.TryGetConnection(out var connection))
            {
                Interlocked.Increment(ref _poolHits);
                _logger.LogDebug("Reused SOCKS connection to {Endpoint}", endpoint);
                return connection;
            }

            // Create new connection
            Interlocked.Increment(ref _poolMisses);
            connection = await CreateConnectionAsync(endpoint, cancellationToken);
            Interlocked.Increment(ref _totalConnectionsCreated);
            
            return new PooledSocksConnection(connection, pool, this);
        }

        private async Task<Socket> CreateConnectionAsync(
            IPEndPoint endpoint,
            CancellationToken cancellationToken)
        {
            var socket = new Socket(endpoint.AddressFamily, SocketType.Stream, ProtocolType.Tcp)
            {
                NoDelay = true,
                LingerState = new LingerOption(false, 0)
            };

            try
            {
                await socket.ConnectAsync(endpoint, cancellationToken);
                _logger.LogDebug("Created new SOCKS connection to {Endpoint}", endpoint);
                return socket;
            }
            catch
            {
                socket.Dispose();
                throw;
            }
        }

        internal void ReturnConnection(Socket socket, ConnectionPool pool)
        {
            if (!socket.Connected || _disposed)
            {
                socket.Dispose();
                Interlocked.Increment(ref _totalConnectionsDisposed);
                return;
            }

            pool.ReturnConnection(socket);
        }

        private void CleanupIdleConnections(object? state)
        {
            try
            {
                var now = DateTime.UtcNow;
                var removed = 0;

                foreach (var pool in _pools.Values)
                {
                    removed += pool.CleanupIdleConnections(now, _options.PooledConnectionIdleTimeout);
                }

                if (removed > 0)
                {
                    Interlocked.Add(ref _totalConnectionsDisposed, removed);
                    _logger.LogDebug("Cleaned up {Count} idle SOCKS connections", removed);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during connection cleanup");
            }
        }

        private static string GetPoolKey(IPEndPoint endpoint) => 
            $"{endpoint.Address}:{endpoint.Port}";

        public void Dispose()
        {
            if (_disposed)
                return;

            _disposed = true;
            _cleanupTimer?.Dispose();

            foreach (var pool in _pools.Values)
            {
                pool.Dispose();
            }

            _pools.Clear();
        }
    }

    /// <summary>
    /// Connection pool for a specific endpoint
    /// </summary>
    internal sealed class ConnectionPool : IDisposable
    {
        private readonly ConcurrentBag<PooledConnection> _connections = new();
        private readonly IPEndPoint _endpoint;
        private readonly ConnectionPoolOptions _options;
        private int _activeCount;

        public int ActiveCount => _activeCount;
        public int IdleCount => _connections.Count;

        public ConnectionPool(IPEndPoint endpoint, ConnectionPoolOptions options)
        {
            _endpoint = endpoint;
            _options = options;
        }

        public bool TryGetConnection(out PooledSocksConnection connection)
        {
            connection = null!;

            while (_connections.TryTake(out var pooled))
            {
                if (pooled.IsExpired || !pooled.Socket.Connected)
                {
                    pooled.Socket.Dispose();
                    continue;
                }

                Interlocked.Increment(ref _activeCount);
                connection = new PooledSocksConnection(pooled.Socket, this, null!);
                return true;
            }

            return false;
        }

        public void ReturnConnection(Socket socket)
        {
            Interlocked.Decrement(ref _activeCount);

            if (_connections.Count >= _options.MaxConnectionsPerEndpoint)
            {
                socket.Dispose();
                return;
            }

            _connections.Add(new PooledConnection(socket, DateTime.UtcNow));
        }

        public int CleanupIdleConnections(DateTime now, TimeSpan idleTimeout)
        {
            var removed = 0;
            var temp = new List<PooledConnection>();

            while (_connections.TryTake(out var pooled))
            {
                if (now - pooled.CreatedAt > idleTimeout || !pooled.Socket.Connected)
                {
                    pooled.Socket.Dispose();
                    removed++;
                }
                else
                {
                    temp.Add(pooled);
                }
            }

            foreach (var pooled in temp)
            {
                _connections.Add(pooled);
            }

            return removed;
        }

        public void Dispose()
        {
            while (_connections.TryTake(out var pooled))
            {
                pooled.Socket.Dispose();
            }
        }

        private sealed class PooledConnection
        {
            public Socket Socket { get; }
            public DateTime CreatedAt { get; }
            public bool IsExpired => DateTime.UtcNow - CreatedAt > TimeSpan.FromMinutes(5);

            public PooledConnection(Socket socket, DateTime createdAt)
            {
                Socket = socket;
                CreatedAt = createdAt;
            }
        }
    }

    /// <summary>
    /// Represents a pooled SOCKS connection
    /// </summary>
    public sealed class PooledSocksConnection : IDisposable
    {
        private readonly Socket _socket;
        private readonly ConnectionPool _pool;
        private readonly SocksConnectionPool _parentPool;
        private bool _disposed;

        public Socket Socket => _socket;
        public bool IsConnected => _socket?.Connected ?? false;

        internal PooledSocksConnection(Socket socket, ConnectionPool pool, SocksConnectionPool parentPool)
        {
            _socket = socket;
            _pool = pool;
            _parentPool = parentPool;
        }

        public void Dispose()
        {
            if (_disposed)
                return;

            _disposed = true;
            _parentPool?.ReturnConnection(_socket, _pool);
        }
    }

    /// <summary>
    /// Connection pool configuration options
    /// </summary>
    public sealed class ConnectionPoolOptions
    {
        public TimeSpan PooledConnectionLifetime { get; set; } = TimeSpan.FromMinutes(2);
        public TimeSpan PooledConnectionIdleTimeout { get; set; } = TimeSpan.FromSeconds(90);
        public TimeSpan ConnectTimeout { get; set; } = TimeSpan.FromSeconds(10);
        public TimeSpan RequestTimeout { get; set; } = TimeSpan.FromSeconds(30);
        public int MaxConnectionsPerServer { get; set; } = 100;
        public int MaxConnectionsPerEndpoint { get; set; } = 20;
    }

    /// <summary>
    /// Connection pool statistics
    /// </summary>
    public sealed record ConnectionPoolStatistics(
        int HttpConnectionsActive,
        int HttpConnectionsIdle,
        int SocksConnectionsActive,
        int SocksConnectionsIdle,
        long SocksConnectionsCreated,
        long SocksConnectionsDisposed,
        long SocksPoolHits,
        long SocksPoolMisses)
    {
        public double SocksPoolHitRate => 
            SocksPoolHits + SocksPoolMisses > 0 
                ? (double)SocksPoolHits / (SocksPoolHits + SocksPoolMisses) 
                : 0;
    }
}