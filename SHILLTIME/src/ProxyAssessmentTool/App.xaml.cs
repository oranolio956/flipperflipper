using System;
using System.IO;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Threading;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using ModernWpf;
using ProxyAssessmentTool.Core.Interfaces;
using ProxyAssessmentTool.Core.Services;
using ProxyAssessmentTool.Services;
using ProxyAssessmentTool.ViewModels;
using ProxyAssessmentTool.Views;
using Serilog;
using Serilog.Events;

namespace ProxyAssessmentTool
{
    /// <summary>
    /// Main application class with dependency injection setup
    /// </summary>
    public partial class App : Application
    {
        private IHost? _host;
        private ILogger<App>? _logger;

        protected override async void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            // Set up global exception handling
            AppDomain.CurrentDomain.UnhandledException += OnUnhandledException;
            DispatcherUnhandledException += OnDispatcherUnhandledException;
            TaskScheduler.UnobservedTaskException += OnUnobservedTaskException;

            try
            {
                // Build and start the host
                _host = CreateHostBuilder(e.Args).Build();
                await _host.StartAsync();

                _logger = _host.Services.GetRequiredService<ILogger<App>>();
                _logger.LogInformation("ProxyAssessmentTool starting up");

                // Check for required files and first-run setup
                await PerformStartupChecksAsync();

                // Apply theme based on Windows settings
                ThemeManager.Current.ApplicationTheme = ThemeManager.Current.ActualApplicationTheme;

                // Create and show the main window
                var mainWindow = _host.Services.GetRequiredService<MainWindow>();
                mainWindow.Show();
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Fatal error during startup: {ex.Message}",
                    "ProxyAssessmentTool",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error
                );
                Shutdown(1);
            }
        }

        protected override async void OnExit(ExitEventArgs e)
        {
            _logger?.LogInformation("ProxyAssessmentTool shutting down");

            if (_host != null)
            {
                await _host.StopAsync(TimeSpan.FromSeconds(5));
                _host.Dispose();
            }

            Log.CloseAndFlush();
            base.OnExit(e);
        }

        private static IHostBuilder CreateHostBuilder(string[] args) =>
            Host.CreateDefaultBuilder(args)
                .UseContentRoot(AppDomain.CurrentDomain.BaseDirectory)
                .ConfigureAppConfiguration((context, config) =>
                {
                    config.SetBasePath(AppDomain.CurrentDomain.BaseDirectory);
                    config.AddJsonFile("appsettings.json", optional: false, reloadOnChange: true);
                    config.AddJsonFile($"appsettings.{context.HostingEnvironment.EnvironmentName}.json", optional: true);
                    config.AddEnvironmentVariables("PAT_");
                    config.AddCommandLine(args);
                })
                .UseSerilog((context, services, configuration) =>
                {
                    configuration
                        .ReadFrom.Configuration(context.Configuration)
                        .MinimumLevel.Debug()
                        .MinimumLevel.Override("Microsoft", LogEventLevel.Information)
                        .Enrich.FromLogContext()
                        .WriteTo.File(
                            Path.Combine(GetLogDirectory(), "proxy-assessment-.log"),
                            rollingInterval: RollingInterval.Day,
                            retainedFileCountLimit: 30,
                            outputTemplate: "[{Timestamp:yyyy-MM-dd HH:mm:ss.fff zzz}] [{Level:u3}] [{SourceContext}] {Message:lj}{NewLine}{Exception}"
                        )
                        .WriteTo.EventLog(
                            "ProxyAssessmentTool",
                            manageEventSource: true,
                            restrictedToMinimumLevel: LogEventLevel.Warning
                        );
                })
                .ConfigureServices((context, services) =>
                {
                    // Configuration
                    services.AddSingleton<IConfiguration>(context.Configuration);
                    
                    // Core Services
                    services.AddSingleton<IConfigurationManager, ConfigurationManager>();
                    services.AddSingleton<IConsentLedger, ConsentLedger>();
                    services.AddSingleton<IAuditLogger, AuditLogger>();
                    services.AddSingleton<IEvidenceStore, EvidenceStore>();
                    services.AddSingleton<IOrchestrator, Orchestrator>();
                    
                    // Discovery & Validation
                    services.AddTransient<IDiscoveryEngine, DiscoveryEngine>();
                    services.AddTransient<IProtocolFingerprinter, ProtocolFingerprinter>();
                    services.AddTransient<ISafeValidator, SafeValidator>();
                    services.AddTransient<IUsageClassifier, UsageClassifier>();
                    
                    // Enrichment Services
                    services.AddTransient<IReputationAnalyzer, ReputationAnalyzer>();
                    services.AddTransient<IGeoAsnEnrichment, GeoAsnEnrichment>();
                    services.AddTransient<ISocialCompatibilityAnalyzer, SocialCompatibilityAnalyzer>();
                    services.AddTransient<ILeakageChecker, LeakageChecker>();
                    services.AddTransient<IUptimeMonitor, UptimeMonitor>();
                    
                    // Risk & Remediation
                    services.AddTransient<IRiskScorer, RiskScorer>();
                    services.AddTransient<IRemediationGenerator, RemediationGenerator>();
                    services.AddTransient<IReportGenerator, ReportGenerator>();
                    
                    // Data Access
                    services.AddSingleton<IDatabaseService, DatabaseService>();
                    services.AddSingleton<IFindingsRepository, FindingsRepository>();
                    
                    // UI Services
                    services.AddSingleton<INavigationService, NavigationService>();
                    services.AddSingleton<IDialogService, DialogService>();
                    services.AddSingleton<INotificationService, NotificationService>();
                    
                    // ViewModels
                    services.AddTransient<MainViewModel>();
                    services.AddTransient<DashboardViewModel>();
                    services.AddTransient<ScopeConsentViewModel>();
                    services.AddTransient<DiscoveryViewModel>();
                    services.AddTransient<ValidationViewModel>();
                    services.AddTransient<FindingsViewModel>();
                    services.AddTransient<ReportsViewModel>();
                    services.AddTransient<SettingsViewModel>();
                    
                    // Views
                    services.AddTransient<MainWindow>();
                    services.AddTransient<DashboardView>();
                    services.AddTransient<ScopeConsentView>();
                    services.AddTransient<DiscoveryView>();
                    services.AddTransient<ValidationView>();
                    services.AddTransient<FindingsView>();
                    services.AddTransient<ReportsView>();
                    services.AddTransient<SettingsView>();
                });

        private async Task PerformStartupChecksAsync()
        {
            var startupValidator = _host!.Services.GetRequiredService<IStartupValidator>();
            var result = await startupValidator.ValidateAsync();
            
            if (!result.IsValid)
            {
                _logger!.LogWarning("Startup validation failed: {Issues}", result.Issues);
                
                // Show first-run wizard if needed
                if (result.RequiresFirstRunSetup)
                {
                    var firstRunWindow = _host.Services.GetRequiredService<FirstRunWizard>();
                    var dialogResult = firstRunWindow.ShowDialog();
                    
                    if (dialogResult != true)
                    {
                        Shutdown(0);
                        return;
                    }
                }
            }
        }

        private static string GetLogDirectory()
        {
            var appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            var logDir = Path.Combine(appData, "ProxyAssessmentTool", "Logs");
            Directory.CreateDirectory(logDir);
            return logDir;
        }

        private void OnUnhandledException(object sender, UnhandledExceptionEventArgs e)
        {
            var exception = e.ExceptionObject as Exception;
            _logger?.LogCritical(exception, "Unhandled exception occurred");
            
            MessageBox.Show(
                $"A critical error occurred: {exception?.Message}\n\nThe application will now close.",
                "Critical Error",
                MessageBoxButton.OK,
                MessageBoxImage.Error
            );
        }

        private void OnDispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
        {
            _logger?.LogError(e.Exception, "Unhandled dispatcher exception");
            
            MessageBox.Show(
                $"An error occurred: {e.Exception.Message}\n\nThe operation has been cancelled.",
                "Error",
                MessageBoxButton.OK,
                MessageBoxImage.Error
            );
            
            e.Handled = true;
        }

        private void OnUnobservedTaskException(object? sender, UnobservedTaskExceptionEventArgs e)
        {
            _logger?.LogError(e.Exception, "Unobserved task exception");
            e.SetObserved();
        }
    }
}