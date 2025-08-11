using System;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media.Animation;
using Microsoft.Extensions.DependencyInjection;
using ProxyAssessmentTool.Core.Services;

namespace ProxyAssessmentTool.Views
{
    public partial class SettingsView : UserControl
    {
        private readonly IGitHubUpdateService _updateService;
        private UpdateCheckResult? _latestUpdateResult;
        private CancellationTokenSource? _downloadCts;
        private bool _isUpdatePanelExpanded = false;

        public SettingsView()
        {
            InitializeComponent();
            
            // Get update service from DI
            var serviceProvider = Application.Current.GetServiceProvider();
            _updateService = serviceProvider.GetRequiredService<IGitHubUpdateService>();
            
            // Subscribe to update notifications
            _updateService.UpdateAvailable += OnUpdateAvailable;
            
            // Initialize UI
            InitializeSettings();
            
            // Check for updates on load
            _ = CheckForUpdatesAsync();
        }

        private void InitializeSettings()
        {
            // Set current version
            var version = GetType().Assembly.GetName().Version;
            AppVersionText.Text = $"{version?.ToString(3) ?? "1.0.0"}";
            CurrentVersionText.Text = $"Current: {version?.ToString(3) ?? "1.0.0"}";
            
            // Load update settings
            var settings = _updateService.GetSettings();
            AutoUpdateToggle.IsOn = settings.AutoCheckEnabled;
            
            // Set check interval
            UpdateIntervalCombo.SelectedIndex = settings.CheckIntervalHours switch
            {
                6 => 0,
                24 => 1,
                168 => 2, // 1 week
                720 => 3, // 1 month
                _ => 1
            };
            
            // Update last check time
            UpdateLastCheckTime(settings.LastCheckTime);
        }

        private async Task CheckForUpdatesAsync()
        {
            try
            {
                UpdateStatusText.Text = "Checking for updates...";
                UpdateBadge.Visibility = Visibility.Collapsed;
                
                var result = await _updateService.CheckForUpdatesAsync();
                _latestUpdateResult = result;
                
                if (!result.Success)
                {
                    UpdateStatusText.Text = "Check failed - tap to retry";
                    return;
                }
                
                if (result.IsUpdateAvailable)
                {
                    UpdateStatusText.Text = $"Version {result.LatestVersion} available";
                    UpdateBadge.Visibility = Visibility.Visible;
                    
                    // Update details panel
                    UpdateVersionText.Text = $"ProxyAssessmentTool {result.LatestVersion}";
                    
                    if (result.UpdateAsset != null)
                    {
                        var sizeMB = result.UpdateAsset.Size / (1024.0 * 1024.0);
                        UpdateSizeText.Text = $"{sizeMB:F1} MB";
                    }
                    
                    if (result.LatestRelease != null)
                    {
                        ReleaseNotesText.Text = result.LatestRelease.Body;
                    }
                }
                else
                {
                    UpdateStatusText.Text = "Your software is up to date";
                }
                
                // Update last check time
                UpdateLastCheckTime(DateTime.UtcNow);
            }
            catch (Exception ex)
            {
                UpdateStatusText.Text = "Check failed - tap to retry";
                Debug.WriteLine($"Update check failed: {ex.Message}");
            }
        }

        private void UpdateLastCheckTime(DateTime? lastCheck)
        {
            if (lastCheck.HasValue)
            {
                var timeAgo = DateTime.UtcNow - lastCheck.Value;
                string timeText;
                
                if (timeAgo.TotalMinutes < 1)
                    timeText = "Just now";
                else if (timeAgo.TotalHours < 1)
                    timeText = $"{(int)timeAgo.TotalMinutes} minutes ago";
                else if (timeAgo.TotalDays < 1)
                    timeText = $"{(int)timeAgo.TotalHours} hours ago";
                else
                    timeText = $"{(int)timeAgo.TotalDays} days ago";
                
                LastCheckText.Text = $"Last checked: {timeText}";
            }
            else
            {
                LastCheckText.Text = "Last checked: Never";
            }
        }

        private void UpdateButton_Click(object sender, RoutedEventArgs e)
        {
            if (_latestUpdateResult?.IsUpdateAvailable == true)
            {
                // Toggle update details panel
                _isUpdatePanelExpanded = !_isUpdatePanelExpanded;
                UpdateDetailsPanel.Visibility = _isUpdatePanelExpanded ? Visibility.Visible : Visibility.Collapsed;
            }
            else
            {
                // Check for updates again
                _ = CheckForUpdatesAsync();
            }
        }

        private async void DownloadInstallButton_Click(object sender, RoutedEventArgs e)
        {
            if (_latestUpdateResult?.LatestRelease == null)
                return;
            
            try
            {
                // Update UI
                DownloadInstallButton.IsEnabled = false;
                DownloadProgress.Visibility = Visibility.Visible;
                DownloadProgressText.Visibility = Visibility.Visible;
                DownloadButtonIcon.Text = "⏸";
                DownloadButtonText.Text = "Downloading...";
                
                // Create progress reporter
                var progress = new Progress<DownloadProgress>(p =>
                {
                    Dispatcher.BeginInvoke(() =>
                    {
                        DownloadProgress.Value = p.PercentComplete;
                        var downloadedMB = p.BytesDownloaded / (1024.0 * 1024.0);
                        var totalMB = p.TotalBytes / (1024.0 * 1024.0);
                        DownloadProgressText.Text = $"{downloadedMB:F1} MB of {totalMB:F1} MB";
                    });
                });
                
                // Download update
                _downloadCts = new CancellationTokenSource();
                var updatePath = await _updateService.DownloadUpdateAsync(
                    _latestUpdateResult.LatestRelease, 
                    progress, 
                    _downloadCts.Token);
                
                // Update UI for installation
                DownloadButtonIcon.Text = "📦";
                DownloadButtonText.Text = "Installing...";
                DownloadProgressText.Text = "Preparing installation...";
                
                // Install update
                var success = await _updateService.InstallUpdateAsync(updatePath);
                
                if (!success)
                {
                    MessageBox.Show(
                        "Failed to install update. Please try again or download manually from GitHub.",
                        "Update Failed",
                        MessageBoxButton.OK,
                        MessageBoxImage.Warning);
                    
                    ResetDownloadUI();
                }
                // If successful, the updater will close this app
            }
            catch (OperationCanceledException)
            {
                ResetDownloadUI();
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Update failed: {ex.Message}",
                    "Update Error",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
                
                ResetDownloadUI();
            }
        }

        private void ResetDownloadUI()
        {
            DownloadInstallButton.IsEnabled = true;
            DownloadProgress.Visibility = Visibility.Collapsed;
            DownloadProgressText.Visibility = Visibility.Collapsed;
            DownloadProgress.Value = 0;
            DownloadButtonIcon.Text = "⬇";
            DownloadButtonText.Text = "Download and Install";
        }

        private async void AutoUpdateToggle_Toggled(object sender, RoutedEventArgs e)
        {
            var settings = _updateService.GetSettings();
            settings.AutoCheckEnabled = AutoUpdateToggle.IsOn;
            await _updateService.SaveSettingsAsync(settings);
        }

        private async void UpdateIntervalCombo_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            var settings = _updateService.GetSettings();
            settings.CheckIntervalHours = UpdateIntervalCombo.SelectedIndex switch
            {
                0 => 6,
                1 => 24,
                2 => 168, // 1 week
                3 => 720, // 1 month
                _ => 24
            };
            await _updateService.SaveSettingsAsync(settings);
        }

        private void GitHubLink_Click(object sender, RoutedEventArgs e)
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = "https://github.com/yourusername/ProxyAssessmentTool",
                UseShellExecute = true
            });
        }

        private void OnUpdateAvailable(object? sender, UpdateAvailableEventArgs e)
        {
            // This is called from background thread
            Dispatcher.BeginInvoke(() =>
            {
                UpdateStatusText.Text = $"Version {e.Version} available";
                UpdateBadge.Visibility = Visibility.Visible;
                
                // The MainWindow will show its own notification badges
                // We just update our UI here
            });
        }
    }

    // Extension method to get service provider
    public static class ApplicationExtensions
    {
        public static IServiceProvider GetServiceProvider(this Application app)
        {
            // This should be set by App.xaml.cs
            return (IServiceProvider)app.Properties["ServiceProvider"]!;
        }
    }
}