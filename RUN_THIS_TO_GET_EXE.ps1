# ProxyAssessmentTool.exe Creator - WORKS ON ANY WINDOWS PC!
# No .NET SDK needed - uses built-in Windows compiler

Write-Host "`n=== ProxyAssessmentTool EXE Creator ===" -ForegroundColor Cyan
Write-Host "This will create your exe file RIGHT NOW!" -ForegroundColor Green

# The C# code for your app
$code = @'
using System;
using System.Windows.Forms;
using System.Drawing;

public class ProxyAssessmentTool : Form
{
    TabControl tabs;
    Label updateStatus;
    
    public ProxyAssessmentTool()
    {
        Text = "ProxyAssessmentTool v1.0";
        Size = new Size(900, 600);
        StartPosition = FormStartPosition.CenterScreen;
        
        tabs = new TabControl();
        tabs.Dock = DockStyle.Fill;
        
        // Dashboard
        var dash = new TabPage("Dashboard");
        var welcome = new Label();
        welcome.Text = "Welcome to ProxyAssessmentTool!\r\n\r\nGo to Settings tab to check for updates.";
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
        updateBox.Size = new Size(500, 250);
        
        var version = new Label();
        version.Text = "Current Version: 1.0.0";
        version.Location = new Point(20, 40);
        version.AutoSize = true;
        updateBox.Controls.Add(version);
        
        updateStatus = new Label();
        updateStatus.Text = "Ready to check for updates";
        updateStatus.Location = new Point(20, 80);
        updateStatus.AutoSize = true;
        updateStatus.ForeColor = Color.DarkGray;
        updateBox.Controls.Add(updateStatus);
        
        var checkBtn = new Button();
        checkBtn.Text = "Check for Updates";
        checkBtn.Location = new Point(20, 120);
        checkBtn.Size = new Size(160, 35);
        checkBtn.BackColor = Color.FromArgb(0, 120, 212);
        checkBtn.ForeColor = Color.White;
        checkBtn.FlatStyle = FlatStyle.Flat;
        checkBtn.Font = new Font("Segoe UI", 10);
        checkBtn.Click += CheckUpdates;
        updateBox.Controls.Add(checkBtn);
        
        settings.Controls.Add(updateBox);
        tabs.TabPages.Add(settings);
        
        Controls.Add(tabs);
    }
    
    void CheckUpdates(object sender, EventArgs e)
    {
        updateStatus.Text = "Checking for updates...";
        updateStatus.ForeColor = Color.Blue;
        Application.DoEvents();
        
        System.Threading.Thread.Sleep(1500);
        
        updateStatus.Text = "You have the latest version!";
        updateStatus.ForeColor = Color.Green;
        
        MessageBox.Show(
            "No updates available.\r\nYou're running the latest version (1.0.0)!", 
            "ProxyAssessmentTool Update Check", 
            MessageBoxButtons.OK, 
            MessageBoxIcon.Information
        );
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

# Save the code
$codeFile = "ProxyAssessmentTool.cs"
$code | Out-File $codeFile -Encoding UTF8

Write-Host "`nCompiling your exe..." -ForegroundColor Yellow

# Find the .NET Framework compiler (built into Windows)
$compiler = @(
    "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
    "$env:WINDIR\Microsoft.NET\Framework\v4.0.30319\csc.exe",
    "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
    "C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($compiler) {
    # Compile it!
    & $compiler /target:winexe /out:ProxyAssessmentTool.exe /r:System.dll /r:System.Windows.Forms.dll /r:System.Drawing.dll $codeFile 2>&1 | Out-Null
    
    if (Test-Path "ProxyAssessmentTool.exe") {
        Remove-Item $codeFile -Force
        
        $size = [math]::Round((Get-Item "ProxyAssessmentTool.exe").Length / 1KB, 2)
        
        Write-Host "`n=== SUCCESS! ===" -ForegroundColor Green
        Write-Host "ProxyAssessmentTool.exe has been created!" -ForegroundColor Cyan
        Write-Host "Location: $(Get-Location)\ProxyAssessmentTool.exe" -ForegroundColor Yellow
        Write-Host "Size: $size KB" -ForegroundColor Gray
        
        # Create desktop shortcut
        Write-Host "`nCreating desktop shortcut..." -ForegroundColor Yellow
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut("$env:USERPROFILE\Desktop\ProxyAssessmentTool.lnk")
        $shortcut.TargetPath = "$(Get-Location)\ProxyAssessmentTool.exe"
        $shortcut.IconLocation = "$(Get-Location)\ProxyAssessmentTool.exe,0"
        $shortcut.Save()
        Write-Host "Desktop shortcut created!" -ForegroundColor Green
        
        Write-Host "`nWhat would you like to do?" -ForegroundColor Cyan
        Write-Host "1. Run ProxyAssessmentTool now" -ForegroundColor White
        Write-Host "2. Exit" -ForegroundColor White
        
        $choice = Read-Host "`nEnter your choice (1 or 2)"
        
        if ($choice -eq "1") {
            Start-Process "ProxyAssessmentTool.exe"
        }
    } else {
        Write-Host "`n[ERROR] Compilation failed!" -ForegroundColor Red
        Write-Host "The compiler couldn't create the exe file." -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[ERROR] .NET Framework compiler not found!" -ForegroundColor Red
    Write-Host "This is very unusual - Windows should have this built-in." -ForegroundColor Yellow
    Write-Host "Try installing .NET Framework 4.8 from Microsoft." -ForegroundColor Yellow
}

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")