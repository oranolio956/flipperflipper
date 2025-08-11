using System;
using System.Windows;
using System.Windows.Threading;

namespace ProxyAssessmentTool.Views
{
    public partial class SplashWindow : Window
    {
        public SplashWindow()
        {
            InitializeComponent();
            
            var version = GetType().Assembly.GetName().Version;
            VersionText.Text = $"Version {version?.ToString(3) ?? "1.0.0"}";
        }

        public void UpdateProgress(string status, double percentage)
        {
            Dispatcher.BeginInvoke(() =>
            {
                StatusText.Text = status;
                ProgressBar.Value = Math.Max(0, Math.Min(100, percentage));
            });
        }
    }
}