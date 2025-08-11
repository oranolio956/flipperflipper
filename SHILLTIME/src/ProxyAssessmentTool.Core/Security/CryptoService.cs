using System;
using System.Runtime.CompilerServices;
using System.Security.Cryptography;
using System.Text;

namespace ProxyAssessmentTool.Core.Security
{
    /// <summary>
    /// Cryptographic service providing secure operations
    /// </summary>
    public sealed class CryptoService : IDisposable
    {
        private readonly byte[] _hmacKey;
        private readonly RandomNumberGenerator _rng;
        private bool _disposed;

        public CryptoService()
        {
            _rng = RandomNumberGenerator.Create();
            _hmacKey = GenerateKey(32); // 256-bit key
        }

        /// <summary>
        /// Generates cryptographically secure random bytes
        /// </summary>
        public byte[] GenerateRandomBytes(int length)
        {
            ThrowIfDisposed();
            
            if (length <= 0)
                throw new ArgumentException("Length must be positive", nameof(length));

            var bytes = new byte[length];
            _rng.GetBytes(bytes);
            return bytes;
        }

        /// <summary>
        /// Generates a secure random token suitable for sessions/nonces
        /// </summary>
        public string GenerateSecureToken(int byteLength = 32)
        {
            ThrowIfDisposed();
            
            var bytes = GenerateRandomBytes(byteLength);
            return Convert.ToBase64String(bytes)
                .TrimEnd('=')
                .Replace('+', '-')
                .Replace('/', '_'); // URL-safe base64
        }

        /// <summary>
        /// Generates a cryptographically secure GUID
        /// </summary>
        public Guid GenerateSecureGuid()
        {
            ThrowIfDisposed();
            
            var bytes = GenerateRandomBytes(16);
            return new Guid(bytes);
        }

        /// <summary>
        /// Computes HMAC-SHA256 for data integrity
        /// </summary>
        public byte[] ComputeHmac(byte[] data)
        {
            ThrowIfDisposed();
            
            if (data == null || data.Length == 0)
                throw new ArgumentException("Data cannot be null or empty", nameof(data));

            using var hmac = new HMACSHA256(_hmacKey);
            return hmac.ComputeHash(data);
        }

        /// <summary>
        /// Computes HMAC-SHA256 for string data
        /// </summary>
        public string ComputeHmacString(string data)
        {
            ThrowIfDisposed();
            
            if (string.IsNullOrEmpty(data))
                throw new ArgumentException("Data cannot be null or empty", nameof(data));

            var bytes = Encoding.UTF8.GetBytes(data);
            var hash = ComputeHmac(bytes);
            return Convert.ToBase64String(hash);
        }

        /// <summary>
        /// Verifies HMAC for data integrity
        /// </summary>
        public bool VerifyHmac(byte[] data, byte[] expectedHmac)
        {
            ThrowIfDisposed();
            
            if (data == null || expectedHmac == null)
                return false;

            var actualHmac = ComputeHmac(data);
            return ConstantTimeEquals(actualHmac, expectedHmac);
        }

        /// <summary>
        /// Constant-time comparison to prevent timing attacks
        /// </summary>
        [MethodImpl(MethodImplOptions.NoInlining | MethodImplOptions.NoOptimization)]
        public static bool ConstantTimeEquals(byte[] a, byte[] b)
        {
            if (a == null || b == null)
                return false;

            if (a.Length != b.Length)
                return false;

            var result = 0;
            for (int i = 0; i < a.Length; i++)
            {
                result |= a[i] ^ b[i];
            }

            return result == 0;
        }

        /// <summary>
        /// Derives a key from a password using PBKDF2
        /// </summary>
        public static byte[] DeriveKey(string password, byte[] salt, int iterations = 100_000, int keyLength = 32)
        {
            if (string.IsNullOrEmpty(password))
                throw new ArgumentException("Password cannot be null or empty", nameof(password));
            
            if (salt == null || salt.Length < 16)
                throw new ArgumentException("Salt must be at least 16 bytes", nameof(salt));

            using var pbkdf2 = new Rfc2898DeriveBytes(
                password,
                salt,
                iterations,
                HashAlgorithmName.SHA256);
            
            return pbkdf2.GetBytes(keyLength);
        }

        /// <summary>
        /// Generates a cryptographically secure salt
        /// </summary>
        public byte[] GenerateSalt(int length = 32)
        {
            ThrowIfDisposed();
            return GenerateRandomBytes(length);
        }

        /// <summary>
        /// Hashes data using SHA256
        /// </summary>
        public static byte[] ComputeSha256(byte[] data)
        {
            if (data == null || data.Length == 0)
                throw new ArgumentException("Data cannot be null or empty", nameof(data));

            return SHA256.HashData(data);
        }

        /// <summary>
        /// Generates a secure key
        /// </summary>
        private byte[] GenerateKey(int length)
        {
            var key = new byte[length];
            _rng.GetBytes(key);
            return key;
        }

        private void ThrowIfDisposed()
        {
            if (_disposed)
                throw new ObjectDisposedException(nameof(CryptoService));
        }

        public void Dispose()
        {
            if (_disposed)
                return;

            _rng?.Dispose();
            
            // Clear sensitive data
            if (_hmacKey != null)
            {
                CryptographicOperations.ZeroMemory(_hmacKey);
            }

            _disposed = true;
        }
    }

    /// <summary>
    /// Static helper methods for common crypto operations
    /// </summary>
    public static class CryptoHelper
    {
        /// <summary>
        /// Generates cryptographically secure random bytes
        /// </summary>
        public static byte[] GetRandomBytes(int length)
        {
            if (length <= 0)
                throw new ArgumentException("Length must be positive", nameof(length));

            return RandomNumberGenerator.GetBytes(length);
        }

        /// <summary>
        /// Generates a secure random integer within a range
        /// </summary>
        public static int GetRandomInt(int minValue, int maxValue)
        {
            if (minValue >= maxValue)
                throw new ArgumentException("Min value must be less than max value");

            long range = (long)maxValue - minValue;
            var bytes = GetRandomBytes(4);
            var value = BitConverter.ToUInt32(bytes, 0);
            return (int)(minValue + (value % range));
        }

        /// <summary>
        /// Generates a secure nonce
        /// </summary>
        public static string GenerateNonce(int byteLength = 16)
        {
            var bytes = GetRandomBytes(byteLength);
            return Convert.ToBase64String(bytes)
                .TrimEnd('=')
                .Replace('+', '-')
                .Replace('/', '_');
        }

        /// <summary>
        /// Securely clears a byte array
        /// </summary>
        public static void SecureClear(byte[] data)
        {
            if (data != null)
            {
                CryptographicOperations.ZeroMemory(data);
            }
        }

        /// <summary>
        /// Constant-time string comparison
        /// </summary>
        public static bool ConstantTimeEquals(string a, string b)
        {
            if (a == null || b == null)
                return a == b;

            if (a.Length != b.Length)
                return false;

            var aBytes = Encoding.UTF8.GetBytes(a);
            var bBytes = Encoding.UTF8.GetBytes(b);

            try
            {
                return CryptoService.ConstantTimeEquals(aBytes, bBytes);
            }
            finally
            {
                SecureClear(aBytes);
                SecureClear(bBytes);
            }
        }
    }
}