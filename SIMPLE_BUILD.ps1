# Simple ProxyAssessmentTool Builder
# This creates a minimal working executable with Settings and Update features

Write-Host "`n=== Building ProxyAssessmentTool ===" -ForegroundColor Cyan

# Create a temporary build directory
$tempDir = "$env:TEMP\ProxyToolBuild_$(Get-Random)"
$outputDir = "$PSScriptRoot\ProxyAssessmentTool_Package"

New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

Write-Host "Creating source files..." -ForegroundColor Yellow

# Create the main C# source file with all features embedded
$mainSource = @'
using System;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Text.Json;
using System.Diagnostics;

namespace ProxyAssessmentTool
{
    public partial class App : Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);
            var mainWindow = new MainWindow();
            mainWindow.Show();
        }
    }

    public partial class MainWindow : Window
    {
        private TabControl tabControl;
        private TextBlock statusText;
        private SettingsView settingsView;

        public MainWindow()
        {
            Title = "ProxyAssessmentTool - Security Assessment Platform";
            Width = 1200;
            Height = 800;
            WindowStartupLocation = WindowStartupLocation.CenterScreen;

            InitializeUI();
        }

        private void InitializeUI()
        {
            var grid = new Grid();
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            // Menu
            var menu = new Menu();
            var fileMenu = new MenuItem { Header = "_File" };
            var exitItem = new MenuItem { Header = "E_xit" };
            exitItem.Click += (s, e) => Application.Current.Shutdown();
            fileMenu.Items.Add(exitItem);
            menu.Items.Add(fileMenu);
            Grid.SetRow(menu, 0);
            grid.Children.Add(menu);

            // Tab Control
            tabControl = new TabControl();
            
            // Dashboard Tab
            var dashboardTab = new TabItem { Header = "Dashboard" };
            var dashboardContent = new TextBlock 
            { 
                Text = "Welcome to ProxyAssessmentTool!\n\nGo to Settings to check for updates.",
                FontSize = 16,
                Margin = new Thickness(20),
                VerticalAlignment = VerticalAlignment.Center,
                HorizontalAlignment = HorizontalAlignment.Center
            };
            dashboardTab.Content = dashboardContent;
            tabControl.Items.Add(dashboardTab);

            // Settings Tab
            var settingsTab = new TabItem { Header = "Settings" };
            settingsView = new SettingsView();
            settingsTab.Content = settingsView;
            tabControl.Items.Add(settingsTab);

            Grid.SetRow(tabControl, 1);
            grid.Children.Add(tabControl);

            // Status Bar
            var statusBar = new StatusBar();
            statusText = new TextBlock { Text = "Ready" };
            statusBar.Items.Add(statusText);
            Grid.SetRow(statusBar, 2);
            grid.Children.Add(statusBar);

            Content = grid;
        }
    }

    public class SettingsView : UserControl
    {
        private TextBlock updateStatusText;
        private Button checkUpdateButton;
        private Button downloadUpdateButton;
        private ProgressBar downloadProgress;
        private TextBlock versionText;
        private UpdateInfo latestUpdate;

        public SettingsView()
        {
            InitializeUI();
            _ = CheckForUpdates();
        }

        private void InitializeUI()
        {
            var scrollViewer = new ScrollViewer();
            var stackPanel = new StackPanel { Margin = new Thickness(20) };

            // Title
            var title = new TextBlock 
            { 
                Text = "Settings", 
                FontSize = 32, 
                FontWeight = FontWeights.Bold,
                Margin = new Thickness(0, 0, 0, 20)
            };
            stackPanel.Children.Add(title);

            // Update Section
            var updateBorder = new Border
            {
                Background = new SolidColorBrush(Colors.LightGray),
                CornerRadius = new CornerRadius(8),
                Padding = new Thickness(20),
                Margin = new Thickness(0, 0, 0, 20)
            };

            var updateStack = new StackPanel();

            var updateTitle = new TextBlock 
            { 
                Text = "Software Updates", 
                FontSize = 20, 
                FontWeight = FontWeights.SemiBold,
                Margin = new Thickness(0, 0, 0, 10)
            };
            updateStack.Children.Add(updateTitle);

            versionText = new TextBlock 
            { 
                Text = "Current Version: 1.0.0",
                FontSize = 14,
                Margin = new Thickness(0, 0, 0, 10)
            };
            updateStack.Children.Add(versionText);

            updateStatusText = new TextBlock 
            { 
                Text = "Checking for updates...",
                FontSize = 14,
                Margin = new Thickness(0, 0, 0, 10)
            };
            updateStack.Children.Add(updateStatusText);

            var buttonPanel = new StackPanel 
            { 
                Orientation = Orientation.Horizontal,
                Margin = new Thickness(0, 10, 0, 0)
            };

            checkUpdateButton = new Button 
            { 
                Content = "Check for Updates",
                Padding = new Thickness(10, 5),
                Margin = new Thickness(0, 0, 10, 0)
            };
            checkUpdateButton.Click += async (s, e) => await CheckForUpdates();
            buttonPanel.Children.Add(checkUpdateButton);

            downloadUpdateButton = new Button 
            { 
                Content = "Download Update",
                Padding = new Thickness(10, 5),
                IsEnabled = false
            };
            downloadUpdateButton.Click += async (s, e) => await DownloadUpdate();
            buttonPanel.Children.Add(downloadUpdateButton);

            updateStack.Children.Add(buttonPanel);

            downloadProgress = new ProgressBar 
            { 
                Height = 20,
                Margin = new Thickness(0, 10, 0, 0),
                Visibility = Visibility.Collapsed
            };
            updateStack.Children.Add(downloadProgress);

            updateBorder.Child = updateStack;
            stackPanel.Children.Add(updateBorder);

            scrollViewer.Content = stackPanel;
            Content = scrollViewer;
        }

        private async Task CheckForUpdates()
        {
            updateStatusText.Text = "Checking for updates...";
            checkUpdateButton.IsEnabled = false;

            try
            {
                using var client = new HttpClient();
                client.DefaultRequestHeaders.Add("User-Agent", "ProxyAssessmentTool/1.0");
                
                // This would normally check your GitHub releases
                // For demo purposes, we'll simulate an update check
                await Task.Delay(1000);
                
                latestUpdate = new UpdateInfo 
                { 
                    Version = "1.1.0",
                    DownloadUrl = "https://github.com/yourusername/ProxyAssessmentTool/releases/download/v1.1.0/ProxyAssessmentTool.exe",
                    ReleaseNotes = "- Added new features\n- Fixed bugs\n- Improved performance"
                };

                updateStatusText.Text = $"Update available: Version {latestUpdate.Version}";
                downloadUpdateButton.IsEnabled = true;
            }
            catch (Exception ex)
            {
                updateStatusText.Text = $"Update check failed: {ex.Message}";
            }
            finally
            {
                checkUpdateButton.IsEnabled = true;
            }
        }

        private async Task DownloadUpdate()
        {
            if (latestUpdate == null) return;

            downloadUpdateButton.IsEnabled = false;
            downloadProgress.Visibility = Visibility.Visible;
            downloadProgress.Value = 0;

            try
            {
                updateStatusText.Text = "Downloading update...";
                
                // Simulate download
                for (int i = 0; i <= 100; i += 10)
                {
                    downloadProgress.Value = i;
                    await Task.Delay(200);
                }

                updateStatusText.Text = "Update downloaded! Restart the application to install.";
                
                var result = MessageBox.Show(
                    "Update downloaded successfully!\n\nWould you like to restart and install the update now?",
                    "Update Ready",
                    MessageBoxButton.YesNo,
                    MessageBoxImage.Information);

                if (result == MessageBoxResult.Yes)
                {
                    // In a real app, this would launch the updater
                    MessageBox.Show("Please restart the application manually to complete the update.", "Restart Required", MessageBoxButton.OK, MessageBoxImage.Information);
                }
            }
            catch (Exception ex)
            {
                updateStatusText.Text = $"Download failed: {ex.Message}";
            }
            finally
            {
                downloadUpdateButton.IsEnabled = true;
                downloadProgress.Visibility = Visibility.Collapsed;
            }
        }
    }

    public class UpdateInfo
    {
        public string Version { get; set; }
        public string DownloadUrl { get; set; }
        public string ReleaseNotes { get; set; }
    }

    public class Program
    {
        [STAThread]
        public static void Main()
        {
            var app = new App();
            app.Run();
        }
    }
}
'@

# Save the source file
$sourceFile = "$tempDir\ProxyAssessmentTool.cs"
$mainSource | Out-File -FilePath $sourceFile -Encoding UTF8

Write-Host "Compiling application..." -ForegroundColor Yellow

# Create a simple project file
$projectContent = @'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0-windows</TargetFramework>
    <UseWPF>true</UseWPF>
    <PublishSingleFile>true</PublishSingleFile>
    <SelfContained>true</SelfContained>
    <RuntimeIdentifier>win-x64</RuntimeIdentifier>
    <EnableCompressionInSingleFile>true</EnableCompressionInSingleFile>
    <IncludeNativeLibrariesForSelfExtract>true</IncludeNativeLibrariesForSelfExtract>
  </PropertyGroup>
</Project>
'@

$projectFile = "$tempDir\ProxyAssessmentTool.csproj"
$projectContent | Out-File -FilePath $projectFile -Encoding UTF8

# Create appsettings.json
$appSettings = @{
    GitHub = @{
        Owner = "yourusername"
        Repository = "ProxyAssessmentTool"
    }
    Updates = @{
        AutoCheckEnabled = $true
        CheckIntervalHours = 24
    }
} | ConvertTo-Json -Depth 3

$appSettings | Out-File -FilePath "$tempDir\appsettings.json" -Encoding UTF8

# Try to compile using dotnet CLI
try {
    Write-Host "Attempting to build with dotnet CLI..." -ForegroundColor Gray
    
    Set-Location $tempDir
    $output = dotnet publish -c Release -r win-x64 --self-contained -p:PublishSingleFile=true -p:EnableWindowsTargeting=true -o $outputDir 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Build successful!" -ForegroundColor Green
    } else {
        throw "Build failed: $output"
    }
}
catch {
    Write-Host "[ERROR] dotnet CLI build failed" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    
    # Alternative: Try using csc directly if available
    Write-Host "`nTrying alternative build method..." -ForegroundColor Yellow
    
    $cscPath = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
    if (Test-Path $cscPath) {
        & $cscPath /target:winexe /out:"$outputDir\ProxyAssessmentTool.exe" /reference:System.dll /reference:System.Windows.Forms.dll $sourceFile
    }
}

# Create the installer
Write-Host "`nCreating installer..." -ForegroundColor Yellow

$installerBat = @'
@echo off
title ProxyAssessmentTool Installer
color 0A

echo.
echo ========================================
echo    ProxyAssessmentTool Installer
echo ========================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\ProxyAssessmentTool"

echo Creating installation directory...
mkdir "%INSTALL_DIR%" 2>nul

echo Installing application...
copy /Y "ProxyAssessmentTool.exe" "%INSTALL_DIR%\" >nul
copy /Y "appsettings.json" "%INSTALL_DIR%\" >nul 2>nul

echo Creating desktop shortcut...
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\ProxyAssessmentTool.lnk'); $s.TargetPath='%INSTALL_DIR%\ProxyAssessmentTool.exe'; $s.Save()"

echo.
echo Installation Complete!
echo.
echo ProxyAssessmentTool has been installed to:
echo %INSTALL_DIR%
echo.

pause
'@

$installerBat | Out-File -FilePath "$outputDir\INSTALL.bat" -Encoding ASCII

# Check if build was successful
if (Test-Path "$outputDir\ProxyAssessmentTool.exe") {
    $exeInfo = Get-Item "$outputDir\ProxyAssessmentTool.exe"
    
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "    BUILD SUCCESSFUL!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "`nOutput location: $outputDir" -ForegroundColor Cyan
    Write-Host "`nFile created:" -ForegroundColor Yellow
    Write-Host "  - ProxyAssessmentTool.exe ($([math]::Round($exeInfo.Length / 1MB, 2)) MB)" -ForegroundColor Gray
    Write-Host "  - INSTALL.bat" -ForegroundColor Gray
    Write-Host "  - appsettings.json" -ForegroundColor Gray
    
    Write-Host "`nTo install:" -ForegroundColor Yellow
    Write-Host "  1. Navigate to: $outputDir" -ForegroundColor Gray
    Write-Host "  2. Run INSTALL.bat" -ForegroundColor Gray
    Write-Host "`nThe application includes:" -ForegroundColor Yellow
    Write-Host "  - Main window with tabs" -ForegroundColor Gray
    Write-Host "  - Settings page with update checker" -ForegroundColor Gray
    Write-Host "  - Simulated update functionality" -ForegroundColor Gray
} else {
    Write-Host "`n[ERROR] Build failed - no executable created" -ForegroundColor Red
    Write-Host "Please ensure you have .NET SDK 8.0 installed" -ForegroundColor Yellow
    Write-Host "Download from: https://dotnet.microsoft.com/download/dotnet/8.0" -ForegroundColor Cyan
}

# Cleanup
Set-Location $PSScriptRoot
Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")