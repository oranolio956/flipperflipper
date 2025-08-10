using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text.RegularExpressions;
using IPNetwork = System.Net.IPNetwork;

namespace ProxyAssessmentTool.Core.Validation
{
    /// <summary>
    /// Result of a validation operation
    /// </summary>
    public sealed record ValidationResult
    {
        public bool IsValid { get; init; }
        public string ErrorCode { get; init; } = string.Empty;
        public string ErrorMessage { get; init; } = string.Empty;
        public Dictionary<string, object> ErrorData { get; init; } = new();

        public static ValidationResult Ok() => new() { IsValid = true };
        
        public static ValidationResult Fail(string errorCode, string errorMessage, Dictionary<string, object>? errorData = null) => 
            new() 
            { 
                IsValid = false, 
                ErrorCode = errorCode, 
                ErrorMessage = errorMessage,
                ErrorData = errorData ?? new()
            };
    }

    /// <summary>
    /// Validates CIDR notation with security considerations
    /// </summary>
    public static class CidrValidator
    {
        private const int MinPrefixLength = 8;
        private const int MaxPrefixLengthIPv4 = 32;
        private const int MaxPrefixLengthIPv6 = 128;
        
        private static readonly Regex CidrRegex = new(
            @"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/(?:3[0-2]|[12]?[0-9])$",
            RegexOptions.Compiled | RegexOptions.CultureInvariant,
            TimeSpan.FromMilliseconds(100));

        public static ValidationResult Validate(string input, bool allowPrivate = true, bool allowIPv6 = true)
        {
            if (string.IsNullOrWhiteSpace(input))
                return ValidationResult.Fail("CIDR_EMPTY", "CIDR notation cannot be empty");

            // Prevent injection attacks
            if (input.Length > 50)
                return ValidationResult.Fail("CIDR_TOO_LONG", "CIDR notation is too long");

            if (ContainsControlCharacters(input))
                return ValidationResult.Fail("CIDR_INVALID_CHARS", "CIDR contains invalid characters");

            try
            {
                if (!IPNetwork.TryParse(input, out var network))
                    return ValidationResult.Fail("CIDR_INVALID", "Invalid CIDR notation format");

                // Check prefix bounds
                var maxPrefix = network.BaseAddress.AddressFamily == AddressFamily.InterNetwork 
                    ? MaxPrefixLengthIPv4 
                    : MaxPrefixLengthIPv6;
                    
                if (network.PrefixLength < MinPrefixLength || network.PrefixLength > maxPrefix)
                    return ValidationResult.Fail("CIDR_PREFIX_BOUNDS", 
                        $"CIDR prefix must be between {MinPrefixLength} and {maxPrefix}",
                        new() { ["prefix"] = network.PrefixLength });

                // IPv6 check
                if (!allowIPv6 && network.BaseAddress.AddressFamily == AddressFamily.InterNetworkV6)
                    return ValidationResult.Fail("CIDR_IPV6_NOT_ALLOWED", "IPv6 addresses are not allowed");

                // Private IP check
                if (!allowPrivate && IsPrivateNetwork(network))
                    return ValidationResult.Fail("CIDR_PRIVATE_NOT_ALLOWED", "Private IP ranges are not allowed");

                return ValidationResult.Ok();
            }
            catch (Exception ex)
            {
                return ValidationResult.Fail("CIDR_PARSE_ERROR", 
                    "Failed to parse CIDR notation",
                    new() { ["exception"] = ex.Message });
            }
        }

        private static bool IsPrivateNetwork(IPNetwork network)
        {
            var privateRanges = new[]
            {
                IPNetwork.Parse("10.0.0.0/8"),
                IPNetwork.Parse("172.16.0.0/12"),
                IPNetwork.Parse("192.168.0.0/16"),
                IPNetwork.Parse("169.254.0.0/16"), // Link-local
                IPNetwork.Parse("127.0.0.0/8"),     // Loopback
                IPNetwork.Parse("fc00::/7"),        // IPv6 ULA
                IPNetwork.Parse("fe80::/10"),       // IPv6 link-local
            };

            return privateRanges.Any(range => range.Contains(network.BaseAddress));
        }

        private static bool ContainsControlCharacters(string input)
        {
            return input.Any(c => char.IsControl(c) && c != '\n' && c != '\r' && c != '\t');
        }
    }

    /// <summary>
    /// Validates hostnames according to RFC specifications
    /// </summary>
    public static class HostnameValidator
    {
        private const int MaxHostnameLength = 253;
        private const int MaxLabelLength = 63;
        
        private static readonly Regex HostnameRegex = new(
            @"^(?=.{1,253}$)(?:[a-zA-Z0-9](?:(?:[a-zA-Z0-9\-]){0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:(?:[a-zA-Z0-9\-]){0,61}[a-zA-Z0-9])?$",
            RegexOptions.Compiled | RegexOptions.CultureInvariant,
            TimeSpan.FromMilliseconds(100));

        public static ValidationResult Validate(string input, bool allowIPAddress = true)
        {
            if (string.IsNullOrWhiteSpace(input))
                return ValidationResult.Fail("HOST_EMPTY", "Hostname cannot be empty");

            if (input.Length > MaxHostnameLength)
                return ValidationResult.Fail("HOST_TOO_LONG", 
                    $"Hostname cannot exceed {MaxHostnameLength} characters");

            // Check for control characters
            if (input.Any(c => char.IsControl(c)))
                return ValidationResult.Fail("HOST_INVALID_CHARS", "Hostname contains control characters");

            // Check if it's an IP address
            if (IPAddress.TryParse(input, out var ip))
            {
                if (!allowIPAddress)
                    return ValidationResult.Fail("HOST_IP_NOT_ALLOWED", "IP addresses are not allowed");
                return ValidationResult.Ok();
            }

            // Validate hostname format
            if (!HostnameRegex.IsMatch(input))
                return ValidationResult.Fail("HOST_INVALID_FORMAT", "Invalid hostname format");

            // Check label lengths
            var labels = input.Split('.');
            foreach (var label in labels)
            {
                if (label.Length > MaxLabelLength)
                    return ValidationResult.Fail("HOST_LABEL_TOO_LONG", 
                        $"Hostname label cannot exceed {MaxLabelLength} characters",
                        new() { ["label"] = label });
            }

            // Additional security checks
            if (Uri.CheckHostName(input) == UriHostNameType.Unknown)
                return ValidationResult.Fail("HOST_URI_INVALID", "Hostname failed URI validation");

            return ValidationResult.Ok();
        }
    }

    /// <summary>
    /// Validates port numbers with range and security checks
    /// </summary>
    public static class PortValidator
    {
        private const int MinPort = 1;
        private const int MaxPort = 65535;
        
        // Well-known privileged ports that might need special handling
        private static readonly HashSet<int> PrivilegedPorts = new()
        {
            22,   // SSH
            23,   // Telnet
            25,   // SMTP
            53,   // DNS
            80,   // HTTP
            110,  // POP3
            443,  // HTTPS
            445,  // SMB
            3389, // RDP
        };

        public static ValidationResult Validate(int port, bool allowPrivileged = true)
        {
            if (port < MinPort || port > MaxPort)
                return ValidationResult.Fail("PORT_OUT_OF_RANGE", 
                    $"Port must be between {MinPort} and {MaxPort}",
                    new() { ["port"] = port });

            if (!allowPrivileged && port < 1024)
                return ValidationResult.Fail("PORT_PRIVILEGED", 
                    "Privileged ports (below 1024) are not allowed",
                    new() { ["port"] = port });

            return ValidationResult.Ok();
        }

        public static ValidationResult ValidateRange(int startPort, int endPort)
        {
            var startValidation = Validate(startPort);
            if (!startValidation.IsValid)
                return startValidation;

            var endValidation = Validate(endPort);
            if (!endValidation.IsValid)
                return endValidation;

            if (startPort > endPort)
                return ValidationResult.Fail("PORT_RANGE_INVALID", 
                    "Start port must be less than or equal to end port",
                    new() { ["start"] = startPort, ["end"] = endPort });

            if (endPort - startPort > 1000)
                return ValidationResult.Fail("PORT_RANGE_TOO_LARGE", 
                    "Port range cannot exceed 1000 ports",
                    new() { ["start"] = startPort, ["end"] = endPort, ["size"] = endPort - startPort + 1 });

            return ValidationResult.Ok();
        }

        public static bool IsPrivilegedPort(int port) => port < 1024;
        
        public static bool IsWellKnownPrivilegedPort(int port) => PrivilegedPorts.Contains(port);
    }

    /// <summary>
    /// Validates file paths with security considerations
    /// </summary>
    public static class FilePathValidator
    {
        private static readonly char[] InvalidPathChars = Path.GetInvalidPathChars();
        private static readonly string[] DangerousPatterns = new[]
        {
            "..",
            "~",
            "$",
            "%",
            "|",
            ";",
            "`",
            "\0",
            "\n",
            "\r"
        };

        public static ValidationResult Validate(string input, bool mustExist = false, bool allowRelative = false)
        {
            if (string.IsNullOrWhiteSpace(input))
                return ValidationResult.Fail("PATH_EMPTY", "File path cannot be empty");

            if (input.Length > 260) // MAX_PATH on Windows
                return ValidationResult.Fail("PATH_TOO_LONG", "File path is too long");

            // Check for invalid characters
            if (input.IndexOfAny(InvalidPathChars) >= 0)
                return ValidationResult.Fail("PATH_INVALID_CHARS", "Path contains invalid characters");

            // Check for dangerous patterns (path traversal)
            foreach (var pattern in DangerousPatterns)
            {
                if (input.Contains(pattern, StringComparison.OrdinalIgnoreCase))
                    return ValidationResult.Fail("PATH_DANGEROUS_PATTERN", 
                        $"Path contains dangerous pattern: {pattern}",
                        new() { ["pattern"] = pattern });
            }

            try
            {
                // Check if path is rooted
                if (!allowRelative && !Path.IsPathRooted(input))
                    return ValidationResult.Fail("PATH_NOT_ABSOLUTE", "Path must be absolute");

                // Get full path to normalize and check
                var fullPath = Path.GetFullPath(input);
                
                // Additional security: ensure the resolved path doesn't escape expected directories
                if (!IsPathSafe(fullPath))
                    return ValidationResult.Fail("PATH_TRAVERSAL", "Path traversal detected");

                if (mustExist && !File.Exists(fullPath) && !Directory.Exists(fullPath))
                    return ValidationResult.Fail("PATH_NOT_FOUND", "Path does not exist");

                return ValidationResult.Ok();
            }
            catch (Exception ex)
            {
                return ValidationResult.Fail("PATH_INVALID", 
                    "Invalid file path",
                    new() { ["exception"] = ex.Message });
            }
        }

        private static bool IsPathSafe(string fullPath)
        {
            // In production, check against allowed base paths
            var systemPaths = new[]
            {
                Environment.GetFolderPath(Environment.SpecialFolder.Windows),
                Environment.GetFolderPath(Environment.SpecialFolder.System),
                Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),
                Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86),
            };

            // Prevent access to system directories
            return !systemPaths.Any(sp => 
                fullPath.StartsWith(sp, StringComparison.OrdinalIgnoreCase));
        }
    }
}