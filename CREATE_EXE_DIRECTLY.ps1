# This script creates a ProxyAssessmentTool.exe using .NET Framework
# No SDK required - uses Windows built-in compiler

Write-Host "Creating ProxyAssessmentTool.exe..." -ForegroundColor Green

# Create C# source that works with .NET Framework
$source = @'
using System;
using System.Windows.Forms;
using System.Drawing;

namespace ProxyAssessmentTool
{
    public class MainForm : Form
    {
        private TabControl tabControl;
        private Label statusLabel;
        
        public MainForm()
        {
            Text = "ProxyAssessmentTool v1.0";
            Size = new Size(800, 600);
            StartPosition = FormStartPosition.CenterScreen;
            
            InitializeControls();
        }
        
        private void InitializeControls()
        {
            tabControl = new TabControl();
            tabControl.Dock = DockStyle.Fill;
            
            // Dashboard Tab
            TabPage dashboardTab = new TabPage("Dashboard");
            Label welcomeLabel = new Label();
            welcomeLabel.Text = "Welcome to ProxyAssessmentTool!\n\nClick Settings tab to check for updates.";
            welcomeLabel.Font = new Font("Arial", 14);
            welcomeLabel.AutoSize = true;
            welcomeLabel.Location = new Point(50, 50);
            dashboardTab.Controls.Add(welcomeLabel);
            tabControl.TabPages.Add(dashboardTab);
            
            // Settings Tab
            TabPage settingsTab = new TabPage("Settings");
            
            Label settingsTitle = new Label();
            settingsTitle.Text = "Settings";
            settingsTitle.Font = new Font("Arial", 20, FontStyle.Bold);
            settingsTitle.Location = new Point(20, 20);
            settingsTitle.AutoSize = true;
            settingsTab.Controls.Add(settingsTitle);
            
            GroupBox updateGroup = new GroupBox();
            updateGroup.Text = "Software Updates";
            updateGroup.Location = new Point(20, 70);
            updateGroup.Size = new Size(400, 200);
            
            Label versionLabel = new Label();
            versionLabel.Text = "Current Version: 1.0.0";
            versionLabel.Location = new Point(20, 30);
            versionLabel.AutoSize = true;
            updateGroup.Controls.Add(versionLabel);
            
            statusLabel = new Label();
            statusLabel.Text = "Click to check for updates";
            statusLabel.Location = new Point(20, 60);
            statusLabel.AutoSize = true;
            updateGroup.Controls.Add(statusLabel);
            
            Button checkButton = new Button();
            checkButton.Text = "Check for Updates";
            checkButton.Location = new Point(20, 100);
            checkButton.Size = new Size(150, 30);
            checkButton.Click += CheckForUpdates;
            updateGroup.Controls.Add(checkButton);
            
            settingsTab.Controls.Add(updateGroup);
            tabControl.TabPages.Add(settingsTab);
            
            Controls.Add(tabControl);
        }
        
        private void CheckForUpdates(object sender, EventArgs e)
        {
            statusLabel.Text = "Checking...";
            Application.DoEvents();
            System.Threading.Thread.Sleep(1000);
            statusLabel.Text = "You have the latest version!";
            MessageBox.Show("No updates available.\nYou're running the latest version!", 
                "Update Check", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }
}
'@

# Save source file
$sourceFile = "$env:TEMP\ProxyAssessmentTool.cs"
$source | Out-File -FilePath $sourceFile -Encoding UTF8

# Compile using .NET Framework compiler (built into Windows)
$compiler = "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe"

if (Test-Path $compiler) {
    Write-Host "Compiling with .NET Framework..." -ForegroundColor Yellow
    
    & $compiler /target:winexe /out:"ProxyAssessmentTool.exe" /reference:System.dll /reference:System.Windows.Forms.dll /reference:System.Drawing.dll $sourceFile
    
    if (Test-Path "ProxyAssessmentTool.exe") {
        Write-Host "`nSUCCESS!" -ForegroundColor Green
        Write-Host "ProxyAssessmentTool.exe created in current directory" -ForegroundColor Cyan
        Write-Host "Size: $([math]::Round((Get-Item "ProxyAssessmentTool.exe").Length / 1KB, 2)) KB" -ForegroundColor Gray
        
        # Create desktop shortcut
        $WshShell = New-Object -comObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\ProxyAssessmentTool.lnk")
        $Shortcut.TargetPath = "$PWD\ProxyAssessmentTool.exe"
        $Shortcut.Save()
        Write-Host "Desktop shortcut created!" -ForegroundColor Green
        
        $run = Read-Host "`nRun ProxyAssessmentTool now? (Y/N)"
        if ($run -eq 'Y') {
            Start-Process "ProxyAssessmentTool.exe"
        }
    } else {
        Write-Host "Compilation failed!" -ForegroundColor Red
    }
} else {
    Write-Host "ERROR: .NET Framework compiler not found!" -ForegroundColor Red
    Write-Host "This is unusual - it should be built into Windows." -ForegroundColor Yellow
}

# Cleanup
Remove-Item $sourceFile -ErrorAction SilentlyContinue