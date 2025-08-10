using System;
using System.Collections.Generic;
using FsCheck;
using FsCheck.Xunit;
using ProxyAssessmentTool.Core.Validation;
using Xunit;

namespace ProxyAssessmentTool.Tests.Core
{
    public class CidrValidatorTests
    {
        [Theory]
        [InlineData("10.0.0.0/8", true)]
        [InlineData("172.16.0.0/12", true)]
        [InlineData("192.168.1.0/24", true)]
        [InlineData("0.0.0.0/0", true)]
        [InlineData("255.255.255.255/32", true)]
        [InlineData("192.168.1.0/33", false)] // Invalid prefix
        [InlineData("192.168.1.0/7", false)]  // Below minimum
        [InlineData("192.168.1.0", false)]    // Missing prefix
        [InlineData("192.168.1.0/", false)]   // Missing prefix number
        [InlineData("256.0.0.0/24", false)]   // Invalid IP
        [InlineData("", false)]
        [InlineData(null, false)]
        [InlineData("192.168.1.0/24; DROP TABLE findings;", false)] // Injection attempt
        public void Validate_BasicCases_ReturnsExpected(string? input, bool expectedValid)
        {
            // Act
            var result = CidrValidator.Validate(input!);

            // Assert
            Assert.Equal(expectedValid, result.IsValid);
        }

        [Fact]
        public void Validate_TooLongInput_ReturnsError()
        {
            // Arrange
            var longCidr = new string('1', 51);

            // Act
            var result = CidrValidator.Validate(longCidr);

            // Assert
            Assert.False(result.IsValid);
            Assert.Equal("CIDR_TOO_LONG", result.ErrorCode);
        }

        [Fact]
        public void Validate_ControlCharacters_ReturnsError()
        {
            // Arrange
            var cidrWithControl = "192.168.1.0/24\0";

            // Act
            var result = CidrValidator.Validate(cidrWithControl);

            // Assert
            Assert.False(result.IsValid);
            Assert.Equal("CIDR_INVALID_CHARS", result.ErrorCode);
        }

        [Theory]
        [InlineData("10.0.0.0/16", false, false)]     // Private, not allowed
        [InlineData("8.8.8.0/24", false, true)]       // Public, allowed
        [InlineData("10.0.0.0/16", true, true)]       // Private, allowed
        [InlineData("2001:db8::/32", true, false)]    // IPv6, not allowed
        [InlineData("2001:db8::/32", true, true)]     // IPv6, allowed
        public void Validate_WithOptions_RespectsSettings(string cidr, bool allowPrivate, bool allowIPv6)
        {
            // Act
            var result = CidrValidator.Validate(cidr, allowPrivate, allowIPv6);

            // Assert
            if (cidr.Contains(':') && !allowIPv6)
            {
                Assert.False(result.IsValid);
                Assert.Equal("CIDR_IPV6_NOT_ALLOWED", result.ErrorCode);
            }
            else if ((cidr.StartsWith("10.") || cidr.StartsWith("192.168.") || cidr.StartsWith("172.")) && !allowPrivate)
            {
                Assert.False(result.IsValid);
                Assert.Equal("CIDR_PRIVATE_NOT_ALLOWED", result.ErrorCode);
            }
            else
            {
                Assert.True(result.IsValid);
            }
        }

        [Property]
        public Property CidrValidator_NeverCrashes_OnRandomInput()
        {
            return Prop.ForAll<string>(input =>
            {
                try
                {
                    var result = CidrValidator.Validate(input ?? "");
                    return result.IsValid || !result.IsValid; // Always returns a result
                }
                catch
                {
                    return false;
                }
            });
        }
    }

    public class HostnameValidatorTests
    {
        [Theory]
        [InlineData("example.com", true)]
        [InlineData("sub.example.com", true)]
        [InlineData("deep.sub.example.com", true)]
        [InlineData("example", true)]
        [InlineData("192.168.1.1", true)]
        [InlineData("2001:db8::1", true)]
        [InlineData("-example.com", false)] // Starts with hyphen
        [InlineData("example-.com", false)] // Ends with hyphen
        [InlineData("exam ple.com", false)] // Contains space
        [InlineData("example..com", false)] // Double dot
        [InlineData("", false)]
        [InlineData(null, false)]
        public void Validate_BasicCases_ReturnsExpected(string? input, bool expectedValid)
        {
            // Act
            var result = HostnameValidator.Validate(input!);

            // Assert
            Assert.Equal(expectedValid, result.IsValid);
        }

        [Fact]
        public void Validate_TooLongHostname_ReturnsError()
        {
            // Arrange
            var longHostname = new string('a', 254);

            // Act
            var result = HostnameValidator.Validate(longHostname);

            // Assert
            Assert.False(result.IsValid);
            Assert.Equal("HOST_TOO_LONG", result.ErrorCode);
        }

        [Fact]
        public void Validate_TooLongLabel_ReturnsError()
        {
            // Arrange
            var longLabel = new string('a', 64) + ".com";

            // Act
            var result = HostnameValidator.Validate(longLabel);

            // Assert
            Assert.False(result.IsValid);
            Assert.Equal("HOST_LABEL_TOO_LONG", result.ErrorCode);
        }

        [Theory]
        [InlineData("192.168.1.1", false, false)]
        [InlineData("192.168.1.1", true, true)]
        [InlineData("example.com", false, true)]
        [InlineData("example.com", true, true)]
        public void Validate_IPAddressOption_RespectsSettings(string input, bool allowIP, bool expectedValid)
        {
            // Act
            var result = HostnameValidator.Validate(input, allowIP);

            // Assert
            Assert.Equal(expectedValid, result.IsValid);
            if (!expectedValid && System.Net.IPAddress.TryParse(input, out _))
            {
                Assert.Equal("HOST_IP_NOT_ALLOWED", result.ErrorCode);
            }
        }

        [Property]
        public Property HostnameValidator_NeverCrashes_OnRandomInput()
        {
            return Prop.ForAll<string>(input =>
            {
                try
                {
                    var result = HostnameValidator.Validate(input ?? "");
                    return result.IsValid || !result.IsValid;
                }
                catch
                {
                    return false;
                }
            });
        }
    }

    public class PortValidatorTests
    {
        [Theory]
        [InlineData(1, true)]
        [InlineData(80, true)]
        [InlineData(443, true)]
        [InlineData(1080, true)]
        [InlineData(8080, true)]
        [InlineData(65535, true)]
        [InlineData(0, false)]
        [InlineData(-1, false)]
        [InlineData(65536, false)]
        [InlineData(100000, false)]
        public void Validate_BasicCases_ReturnsExpected(int port, bool expectedValid)
        {
            // Act
            var result = PortValidator.Validate(port);

            // Assert
            Assert.Equal(expectedValid, result.IsValid);
        }

        [Theory]
        [InlineData(22, false, false)]    // SSH, not allowed
        [InlineData(80, false, false)]    // HTTP, not allowed
        [InlineData(443, false, false)]   // HTTPS, not allowed
        [InlineData(1024, false, true)]   // First non-privileged
        [InlineData(8080, false, true)]   // Non-privileged
        [InlineData(22, true, true)]      // SSH, allowed
        public void Validate_PrivilegedPorts_RespectsSettings(int port, bool allowPrivileged, bool expectedValid)
        {
            // Act
            var result = PortValidator.Validate(port, allowPrivileged);

            // Assert
            Assert.Equal(expectedValid, result.IsValid);
            if (!expectedValid && port < 1024)
            {
                Assert.Equal("PORT_PRIVILEGED", result.ErrorCode);
            }
        }

        [Theory]
        [InlineData(1, 100, true)]
        [InlineData(8000, 8100, true)]
        [InlineData(100, 1, false)]      // Start > End
        [InlineData(1, 2000, false)]     // Range too large
        [InlineData(0, 100, false)]      // Invalid start
        [InlineData(1, 100000, false)]   // Invalid end
        public void ValidateRange_BasicCases_ReturnsExpected(int start, int end, bool expectedValid)
        {
            // Act
            var result = PortValidator.ValidateRange(start, end);

            // Assert
            Assert.Equal(expectedValid, result.IsValid);
        }

        [Theory]
        [InlineData(22, true)]
        [InlineData(80, true)]
        [InlineData(443, true)]
        [InlineData(3389, true)]
        [InlineData(8080, false)]
        [InlineData(1080, false)]
        public void IsWellKnownPrivilegedPort_ReturnsExpected(int port, bool expected)
        {
            // Act
            var result = PortValidator.IsWellKnownPrivilegedPort(port);

            // Assert
            Assert.Equal(expected, result);
        }
    }

    public class FilePathValidatorTests
    {
        [Theory]
        [InlineData(@"C:\Users\test\file.txt", true)]
        [InlineData(@"C:\Program Files\app\config.yaml", true)]
        [InlineData(@"/home/user/file.txt", true)]
        [InlineData(@"./relative/path.txt", false)] // Relative not allowed by default
        [InlineData(@"..\traversal\attempt.txt", false)]
        [InlineData(@"C:\Users\test\..\..\Windows\System32", false)]
        [InlineData("", false)]
        [InlineData(null, false)]
        public void Validate_BasicCases_ReturnsExpected(string? input, bool expectedValid)
        {
            // Skip non-Windows paths on Windows and vice versa
            if (input != null && Environment.OSVersion.Platform == PlatformID.Win32NT && input.StartsWith("/"))
                return;
            if (input != null && Environment.OSVersion.Platform != PlatformID.Win32NT && input.Contains(@"\"))
                return;

            // Act
            var result = FilePathValidator.Validate(input!);

            // Assert
            Assert.Equal(expectedValid, result.IsValid);
        }

        [Fact]
        public void Validate_DangerousPatterns_ReturnsError()
        {
            // Arrange
            var dangerousPaths = new[]
            {
                @"C:\Users\test\..\..\secret",
                @"C:\Users\test;rm -rf /",
                @"C:\Users\test`whoami`",
                @"C:\Users\test$HOME",
                @"C:\Users\test%WINDIR%"
            };

            // Act & Assert
            foreach (var path in dangerousPaths)
            {
                var result = FilePathValidator.Validate(path);
                Assert.False(result.IsValid);
                Assert.Equal("PATH_DANGEROUS_PATTERN", result.ErrorCode);
            }
        }

        [Fact]
        public void Validate_InvalidCharacters_ReturnsError()
        {
            // Arrange
            var invalidPath = "C:\\Users\\test<>file.txt";

            // Act
            var result = FilePathValidator.Validate(invalidPath);

            // Assert
            Assert.False(result.IsValid);
            Assert.Equal("PATH_INVALID_CHARS", result.ErrorCode);
        }

        [Property]
        public Property FilePathValidator_NeverCrashes_OnRandomInput()
        {
            return Prop.ForAll<string>(input =>
            {
                try
                {
                    var result = FilePathValidator.Validate(input ?? "");
                    return result.IsValid || !result.IsValid;
                }
                catch
                {
                    return false;
                }
            });
        }
    }
}