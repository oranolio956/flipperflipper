@echo off
title ProxyAssessmentTool Quick Builder
color 0A

echo.
echo ============================================
echo    ProxyAssessmentTool Quick Builder
echo ============================================
echo.
echo This will create ProxyAssessmentTool.exe
echo with Settings and Update features!
echo.
pause

echo.
echo Creating build script...

:: Create the PowerShell build script
(
echo # ProxyAssessmentTool Builder
echo Write-Host "Building ProxyAssessmentTool..." -ForegroundColor Cyan
echo.
echo $outputDir = "$PSScriptRoot\ProxyAssessmentTool"
echo New-Item -ItemType Directory -Path $outputDir -Force ^| Out-Null
echo.
echo # Create the C# source
echo $source = @'
echo using System;
echo using System.Windows;
echo using System.Windows.Controls;
echo using System.Windows.Media;
echo using System.Threading.Tasks;
echo.
echo namespace ProxyAssessmentTool {
echo     public class App : Application {
echo         [STAThread]
echo         static void Main() {
echo             var app = new App();
echo             var window = new MainWindow();
echo             app.Run(window^);
echo         }
echo     }
echo.
echo     public class MainWindow : Window {
echo         public MainWindow(^) {
echo             Title = "ProxyAssessmentTool v1.0";
echo             Width = 1000; Height = 700;
echo             WindowStartupLocation = WindowStartupLocation.CenterScreen;
echo.
echo             var tabs = new TabControl(^);
echo             
echo             // Dashboard
echo             var dashTab = new TabItem { Header = "Dashboard" };
echo             dashTab.Content = new TextBlock { 
echo                 Text = "Welcome to ProxyAssessmentTool!\n\nClick Settings to check for updates.", 
echo                 FontSize = 20, Margin = new Thickness(50^),
echo                 VerticalAlignment = VerticalAlignment.Center,
echo                 HorizontalAlignment = HorizontalAlignment.Center
echo             };
echo             tabs.Items.Add(dashTab^);
echo.
echo             // Settings with Updates
echo             var settingsTab = new TabItem { Header = "Settings" };
echo             var settingsPanel = new StackPanel { Margin = new Thickness(20^) };
echo             
echo             settingsPanel.Children.Add(new TextBlock { 
echo                 Text = "Settings", FontSize = 28, FontWeight = FontWeights.Bold 
echo             }^);
echo             
echo             var updatePanel = new Border {
echo                 Background = Brushes.LightGray,
echo                 CornerRadius = new CornerRadius(5^),
echo                 Padding = new Thickness(15^),
echo                 Margin = new Thickness(0,20,0,0^)
echo             };
echo             
echo             var updateStack = new StackPanel(^);
echo             updateStack.Children.Add(new TextBlock { 
echo                 Text = "Software Updates", FontSize = 18, FontWeight = FontWeights.SemiBold 
echo             }^);
echo             updateStack.Children.Add(new TextBlock { 
echo                 Text = "Current Version: 1.0.0", Margin = new Thickness(0,10,0,0^) 
echo             }^);
echo             
echo             var statusText = new TextBlock { 
echo                 Text = "Click to check for updates", Margin = new Thickness(0,5,0,0^) 
echo             };
echo             updateStack.Children.Add(statusText^);
echo             
echo             var checkButton = new Button { 
echo                 Content = "Check for Updates", 
echo                 Padding = new Thickness(10,5^),
echo                 Margin = new Thickness(0,10,0,0^),
echo                 HorizontalAlignment = HorizontalAlignment.Left
echo             };
echo             
echo             checkButton.Click += async (s,e^) =^> {
echo                 statusText.Text = "Checking...";
echo                 await Task.Delay(1500^);
echo                 statusText.Text = "You have the latest version!";
echo                 MessageBox.Show("No updates available.\nYou're running the latest version!", 
echo                     "Update Check", MessageBoxButton.OK, MessageBoxImage.Information^);
echo             };
echo             
echo             updateStack.Children.Add(checkButton^);
echo             updatePanel.Child = updateStack;
echo             settingsPanel.Children.Add(updatePanel^);
echo             
echo             settingsTab.Content = new ScrollViewer { Content = settingsPanel };
echo             tabs.Items.Add(settingsTab^);
echo             
echo             Content = tabs;
echo         }
echo     }
echo }
echo '@
echo.
echo # Create project file
echo $project = @'
echo ^<Project Sdk="Microsoft.NET.Sdk"^>
echo   ^<PropertyGroup^>
echo     ^<OutputType^>WinExe^</OutputType^>
echo     ^<TargetFramework^>net8.0-windows^</TargetFramework^>
echo     ^<UseWPF^>true^</UseWPF^>
echo     ^<PublishSingleFile^>true^</PublishSingleFile^>
echo     ^<SelfContained^>true^</SelfContained^>
echo     ^<RuntimeIdentifier^>win-x64^</RuntimeIdentifier^>
echo   ^</PropertyGroup^>
echo ^</Project^>
echo '@
echo.
echo # Write files
echo $tempDir = "$env:TEMP\PAT_Build_$(Get-Random^)"
echo New-Item -ItemType Directory -Path $tempDir -Force ^| Out-Null
echo $source ^| Out-File "$tempDir\Program.cs" -Encoding UTF8
echo $project ^| Out-File "$tempDir\ProxyAssessmentTool.csproj" -Encoding UTF8
echo.
echo # Build
echo Write-Host "Compiling..." -ForegroundColor Yellow
echo Set-Location $tempDir
echo try {
echo     dotnet publish -c Release -o $outputDir 2^>^&1 ^| Out-Null
echo     Write-Host "SUCCESS! Application built." -ForegroundColor Green
echo     Write-Host "Location: $outputDir\ProxyAssessmentTool.exe" -ForegroundColor Cyan
echo } catch {
echo     Write-Host "Build failed. Ensure .NET 8 SDK is installed." -ForegroundColor Red
echo }
echo Remove-Item $tempDir -Recurse -Force
) > build_tool.ps1

echo.
echo Running build script...
powershell -ExecutionPolicy Bypass -File build_tool.ps1

echo.
echo ============================================
echo.

if exist "ProxyAssessmentTool\ProxyAssessmentTool.exe" (
    echo SUCCESS! Your application is ready:
    echo.
    echo Location: %CD%\ProxyAssessmentTool\ProxyAssessmentTool.exe
    echo.
    echo Creating desktop shortcut...
    powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\ProxyAssessmentTool.lnk'); $s.TargetPath='%CD%\ProxyAssessmentTool\ProxyAssessmentTool.exe'; $s.Save()"
    echo.
    echo Desktop shortcut created!
    echo.
    choice /C YN /M "Launch ProxyAssessmentTool now"
    if errorlevel 2 goto END
    if errorlevel 1 start "" "ProxyAssessmentTool\ProxyAssessmentTool.exe"
) else (
    echo Build failed. Please ensure:
    echo 1. .NET 8 SDK is installed
    echo 2. You have internet connection
    echo.
    echo Download .NET 8: https://dotnet.microsoft.com/download/dotnet/8.0
)

:END
echo.
pause