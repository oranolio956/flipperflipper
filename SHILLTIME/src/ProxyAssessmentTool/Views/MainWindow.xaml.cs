using System;
using System.Diagnostics;
using System.IO;
using System.Windows;
using Microsoft.Win32;

namespace ProxyAssessmentTool.Views
{
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
            
            var version = GetType().Assembly.GetName().Version;
            VersionText.Text = $"Version {version?.ToString(3) ?? "1.0.0"}";
        }

        private void ExitMenuItem_Click(object sender, RoutedEventArgs e)
        {
            Application.Current.Shutdown(0);
        }

        private void SettingsMenuItem_Click(object sender, RoutedEventArgs e)
        {
            StatusText.Text = "Settings dialog not yet implemented";
        }

        private void CollectDiagnostics_Click(object sender, RoutedEventArgs e)
        {
            StatusText.Text = "Collecting diagnostics...";
            // TODO: Implement diagnostic collection
        }

        private void CheckForUpdates_Click(object sender, RoutedEventArgs e)
        {
            StatusText.Text = "Checking for updates...";
            // TODO: Implement update check
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
    }
}