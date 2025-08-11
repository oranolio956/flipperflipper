using System;
using System.IO;
using System.Windows;
using ProxyAssessmentTool.Updater.Views;

namespace ProxyAssessmentTool.Updater
{
    public partial class App : Application
    {
        [STAThread]
        public static void Main(string[] args)
        {
            var app = new App();
            app.InitializeComponent();
            app.Run();
        }

        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);
            
            // Check command line arguments
            if (e.Args.Length == 0)
            {
                MessageBox.Show(
                    "No update package specified.\n\nUsage: ProxyAssessmentTool.Updater.exe <package.paup>",
                    "ProxyAssessmentTool Updater",
                    MessageBoxButton.OK,
                    MessageBoxImage.Information);
                Shutdown(1);
                return;
            }
            
            var packagePath = e.Args[0];
            
            // Verify file exists
            if (!File.Exists(packagePath))
            {
                MessageBox.Show(
                    $"Update package not found:\n{packagePath}",
                    "ProxyAssessmentTool Updater",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
                Shutdown(1);
                return;
            }
            
            // Show update window
            var mainWindow = new MainWindow(packagePath);
            mainWindow.Show();
        }
    }
}