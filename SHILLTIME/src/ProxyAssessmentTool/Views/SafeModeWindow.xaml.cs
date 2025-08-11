using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Windows;

namespace ProxyAssessmentTool.Views
{
    public partial class SafeModeWindow : Window
    {
        private readonly string _reason;
        private readonly Exception? _exception;
        private readonly DateTime _timestamp;

        public SafeModeWindow(string reason, Exception? exception = null)
        {
            InitializeComponent();
            
            _reason = reason;
            _exception = exception;
            _timestamp = DateTime.Now;
            
            InitializeDiagnostics();
        }

        private void InitializeDiagnostics()
        {
            // Summary
            SummaryText.Text = _reason;
            
            // Technical details
            if (_exception != null)
            {
                var details = new StringBuilder();
                details.AppendLine($"Exception Type: {_exception.GetType().FullName}");
                details.AppendLine($"Message: {_exception.Message}");
                details.AppendLine();
                details.AppendLine("Stack Trace:");
                details.AppendLine(_exception.StackTrace);
                
                if (_exception.InnerException != null)
                {
                    details.AppendLine();
                    details.AppendLine("Inner Exception:");
                    details.AppendLine($"Type: {_exception.InnerException.GetType().FullName}");
                    details.AppendLine($"Message: {_exception.InnerException.Message}");
                    details.AppendLine(_exception.InnerException.StackTrace);
                }
                
                DetailsText.Text = details.ToString();
            }
            
            // Diagnostic info
            StartupTimeText.Text = _timestamp.ToString("yyyy-MM-dd HH:mm:ss");
            LogLocationText.Text = GetLogPath();
            VersionText.Text = GetType().Assembly.GetName().Version?.ToString() ?? "Unknown";
            EnvironmentText.Text = $"{Environment.OSVersion} | .NET {Environment.Version}";
        }

        private void OpenLogsButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = GetLogPath(),
                    UseShellExecute = true
                });
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to open logs folder: {ex.Message}", "Error", 
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void CopyDiagnosticsButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var diagnostics = new StringBuilder();
                diagnostics.AppendLine("ProxyAssessmentTool - Safe Mode Diagnostics");
                diagnostics.AppendLine("==========================================");
                diagnostics.AppendLine();
                diagnostics.AppendLine($"Timestamp: {_timestamp:yyyy-MM-dd HH:mm:ss}");
                diagnostics.AppendLine($"Reason: {_reason}");
                diagnostics.AppendLine($"Version: {VersionText.Text}");
                diagnostics.AppendLine($"Environment: {EnvironmentText.Text}");
                diagnostics.AppendLine($"Log Path: {LogLocationText.Text}");
                diagnostics.AppendLine();
                
                if (!string.IsNullOrEmpty(DetailsText.Text))
                {
                    diagnostics.AppendLine("Technical Details:");
                    diagnostics.AppendLine(DetailsText.Text);
                }
                
                Clipboard.SetText(diagnostics.ToString());
                MessageBox.Show("Diagnostics copied to clipboard!", "Success", 
                    MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to copy diagnostics: {ex.Message}", "Error", 
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void RestartButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = Process.GetCurrentProcess().MainModule!.FileName,
                    UseShellExecute = true
                });
                Application.Current.Shutdown(0);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to restart application: {ex.Message}", "Error", 
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void ExitButton_Click(object sender, RoutedEventArgs e)
        {
            Application.Current.Shutdown(1);
        }

        private static string GetLogPath()
        {
            return Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "ProxyAssessmentTool",
                "logs");
        }
    }
}