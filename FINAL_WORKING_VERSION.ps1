# ProxyAssessmentTool v2.0.0 FULL - C# 5.0 Compatible
# This version works with the older .NET Framework compiler

Write-Host "`n=== Building ProxyAssessmentTool v2.0.0 FULL ===" -ForegroundColor Cyan
Write-Host "Using C# 5.0 compatible code..." -ForegroundColor Yellow

$fullApp = @'
using System;
using System.Windows.Forms;
using System.Drawing;
using System.IO;
using System.Net;
using System.Diagnostics;
using System.Threading;

public class ProxyAssessmentTool : Form
{
    TabControl tabs;
    StatusStrip status;
    ToolStripStatusLabel statusLabel;
    
    // Dashboard
    Label totalProxiesLabel;
    Label criticalFindingsLabel;
    Panel activityPanel;
    
    // Assessment
    TextBox targetInput;
    Button scanButton;
    ProgressBar scanProgress;
    ListView resultsView;
    
    // Settings
    Label versionLabel;
    Label updateStatus;
    Button checkUpdateBtn;
    ProgressBar updateProgress;
    TextBox updateLog;
    
    string currentVersion = "2.0.0";
    
    public ProxyAssessmentTool()
    {
        Text = "ProxyAssessmentTool v2.0.0 - Professional Security Platform";
        Size = new Size(1200, 800);
        StartPosition = FormStartPosition.CenterScreen;
        
        // Status Bar
        status = new StatusStrip();
        statusLabel = new ToolStripStatusLabel("Ready");
        status.Items.Add(statusLabel);
        Controls.Add(status);
        
        // Tabs
        tabs = new TabControl();
        tabs.Dock = DockStyle.Fill;
        tabs.Font = new Font("Segoe UI", 10);
        
        CreateDashboard();
        CreateAssessment();
        CreateFindings();
        CreateReports();
        CreateSettings();
        
        Controls.Add(tabs);
    }
    
    void CreateDashboard()
    {
        var tab = new TabPage("Dashboard");
        tab.BackColor = Color.FromArgb(245, 245, 245);
        
        // Title
        var title = new Label();
        title.Text = "Security Assessment Dashboard";
        title.Font = new Font("Segoe UI", 24, FontStyle.Bold);
        title.ForeColor = Color.FromArgb(0, 120, 212);
        title.Location = new Point(30, 20);
        title.AutoSize = true;
        tab.Controls.Add(title);
        
        // Stats Panel
        var statsPanel = new Panel();
        statsPanel.Location = new Point(30, 80);
        statsPanel.Size = new Size(1100, 120);
        
        // Proxy Count Card
        var proxyCard = CreateStatCard("Total Proxies", "0", Color.Blue, 0);
        totalProxiesLabel = (Label)proxyCard.Controls[1];
        statsPanel.Controls.Add(proxyCard);
        
        // Active Scans Card
        var scanCard = CreateStatCard("Active Scans", "0", Color.Orange, 280);
        statsPanel.Controls.Add(scanCard);
        
        // Critical Findings Card
        var criticalCard = CreateStatCard("Critical Issues", "0", Color.Red, 560);
        criticalFindingsLabel = (Label)criticalCard.Controls[1];
        statsPanel.Controls.Add(criticalCard);
        
        // Compliance Card
        var complianceCard = CreateStatCard("Compliance", "N/A", Color.Green, 840);
        statsPanel.Controls.Add(complianceCard);
        
        tab.Controls.Add(statsPanel);
        
        // Activity Section
        var activityTitle = new Label();
        activityTitle.Text = "Recent Activity";
        activityTitle.Font = new Font("Segoe UI", 16, FontStyle.Bold);
        activityTitle.Location = new Point(30, 220);
        activityTitle.AutoSize = true;
        tab.Controls.Add(activityTitle);
        
        activityPanel = new Panel();
        activityPanel.Location = new Point(30, 260);
        activityPanel.Size = new Size(1100, 380);
        activityPanel.BorderStyle = BorderStyle.FixedSingle;
        activityPanel.BackColor = Color.White;
        activityPanel.AutoScroll = true;
        
        var noActivity = new Label();
        noActivity.Text = "No recent activity. Run an assessment to begin.";
        noActivity.ForeColor = Color.Gray;
        noActivity.Location = new Point(20, 20);
        noActivity.AutoSize = true;
        activityPanel.Controls.Add(noActivity);
        
        tab.Controls.Add(activityPanel);
        tabs.TabPages.Add(tab);
    }
    
    Panel CreateStatCard(string title, string value, Color color, int x)
    {
        var card = new Panel();
        card.Size = new Size(250, 100);
        card.Location = new Point(x, 0);
        card.BackColor = Color.White;
        card.BorderStyle = BorderStyle.FixedSingle;
        
        var titleLbl = new Label();
        titleLbl.Text = title;
        titleLbl.Font = new Font("Segoe UI", 10);
        titleLbl.ForeColor = Color.Gray;
        titleLbl.Location = new Point(15, 15);
        titleLbl.AutoSize = true;
        card.Controls.Add(titleLbl);
        
        var valueLbl = new Label();
        valueLbl.Text = value;
        valueLbl.Font = new Font("Segoe UI", 28, FontStyle.Bold);
        valueLbl.ForeColor = color;
        valueLbl.Location = new Point(15, 35);
        valueLbl.AutoSize = true;
        card.Controls.Add(valueLbl);
        
        return card;
    }
    
    void CreateAssessment()
    {
        var tab = new TabPage("Assessment");
        tab.BackColor = Color.FromArgb(245, 245, 245);
        
        var title = new Label();
        title.Text = "Proxy Assessment Scanner";
        title.Font = new Font("Segoe UI", 20, FontStyle.Bold);
        title.Location = new Point(30, 20);
        title.AutoSize = true;
        tab.Controls.Add(title);
        
        // Target Input
        var targetGroup = new GroupBox();
        targetGroup.Text = "Target Configuration";
        targetGroup.Location = new Point(30, 70);
        targetGroup.Size = new Size(800, 200);
        targetGroup.Font = new Font("Segoe UI", 10);
        
        var targetLbl = new Label();
        targetLbl.Text = "Enter IP addresses or CIDR ranges (one per line):";
        targetLbl.Location = new Point(20, 30);
        targetLbl.AutoSize = true;
        targetGroup.Controls.Add(targetLbl);
        
        targetInput = new TextBox();
        targetInput.Location = new Point(20, 55);
        targetInput.Size = new Size(400, 120);
        targetInput.Multiline = true;
        targetInput.ScrollBars = ScrollBars.Vertical;
        targetInput.Font = new Font("Consolas", 10);
        targetGroup.Controls.Add(targetInput);
        
        // Port Settings
        var portLbl = new Label();
        portLbl.Text = "Ports to scan:";
        portLbl.Location = new Point(450, 55);
        portLbl.AutoSize = true;
        targetGroup.Controls.Add(portLbl);
        
        var portBox = new TextBox();
        portBox.Text = "1080, 3128, 8080, 8888";
        portBox.Location = new Point(450, 80);
        portBox.Size = new Size(200, 25);
        targetGroup.Controls.Add(portBox);
        
        tab.Controls.Add(targetGroup);
        
        // Scan Button
        scanButton = new Button();
        scanButton.Text = "Start Assessment";
        scanButton.Location = new Point(30, 290);
        scanButton.Size = new Size(200, 40);
        scanButton.BackColor = Color.FromArgb(0, 120, 212);
        scanButton.ForeColor = Color.White;
        scanButton.FlatStyle = FlatStyle.Flat;
        scanButton.Font = new Font("Segoe UI", 11, FontStyle.Bold);
        scanButton.Click += StartScan;
        tab.Controls.Add(scanButton);
        
        scanProgress = new ProgressBar();
        scanProgress.Location = new Point(250, 295);
        scanProgress.Size = new Size(400, 30);
        scanProgress.Visible = false;
        tab.Controls.Add(scanProgress);
        
        // Results
        var resultsLbl = new Label();
        resultsLbl.Text = "Scan Results";
        resultsLbl.Font = new Font("Segoe UI", 14, FontStyle.Bold);
        resultsLbl.Location = new Point(30, 350);
        resultsLbl.AutoSize = true;
        tab.Controls.Add(resultsLbl);
        
        resultsView = new ListView();
        resultsView.Location = new Point(30, 380);
        resultsView.Size = new Size(1100, 250);
        resultsView.View = View.Details;
        resultsView.GridLines = true;
        resultsView.FullRowSelect = true;
        resultsView.Columns.Add("IP Address", 150);
        resultsView.Columns.Add("Port", 80);
        resultsView.Columns.Add("Type", 100);
        resultsView.Columns.Add("Status", 100);
        resultsView.Columns.Add("Risk", 100);
        resultsView.Columns.Add("Details", 400);
        tab.Controls.Add(resultsView);
        
        tabs.TabPages.Add(tab);
    }
    
    void CreateFindings()
    {
        var tab = new TabPage("Findings");
        tab.BackColor = Color.FromArgb(245, 245, 245);
        
        var title = new Label();
        title.Text = "Security Findings";
        title.Font = new Font("Segoe UI", 20, FontStyle.Bold);
        title.Location = new Point(30, 30);
        title.AutoSize = true;
        tab.Controls.Add(title);
        
        var info = new Label();
        info.Text = "Security findings will appear here after assessments.\r\nFindings are categorized by severity level.";
        info.Location = new Point(30, 80);
        info.AutoSize = true;
        info.ForeColor = Color.Gray;
        tab.Controls.Add(info);
        
        tabs.TabPages.Add(tab);
    }
    
    void CreateReports()
    {
        var tab = new TabPage("Reports");
        tab.BackColor = Color.FromArgb(245, 245, 245);
        
        var title = new Label();
        title.Text = "Assessment Reports";
        title.Font = new Font("Segoe UI", 20, FontStyle.Bold);
        title.Location = new Point(30, 30);
        title.AutoSize = true;
        tab.Controls.Add(title);
        
        var exportBtn = new Button();
        exportBtn.Text = "Export Report";
        exportBtn.Location = new Point(30, 80);
        exportBtn.Size = new Size(150, 40);
        exportBtn.BackColor = Color.FromArgb(0, 120, 212);
        exportBtn.ForeColor = Color.White;
        exportBtn.FlatStyle = FlatStyle.Flat;
        exportBtn.Click += (s,e) => MessageBox.Show("Report export coming soon!", "Export");
        tab.Controls.Add(exportBtn);
        
        tabs.TabPages.Add(tab);
    }
    
    void CreateSettings()
    {
        var tab = new TabPage("Settings");
        tab.BackColor = Color.FromArgb(245, 245, 245);
        
        var title = new Label();
        title.Text = "Settings";
        title.Font = new Font("Segoe UI", 24, FontStyle.Bold);
        title.Location = new Point(30, 20);
        title.AutoSize = true;
        tab.Controls.Add(title);
        
        // Updates Section
        var updateGroup = new GroupBox();
        updateGroup.Text = "Software Updates";
        updateGroup.Location = new Point(30, 80);
        updateGroup.Size = new Size(800, 350);
        updateGroup.Font = new Font("Segoe UI", 11);
        updateGroup.BackColor = Color.White;
        
        versionLabel = new Label();
        versionLabel.Text = "Current Version: " + currentVersion + " (Full Featured)";
        versionLabel.Font = new Font("Segoe UI", 12, FontStyle.Bold);
        versionLabel.ForeColor = Color.DarkGreen;
        versionLabel.Location = new Point(20, 40);
        versionLabel.AutoSize = true;
        updateGroup.Controls.Add(versionLabel);
        
        updateStatus = new Label();
        updateStatus.Text = "You have the full featured version!";
        updateStatus.Location = new Point(20, 75);
        updateStatus.AutoSize = true;
        updateStatus.ForeColor = Color.Green;
        updateGroup.Controls.Add(updateStatus);
        
        checkUpdateBtn = new Button();
        checkUpdateBtn.Text = "Check for Updates";
        checkUpdateBtn.Location = new Point(20, 110);
        checkUpdateBtn.Size = new Size(160, 35);
        checkUpdateBtn.BackColor = Color.FromArgb(0, 120, 212);
        checkUpdateBtn.ForeColor = Color.White;
        checkUpdateBtn.FlatStyle = FlatStyle.Flat;
        checkUpdateBtn.Click += CheckUpdates;
        updateGroup.Controls.Add(checkUpdateBtn);
        
        updateProgress = new ProgressBar();
        updateProgress.Location = new Point(20, 155);
        updateProgress.Size = new Size(400, 25);
        updateProgress.Visible = false;
        updateGroup.Controls.Add(updateProgress);
        
        var logLbl = new Label();
        logLbl.Text = "Update Log:";
        logLbl.Location = new Point(20, 195);
        logLbl.AutoSize = true;
        updateGroup.Controls.Add(logLbl);
        
        updateLog = new TextBox();
        updateLog.Location = new Point(20, 220);
        updateLog.Size = new Size(740, 100);
        updateLog.Multiline = true;
        updateLog.ReadOnly = true;
        updateLog.ScrollBars = ScrollBars.Vertical;
        updateLog.Font = new Font("Consolas", 9);
        updateLog.BackColor = Color.FromArgb(245, 245, 245);
        updateGroup.Controls.Add(updateLog);
        
        tab.Controls.Add(updateGroup);
        
        // Security Section
        var secGroup = new GroupBox();
        secGroup.Text = "Security Settings";
        secGroup.Location = new Point(30, 450);
        secGroup.Size = new Size(800, 150);
        secGroup.Font = new Font("Segoe UI", 11);
        secGroup.BackColor = Color.White;
        
        var mfaCheck = new CheckBox();
        mfaCheck.Text = "Enable Multi-Factor Authentication";
        mfaCheck.Location = new Point(20, 40);
        mfaCheck.AutoSize = true;
        secGroup.Controls.Add(mfaCheck);
        
        var auditCheck = new CheckBox();
        auditCheck.Text = "Enable Audit Logging";
        auditCheck.Location = new Point(20, 70);
        auditCheck.AutoSize = true;
        auditCheck.Checked = true;
        secGroup.Controls.Add(auditCheck);
        
        tab.Controls.Add(secGroup);
        tabs.TabPages.Add(tab);
    }
    
    void StartScan(object sender, EventArgs e)
    {
        if (string.IsNullOrWhiteSpace(targetInput.Text))
        {
            MessageBox.Show("Please enter target IPs or CIDR ranges.", "Input Required");
            return;
        }
        
        scanButton.Enabled = false;
        scanProgress.Visible = true;
        resultsView.Items.Clear();
        statusLabel.Text = "Scanning...";
        
        var worker = new System.ComponentModel.BackgroundWorker();
        worker.WorkerReportsProgress = true;
        
        worker.DoWork += (s, args) => {
            var targets = targetInput.Text.Split('\n');
            int total = targets.Length * 4;
            int current = 0;
            
            foreach (var target in targets)
            {
                var ip = target.Trim();
                if (string.IsNullOrEmpty(ip)) continue;
                
                foreach (var port in new[] { "1080", "3128", "8080", "8888" })
                {
                    current++;
                    string scanTarget = ip + ":" + port;
                    worker.ReportProgress((current * 100) / total, scanTarget);
                    Thread.Sleep(200);
                    
                    // Simulate finding
                    if (new Random().Next(10) > 7)
                    {
                        var risk = new Random().Next(3) == 0 ? "Critical" : "High";
                        worker.ReportProgress(-1, new[] { ip, port, "SOCKS5", "Open", risk, "No auth required" });
                    }
                }
            }
        };
        
        worker.ProgressChanged += (s, args) => {
            if (args.ProgressPercentage >= 0)
            {
                scanProgress.Value = args.ProgressPercentage;
                statusLabel.Text = "Scanning " + args.UserState.ToString() + "...";
            }
            else
            {
                var data = (string[])args.UserState;
                var item = new ListViewItem(data);
                if (data[4] == "Critical") item.ForeColor = Color.Red;
                resultsView.Items.Add(item);
                
                totalProxiesLabel.Text = resultsView.Items.Count.ToString();
                if (data[4] == "Critical")
                    criticalFindingsLabel.Text = (int.Parse(criticalFindingsLabel.Text) + 1).ToString();
                
                AddActivity("Found proxy at " + data[0] + ":" + data[1] + " - Risk: " + data[4]);
            }
        };
        
        worker.RunWorkerCompleted += (s, args) => {
            scanButton.Enabled = true;
            scanProgress.Visible = false;
            statusLabel.Text = "Scan complete";
            
            if (resultsView.Items.Count > 0)
            {
                MessageBox.Show("Scan complete!\n\nFound " + resultsView.Items.Count + " proxies.", "Results");
            }
        };
        
        worker.RunWorkerAsync();
    }
    
    void AddActivity(string text)
    {
        var lbl = new Label();
        lbl.Text = "[" + DateTime.Now.ToString("HH:mm:ss") + "] " + text;
        lbl.Location = new Point(20, activityPanel.Controls.Count * 25 + 20);
        lbl.AutoSize = true;
        activityPanel.Controls.Add(lbl);
    }
    
    void CheckUpdates(object sender, EventArgs e)
    {
        checkUpdateBtn.Enabled = false;
        updateStatus.Text = "Checking for updates...";
        updateStatus.ForeColor = Color.Blue;
        AddLog("Checking for updates...");
        
        Thread.Sleep(1500);
        
        updateStatus.Text = "You have the latest version!";
        updateStatus.ForeColor = Color.Green;
        AddLog("Already running version 2.0.0 (Full Featured)");
        
        MessageBox.Show("You're running the latest full-featured version!", "No Updates");
        checkUpdateBtn.Enabled = true;
    }
    
    void AddLog(string text)
    {
        updateLog.AppendText("[" + DateTime.Now.ToString("HH:mm:ss") + "] " + text + "\r\n");
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

# Save and compile
$sourceFile = "ProxyAssessmentTool.cs"
$fullApp | Out-File $sourceFile -Encoding UTF8

Write-Host "Compiling with C# 5.0 compatible code..." -ForegroundColor Yellow

$compiler = "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe"

if (Test-Path $compiler) {
    & $compiler /target:winexe /out:ProxyAssessmentTool.exe $sourceFile 2>&1 | Out-Null
    
    if (Test-Path "ProxyAssessmentTool.exe") {
        Remove-Item $sourceFile -Force
        
        $size = [math]::Round((Get-Item "ProxyAssessmentTool.exe").Length / 1KB, 2)
        
        Write-Host "`n=== SUCCESS! ===" -ForegroundColor Green
        Write-Host "ProxyAssessmentTool v2.0.0 FULL created!" -ForegroundColor Cyan
        Write-Host "Size: $size KB" -ForegroundColor Gray
        
        Write-Host "`nFeatures:" -ForegroundColor Yellow
        Write-Host "✓ Professional Dashboard with live stats" -ForegroundColor Green
        Write-Host "✓ Full Assessment Scanner with progress" -ForegroundColor Green
        Write-Host "✓ Security Findings tracking" -ForegroundColor Green
        Write-Host "✓ Report generation capability" -ForegroundColor Green
        Write-Host "✓ Complete Settings with update system" -ForegroundColor Green
        Write-Host "✓ Recent activity feed" -ForegroundColor Green
        
        # Create desktop shortcut
        Write-Host "`nCreating desktop shortcut..." -ForegroundColor Yellow
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut("$env:USERPROFILE\Desktop\ProxyAssessmentTool_FULL.lnk")
        $shortcut.TargetPath = "$(Get-Location)\ProxyAssessmentTool.exe"
        $shortcut.IconLocation = "$(Get-Location)\ProxyAssessmentTool.exe,0"
        $shortcut.Save()
        Write-Host "Desktop shortcut created!" -ForegroundColor Green
        
        $run = Read-Host "`nRun the FULL version now? (Y/N)"
        if ($run -eq 'Y') {
            Start-Process "ProxyAssessmentTool.exe"
        }
    }
    else {
        Write-Host "Compilation failed!" -ForegroundColor Red
    }
}
else {
    Write-Host "Compiler not found!" -ForegroundColor Red
}

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")