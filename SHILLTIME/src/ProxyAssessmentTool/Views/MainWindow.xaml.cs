using System;
using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Win32;
using ProxyAssessmentTool.Core.Services;

namespace ProxyAssessmentTool.Views
{
    public partial class MainWindow : Window
    {
        private readonly IServiceProvider _serviceProvider;
        private readonly IGitHubUpdateService? _updateService;

        public MainWindow()
        {
            InitializeComponent();
            
            var version = GetType().Assembly.GetName().Version;
            VersionText.Text = $"Version {version?.ToString(3) ?? "1.0.0"}";
            
            // Get service provider from App
            _serviceProvider = Application.Current.GetServiceProvider();
            
            // Get update service and subscribe to notifications
            _updateService = _serviceProvider.GetService<IGitHubUpdateService>();
            if (_updateService != null)
            {
                _updateService.UpdateAvailable += OnUpdateAvailable;
            }
            
            // Navigate to dashboard by default
            NavigateTo("Dashboard");
        }

        private void NavigationButton_Click(object sender, RoutedEventArgs e)
        {
            if (sender is RadioButton button && button.Tag is string viewName)
            {
                NavigateTo(viewName);
            }
        }

        private void NavigateTo(string viewName)
        {
            try
            {
                object? content = viewName switch
                {
                    "Dashboard" => new TextBlock 
                    { 
                        Text = "Dashboard View", 
                        FontSize = 24, 
                        HorizontalAlignment = HorizontalAlignment.Center,
                        VerticalAlignment = VerticalAlignment.Center
                    },
                    "Assessment" => new TextBlock 
                    { 
                        Text = "Assessment View", 
                        FontSize = 24, 
                        HorizontalAlignment = HorizontalAlignment.Center,
                        VerticalAlignment = VerticalAlignment.Center
                    },
                    "Findings" => new TextBlock 
                    { 
                        Text = "Findings View", 
                        FontSize = 24, 
                        HorizontalAlignment = HorizontalAlignment.Center,
                        VerticalAlignment = VerticalAlignment.Center
                    },
                    "Reports" => new TextBlock 
                    { 
                        Text = "Reports View", 
                        FontSize = 24, 
                        HorizontalAlignment = HorizontalAlignment.Center,
                        VerticalAlignment = VerticalAlignment.Center
                    },
                    "Settings" => _serviceProvider.GetService<SettingsView>() ?? new SettingsView(),
                    _ => null
                };
                
                if (content != null)
                {
                    ContentFrame.Content = content;
                    StatusText.Text = $"{viewName} loaded";
                }
            }
            catch (Exception ex)
            {
                StatusText.Text = $"Failed to load {viewName}";
                Debug.WriteLine($"Navigation error: {ex.Message}");
            }
        }

        private void ExitMenuItem_Click(object sender, RoutedEventArgs e)
        {
            Application.Current.Shutdown(0);
        }

        private void SettingsMenuItem_Click(object sender, RoutedEventArgs e)
        {
            // Navigate to settings
            SettingsNav.IsChecked = true;
            NavigateTo("Settings");
        }

        private void CollectDiagnostics_Click(object sender, RoutedEventArgs e)
        {
            StatusText.Text = "Collecting diagnostics...";
            // TODO: Implement diagnostic collection
        }

        private void CheckForUpdates_Click(object sender, RoutedEventArgs e)
        {
            // Navigate to settings and trigger update check
            SettingsNav.IsChecked = true;
            NavigateTo("Settings");
            
            if (ContentFrame.Content is SettingsView settingsView)
            {
                // Settings view will check for updates on load
            }
        }

        private void ApplyUpdate_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new OpenFileDialog
            {
                Filter = "Update Packages (*.paup)|*.paup|All Files (*.*)|*.*",
                Title = "Select Update Package"
            };
            
            if (dialog.ShowDialog() == true)
            {
                LaunchUpdater(dialog.FileName);
            }
        }

        private void ViewUpdateHistory_Click(object sender, RoutedEventArgs e)
        {
            StatusText.Text = "Update history not yet implemented";
        }

        private void Documentation_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = "https://github.com/yourusername/ProxyAssessmentTool/wiki",
                    UseShellExecute = true
                });
            }
            catch
            {
                StatusText.Text = "Failed to open documentation";
            }
        }

        private void About_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show(
                "ProxyAssessmentTool\n" +
                $"Version {VersionText.Text}\n\n" +
                "A security assessment platform for authorized testing only.\n\n" +
                "© 2024 ProxyAssessmentTool Contributors",
                "About ProxyAssessmentTool",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }

        private void UpdateAvailableIndicator_Click(object sender, System.Windows.Input.MouseButtonEventArgs e)
        {
            // Navigate to settings when update indicator is clicked
            SettingsNav.IsChecked = true;
            NavigateTo("Settings");
        }

        private void LaunchUpdater(string updateFile)
        {
            try
            {
                var updaterPath = Path.Combine(AppContext.BaseDirectory, "ProxyAssessmentTool.Updater.exe");
                if (File.Exists(updaterPath))
                {
                    Process.Start(new ProcessStartInfo
                    {
                        FileName = updaterPath,
                        Arguments = $"\"{updateFile}\"",
                        UseShellExecute = true
                    });
                }
                else
                {
                    MessageBox.Show(
                        "Update component not found.\nPlease reinstall the application.",
                        "Updater Missing",
                        MessageBoxButton.OK,
                        MessageBoxImage.Warning);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to launch updater: {ex.Message}", "Error", 
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void OnUpdateAvailable(object? sender, UpdateAvailableEventArgs e)
        {
            // Update UI on main thread
            Dispatcher.BeginInvoke(() =>
            {
                // Show update badge on settings
                SettingsUpdateBadge.Visibility = Visibility.Visible;
                
                // Show update indicator in status bar
                UpdateAvailableIndicator.Visibility = Visibility.Visible;
                
                // Update status text
                StatusText.Text = $"Update available: Version {e.Version}";
            });
        }

        protected override void OnClosed(EventArgs e)
        {
            // Unsubscribe from update notifications
            if (_updateService != null)
            {
                _updateService.UpdateAvailable -= OnUpdateAvailable;
            }
            
            base.OnClosed(e);
        }
    }
}