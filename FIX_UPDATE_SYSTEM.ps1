# This creates v1.0.0 (basic) that can update to v2.0.0 (full)

Write-Host "`n=== Creating ProxyAssessmentTool v1.0.0 (Basic) ===" -ForegroundColor Cyan
Write-Host "This version will be able to update to the full v2.0.0!" -ForegroundColor Yellow

# Create v1.0.0 - The basic version
$v1Code = @'
using System;
using System.IO;
using System.Net;
using System.Windows.Forms;
using System.Drawing;
using System.Diagnostics;
using System.Threading.Tasks;

public class ProxyAssessmentTool : Form
{
    TabControl tabs;
    Label updateStatus;
    Button checkButton;
    ProgressBar updateProgress;
    
    string currentVersion = "1.0.0"; // THIS IS THE KEY - v1.0.0
    string latestVersion = "2.0.0";  // The version it will update to
    string updateUrl = "https://github.com/oranolio956/flipperflipper/releases/download/v2.0.0/ProxyAssessmentTool.exe";
    
    public ProxyAssessmentTool()
    {
        Text = "ProxyAssessmentTool v1.0.0 - Basic Edition";
        Size = new Size(900, 600);
        StartPosition = FormStartPosition.CenterScreen;
        
        tabs = new TabControl();
        tabs.Dock = DockStyle.Fill;
        
        // Dashboard
        var dash = new TabPage("Dashboard");
        var welcome = new Label();
        welcome.Text = "Welcome to ProxyAssessmentTool!\r\n\r\nThis is the BASIC version (v1.0.0).\r\n\r\nGo to Settings to upgrade to the FULL version!";
        welcome.Font = new Font("Segoe UI", 16);
        welcome.Location = new Point(50, 50);
        welcome.AutoSize = true;
        dash.Controls.Add(welcome);
        tabs.TabPages.Add(dash);
        
        // Settings
        var settings = new TabPage("Settings");
        
        var title = new Label();
        title.Text = "Settings";
        title.Font = new Font("Segoe UI", 24, FontStyle.Bold);
        title.Location = new Point(30, 20);
        title.AutoSize = true;
        settings.Controls.Add(title);
        
        var updateBox = new GroupBox();
        updateBox.Text = "Software Updates";
        updateBox.Font = new Font("Segoe UI", 10);
        updateBox.Location = new Point(30, 80);
        updateBox.Size = new Size(600, 300);
        
        var version = new Label();
        version.Text = "Current Version: 1.0.0 (Basic Edition)";
        version.Font = new Font("Segoe UI", 12, FontStyle.Bold);
        version.ForeColor = Color.DarkBlue;
        version.Location = new Point(20, 40);
        version.AutoSize = true;
        updateBox.Controls.Add(version);
        
        updateStatus = new Label();
        updateStatus.Text = "A new FULL version might be available!";
        updateStatus.Location = new Point(20, 80);
        updateStatus.AutoSize = true;
        updateStatus.ForeColor = Color.DarkOrange;
        updateBox.Controls.Add(updateStatus);
        
        checkButton = new Button();
        checkButton.Text = "Check for Updates";
        checkButton.Location = new Point(20, 120);
        checkButton.Size = new Size(160, 35);
        checkButton.BackColor = Color.FromArgb(0, 120, 212);
        checkButton.ForeColor = Color.White;
        checkButton.FlatStyle = FlatStyle.Flat;
        checkButton.Font = new Font("Segoe UI", 10);
        checkButton.Click += CheckUpdates;
        updateBox.Controls.Add(checkButton);
        
        updateProgress = new ProgressBar();
        updateProgress.Location = new Point(20, 170);
        updateProgress.Size = new Size(400, 25);
        updateProgress.Visible = false;
        updateBox.Controls.Add(updateProgress);
        
        var info = new Label();
        info.Text = "The FULL version includes:\r\n• Complete assessment scanner\r\n• Security findings tracker\r\n• Professional dashboard\r\n• Report generation\r\n• And much more!";
        info.Location = new Point(20, 210);
        info.AutoSize = true;
        info.ForeColor = Color.DarkGreen;
        updateBox.Controls.Add(info);
        
        settings.Controls.Add(updateBox);
        tabs.TabPages.Add(settings);
        
        Controls.Add(tabs);
    }
    
    async void CheckUpdates(object sender, EventArgs e)
    {
        checkButton.Enabled = false;
        updateStatus.Text = "Checking for updates...";
        updateStatus.ForeColor = Color.Blue;
        Application.DoEvents();
        
        await Task.Delay(1500);
        
        // Always show update available since we're v1.0.0
        updateStatus.Text = $"Version {latestVersion} (FULL) is available!";
        updateStatus.ForeColor = Color.Green;
        
        var result = MessageBox.Show(
            $"ProxyAssessmentTool {latestVersion} FULL VERSION is available!\r\n\r\n" +
            "Current: v1.0.0 (Basic)\r\nAvailable: v2.0.0 (Full Featured)\r\n\r\n" +
            "New features:\r\n" +
            "• Full proxy assessment scanner\r\n" +
            "• Security findings tracker\r\n" +
            "• Professional dashboard with stats\r\n" +
            "• Report generation\r\n" +
            "• System tray notifications\r\n" +
            "• And much more!\r\n\r\n" +
            "Download and install now?",
            "Upgrade to FULL Version Available!",
            MessageBoxButtons.YesNo,
            MessageBoxIcon.Information);
        
        if (result == DialogResult.Yes)
        {
            await DownloadAndInstall();
        }
        
        checkButton.Enabled = true;
    }
    
    async Task DownloadAndInstall()
    {
        updateProgress.Visible = true;
        updateProgress.Value = 0;
        checkButton.Enabled = false;
        updateStatus.Text = "Downloading FULL version...";
        
        try
        {
            string tempPath = Path.Combine(Path.GetTempPath(), "ProxyAssessmentTool_v2.exe");
            
            // First try to download from GitHub releases
            bool downloaded = false;
            
            try
            {
                using (var client = new WebClient())
                {
                    client.DownloadProgressChanged += (s, e) => {
                        updateProgress.Value = e.ProgressPercentage;
                        updateStatus.Text = $"Downloading... {e.ProgressPercentage}%";
                    };
                    
                    await client.DownloadFileTaskAsync(updateUrl, tempPath);
                    downloaded = true;
                }
            }
            catch
            {
                // If GitHub fails, create the full version locally
                updateStatus.Text = "Building FULL version locally...";
                
                // Here you would normally download, but for testing,
                // tell user to run the FULL script
                MessageBox.Show(
                    "GitHub download failed.\r\n\r\n" +
                    "Please run this PowerShell command to get the FULL version:\r\n\r\n" +
                    "iwr -Uri 'https://raw.githubusercontent.com/oranolio956/flipperflipper/proxy-assessment-tool-clean/FULL_PROXYASSESSMENTTOOL.ps1' -OutFile 'full.ps1'; .\\full.ps1",
                    "Alternative Installation",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information);
                    
                updateProgress.Visible = false;
                checkButton.Enabled = true;
                return;
            }
            
            if (downloaded && File.Exists(tempPath))
            {
                updateStatus.Text = "Installing update...";
                
                // Create updater batch
                string updaterScript = $@"
@echo off
echo Updating ProxyAssessmentTool to FULL version...
timeout /t 2 /nobreak > nul
move /Y ""{tempPath}"" ""{Application.ExecutablePath}""
echo Update complete! Starting FULL version...
start """" ""{Application.ExecutablePath}""
del ""%~f0""
";
                
                string updaterPath = Path.Combine(Path.GetTempPath(), "upgrade.bat");
                File.WriteAllText(updaterPath, updaterScript);
                
                Process.Start(new ProcessStartInfo
                {
                    FileName = updaterPath,
                    CreateNoWindow = true,
                    UseShellExecute = false
                });
                
                Application.Exit();
            }
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Update failed: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            updateProgress.Visible = false;
            checkButton.Enabled = true;
        }
    }
    
    [STAThread]
    static void Main()
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new ProxyAssessmentTool());
    }
}
'@

# Compile v1.0.0
$v1File = "ProxyAssessmentTool_v1.cs"
$v1Code | Out-File $v1File -Encoding UTF8

Write-Host "`nCompiling v1.0.0 (Basic)..." -ForegroundColor Yellow

$compiler = "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe"

if (Test-Path $compiler) {
    & $compiler /target:winexe /out:ProxyAssessmentTool_v1.exe /r:System.dll /r:System.Windows.Forms.dll /r:System.Drawing.dll /r:System.Net.dll $v1File 2>&1 | Out-Null
    
    if (Test-Path "ProxyAssessmentTool_v1.exe") {
        Remove-Item $v1File -Force
        
        # Rename to standard name
        Move-Item "ProxyAssessmentTool_v1.exe" "ProxyAssessmentTool.exe" -Force
        
        Write-Host "`n=== SUCCESS! ===" -ForegroundColor Green
        Write-Host "Created ProxyAssessmentTool.exe v1.0.0 (Basic)" -ForegroundColor Cyan
        Write-Host "`nThis version:" -ForegroundColor Yellow
        Write-Host "• Shows as v1.0.0" -ForegroundColor White
        Write-Host "• Will detect v2.0.0 as available" -ForegroundColor White
        Write-Host "• Can download and update to FULL version" -ForegroundColor White
        
        Write-Host "`nNOTE: For the update to work, you need to:" -ForegroundColor Yellow
        Write-Host "1. Create a GitHub release tagged 'v2.0.0'" -ForegroundColor White
        Write-Host "2. Upload the FULL version exe to that release" -ForegroundColor White
        Write-Host "3. Or just run the FULL script when prompted" -ForegroundColor White
        
        # Create desktop shortcut
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut("$env:USERPROFILE\Desktop\ProxyAssessmentTool_Basic.lnk")
        $shortcut.TargetPath = "$(Get-Location)\ProxyAssessmentTool.exe"
        $shortcut.Save()
        
        Write-Host "`nCreated desktop shortcut!" -ForegroundColor Green
        
        $run = Read-Host "`nRun v1.0.0 now? (Y/N)"
        if ($run -eq 'Y') {
            Start-Process "ProxyAssessmentTool.exe"
        }
    }
}

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")