using System;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Threading;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using ProxyAssessmentTool.Core;
using ProxyAssessmentTool.Core.Interfaces;
using ProxyAssessmentTool.Core.Services;
using ProxyAssessmentTool.Views;
using Serilog;
using Serilog.Events;

namespace ProxyAssessmentTool
{
    public partial class App : Application
    {
        private IHost? _host;
        private SplashWindow? _splash;
        private readonly Stopwatch _startupTimer = Stopwatch.StartNew();
        private readonly StartupHealthTracker _healthTracker = new();
        private CancellationTokenSource? _startupCts;
        
        [STAThread]
        public static void Main()
        {
            // Set DPI awareness before any UI creation
            SetProcessDpiAwareness();
            
            // Configure global exception handlers first
            AppDomain.CurrentDomain.UnhandledException += OnUnhandledException;
            TaskScheduler.UnobservedTaskException += OnUnobservedTaskException;
            
            var app = new App();
            app.InitializeComponent();
            app.Run();
        }

        protected override async void OnStartup(StartupEventArgs e)
        {
            // Critical: Keep OnStartup minimal and use async properly
            base.OnStartup(e);
            
            try
            {
                _healthTracker.RecordStartupBegin();
                
                // Show splash immediately
                _splash = new SplashWindow();
                _splash.Show();
                _splash.UpdateProgress("Initializing...", 0);
                
                // Start async initialization with timeout
                _startupCts = new CancellationTokenSource(TimeSpan.FromSeconds(30));
                var initSuccess = await InitializeApplicationAsync(_startupCts.Token);
                
                if (!initSuccess)
                {
                    ShowSafeMode("Startup timeout - entering Safe Mode");
                    return;
                }
                
                // Show main window
                await Dispatcher.InvokeAsync(() =>
                {
                    var mainWindow = _host!.Services.GetRequiredService<MainWindow>();
                    mainWindow.Show();
                    
                    // Only now switch shutdown mode
                    ShutdownMode = ShutdownMode.OnMainWindowClose;
                    
                    _splash?.Close();
                    _splash = null;
                });
                
                _healthTracker.RecordStartupSuccess(_startupTimer.Elapsed);
            }
            catch (Exception ex)
            {
                _healthTracker.RecordStartupFailure(ex, _startupTimer.Elapsed);
                ShowSafeMode($"Startup failed: {ex.Message}", ex);
            }
        }

        private async Task<bool> InitializeApplicationAsync(CancellationToken ct)
        {
            try
            {
                // Step 1: Initialize logging
                _splash?.UpdateProgress("Setting up logging...", 10);
                ConfigureLogging();
                Log.Information("Application starting - Version {Version}", GetType().Assembly.GetName().Version);
                
                // Step 2: Verify environment
                _splash?.UpdateProgress("Checking environment...", 20);
                if (!await VerifyEnvironmentAsync(ct))
                    return false;
                
                // Step 3: Build DI container
                _splash?.UpdateProgress("Loading services...", 40);
                _host = CreateHostBuilder().Build();
                
                // Step 4: Initialize database
                _splash?.UpdateProgress("Initializing database...", 60);
                using var scope = _host.Services.CreateScope();
                var dbService = scope.ServiceProvider.GetRequiredService<IDatabaseService>();
                await dbService.InitializeAsync(ct);
                
                // Step 5: Warm up critical services
                _splash?.UpdateProgress("Starting services...", 80);
                await _host.StartAsync(ct);
                
                // Step 6: Verify file associations
                _splash?.UpdateProgress("Configuring file associations...", 90);
                VerifyFileAssociations();
                
                _splash?.UpdateProgress("Ready!", 100);
                await Task.Delay(500, ct); // Brief pause to show completion
                
                return true;
            }
            catch (OperationCanceledException)
            {
                Log.Warning("Startup initialization cancelled (timeout)");
                return false;
            }
            catch (Exception ex)
            {
                Log.Fatal(ex, "Failed to initialize application");
                throw;
            }
        }

        private void ConfigureLogging()
        {
            var logPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "ProxyAssessmentTool",
                "logs",
                $"{DateTime.Now:yyyy-MM-dd}.ndjson");
            
            Directory.CreateDirectory(Path.GetDirectoryName(logPath)!);
            
            Log.Logger = new LoggerConfiguration()
                .MinimumLevel.Debug()
                .MinimumLevel.Override("Microsoft", LogEventLevel.Information)
                .Enrich.FromLogContext()
                .Enrich.WithThreadId()
                .Enrich.WithProcessId()
                .WriteTo.File(
                    logPath,
                    formatter: new Serilog.Formatting.Compact.CompactJsonFormatter(),
                    rollingInterval: RollingInterval.Day,
                    retainedFileCountLimit: 7,
                    fileSizeLimitBytes: 50_000_000)
                .WriteTo.Debug()
                .CreateLogger();
        }

        private async Task<bool> VerifyEnvironmentAsync(CancellationToken ct)
        {
            try
            {
                // Check app data directory
                var appData = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "ProxyAssessmentTool");
                
                Directory.CreateDirectory(appData);
                Directory.CreateDirectory(Path.Combine(appData, "data"));
                Directory.CreateDirectory(Path.Combine(appData, "config"));
                Directory.CreateDirectory(Path.Combine(appData, "reports"));
                
                // Test write permissions
                var testFile = Path.Combine(appData, $"test_{Guid.NewGuid()}.tmp");
                await File.WriteAllTextAsync(testFile, "test", ct);
                File.Delete(testFile);
                
                return true;
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Environment verification failed");
                return false;
            }
        }

        private void VerifyFileAssociations()
        {
            try
            {
                // Check if running from file association
                var args = Environment.GetCommandLineArgs();
                if (args.Length > 1 && File.Exists(args[1]))
                {
                    var file = args[1];
                    var ext = Path.GetExtension(file)?.ToLowerInvariant();
                    
                    if (ext == ".paup")
                    {
                        // Launch updater instead
                        LaunchUpdater(file);
                        Shutdown(0);
                    }
                }
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "File association check failed");
            }
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
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to launch updater");
            }
        }

        private IHostBuilder CreateHostBuilder()
        {
            return Host.CreateDefaultBuilder()
                .UseSerilog()
                .ConfigureServices((context, services) =>
                {
                    // Core services
                    services.AddSingleton<IConfigurationManager, ConfigurationManager>();
                    services.AddSingleton<IDatabaseService, DatabaseService>();
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
                    
                    // Windows
                    services.AddTransient<MainWindow>();
                    services.AddTransient<SafeModeWindow>();
                });
        }

        private void ShowSafeMode(string reason, Exception? exception = null)
        {
            try
            {
                Log.Warning("Entering Safe Mode: {Reason}", reason);
                
                // Ensure we're on UI thread
                if (!Dispatcher.CheckAccess())
                {
                    Dispatcher.Invoke(() => ShowSafeMode(reason, exception));
                    return;
                }
                
                _splash?.Close();
                
                var safeModeWindow = new SafeModeWindow(reason, exception);
                safeModeWindow.Show();
                
                // Keep app alive in safe mode
                ShutdownMode = ShutdownMode.OnLastWindowClose;
            }
            catch (Exception ex)
            {
                // Last resort - show message box
                MessageBox.Show(
                    $"Critical startup failure:\n\n{reason}\n\nPlease check logs at:\n{GetLogPath()}",
                    "ProxyAssessmentTool - Safe Mode",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
                
                Log.Fatal(ex, "Failed to show Safe Mode window");
                Shutdown(1);
            }
        }

        private void OnDispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
        {
            Log.Error(e.Exception, "Unhandled dispatcher exception");
            
            if (!_host?.Services.GetService<MainWindow>()?.IsLoaded ?? true)
            {
                // Still in startup - show safe mode
                ShowSafeMode("Unhandled exception during startup", e.Exception);
                e.Handled = true;
            }
            else
            {
                // Runtime error - show error dialog
                MessageBox.Show(
                    $"An unexpected error occurred:\n\n{e.Exception.Message}\n\nThe application will continue running.",
                    "Error",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
                e.Handled = true;
            }
        }

        private static void OnUnhandledException(object sender, UnhandledExceptionEventArgs e)
        {
            var exception = e.ExceptionObject as Exception;
            Log.Fatal(exception, "Unhandled exception - IsTerminating: {IsTerminating}", e.IsTerminating);
            
            if (e.IsTerminating)
            {
                MessageBox.Show(
                    $"Fatal error:\n\n{exception?.Message ?? "Unknown error"}\n\nThe application must close.",
                    "ProxyAssessmentTool - Fatal Error",
                    MessageBoxButton.OK,
                    MessageBoxImage.Stop);
            }
        }

        private static void OnUnobservedTaskException(object? sender, UnobservedTaskExceptionEventArgs e)
        {
            Log.Error(e.Exception, "Unobserved task exception");
            e.SetObserved(); // Prevent process termination
        }

        protected override void OnExit(ExitEventArgs e)
        {
            _startupCts?.Cancel();
            _host?.Dispose();
            Log.CloseAndFlush();
            base.OnExit(e);
        }

        private static string GetLogPath()
        {
            return Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "ProxyAssessmentTool",
                "logs");
        }

        [System.Runtime.InteropServices.DllImport("user32.dll")]
        private static extern bool SetProcessDPIAware();
        
        private static void SetProcessDpiAwareness()
        {
            try
            {
                SetProcessDPIAware();
            }
            catch
            {
                // Ignore - not critical
            }
        }
    }
}