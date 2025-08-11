using System;
using System.IO;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using System.Threading.Tasks;
using ProxyAssessmentTool.Updater.Models;

namespace ProxyAssessmentTool.Updater.Services
{
    public class SignatureValidator
    {
        private readonly string _expectedThumbprint;
        
        public SignatureValidator(string expectedThumbprint)
        {
            _expectedThumbprint = expectedThumbprint.Replace(" ", "").ToUpperInvariant();
        }

        public async Task<ValidationResult> ValidateUpdatePackageAsync(string packagePath)
        {
            try
            {
                // Step 1: Verify Authenticode signature on the .paup file
                var authenticodeResult = VerifyAuthenticode(packagePath);
                if (!authenticodeResult.IsValid)
                    return authenticodeResult;
                
                // Step 2: Extract and verify manifest
                using var archive = System.IO.Compression.ZipFile.OpenRead(packagePath);
                var manifestEntry = archive.GetEntry("manifest.json");
                if (manifestEntry == null)
                    return ValidationResult.Fail("Missing manifest.json");
                
                using var manifestStream = manifestEntry.Open();
                using var reader = new StreamReader(manifestStream);
                var manifestJson = await reader.ReadToEndAsync();
                
                var manifest = System.Text.Json.JsonSerializer.Deserialize<UpdateManifest>(manifestJson);
                if (manifest == null)
                    return ValidationResult.Fail("Invalid manifest format");
                
                // Step 3: Verify publisher thumbprint
                if (!string.Equals(manifest.PublisherThumbprint, _expectedThumbprint, StringComparison.OrdinalIgnoreCase))
                    return ValidationResult.Fail($"Invalid publisher thumbprint: {manifest.PublisherThumbprint}");
                
                // Step 4: Verify file hashes
                foreach (var file in manifest.Files)
                {
                    var fileEntry = archive.GetEntry(file.Path);
                    if (fileEntry == null)
                        return ValidationResult.Fail($"Missing file: {file.Path}");
                    
                    using var fileStream = fileEntry.Open();
                    var actualHash = await ComputeSha256Async(fileStream);
                    
                    if (!string.Equals(actualHash, file.Sha256, StringComparison.OrdinalIgnoreCase))
                        return ValidationResult.Fail($"Hash mismatch for {file.Path}");
                }
                
                return ValidationResult.Success(manifest);
            }
            catch (Exception ex)
            {
                return ValidationResult.Fail($"Validation error: {ex.Message}");
            }
        }

        private ValidationResult VerifyAuthenticode(string filePath)
        {
            try
            {
                var cert = X509Certificate.CreateFromSignedFile(filePath);
                if (cert == null)
                    return ValidationResult.Fail("File is not signed");
                
                var cert2 = new X509Certificate2(cert);
                
                // Verify certificate chain
                var chain = new X509Chain
                {
                    ChainPolicy = new X509ChainPolicy
                    {
                        RevocationMode = X509RevocationMode.Online,
                        RevocationFlag = X509RevocationFlag.ExcludeRoot,
                        UrlRetrievalTimeout = TimeSpan.FromSeconds(30)
                    }
                };
                
                if (!chain.Build(cert2))
                    return ValidationResult.Fail("Certificate chain validation failed");
                
                // Verify thumbprint
                var thumbprint = cert2.Thumbprint;
                if (!string.Equals(thumbprint, _expectedThumbprint, StringComparison.OrdinalIgnoreCase))
                    return ValidationResult.Fail($"Wrong certificate thumbprint: {thumbprint}");
                
                // Check expiration
                if (cert2.NotAfter < DateTime.Now)
                    return ValidationResult.Fail("Certificate has expired");
                
                return ValidationResult.Success();
            }
            catch (Exception ex)
            {
                return ValidationResult.Fail($"Authenticode verification failed: {ex.Message}");
            }
        }

        private static async Task<string> ComputeSha256Async(Stream stream)
        {
            using var sha256 = SHA256.Create();
            var hash = await sha256.ComputeHashAsync(stream);
            return BitConverter.ToString(hash).Replace("-", "").ToUpperInvariant();
        }
    }

    public class ValidationResult
    {
        public bool IsValid { get; }
        public string? ErrorMessage { get; }
        public UpdateManifest? Manifest { get; }
        
        private ValidationResult(bool isValid, string? errorMessage = null, UpdateManifest? manifest = null)
        {
            IsValid = isValid;
            ErrorMessage = errorMessage;
            Manifest = manifest;
        }
        
        public static ValidationResult Success(UpdateManifest? manifest = null) => new(true, null, manifest);
        public static ValidationResult Fail(string error) => new(false, error);
    }
}