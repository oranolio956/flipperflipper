using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using ProxyAssessmentTool.Core.Models;

namespace ProxyAssessmentTool.Core.Services
{
    public interface IGitHubUpdateService
    {
        Task<UpdateCheckResult> CheckForUpdatesAsync(CancellationToken cancellationToken = default);
        Task<string> DownloadUpdateAsync(GitHubRelease release, IProgress<DownloadProgress>? progress = null, CancellationToken cancellationToken = default);
        Task<bool> InstallUpdateAsync(string updateFilePath);
        UpdateSettings GetSettings();
        Task SaveSettingsAsync(UpdateSettings settings);
        event EventHandler<UpdateAvailableEventArgs>? UpdateAvailable;
    }

    public class GitHubUpdateService : IGitHubUpdateService, IDisposable
    {
        private readonly ILogger<GitHubUpdateService> _logger;
        private readonly IConfiguration _configuration;
        private readonly HttpClient _httpClient;
        private readonly string _repoOwner;
        private readonly string _repoName;
        private readonly Version _currentVersion;
        private readonly string _settingsPath;
        private Timer? _checkTimer;
        private UpdateSettings _settings;

        public event EventHandler<UpdateAvailableEventArgs>? UpdateAvailable;

        public GitHubUpdateService(ILogger<GitHubUpdateService> logger, IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
            _httpClient = new HttpClient();
            _httpClient.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/vnd.github.v3+json"));
            _httpClient.DefaultRequestHeaders.UserAgent.ParseAdd("ProxyAssessmentTool/1.0");
            
            // Read from configuration
            _repoOwner = _configuration["GitHub:Owner"] ?? "yourusername";
            _repoName = _configuration["GitHub:Repository"] ?? "ProxyAssessmentTool";
            
            var assembly = typeof(GitHubUpdateService).Assembly;
            _currentVersion = assembly.GetName().Version ?? new Version(1, 0, 0);
            
            var appData = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "ProxyAssessmentTool");
            _settingsPath = Path.Combine(appData, "updateSettings.json");
            
            _settings = LoadSettings();
            StartBackgroundChecker();
            
            _logger.LogInformation("GitHub update service initialized for {Owner}/{Repo}", _repoOwner, _repoName);
        }

        public async Task<UpdateCheckResult> CheckForUpdatesAsync(CancellationToken cancellationToken = default)
        {
            try
            {
                _logger.LogInformation("Checking for updates from GitHub");
                
                var url = $"https://api.github.com/repos/{_repoOwner}/{_repoName}/releases/latest";
                var response = await _httpClient.GetAsync(url, cancellationToken);
                
                if (!response.IsSuccessStatusCode)
                {
                    _logger.LogWarning("Failed to check for updates: {StatusCode}", response.StatusCode);
                    return new UpdateCheckResult { Success = false, Error = $"GitHub API returned {response.StatusCode}" };
                }
                
                var json = await response.Content.ReadAsStringAsync(cancellationToken);
                var release = JsonSerializer.Deserialize<GitHubRelease>(json, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });
                
                if (release == null)
                {
                    return new UpdateCheckResult { Success = false, Error = "Failed to parse release data" };
                }
                
                // Parse version from tag (assume tags like "v1.2.3")
                var versionString = release.TagName.TrimStart('v', 'V');
                if (!Version.TryParse(versionString, out var latestVersion))
                {
                    return new UpdateCheckResult { Success = false, Error = "Invalid version format in release tag" };
                }
                
                var isUpdateAvailable = latestVersion > _currentVersion;
                
                // Find the .paup asset
                var updateAsset = release.Assets?.FirstOrDefault(a => a.Name.EndsWith(".paup", StringComparison.OrdinalIgnoreCase));
                if (isUpdateAvailable && updateAsset == null)
                {
                    _logger.LogWarning("Update available but no .paup file found in release assets");
                    isUpdateAvailable = false;
                }
                
                _settings.LastCheckTime = DateTime.UtcNow;
                await SaveSettingsAsync(_settings);
                
                var result = new UpdateCheckResult
                {
                    Success = true,
                    IsUpdateAvailable = isUpdateAvailable,
                    LatestRelease = release,
                    CurrentVersion = _currentVersion,
                    LatestVersion = latestVersion,
                    UpdateAsset = updateAsset
                };
                
                if (isUpdateAvailable && _settings.AutoCheckEnabled)
                {
                    UpdateAvailable?.Invoke(this, new UpdateAvailableEventArgs(release, latestVersion));
                }
                
                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error checking for updates");
                return new UpdateCheckResult { Success = false, Error = ex.Message };
            }
        }

        public async Task<string> DownloadUpdateAsync(GitHubRelease release, IProgress<DownloadProgress>? progress = null, CancellationToken cancellationToken = default)
        {
            var updateAsset = release.Assets?.FirstOrDefault(a => a.Name.EndsWith(".paup", StringComparison.OrdinalIgnoreCase));
            if (updateAsset == null)
            {
                throw new InvalidOperationException("No update package found in release");
            }
            
            var tempPath = Path.Combine(Path.GetTempPath(), $"ProxyAssessmentTool_Update_{Guid.NewGuid()}.paup");
            
            try
            {
                _logger.LogInformation("Downloading update from {Url}", updateAsset.BrowserDownloadUrl);
                
                using var response = await _httpClient.GetAsync(updateAsset.BrowserDownloadUrl, HttpCompletionOption.ResponseHeadersRead, cancellationToken);
                response.EnsureSuccessStatusCode();
                
                var totalBytes = response.Content.Headers.ContentLength ?? -1;
                var buffer = new byte[81920]; // 80KB buffer
                var totalRead = 0L;
                
                using var fileStream = File.Create(tempPath);
                using var contentStream = await response.Content.ReadAsStreamAsync(cancellationToken);
                
                while (true)
                {
                    var bytesRead = await contentStream.ReadAsync(buffer, 0, buffer.Length, cancellationToken);
                    if (bytesRead == 0)
                        break;
                    
                    await fileStream.WriteAsync(buffer, 0, bytesRead, cancellationToken);
                    totalRead += bytesRead;
                    
                    if (totalBytes > 0)
                    {
                        var percentage = (int)((totalRead * 100) / totalBytes);
                        progress?.Report(new DownloadProgress
                        {
                            BytesDownloaded = totalRead,
                            TotalBytes = totalBytes,
                            PercentComplete = percentage
                        });
                    }
                }
                
                _logger.LogInformation("Update downloaded successfully to {Path}", tempPath);
                return tempPath;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to download update");
                
                if (File.Exists(tempPath))
                {
                    try { File.Delete(tempPath); } catch { }
                }
                
                throw;
            }
        }

        public async Task<bool> InstallUpdateAsync(string updateFilePath)
        {
            try
            {
                if (!File.Exists(updateFilePath))
                {
                    throw new FileNotFoundException("Update file not found", updateFilePath);
                }
                
                // Launch the updater
                var updaterPath = Path.Combine(AppContext.BaseDirectory, "ProxyAssessmentTool.Updater.exe");
                if (!File.Exists(updaterPath))
                {
                    _logger.LogError("Updater executable not found at {Path}", updaterPath);
                    return false;
                }
                
                var startInfo = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = updaterPath,
                    Arguments = $"\"{updateFilePath}\"",
                    UseShellExecute = true
                };
                
                _logger.LogInformation("Launching updater with package {Package}", updateFilePath);
                System.Diagnostics.Process.Start(startInfo);
                
                // The updater will handle closing this app
                await Task.Delay(1000); // Give updater time to start
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to install update");
                return false;
            }
        }

        public UpdateSettings GetSettings() => _settings;

        public async Task SaveSettingsAsync(UpdateSettings settings)
        {
            _settings = settings;
            
            try
            {
                var json = JsonSerializer.Serialize(settings, new JsonSerializerOptions { WriteIndented = true });
                var dir = Path.GetDirectoryName(_settingsPath);
                if (!string.IsNullOrEmpty(dir))
                    Directory.CreateDirectory(dir);
                
                await File.WriteAllTextAsync(_settingsPath, json);
                
                // Restart timer if auto-check setting changed
                StartBackgroundChecker();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to save update settings");
            }
        }

        private UpdateSettings LoadSettings()
        {
            try
            {
                if (File.Exists(_settingsPath))
                {
                    var json = File.ReadAllText(_settingsPath);
                    return JsonSerializer.Deserialize<UpdateSettings>(json) ?? new UpdateSettings();
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to load update settings, using defaults");
            }
            
            // Load defaults from configuration
            var settings = new UpdateSettings
            {
                AutoCheckEnabled = _configuration.GetValue<bool>("Updates:AutoCheckEnabled", true),
                CheckIntervalHours = _configuration.GetValue<int>("Updates:CheckIntervalHours", 24),
                ShowPreReleases = _configuration.GetValue<bool>("Updates:ShowPreReleases", false)
            };
            
            return settings;
        }

        private void StartBackgroundChecker()
        {
            _checkTimer?.Dispose();
            
            if (!_settings.AutoCheckEnabled)
                return;
            
            // Check on startup and then periodically
            Task.Run(async () =>
            {
                await Task.Delay(TimeSpan.FromSeconds(30)); // Wait 30s after startup
                await CheckForUpdatesAsync();
            });
            
            // Check every N hours based on settings
            var interval = TimeSpan.FromHours(_settings.CheckIntervalHours);
            _checkTimer = new Timer(async _ => await CheckForUpdatesAsync(), null, interval, interval);
        }

        public void Dispose()
        {
            _checkTimer?.Dispose();
            _httpClient?.Dispose();
        }
    }

    public class UpdateCheckResult
    {
        public bool Success { get; set; }
        public string? Error { get; set; }
        public bool IsUpdateAvailable { get; set; }
        public GitHubRelease? LatestRelease { get; set; }
        public Version? CurrentVersion { get; set; }
        public Version? LatestVersion { get; set; }
        public GitHubAsset? UpdateAsset { get; set; }
    }

    public class GitHubRelease
    {
        public string TagName { get; set; } = "";
        public string Name { get; set; } = "";
        public string Body { get; set; } = "";
        public bool Prerelease { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime PublishedAt { get; set; }
        public List<GitHubAsset>? Assets { get; set; }
    }

    public class GitHubAsset
    {
        public string Name { get; set; } = "";
        public string BrowserDownloadUrl { get; set; } = "";
        public long Size { get; set; }
        public string ContentType { get; set; } = "";
    }

    public class UpdateSettings
    {
        public bool AutoCheckEnabled { get; set; } = true;
        public int CheckIntervalHours { get; set; } = 24;
        public DateTime? LastCheckTime { get; set; }
        public bool AutoDownload { get; set; } = false;
        public bool ShowPreReleases { get; set; } = false;
    }

    public class UpdateAvailableEventArgs : EventArgs
    {
        public GitHubRelease Release { get; }
        public Version Version { get; }
        
        public UpdateAvailableEventArgs(GitHubRelease release, Version version)
        {
            Release = release;
            Version = version;
        }
    }

    public class DownloadProgress
    {
        public long BytesDownloaded { get; set; }
        public long TotalBytes { get; set; }
        public int PercentComplete { get; set; }
    }
}