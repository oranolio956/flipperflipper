// Critical Fixes for ProxyAssessmentTool
// This file contains fixes for the most critical issues identified in the bug analysis

using System;
using System.Collections.Generic;
using System.Net;
using System.Security.Cryptography;
using System.Text.RegularExpressions;
using System.Threading;

namespace ProxyAssessmentTool.Core.Models.Fixed
{
    /// <summary>
    /// Thread-safe version of the Finding class with critical bug fixes
    /// </summary>
    public class FindingFixed
    {
        private readonly object _lockObject = new object();
        private List<string> _eligibilityFailureReasons = new();
        private IPAddress _ipAddress = IPAddress.None;
        
        // Constants for validation
        private const double FRAUD_SCORE_EPSILON = 0.0001;
        private const string US_COUNTRY_CODE = "US";
        
        public string Id { get; set; } = GenerateSecureId();
        public DateTime DiscoveredAt { get; set; } = DateTime.UtcNow;
        public DateTime LastUpdated { get; set; } = DateTime.UtcNow;
        
        // Fixed: Null-safe IP address property
        public IPAddress IpAddress 
        { 
            get => _ipAddress;
            set => _ipAddress = value ?? throw new ArgumentNullException(nameof(value), "IP address cannot be null");
        }
        
        public int Port { get; set; }
        public ProxyProtocol Protocol { get; set; }
        public AuthMethod SelectedAuthMethod { get; set; }
        public double FraudScore { get; set; }
        public string? CountryCode { get; set; }
        public bool IsMobile { get; set; }
        public bool IsEligible { get; private set; }
        
        // Thread-safe eligibility failure reasons
        public IReadOnlyList<string> EligibilityFailureReasons 
        { 
            get 
            { 
                lock (_lockObject) 
                { 
                    return _eligibilityFailureReasons.AsReadOnly(); 
                } 
            } 
        }
        
        // Fixed: Thread-safe eligibility check with proper floating-point comparison
        public void CheckEligibility()
        {
            var reasons = new List<string>();
            
            if (Protocol != ProxyProtocol.Socks5)
                reasons.Add($"Protocol is {Protocol}, not SOCKS5");
                
            if (SelectedAuthMethod != AuthMethod.NoAuth)
                reasons.Add($"Auth method is {SelectedAuthMethod}, not NoAuth");
                
            // Fixed: Proper floating-point comparison
            if (Math.Abs(FraudScore) > FRAUD_SCORE_EPSILON)
                reasons.Add($"Fraud score is {FraudScore:F4}, not 0");
                
            if (!string.Equals(CountryCode, US_COUNTRY_CODE, StringComparison.OrdinalIgnoreCase))
                reasons.Add($"Country is {CountryCode ?? "null"}, not US");
                
            if (!IsMobile)
                reasons.Add("Network is not mobile");
            
            // Thread-safe assignment
            lock (_lockObject)
            {
                _eligibilityFailureReasons = reasons;
                IsEligible = reasons.Count == 0;
            }
        }
        
        // Secure ID generation
        private static string GenerateSecureId()
        {
            using (var rng = RandomNumberGenerator.Create())
            {
                var bytes = new byte[16];
                rng.GetBytes(bytes);
                return new Guid(bytes).ToString();
            }
        }
    }
}

namespace ProxyAssessmentTool.Core.Validation
{
    /// <summary>
    /// Input validation utilities to prevent injection attacks
    /// </summary>
    public static class InputValidator
    {
        private static readonly Regex CidrRegex = new Regex(
            @"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/(?:3[0-2]|[12]?[0-9])$",
            RegexOptions.Compiled | RegexOptions.CultureInvariant);
            
        private static readonly Regex HostnameRegex = new Regex(
            @"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$",
            RegexOptions.Compiled | RegexOptions.CultureInvariant);
        
        /// <summary>
        /// Validates CIDR notation to prevent injection attacks
        /// </summary>
        public static bool IsValidCidr(string cidr)
        {
            if (string.IsNullOrWhiteSpace(cidr))
                return false;
                
            if (!CidrRegex.IsMatch(cidr))
                return false;
                
            // Additional validation
            var parts = cidr.Split('/');
            if (parts.Length != 2)
                return false;
                
            if (!IPAddress.TryParse(parts[0], out _))
                return false;
                
            if (!int.TryParse(parts[1], out int maskBits))
                return false;
                
            return maskBits >= 0 && maskBits <= 32;
        }
        
        /// <summary>
        /// Validates port number
        /// </summary>
        public static bool IsValidPort(int port)
        {
            return port >= 1 && port <= 65535;
        }
        
        /// <summary>
        /// Validates hostname
        /// </summary>
        public static bool IsValidHostname(string hostname)
        {
            if (string.IsNullOrWhiteSpace(hostname))
                return false;
                
            if (hostname.Length > 253)
                return false;
                
            return HostnameRegex.IsMatch(hostname);
        }
        
        /// <summary>
        /// Sanitizes string input to prevent injection
        /// </summary>
        public static string SanitizeInput(string input, int maxLength = 1000)
        {
            if (string.IsNullOrWhiteSpace(input))
                return string.Empty;
                
            // Remove control characters
            input = Regex.Replace(input, @"[\x00-\x1F\x7F]", string.Empty);
            
            // Limit length
            if (input.Length > maxLength)
                input = input.Substring(0, maxLength);
                
            return input.Trim();
        }
    }
}

namespace ProxyAssessmentTool.Core.Security
{
    /// <summary>
    /// Cryptographic utilities for secure operations
    /// </summary>
    public class CryptoService
    {
        private readonly byte[] _key;
        
        public CryptoService()
        {
            // In production, this should come from secure storage
            using (var rng = RandomNumberGenerator.Create())
            {
                _key = new byte[32]; // 256 bits
                rng.GetBytes(_key);
            }
        }
        
        /// <summary>
        /// Computes HMAC for evidence integrity
        /// </summary>
        public string ComputeHMAC(byte[] data)
        {
            if (data == null || data.Length == 0)
                throw new ArgumentException("Data cannot be null or empty", nameof(data));
                
            using (var hmac = new HMACSHA256(_key))
            {
                var hash = hmac.ComputeHash(data);
                return Convert.ToBase64String(hash);
            }
        }
        
        /// <summary>
        /// Generates cryptographically secure random bytes
        /// </summary>
        public static byte[] GenerateRandomBytes(int length)
        {
            if (length <= 0)
                throw new ArgumentException("Length must be positive", nameof(length));
                
            using (var rng = RandomNumberGenerator.Create())
            {
                var bytes = new byte[length];
                rng.GetBytes(bytes);
                return bytes;
            }
        }
        
        /// <summary>
        /// Constant-time comparison to prevent timing attacks
        /// </summary>
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
    }
}

namespace ProxyAssessmentTool.App.Fixed
{
    using System.Threading.Tasks;
    using System.Windows;
    
    /// <summary>
    /// Fixed application startup without async void
    /// </summary>
    public partial class AppFixed : Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);
            
            // Proper async initialization
            Task.Run(async () =>
            {
                try
                {
                    await InitializeApplicationAsync(e);
                }
                catch (Exception ex)
                {
                    // Log the exception
                    await Dispatcher.InvokeAsync(() =>
                    {
                        MessageBox.Show(
                            $"Failed to start application: {ex.Message}",
                            "Startup Error",
                            MessageBoxButton.OK,
                            MessageBoxImage.Error);
                        Shutdown(1);
                    });
                }
            });
        }
        
        private async Task InitializeApplicationAsync(StartupEventArgs e)
        {
            // Initialization logic here
            await Task.Delay(100); // Placeholder
            
            // Switch to UI thread for UI operations
            await Dispatcher.InvokeAsync(() =>
            {
                // Create and show main window
                var mainWindow = new MainWindow();
                mainWindow.Show();
            });
        }
    }
}