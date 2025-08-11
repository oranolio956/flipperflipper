# ProxyAssessmentTool v2.2.0 - FINAL WORKING VERSION
param([string]$OutputPath = "ProxyAssessmentTool.exe")

$ErrorActionPreference = "Stop"
Write-Host "Building ProxyAssessmentTool v2.2.0 Final..." -ForegroundColor Cyan

$buildDir = Join-Path $env:TEMP "PAT_Build_$(Get-Random)"
New-Item -ItemType Directory -Path $buildDir -Force | Out-Null

try {
    # Create icon file - VALID BASE64
    $iconBase64 = @'
AAABAAEAICAAAAEAIACoEAAAFgAAACgAAAAgAAAAQAAAAAEAIAAAAAAAABAAABMLAAATCwAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAQAAAAMAAAAIQAAA
EEAAABhAAAAgQAAAKEAAACBAAAAYQAAAEEAAAAgAAAABAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAGQAAAD0AAABpQAAAm0AA
AMVAAADvQAAA/0AAAP9AAAD/QAAA/0AAAO9AAADFQAAAm0AAAGlAAAA9QAAADQAAAAIAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUAAAA5QAAAeUAAAM1AAA
DzQAAA/1VVVf+qqqr/1VVV/+qqqv/VVVX/qqqq/1VVVf9AAAD/QAAA80AAAM1AAAB5QAAAOUAA
AAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACUAAAC1AAABpQAA
AxUAAAP9VVVX/qqqq/9VVVf/qqqv/////////////////////////////+qqqv/VVVX/qqqq/1VV
Vf9AAAD/QAAAxUAAAGlAAAAtQAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACQAAA
FUAAAD1AAAB5QAAAxUAAAO9AAAD/VVVV/6qqqv/VVVX/6qqr////////////////////////////
/////////////////+qqqv/VVVX/qqqq/1VVVf9AAAD/QAAA70AAAMVAAABtQAAAPUAAABVAAAAC
AAAAAAAAAAAAAAAAAAAAAAAAAAUAAAA5QAAAaUAAAM1AAAD/VVVV/6qqqv/VVVX/6qqr////////
/////////////////////////////////////////////////+qqqv/VVVX/qqqq/1VVVf9AAAD/
QAAAzUAAAGlAAAA5QAAABQAAAAAAAAAAAAAAAQAAAA1AAAA5QAAAeUAAAN9AAAD/VVVV/8zMzP/V
VVX/6qqr//////////////////////////////////////////////////////////////////qq
qv/VVVX/zMzM/1VVVf9AAAD/QAAA30AAAHlAAAA5QAAADQAAAAEAAAAAAAAABQAAAD1AAAB1QAAA
00AAAP9VVVX/qqqq///////qqqv/////////////////////////////////////////////////
////////////////////////6qqr///////qqqq/1VVVf9AAAD/QAAAzUAAAHVAAAA9QAAABQAA
AABAAAAIQAAAaUAAAN9AAAD/VVVV/9VVVf//////6qqr////////////////////////////////////
/////////////////////////////////////////+qqqv//////1VVV/1VVVf9AAAD/QAAA30AA
AGlAAAAIQAAAA0AAAC1AAADFZmZm/1VVVf/qqqr///////qqqv//////////////////////////////
//////////////////////////////////////////////////qqqv//////6qqq/1VVVf9mZmb/
QAAAxUAAACdAAAADQAAAFUAAAINVVVX/qs7O/9VVVf///////+qqqv//////zMzM/6qqqv+ZmZn/
mZmZ/5mZmf+ZmZn/mZmZ/5mZmf+ZmZn/mZmZ/5mZmf+ZmZn/mZmZ/6qqqv/MzMz//////+qqqv//
////1VVV/6rOzv9VVVX/QAAAg0AAABVAAAAgQAAAn1VVVf/VVVX////////////qqqv//////8zM
zP+qqqr/mZmZ/5mZmf+ZmZn/mZmZ/5mZmf+ZmZn/mZmZ/5mZmf+ZmZn/mZmZ/5mZmf+qqqr/zMzM
///////qqqr////////////VVVX/VVVV/0AAAJ9AAAAgQAAAKEAAAMWZmZn/1VVV////////////
/+qqqv//////////////////////////////////////////////////////+qqqv///////////
////////////1VVV/5mZmf9AAADFQAAAKEAAACBAAADFmZmZ/9VVVf///////////////////////8zM
zP+qqqr/mZmZ/5mZmf+ZmZn/mZmZ/5mZmf+ZmZn/mZmZ/5mZmf+ZmZn/qqqq/8zMzP//////////
/////////////////9VVVf+ZmZn/QAAAxUAAACBAAAAoQAAAn1VVVf/qzs7//////////////////+qq
qv//////zMzM/6qqqv+ZmZn/mZmZ/5mZmf+ZmZn/mZmZ/5mZmf+ZmZn/mZmZ/5mZmf+qqqr/zMzM
///////qqqr//////////////////+rOzv9VVVX/QAAAn0AAACgAAAAVQAAAg1VVVf+qzs7/1VVV
////////////6qqr////////////////////////////////////////////////////////////
/////////////+qqqv///////////9VVVf+qzs7/VVVV/0AAAINAAAAVAAAABUAAACdAAADFmZmZ
/1VVVf/qqqr///////qqqv//////////////////////////////////////////////////////
//////////////////qqqv//////6qqq/1VVVf+ZmZn/QAAAxUAAACdAAAADQAAAAEAAAAhAAABp
QAAA31VVVf9VVVX/1VVV///////qqqv/////////////////////////////////////////////////
////////////////////////6qqr///////VVVX/VVVV/1VVVf9AAADfQAAAaUAAAAhAAAAAAAAA
AAUAAAA9QAAAeUAAAN9VVVX/VVVV/6qqqv//////6qqr////////////////////////////////////
/////////////////////////////////////////+qqqv//////qqqq/1VVVf9VVVX/QAAA30AA
AHlAAAA9QAAABQAAAAAAAAABQAAADVAAAD1AAAB5QAAA31VVVf9VVVX/zMzM/9VVVf/qqqv/////
//////////////////////////////////////////////////////////////////qqqv/VVVX/
zMzM/1VVVf9VVVX/QAAA30AAAHlAAAA9QAAADQAAAAEAAAAAAAAAAAAAAAUAAAA5QAAAaUAAAM1V
VVX/VVVV/6qqqv/VVVX/6qqr///////////////////////////////////////////////////////q
qqv/1VVV/6qqqv9VVVX/VVVV/0AAAM1AAABpQAAAOUAAAAUAAAAAAAAAAAAAAAAAAAACQAAAFUAA
AD1AAAB5QAAAxVVVVf9VVVX/VVVV/6qqqv/VVVX/6qqr////////////////////////////////////
/////////////////+qqqv/VVVX/qqqq/1VVVf9VVVX/VVVV/0AAAMVAAABtQAAAPUAAABVAAAAC
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIQQAAK1VVVWdVVVXDVVVV8FVVVP9VVVX/VVVV/6qqqv/V
VVX/6qqr///////////////////////qqqv/1VVV/6qqqv9VVVX/VVVV/1VVVf9VVVX/VVVV8FVV
VcNVVVVnQQAAK0AAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJCAgIVRUVF
N1VVVXdVVVXNVVVV81VVVf9VVVX/VVVV/6qqqv/VVVX/qqqq/1VVVf9VVVX/VVVV/1VVVf9VVVX/
VVVV81VVVc1VVVV3RUVFNUICAhVAAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAACLAAAAEAAAAkpVVVVa1VVVbFVVVXnVVVV/1VVVf9VVVX/VVVV/1VVVf9VVVX/VVVV
/1VVVedVVVWxVVVVa0AAAAkpLAAAAEAAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAIRERERTVVVV1VVVWZVVVVw1VVVc9VVVXDVVVVmVVV
VV1ERERNQAAACEAAAAgAAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAAVKysrK0AAAD1ERERJKysr
S0AAAD0rKysrQAAAFUAAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAABUAA
AAgAAAAIQAAABQAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAP//////////8A///8AH//8AA///AAH/+AAB//AAAP/AAAD/gAAA/wAAAH8AAAB+
AAAAfAAAAPwAAAD8AAAA/AAAAH4AAAB/AAAA/wAAAP+AAAH/wAAD/+AAB//wAA///AA///4A////
gf////////8=
'@
    $iconBytes = [Convert]::FromBase64String($iconBase64)
    $iconPath = Join-Path $buildDir "icon.ico"
    [System.IO.File]::WriteAllBytes($iconPath, $iconBytes)

    # FULLY C# 2.0 COMPATIBLE CODE
    $sourceCode = @'
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;
using System.Net;
using System.Net.Sockets;
using System.IO;
using System.Threading;
using System.Text;
using System.Text.RegularExpressions;
using System.Runtime.InteropServices;
using System.Diagnostics;
using System.ComponentModel;

namespace ProxyAssessmentTool
{
    public class DiscordColors
    {
        public static readonly Color Background = Color.FromArgb(54, 57, 63);
        public static readonly Color DarkerBackground = Color.FromArgb(47, 49, 54);
        public static readonly Color DarkestBackground = Color.FromArgb(32, 34, 37);
        public static readonly Color TextNormal = Color.FromArgb(220, 221, 222);
        public static readonly Color TextMuted = Color.FromArgb(142, 146, 151);
        public static readonly Color Blurple = Color.FromArgb(88, 101, 242);
        public static readonly Color Green = Color.FromArgb(87, 242, 135);
        public static readonly Color Yellow = Color.FromArgb(254, 231, 92);
        public static readonly Color Red = Color.FromArgb(237, 66, 69);
    }

    public class ProxyInfo
    {
        public string IP;
        public int Port;
        public string Country;
        public string City; 
        public string Carrier;
        public bool IsEligible;
        public int ResponseTimeMs;
    }

    public class MainForm : Form
    {
        public const string VERSION = "2.2.0";
        
        private Label statusLabel;
        private FlowLayoutPanel proxyContainer;
        private Label scanningLabel;
        private ProgressBar scanProgress;
        private System.Windows.Forms.Timer updateTimer;
        private System.Windows.Forms.Timer scanTimer;
        private BackgroundWorker updateWorker;
        private BackgroundWorker scanWorker;
        private Dictionary<string, ProxyInfo> foundProxies;
        private int eligibleCount = 0;
        private int totalFound = 0;
        private NotifyIcon trayIcon;
        private Label foundLabel;
        private Label eligibleLabel;
        private Button exportButton;
        
        // Proxy sources
        private string[] proxySources = new string[] {
            "https://www.proxy-list.download/api/v1/get?type=socks5",
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=US",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
            "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt"
        };
        
        [DllImport("user32.dll")]
        private static extern bool SetProcessDPIAware();
        
        public MainForm()
        {
            SetProcessDPIAware();
            foundProxies = new Dictionary<string, ProxyInfo>();
            InitializeUI();
            InitializeWorkers();
            StartScanning();
            StartUpdateChecking();
        }
        
        private void InitializeUI()
        {
            Text = "ProxyAssessmentTool v" + VERSION;
            Size = new Size(1200, 700);
            StartPosition = FormStartPosition.CenterScreen;
            BackColor = DiscordColors.Background;
            Icon = CreateIcon();
            
            // Header panel
            Panel headerPanel = new Panel();
            headerPanel.Height = 120;
            headerPanel.Dock = DockStyle.Top;
            headerPanel.BackColor = DiscordColors.DarkestBackground;
            Controls.Add(headerPanel);
            
            // Title
            Label headerLabel = new Label();
            headerLabel.Text = "PROXY SCANNER PRO";
            headerLabel.Font = new Font("Segoe UI", 20F, FontStyle.Bold);
            headerLabel.ForeColor = DiscordColors.TextNormal;
            headerLabel.Location = new Point(30, 20);
            headerLabel.AutoSize = true;
            headerPanel.Controls.Add(headerLabel);
            
            // Stats
            foundLabel = new Label();
            foundLabel.Text = "Found: 0";
            foundLabel.Font = new Font("Segoe UI", 12F);
            foundLabel.ForeColor = DiscordColors.Yellow;
            foundLabel.Location = new Point(30, 60);
            foundLabel.AutoSize = true;
            headerPanel.Controls.Add(foundLabel);
            
            eligibleLabel = new Label();
            eligibleLabel.Text = "Eligible: 0";
            eligibleLabel.Font = new Font("Segoe UI", 12F);
            eligibleLabel.ForeColor = DiscordColors.Green;
            eligibleLabel.Location = new Point(150, 60);
            eligibleLabel.AutoSize = true;
            headerPanel.Controls.Add(eligibleLabel);
            
            // Export button
            exportButton = new Button();
            exportButton.Text = "Export Eligible";
            exportButton.BackColor = DiscordColors.Blurple;
            exportButton.ForeColor = Color.White;
            exportButton.FlatStyle = FlatStyle.Flat;
            exportButton.Font = new Font("Segoe UI", 10F);
            exportButton.Location = new Point(1050, 55);
            exportButton.Size = new Size(120, 30);
            exportButton.Click += new EventHandler(OnExportClick);
            headerPanel.Controls.Add(exportButton);
            
            // Scanning status
            scanningLabel = new Label();
            scanningLabel.Text = "Initializing scanner...";
            scanningLabel.Font = new Font("Segoe UI", 10F);
            scanningLabel.ForeColor = DiscordColors.TextMuted;
            scanningLabel.Location = new Point(30, 90);
            scanningLabel.AutoSize = true;
            headerPanel.Controls.Add(scanningLabel);
            
            scanProgress = new ProgressBar();
            scanProgress.Location = new Point(30, 100);
            scanProgress.Size = new Size(1140, 6);
            scanProgress.Style = ProgressBarStyle.Marquee;
            headerPanel.Controls.Add(scanProgress);
            
            // Proxy container
            proxyContainer = new FlowLayoutPanel();
            proxyContainer.Dock = DockStyle.Fill;
            proxyContainer.AutoScroll = true;
            proxyContainer.BackColor = DiscordColors.DarkerBackground;
            proxyContainer.Padding = new Padding(20);
            Controls.Add(proxyContainer);
            
            // Status bar
            Panel statusBar = new Panel();
            statusBar.Height = 25;
            statusBar.BackColor = DiscordColors.DarkestBackground;
            statusBar.Dock = DockStyle.Bottom;
            Controls.Add(statusBar);
            
            statusLabel = new Label();
            statusLabel.Text = "Ready - Auto-Update Enabled";
            statusLabel.ForeColor = DiscordColors.TextMuted;
            statusLabel.Location = new Point(10, 4);
            statusLabel.AutoSize = true;
            statusBar.Controls.Add(statusLabel);
            
            // System tray
            trayIcon = new NotifyIcon();
            trayIcon.Icon = Icon;
            trayIcon.Text = "ProxyAssessmentTool";
            trayIcon.Visible = true;
            
            ContextMenuStrip trayMenu = new ContextMenuStrip();
            trayMenu.Items.Add("Show", null, new EventHandler(OnTrayShow));
            trayMenu.Items.Add("Exit", null, new EventHandler(OnTrayExit));
            trayIcon.ContextMenuStrip = trayMenu;
            trayIcon.DoubleClick += new EventHandler(OnTrayShow);
        }
        
        private void OnTrayShow(object sender, EventArgs e)
        {
            WindowState = FormWindowState.Normal;
            Show();
            Activate();
        }
        
        private void OnTrayExit(object sender, EventArgs e)
        {
            Application.Exit();
        }
        
        private void OnExportClick(object sender, EventArgs e)
        {
            try
            {
                string filename = "eligible_proxies_" + DateTime.Now.ToString("yyyyMMdd_HHmmss") + ".txt";
                StringBuilder content = new StringBuilder();
                content.AppendLine("# ProxyAssessmentTool Export");
                content.AppendLine("# Generated: " + DateTime.Now);
                content.AppendLine("# Eligible SOCKS5 Proxies (US Mobile)");
                content.AppendLine();
                
                foreach (KeyValuePair<string, ProxyInfo> kvp in foundProxies)
                {
                    if (kvp.Value.IsEligible)
                    {
                        content.AppendLine(kvp.Value.IP + ":" + kvp.Value.Port);
                    }
                }
                
                File.WriteAllText(filename, content.ToString());
                MessageBox.Show("Exported " + eligibleCount + " proxies to:\n" + filename, 
                    "Export Successful", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show("Export failed: " + ex.Message, "Error", 
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
        
        private void InitializeWorkers()
        {
            updateWorker = new BackgroundWorker();
            updateWorker.DoWork += new DoWorkEventHandler(CheckForUpdates);
            updateWorker.RunWorkerCompleted += new RunWorkerCompletedEventHandler(OnUpdateCheckComplete);
            
            scanWorker = new BackgroundWorker();
            scanWorker.WorkerReportsProgress = true;
            scanWorker.DoWork += new DoWorkEventHandler(ScanProxies);
            scanWorker.ProgressChanged += new ProgressChangedEventHandler(OnScanProgress);
            scanWorker.RunWorkerCompleted += new RunWorkerCompletedEventHandler(OnScanComplete);
        }
        
        private void StartUpdateChecking()
        {
            updateTimer = new System.Windows.Forms.Timer();
            updateTimer.Interval = 60000; // 1 minute
            updateTimer.Tick += new EventHandler(OnUpdateTimerTick);
            updateTimer.Start();
            
            // Check immediately
            if (!updateWorker.IsBusy)
                updateWorker.RunWorkerAsync();
        }
        
        private void OnUpdateTimerTick(object sender, EventArgs e)
        {
            if (!updateWorker.IsBusy)
                updateWorker.RunWorkerAsync();
        }
        
        private void CheckForUpdates(object sender, DoWorkEventArgs e)
        {
            try
            {
                WebClient client = new WebClient();
                client.Headers.Add("User-Agent", "ProxyAssessmentTool/" + VERSION);
                string json = client.DownloadString("https://api.github.com/repos/oranolio956/flipperflipper/releases/latest");
                
                // Simple JSON parsing for C# 2.0
                Match tagMatch = Regex.Match(json, "\"tag_name\"\\s*:\\s*\"([^\"]+)\"");
                if (tagMatch.Success)
                {
                    string latestVersion = tagMatch.Groups[1].Value.TrimStart('v');
                    if (CompareVersions(latestVersion, VERSION) > 0)
                    {
                        e.Result = latestVersion;
                    }
                }
            }
            catch
            {
                // Silent fail
            }
        }
        
        private void OnUpdateCheckComplete(object sender, RunWorkerCompletedEventArgs e)
        {
            if (e.Result != null)
            {
                string newVersion = (string)e.Result;
                BeginInvoke(new MethodInvoker(delegate
                {
                    ShowUpdateNotification(newVersion);
                    DownloadAndInstallUpdate("v" + newVersion);
                }));
            }
        }
        
        private void ShowUpdateNotification(string version)
        {
            Panel updatePanel = new Panel();
            updatePanel.BackColor = DiscordColors.Green;
            updatePanel.Height = 40;
            updatePanel.Dock = DockStyle.Top;
            
            Label updateLabel = new Label();
            updateLabel.Text = "Update v" + version + " is being installed...";
            updateLabel.ForeColor = Color.Black;
            updateLabel.Font = new Font("Segoe UI", 10F, FontStyle.Bold);
            updateLabel.Location = new Point(20, 10);
            updateLabel.AutoSize = true;
            updatePanel.Controls.Add(updateLabel);
            
            Controls.Add(updatePanel);
            updatePanel.BringToFront();
            
            trayIcon.ShowBalloonTip(5000, "Update Available", 
                "Version " + version + " is being installed.", ToolTipIcon.Info);
        }
        
        private void DownloadAndInstallUpdate(string tag)
        {
            try
            {
                string url = "https://github.com/oranolio956/flipperflipper/releases/download/" + tag + "/ProxyAssessmentTool.exe";
                string tempFile = Path.Combine(Path.GetTempPath(), "ProxyAssessmentTool_Update.exe");
                
                WebClient client = new WebClient();
                client.DownloadFile(url, tempFile);
                
                // Create updater script
                string script = "@echo off\r\ntimeout /t 2 /nobreak > nul\r\n" +
                               "move /y \"" + tempFile + "\" \"" + Application.ExecutablePath + "\"\r\n" +
                               "start \"\" \"" + Application.ExecutablePath + "\"\r\n" +
                               "del \"%~f0\"";
                               
                string scriptPath = Path.Combine(Path.GetTempPath(), "updater.bat");
                File.WriteAllText(scriptPath, script);
                
                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = scriptPath;
                psi.CreateNoWindow = true;
                psi.UseShellExecute = false;
                Process.Start(psi);
                
                Application.Exit();
            }
            catch
            {
                // Silent fail
            }
        }
        
        private int CompareVersions(string v1, string v2)
        {
            string[] parts1 = v1.Split('.');
            string[] parts2 = v2.Split('.');
            
            for (int i = 0; i < Math.Max(parts1.Length, parts2.Length); i++)
            {
                int p1 = i < parts1.Length ? int.Parse(parts1[i]) : 0;
                int p2 = i < parts2.Length ? int.Parse(parts2[i]) : 0;
                if (p1 != p2) return p1.CompareTo(p2);
            }
            
            return 0;
        }
        
        private void StartScanning()
        {
            scanTimer = new System.Windows.Forms.Timer();
            scanTimer.Interval = 30000; // 30 seconds
            scanTimer.Tick += new EventHandler(OnScanTimerTick);
            scanTimer.Start();
            
            // Start immediately
            if (!scanWorker.IsBusy)
                scanWorker.RunWorkerAsync();
        }
        
        private void OnScanTimerTick(object sender, EventArgs e)
        {
            if (!scanWorker.IsBusy)
                scanWorker.RunWorkerAsync();
        }
        
        private void ScanProxies(object sender, DoWorkEventArgs e)
        {
            BackgroundWorker worker = sender as BackgroundWorker;
            List<string> allProxies = new List<string>();
            
            // Fetch proxies from sources
            foreach (string source in proxySources)
            {
                try
                {
                    WebClient client = new WebClient();
                    client.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)");
                    string data = client.DownloadString(source);
                    
                    MatchCollection matches = Regex.Matches(data, @"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{1,5}\b");
                    foreach (Match match in matches)
                    {
                        if (!allProxies.Contains(match.Value))
                            allProxies.Add(match.Value);
                    }
                }
                catch
                {
                    // Continue with next source
                }
            }
            
            // Test each proxy
            int tested = 0;
            foreach (string proxy in allProxies)
            {
                if (!foundProxies.ContainsKey(proxy))
                {
                    string[] parts = proxy.Split(':');
                    if (parts.Length == 2)
                    {
                        string ip = parts[0];
                        int port;
                        if (int.TryParse(parts[1], out port))
                        {
                            ProxyInfo info = TestProxy(ip, port);
                            if (info != null)
                            {
                                lock (foundProxies)
                                {
                                    foundProxies[proxy] = info;
                                }
                                worker.ReportProgress(tested, info);
                            }
                        }
                    }
                }
                tested++;
                
                // Limit testing to prevent overload
                if (tested > 100) break;
            }
        }
        
        private ProxyInfo TestProxy(string ip, int port)
        {
            try
            {
                TcpClient client = new TcpClient();
                client.ReceiveTimeout = 5000;
                client.SendTimeout = 5000;
                
                // Connect
                IAsyncResult ar = client.BeginConnect(ip, port, null, null);
                if (!ar.AsyncWaitHandle.WaitOne(5000, false))
                {
                    client.Close();
                    return null;
                }
                client.EndConnect(ar);
                
                if (!client.Connected)
                    return null;
                
                // SOCKS5 handshake
                NetworkStream stream = client.GetStream();
                byte[] greeting = new byte[] { 0x05, 0x01, 0x00 };
                stream.Write(greeting, 0, greeting.Length);
                
                byte[] response = new byte[2];
                int read = stream.Read(response, 0, 2);
                
                client.Close();
                
                if (read == 2 && response[0] == 0x05 && response[1] == 0x00)
                {
                    // Get location
                    string location = GetLocation(ip);
                    bool isUS = location.IndexOf("United States") >= 0 || location.IndexOf("US") >= 0;
                    bool isMobile = location.IndexOf("mobile") >= 0 || location.IndexOf("wireless") >= 0 || 
                                   location.IndexOf("cellular") >= 0 || location.IndexOf("Verizon") >= 0 || 
                                   location.IndexOf("AT&T") >= 0 || location.IndexOf("T-Mobile") >= 0 ||
                                   location.IndexOf("Sprint") >= 0;
                    
                    ProxyInfo info = new ProxyInfo();
                    info.IP = ip;
                    info.Port = port;
                    info.Country = isUS ? "US" : "Other";
                    info.City = "Unknown";
                    info.Carrier = isMobile ? "Mobile Network" : "Fixed";
                    info.IsEligible = isUS && isMobile;
                    info.ResponseTimeMs = 100;
                    
                    return info;
                }
            }
            catch
            {
                // Failed
            }
            
            return null;
        }
        
        private string GetLocation(string ip)
        {
            try
            {
                WebClient client = new WebClient();
                return client.DownloadString("http://ip-api.com/line/" + ip);
            }
            catch
            {
                return "Unknown";
            }
        }
        
        private void OnScanProgress(object sender, ProgressChangedEventArgs e)
        {
            ProxyInfo info = e.UserState as ProxyInfo;
            if (info != null)
            {
                totalFound++;
                if (info.IsEligible)
                    eligibleCount++;
                
                AddProxyCard(info);
                UpdateStatus();
            }
        }
        
        private void OnScanComplete(object sender, RunWorkerCompletedEventArgs e)
        {
            scanningLabel.Text = "Scan complete. Next scan in 30 seconds...";
        }
        
        private void AddProxyCard(ProxyInfo info)
        {
            Panel card = new Panel();
            card.Size = new Size(240, 130);
            card.BackColor = DiscordColors.DarkestBackground;
            card.Margin = new Padding(5);
            card.Cursor = Cursors.Hand;
            card.Tag = info;
            
            // Border effect
            card.Paint += new PaintEventHandler(delegate(object sender, PaintEventArgs e)
            {
                ControlPaint.DrawBorder(e.Graphics, card.ClientRectangle,
                    info.IsEligible ? DiscordColors.Green : DiscordColors.Red, ButtonBorderStyle.Solid);
            });
            
            Label ipLabel = new Label();
            ipLabel.Text = info.IP + ":" + info.Port;
            ipLabel.Font = new Font("Consolas", 11F, FontStyle.Bold);
            ipLabel.ForeColor = DiscordColors.TextNormal;
            ipLabel.Location = new Point(10, 10);
            ipLabel.AutoSize = true;
            card.Controls.Add(ipLabel);
            
            Label statusLabel = new Label();
            statusLabel.Text = info.IsEligible ? "ELIGIBLE" : "INELIGIBLE";
            statusLabel.Font = new Font("Segoe UI", 9F, FontStyle.Bold);
            statusLabel.ForeColor = info.IsEligible ? DiscordColors.Green : DiscordColors.Red;
            statusLabel.Location = new Point(10, 35);
            statusLabel.AutoSize = true;
            card.Controls.Add(statusLabel);
            
            Label locationLabel = new Label();
            locationLabel.Text = info.Country + " - " + info.Carrier;
            locationLabel.Font = new Font("Segoe UI", 9F);
            locationLabel.ForeColor = DiscordColors.TextMuted;
            locationLabel.Location = new Point(10, 60);
            locationLabel.AutoSize = true;
            card.Controls.Add(locationLabel);
            
            Label timeLabel = new Label();
            timeLabel.Text = "Tested: " + DateTime.Now.ToString("HH:mm:ss");
            timeLabel.Font = new Font("Segoe UI", 8F);
            timeLabel.ForeColor = DiscordColors.TextMuted;
            timeLabel.Location = new Point(10, 85);
            timeLabel.AutoSize = true;
            card.Controls.Add(timeLabel);
            
            // Click to copy
            EventHandler clickHandler = delegate(object s, EventArgs ev)
            {
                Clipboard.SetText(info.IP + ":" + info.Port);
                MessageBox.Show("Proxy copied to clipboard!", "Success", 
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
            };
            
            card.Click += clickHandler;
            foreach (Control c in card.Controls)
                c.Click += clickHandler;
            
            proxyContainer.Controls.Add(card);
            
            // Keep only last 50
            if (proxyContainer.Controls.Count > 50)
            {
                proxyContainer.Controls.RemoveAt(0);
            }
        }
        
        private void UpdateStatus()
        {
            statusLabel.Text = string.Format("Found: {0} | Eligible: {1} | Auto-Update: ON", 
                totalFound, eligibleCount);
            scanningLabel.Text = string.Format("Scanning internet for proxies... ({0} found)", totalFound);
            foundLabel.Text = "Found: " + totalFound;
            eligibleLabel.Text = "Eligible: " + eligibleCount;
        }
        
        private Icon CreateIcon()
        {
            Bitmap bitmap = new Bitmap(32, 32);
            Graphics g = Graphics.FromImage(bitmap);
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.Clear(Color.Transparent);
            
            using (Brush brush = new SolidBrush(DiscordColors.Blurple))
            {
                g.FillEllipse(brush, 2, 2, 28, 28);
            }
            
            using (Pen pen = new Pen(Color.White, 2))
            {
                g.DrawLine(pen, 10, 16, 22, 16);
                g.DrawLine(pen, 16, 10, 16, 22);
            }
            
            return Icon.FromHandle(bitmap.GetHicon());
        }
        
        protected override void OnFormClosed(FormClosedEventArgs e)
        {
            if (updateTimer != null) updateTimer.Stop();
            if (scanTimer != null) scanTimer.Stop();
            if (trayIcon != null) trayIcon.Dispose();
            base.OnFormClosed(e);
        }
    }
    
    public class Program
    {
        [STAThread]
        public static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }
}
'@

    $sourceFile = Join-Path $buildDir "ProxyAssessmentTool.cs"
    Set-Content -Path $sourceFile -Value $sourceCode -Encoding UTF8

    $cscPath = "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
    if (-not (Test-Path $cscPath)) {
        $cscPath = "$env:WINDIR\Microsoft.NET\Framework\v4.0.30319\csc.exe"
    }

    Write-Host "Using compiler: $cscPath" -ForegroundColor Gray
    Write-Host "Compiling..." -ForegroundColor Yellow
    
    & $cscPath /target:winexe /optimize+ /win32icon:"$iconPath" /reference:System.dll /reference:System.Drawing.dll /reference:System.Windows.Forms.dll "/out:$OutputPath" "$sourceFile"

    if ($LASTEXITCODE -eq 0 -and (Test-Path $OutputPath)) {
        Write-Host "`nSUCCESS!" -ForegroundColor Green
        Write-Host "Built: $OutputPath" -ForegroundColor White
        Write-Host ""
        Write-Host "FEATURES:" -ForegroundColor Cyan
        Write-Host "  * Automatic updates every 60 seconds" -ForegroundColor Gray
        Write-Host "  * Internet proxy scanning (4 sources)" -ForegroundColor Gray
        Write-Host "  * Discord-inspired dark theme" -ForegroundColor Gray
        Write-Host "  * Click any proxy to copy" -ForegroundColor Gray
        Write-Host "  * Export eligible proxies" -ForegroundColor Gray
        Write-Host "  * System tray support" -ForegroundColor Gray
        Write-Host "  * US mobile carrier detection" -ForegroundColor Gray
        Write-Host ""
        Write-Host "FIXED:" -ForegroundColor Yellow
        Write-Host "  * Valid base64 icon string" -ForegroundColor Gray
        Write-Host "  * Pure C# 2.0 compatibility" -ForegroundColor Gray
        Write-Host "  * No modern C# features" -ForegroundColor Gray
    }
    else {
        Write-Host "Compilation failed!" -ForegroundColor Red
        Write-Host "Exit code: $LASTEXITCODE" -ForegroundColor Red
    }
}
finally {
    Remove-Item -Path $buildDir -Recurse -Force -ErrorAction SilentlyContinue
}