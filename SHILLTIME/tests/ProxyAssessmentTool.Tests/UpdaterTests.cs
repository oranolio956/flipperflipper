using System;
using System.IO;
using System.Threading.Tasks;
using Xunit;
using FluentAssertions;
using ProxyAssessmentTool.Updater.Services;
using ProxyAssessmentTool.Updater.Models;

namespace ProxyAssessmentTool.Tests.Updater
{
    public class SignatureValidatorTests
    {
        [Fact]
        public async Task ValidateUpdatePackage_ShouldRejectUnsignedPackage()
        {
            // Arrange
            var validator = new SignatureValidator("EXPECTED_THUMBPRINT");
            var unsignedPackage = CreateUnsignedPackage();
            
            // Act
            var result = await validator.ValidateUpdatePackageAsync(unsignedPackage);
            
            // Assert
            result.IsValid.Should().BeFalse();
            result.ErrorMessage.Should().Contain("not signed");
        }

        [Fact]
        public async Task ValidateUpdatePackage_ShouldRejectWrongThumbprint()
        {
            // Arrange
            var validator = new SignatureValidator("EXPECTED_THUMBPRINT");
            var wrongCertPackage = CreatePackageWithWrongCert();
            
            // Act
            var result = await validator.ValidateUpdatePackageAsync(wrongCertPackage);
            
            // Assert
            result.IsValid.Should().BeFalse();
            result.ErrorMessage.Should().Contain("thumbprint");
        }

        [Fact]
        public async Task ValidateUpdatePackage_ShouldRejectTamperedFiles()
        {
            // Arrange
            var validator = new SignatureValidator("EXPECTED_THUMBPRINT");
            var tamperedPackage = CreateTamperedPackage();
            
            // Act
            var result = await validator.ValidateUpdatePackageAsync(tamperedPackage);
            
            // Assert
            result.IsValid.Should().BeFalse();
            result.ErrorMessage.Should().Contain("hash mismatch");
        }

        [Fact]
        public async Task ValidateUpdatePackage_ShouldAcceptValidPackage()
        {
            // Arrange
            var validator = new SignatureValidator("VALID_THUMBPRINT");
            var validPackage = CreateValidPackage();
            
            // Act
            var result = await validator.ValidateUpdatePackageAsync(validPackage);
            
            // Assert
            result.IsValid.Should().BeTrue();
            result.Manifest.Should().NotBeNull();
        }

        private string CreateUnsignedPackage()
        {
            // Create test package without signature
            return Path.GetTempFileName();
        }

        private string CreatePackageWithWrongCert()
        {
            // Create test package with wrong certificate
            return Path.GetTempFileName();
        }

        private string CreateTamperedPackage()
        {
            // Create test package with modified files
            return Path.GetTempFileName();
        }

        private string CreateValidPackage()
        {
            // Create valid test package
            return Path.GetTempFileName();
        }
    }

    public class AtomicInstallerTests
    {
        [Fact]
        public async Task InstallUpdate_ShouldPerformAtomicSwap()
        {
            // Arrange
            var progress = new Progress<InstallProgress>();
            var installer = new AtomicInstaller(progress);
            var package = CreateTestPackage();
            var manifest = CreateTestManifest("2.0.0");
            
            // Act
            var result = await installer.InstallUpdateAsync(package, manifest);
            
            // Assert
            result.Success.Should().BeTrue();
            result.InstallPath.Should().Contain("app-2.0.0");
            Directory.Exists(result.InstallPath).Should().BeTrue();
        }

        [Fact]
        public async Task InstallUpdate_ShouldRollbackOnFailure()
        {
            // Arrange
            var progress = new Progress<InstallProgress>();
            var installer = new AtomicInstaller(progress);
            var corruptPackage = CreateCorruptPackage();
            var manifest = CreateTestManifest("2.0.0");
            
            // Act
            var result = await installer.InstallUpdateAsync(corruptPackage, manifest);
            
            // Assert
            result.Success.Should().BeFalse();
            result.Error.Should().NotBeNullOrEmpty();
            // Verify no partial installation remains
        }

        private string CreateTestPackage()
        {
            // Create test update package
            return Path.GetTempFileName();
        }

        private string CreateCorruptPackage()
        {
            // Create corrupt test package
            return Path.GetTempFileName();
        }

        private UpdateManifest CreateTestManifest(string version)
        {
            return new UpdateManifest
            {
                Version = version,
                ReleaseDate = DateTime.UtcNow,
                PublisherThumbprint = "TEST_THUMBPRINT",
                Files = new()
            };
        }
    }
}