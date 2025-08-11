# ProxyAssessmentTool v2.2.0 - Auto-Update Edition with Icon
param([string]$OutputPath = "ProxyAssessmentTool.exe")

$ErrorActionPreference = "Stop"
Write-Host "Building ProxyAssessmentTool v2.2.0 Auto-Update Edition..." -ForegroundColor Cyan

$buildDir = Join-Path $env:TEMP "PAT_Build_$(Get-Random)"
New-Item -ItemType Directory -Path $buildDir -Force | Out-Null

try {
    # Create icon file
    $iconBase64 = @'
AAABAAEAICAAAAEAIACoEAAAFgAAACgAAAAgAAAAQAAAAAEAIAAAAAAAABAAABMLAAATCwAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAQAAAAMAAAAIQAAA
EEAAABhAAAAgQAAAKEAAACBAAAAYQAAAEEAAAAgAAAABAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAGQAAAD0AAABpQAAAm0AA
AMVAAADvQAAA/0AAAP9AAAD/QAAA/0AAAO9AAADFQAAAm0AAAGlAAAA9QAAADQAAAAIAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUAAAA5QAAAeUAAANFAA
ADzQAAA/1VVVf+qqqr/1VVV/+qqqv/VVVX/qqqq/1VVVf9AAAD/QAAA80AAAM1AAAB5QAAAOUAA
AAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACUAAAC1AAABpQAA
AxUAAAP9VVVX/qqqq/9VVVf/qqqv/////////////////////////////+qqqv/VVVX/qqqq/1VV
Vf9AAAD/QAAAxUAAAGlAAAAtQAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACQAAA
FUAAAD1AAAB5QAAAxUAAAO9AAAD/VVVV/6qqqv/VVVX/6qqr////////////////////////////
/////////////////+qqqv/VVVX/qqqq/1VVVf9AAAD/QAAAxUAAAGlAAAAtQAAACAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAACQAAAFUAAAD1AAAB5QAAAxUAAAO9AAAD/VVVV/6qqqv/VVVX/6qq
r/////////////////////////////////////////////////+qqqv/VVVX/qqqq/1VVVf9AAAD/QAAAzUAAAGl
AAAA5QAAABQAAAAAAAAAAAAAAAQAAAA1AAAA5QAAAeUAAAN9AAAD/VVVV/8zMzP/VVVX/6qqr////////
//////////////////////////////////////////////////////////////////qqqv/VVVX/zMzM/1VVVf9AAAD/QAAA30AAAHlAAAA5QAAADQAAAAEAAAAAAAAABQAAAD1AAAB1QAAA
00AAAP9VVVX/qqqq///////qqqv/////////////////////////////////////////////////
////////////////////////6qqr///////qqqq/1VVVf9AAAD/QAAAzUAAAHVAAAA9QAAABQAAAAA
AAAAAAAAAAAAAAAAAAAAAIAAAaUAAAN9AAAD/VVVV/9VVVf//////6qqr////////////////////////////////////
/////////////////////////////////////////+qqqv//////1VVV/1VVVf9AAAD/QAAA30AAAGlAAAAIQAA
AA0AAAC1AAADRZmZm/1VVVf/qqqr///////qqqv//////////////////////////////
//////////////////////////////////////////////////qqqv//////6qqq/1VVVf9mZmb/
QAAAxUAAACdAAAADQAAAFUAAAIVVVVX/qs7O/9VVVf///////+qqqv//////zMzM/6qqqv+ZmZn/
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
/////////////////////////////////////////+qqqv//////qqqq/1VVVf9VVVX/QAAA30AAAHlAAAA9QAAABQAAAAAAAAABQAAADVAAAD1AAAB5QAAA31VVVf9VVVX/zMzM/9VVVf/qqqv/////
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
AAAAAAAAAAAAAP//////////8A///8AH//8AA///AAH/+AAB//AAAP/AAAD/gAAA/wAAAH8AAAB+
AAAAfAAAAPwAAAD8AAAA/AAAAH4AAAB/AAAA/wAAAP+AAAH/wAAD/+AAB//wAA///AA///4A////
gf////////8=
'@
    $iconBytes = [Convert]::FromBase64String($iconBase64)
    $iconPath = Join-Path $buildDir "icon.ico"
    [System.IO.File]::WriteAllBytes($iconPath, $iconBytes)

    $sourceCode = @'
using System;
using System.Collections.Generic;
using System.Collections.Concurrent;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;
using System.Net;
using System.Net.Sockets;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Runtime.InteropServices;
using System.Diagnostics;
using System.Security.Cryptography;

namespace ProxyAssessmentTool
{
    public class DiscordColors
    {
        public static readonly Color Background = Color.FromArgb(54, 57, 63);
        public static readonly Color DarkerBackground = Color.FromArgb(47, 49, 54);
        public static readonly Color DarkestBackground = Color.FromArgb(32, 34, 37);
        public static readonly Color ChannelBar = Color.FromArgb(41, 43, 47);
        public static readonly Color TextNormal = Color.FromArgb(220, 221, 222);
        public static readonly Color TextMuted = Color.FromArgb(142, 146, 151);
        public static readonly Color Interactive = Color.FromArgb(185, 187, 190);
        public static readonly Color Blurple = Color.FromArgb(88, 101, 242);
        public static readonly Color Green = Color.FromArgb(87, 242, 135);
        public static readonly Color Yellow = Color.FromArgb(254, 231, 92);
        public static readonly Color Red = Color.FromArgb(237, 66, 69);
        public static readonly Color StreamingPurple = Color.FromArgb(89, 54, 149);
    }

    public class AutoUpdater
    {
        private System.Windows.Forms.Timer updateTimer;
        private MainForm mainForm;
        private const string UPDATE_CHECK_URL = "https://api.github.com/repos/oranolio956/flipperflipper/releases/latest";
        
        public AutoUpdater(MainForm form)
        {
            mainForm = form;
            updateTimer = new System.Windows.Forms.Timer();
            updateTimer.Interval = 60000; // Check every minute
            updateTimer.Tick += async (s, e) => await CheckForUpdatesAsync();
            updateTimer.Start();
            
            // Check immediately on startup
            Task.Run(async () => await CheckForUpdatesAsync());
        }
        
        private async Task CheckForUpdatesAsync()
        {
            try
            {
                using (var client = new WebClient())
                {
                    client.Headers.Add("User-Agent", "ProxyAssessmentTool/" + MainForm.VERSION);
                    var response = await client.DownloadStringTaskAsync(UPDATE_CHECK_URL);
                    
                    if (response.Contains("\"tag_name\":"))
                    {
                        var start = response.IndexOf("\"tag_name\":\"") + 12;
                        var end = response.IndexOf("\"", start);
                        var tag = response.Substring(start, end - start);
                        var latestVersion = tag.TrimStart('v');
                        
                        if (CompareVersions(latestVersion, MainForm.VERSION) > 0)
                        {
                            mainForm.BeginInvoke(new Action(() => 
                            {
                                mainForm.ShowUpdateNotification(latestVersion);
                                DownloadAndInstallUpdate(tag);
                            }));
                        }
                    }
                }
            }
            catch { /* Silent fail for auto-updates */ }
        }
        
        private void DownloadAndInstallUpdate(string tag)
        {
            try
            {
                var url = "https://github.com/oranolio956/flipperflipper/releases/download/" + tag + "/ProxyAssessmentTool.exe";
                var tempFile = Path.Combine(Path.GetTempPath(), "ProxyAssessmentTool_Update.exe");
                
                using (var client = new WebClient())
                {
                    client.DownloadFile(url, tempFile);
                }
                
                var updaterScript = "@echo off\ntimeout /t 2 /nobreak > nul\nmove /y \"" + tempFile + "\" \"" + Application.ExecutablePath + "\"\nstart \"\" \"" + Application.ExecutablePath + "\"\ndel \"%~f0\"";
                var updaterPath = Path.Combine(Path.GetTempPath(), "updater.bat");
                File.WriteAllText(updaterPath, updaterScript);
                
                Process.Start(new ProcessStartInfo
                {
                    FileName = updaterPath,
                    CreateNoWindow = true,
                    UseShellExecute = false
                });
                
                Application.Exit();
            }
            catch { /* Silent fail */ }
        }
        
        private int CompareVersions(string v1, string v2)
        {
            var parts1 = v1.Split('.').Select(int.Parse).ToArray();
            var parts2 = v2.Split('.').Select(int.Parse).ToArray();
            
            for (int i = 0; i < Math.Max(parts1.Length, parts2.Length); i++)
            {
                var p1 = i < parts1.Length ? parts1[i] : 0;
                var p2 = i < parts2.Length ? parts2[i] : 0;
                if (p1 != p2) return p1.CompareTo(p2);
            }
            
            return 0;
        }
    }

    public class ModernButton : Button
    {
        private bool isHovered = false;
        private Color normalColor;
        private Color hoverColor;
        
        public ModernButton()
        {
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | 
                    ControlStyles.DoubleBuffer | ControlStyles.ResizeRedraw, true);
            FlatStyle = FlatStyle.Flat;
            FlatAppearance.BorderSize = 0;
            Font = new Font("Segoe UI", 9F, FontStyle.Regular);
            ForeColor = Color.White;
            Cursor = Cursors.Hand;
            normalColor = DiscordColors.Blurple;
            hoverColor = Color.FromArgb(71, 82, 196);
        }
        
        protected override void OnPaint(PaintEventArgs e)
        {
            e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            e.Graphics.InterpolationMode = InterpolationMode.HighQualityBicubic;
            
            using (var path = GetRoundedRect(ClientRectangle, 4))
            using (var brush = new SolidBrush(isHovered ? hoverColor : normalColor))
            {
                e.Graphics.FillPath(brush, path);
            }
            
            TextRenderer.DrawText(e.Graphics, Text, Font, ClientRectangle, ForeColor,
                TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter);
        }
        
        protected override void OnMouseEnter(EventArgs e)
        {
            isHovered = true;
            Invalidate();
            base.OnMouseEnter(e);
        }
        
        protected override void OnMouseLeave(EventArgs e)
        {
            isHovered = false;
            Invalidate();
            base.OnMouseLeave(e);
        }
        
        private GraphicsPath GetRoundedRect(Rectangle rect, int radius)
        {
            var path = new GraphicsPath();
            path.AddArc(rect.X, rect.Y, radius * 2, radius * 2, 180, 90);
            path.AddArc(rect.Right - radius * 2, rect.Y, radius * 2, radius * 2, 270, 90);
            path.AddArc(rect.Right - radius * 2, rect.Bottom - radius * 2, radius * 2, radius * 2, 0, 90);
            path.AddArc(rect.X, rect.Bottom - radius * 2, radius * 2, radius * 2, 90, 90);
            path.CloseFigure();
            return path;
        }
    }

    public class ProxyCard : Panel
    {
        private bool isHovered = false;
        private ProxyInfo proxyInfo;
        
        public ProxyInfo ProxyInfo 
        { 
            get { return proxyInfo; }
            set { proxyInfo = value; Invalidate(); }
        }
        
        public ProxyCard()
        {
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | 
                    ControlStyles.DoubleBuffer | ControlStyles.ResizeRedraw, true);
            BackColor = DiscordColors.DarkestBackground;
            Size = new Size(280, 140);
            Padding = new Padding(16);
            Cursor = Cursors.Hand;
        }
        
        protected override void OnPaint(PaintEventArgs e)
        {
            e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            
            var bgColor = isHovered ? DiscordColors.ChannelBar : BackColor;
            
            using (var path = GetRoundedRect(new Rectangle(0, 0, Width - 1, Height - 1), 8))
            {
                e.Graphics.FillPath(new SolidBrush(bgColor), path);
                e.Graphics.DrawPath(new Pen(DiscordColors.ChannelBar, 1), path);
            }
            
            base.OnPaint(e);
        }
        
        protected override void OnMouseEnter(EventArgs e)
        {
            isHovered = true;
            Invalidate();
            base.OnMouseEnter(e);
        }
        
        protected override void OnMouseLeave(EventArgs e)
        {
            isHovered = false;
            Invalidate();
            base.OnMouseLeave(e);
        }
        
        protected override void OnClick(EventArgs e)
        {
            if (proxyInfo != null)
            {
                Clipboard.SetText(proxyInfo.IP + ":" + proxyInfo.Port);
                MessageBox.Show("Proxy copied to clipboard!", "Copied", 
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            base.OnClick(e);
        }
        
        private GraphicsPath GetRoundedRect(Rectangle rect, int radius)
        {
            var path = new GraphicsPath();
            path.AddArc(rect.X, rect.Y, radius * 2, radius * 2, 180, 90);
            path.AddArc(rect.Right - radius * 2, rect.Y, radius * 2, radius * 2, 270, 90);
            path.AddArc(rect.Right - radius * 2, rect.Bottom - radius * 2, radius * 2, radius * 2, 0, 90);
            path.AddArc(rect.X, rect.Bottom - radius * 2, radius * 2, radius * 2, 90, 90);
            path.CloseFigure();
            return path;
        }
    }

    public class MainForm : Form
    {
        public const string VERSION = "2.2.0";
        private Panel sidePanel;
        private Panel contentPanel;
        private Label statusLabel;
        private FlowLayoutPanel proxyContainer;
        private FlowLayoutPanel eligibleContainer;
        private Label scanningLabel;
        private ProgressBar scanProgress;
        private Label foundCountLabel;
        private Label eligibleCountLabel;
        private System.Windows.Forms.Timer animationTimer;
        private int animationStep = 0;
        private CancellationTokenSource scanCancellation;
        private ConcurrentDictionary<string, ProxyInfo> allProxies = new ConcurrentDictionary<string, ProxyInfo>();
        private ConcurrentDictionary<string, ProxyInfo> eligibleProxies = new ConcurrentDictionary<string, ProxyInfo>();
        private SemaphoreSlim testSemaphore = new SemaphoreSlim(50);
        private System.Windows.Forms.Timer autoExportTimer;
        private ModernButton exportButton;
        private ModernButton pauseButton;
        private bool isPaused = false;
        private TabControl tabControl;
        private RichTextBox logBox;
        private CheckBox autoScrollCheckBox;
        private AutoUpdater autoUpdater;
        private NotifyIcon trayIcon;
        private Panel updateNotificationPanel;
        
        // Enhanced proxy sources
        private readonly string[] proxySources = new string[]
        {
            "https://www.proxy-list.download/api/v1/get?type=socks5",
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=US",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
            "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
            "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
            "https://api.openproxylist.xyz/socks5.txt"
        };
        
        // Mobile carrier detection patterns
        private readonly Dictionary<string, string[]> carrierPatterns = new Dictionary<string, string[]>
        {
            ["Verizon"] = new[] { "verizon", "vzw", "cellco" },
            ["AT&T"] = new[] { "att", "at&t", "mobility", "cingular" },
            ["T-Mobile"] = new[] { "t-mobile", "tmobile", "metro" },
            ["Sprint"] = new[] { "sprint" },
            ["US Cellular"] = new[] { "uscellular", "uscc" },
            ["Cricket"] = new[] { "cricket" },
            ["Boost"] = new[] { "boost" }
        };
        
        [DllImport("user32.dll")]
        private static extern bool SetProcessDPIAware();
        
        public MainForm()
        {
            SetProcessDPIAware();
            InitializeUI();
            InitializeTrayIcon();
            autoUpdater = new AutoUpdater(this);
            StartAutoScan();
        }
        
        private void InitializeTrayIcon()
        {
            trayIcon = new NotifyIcon();
            trayIcon.Icon = Icon;
            trayIcon.Text = "ProxyAssessmentTool v" + VERSION;
            trayIcon.Visible = true;
            
            var contextMenu = new ContextMenuStrip();
            contextMenu.Items.Add("Show", null, (s, e) => { WindowState = FormWindowState.Normal; Show(); });
            contextMenu.Items.Add("Exit", null, (s, e) => Application.Exit());
            trayIcon.ContextMenuStrip = contextMenu;
            
            trayIcon.DoubleClick += (s, e) => { WindowState = FormWindowState.Normal; Show(); };
        }
        
        public void ShowUpdateNotification(string newVersion)
        {
            if (updateNotificationPanel != null) return;
            
            updateNotificationPanel = new Panel();
            updateNotificationPanel.BackColor = DiscordColors.Green;
            updateNotificationPanel.Height = 40;
            updateNotificationPanel.Dock = DockStyle.Top;
            
            var label = new Label();
            label.Text = "Update v" + newVersion + " is being installed automatically...";
            label.ForeColor = Color.Black;
            label.Font = new Font("Segoe UI", 10F, FontStyle.Bold);
            label.Location = new Point(20, 10);
            label.AutoSize = true;
            updateNotificationPanel.Controls.Add(label);
            
            Controls.Add(updateNotificationPanel);
            updateNotificationPanel.BringToFront();
            
            trayIcon.ShowBalloonTip(5000, "Update Available", 
                "ProxyAssessmentTool v" + newVersion + " is being installed automatically.", 
                ToolTipIcon.Info);
        }
        
        private void InitializeUI()
        {
            Text = "ProxyAssessmentTool v" + VERSION + " - Auto-Update Edition";
            Size = new Size(1400, 800);
            StartPosition = FormStartPosition.CenterScreen;
            BackColor = DiscordColors.Background;
            Icon = CreateIcon();
            
            // Side panel (Discord-style)
            sidePanel = new Panel();
            sidePanel.BackColor = DiscordColors.DarkestBackground;
            sidePanel.Width = 240;
            sidePanel.Dock = DockStyle.Left;
            
            // Logo/Title
            var logoPanel = new Panel();
            logoPanel.Height = 52;
            logoPanel.BackColor = DiscordColors.DarkestBackground;
            logoPanel.Dock = DockStyle.Top;
            
            var titleLabel = new Label();
            titleLabel.Text = "PROXY SCANNER PRO";
            titleLabel.Font = new Font("Segoe UI", 12F, FontStyle.Bold);
            titleLabel.ForeColor = DiscordColors.TextNormal;
            titleLabel.Location = new Point(16, 16);
            titleLabel.AutoSize = true;
            logoPanel.Controls.Add(titleLabel);
            
            sidePanel.Controls.Add(logoPanel);
            
            // Menu items
            AddMenuItem(sidePanel, "Dashboard", 60, true, 0);
            AddMenuItem(sidePanel, "Eligible Proxies", 100, false, 1);
            AddMenuItem(sidePanel, "Analytics", 140, false, 2);
            AddMenuItem(sidePanel, "Logs", 180, false, 3);
            AddMenuItem(sidePanel, "Settings", 220, false, 4);
            
            // Control buttons at bottom
            pauseButton = new ModernButton();
            pauseButton.Text = "Pause Scanning";
            pauseButton.Size = new Size(208, 36);
            pauseButton.Location = new Point(16, sidePanel.Height - 140);
            pauseButton.Click += OnPauseClick;
            sidePanel.Controls.Add(pauseButton);
            
            exportButton = new ModernButton();
            exportButton.Text = "Export Eligible";
            exportButton.Size = new Size(208, 36);
            exportButton.Location = new Point(16, sidePanel.Height - 90);
            exportButton.Click += OnExportClick;
            sidePanel.Controls.Add(exportButton);
            
            Controls.Add(sidePanel);
            
            // Content panel with tabs
            contentPanel = new Panel();
            contentPanel.BackColor = DiscordColors.Background;
            contentPanel.Dock = DockStyle.Fill;
            
            tabControl = new TabControl();
            tabControl.Dock = DockStyle.Fill;
            tabControl.Appearance = TabAppearance.FlatButtons;
            tabControl.ItemSize = new Size(0, 1);
            tabControl.SizeMode = TabSizeMode.Fixed;
            
            // Dashboard tab
            var dashboardTab = new TabPage();
            dashboardTab.BackColor = DiscordColors.Background;
            InitializeDashboard(dashboardTab);
            tabControl.TabPages.Add(dashboardTab);
            
            // Eligible proxies tab
            var eligibleTab = new TabPage();
            eligibleTab.BackColor = DiscordColors.Background;
            InitializeEligibleTab(eligibleTab);
            tabControl.TabPages.Add(eligibleTab);
            
            // Analytics tab
            var analyticsTab = new TabPage();
            analyticsTab.BackColor = DiscordColors.Background;
            InitializeAnalyticsTab(analyticsTab);
            tabControl.TabPages.Add(analyticsTab);
            
            // Logs tab
            var logsTab = new TabPage();
            logsTab.BackColor = DiscordColors.Background;
            InitializeLogsTab(logsTab);
            tabControl.TabPages.Add(logsTab);
            
            // Settings tab
            var settingsTab = new TabPage();
            settingsTab.BackColor = DiscordColors.Background;
            InitializeSettingsTab(settingsTab);
            tabControl.TabPages.Add(settingsTab);
            
            contentPanel.Controls.Add(tabControl);
            Controls.Add(contentPanel);
            
            // Status bar
            var statusBar = new Panel();
            statusBar.Height = 22;
            statusBar.BackColor = DiscordColors.DarkestBackground;
            statusBar.Dock = DockStyle.Bottom;
            
            statusLabel = new Label();
            statusLabel.Text = "Ready - v" + VERSION + " (Auto-Update Enabled)";
            statusLabel.ForeColor = DiscordColors.TextMuted;
            statusLabel.Font = new Font("Segoe UI", 9F);
            statusLabel.Location = new Point(10, 3);
            statusLabel.AutoSize = true;
            statusBar.Controls.Add(statusLabel);
            
            var memoryLabel = new Label();
            memoryLabel.Text = "Memory: " + (GC.GetTotalMemory(false) / 1024 / 1024) + " MB";
            memoryLabel.ForeColor = DiscordColors.TextMuted;
            memoryLabel.Font = new Font("Segoe UI", 9F);
            memoryLabel.Location = new Point(statusBar.Width - 150, 3);
            memoryLabel.AutoSize = true;
            statusBar.Controls.Add(memoryLabel);
            
            Controls.Add(statusBar);
            
            // Animation timer
            animationTimer = new System.Windows.Forms.Timer();
            animationTimer.Interval = 500;
            animationTimer.Tick += AnimateScanningLabel;
            animationTimer.Start();
            
            // Auto-export timer (every 5 minutes)
            autoExportTimer = new System.Windows.Forms.Timer();
            autoExportTimer.Interval = 300000;
            autoExportTimer.Tick += (s, e) => AutoExportEligible();
            autoExportTimer.Start();
            
            // Memory cleanup timer
            var gcTimer = new System.Windows.Forms.Timer();
            gcTimer.Interval = 60000;
            gcTimer.Tick += (s, e) => {
                GC.Collect();
                GC.WaitForPendingFinalizers();
                GC.Collect();
                memoryLabel.Text = "Memory: " + (GC.GetTotalMemory(false) / 1024 / 1024) + " MB";
            };
            gcTimer.Start();
        }
        
        private void InitializeDashboard(TabPage tab)
        {
            // Header
            var headerLabel = new Label();
            headerLabel.Text = "Automatic Proxy Scanner";
            headerLabel.Font = new Font("Segoe UI", 24F, FontStyle.Bold);
            headerLabel.ForeColor = DiscordColors.TextNormal;
            headerLabel.Location = new Point(40, 20);
            headerLabel.AutoSize = true;
            tab.Controls.Add(headerLabel);
            
            var subLabel = new Label();
            subLabel.Text = "Professional-grade proxy discovery and validation";
            subLabel.Font = new Font("Segoe UI", 11F);
            subLabel.ForeColor = DiscordColors.TextMuted;
            subLabel.Location = new Point(40, 55);
            subLabel.AutoSize = true;
            tab.Controls.Add(subLabel);
            
            // Stats cards
            var statsPanel = new FlowLayoutPanel();
            statsPanel.Location = new Point(40, 100);
            statsPanel.Size = new Size(1060, 130);
            statsPanel.AutoScroll = false;
            
            AddStatCard(statsPanel, "PROXIES FOUND", "0", DiscordColors.Blurple);
            AddStatCard(statsPanel, "ELIGIBLE", "0", DiscordColors.Green);
            AddStatCard(statsPanel, "SUCCESS RATE", "0%", DiscordColors.Yellow);
            AddStatCard(statsPanel, "SCANNING", "ACTIVE", DiscordColors.StreamingPurple);
            
            tab.Controls.Add(statsPanel);
            
            // Scanning status
            scanningLabel = new Label();
            scanningLabel.Text = "Initializing scanner...";
            scanningLabel.Font = new Font("Segoe UI", 10F);
            scanningLabel.ForeColor = DiscordColors.Yellow;
            scanningLabel.Location = new Point(40, 250);
            scanningLabel.AutoSize = true;
            tab.Controls.Add(scanningLabel);
            
            scanProgress = new ProgressBar();
            scanProgress.Location = new Point(40, 280);
            scanProgress.Size = new Size(1060, 6);
            scanProgress.Style = ProgressBarStyle.Marquee;
            tab.Controls.Add(scanProgress);
            
            // Found proxies container
            var proxyLabel = new Label();
            proxyLabel.Text = "Live Discoveries";
            proxyLabel.Font = new Font("Segoe UI", 14F, FontStyle.Bold);
            proxyLabel.ForeColor = DiscordColors.TextNormal;
            proxyLabel.Location = new Point(40, 310);
            proxyLabel.AutoSize = true;
            tab.Controls.Add(proxyLabel);
            
            foundCountLabel = new Label();
            foundCountLabel.Text = "0 proxies discovered";
            foundCountLabel.Font = new Font("Segoe UI", 9F);
            foundCountLabel.ForeColor = DiscordColors.TextMuted;
            foundCountLabel.Location = new Point(180, 316);
            foundCountLabel.AutoSize = true;
            tab.Controls.Add(foundCountLabel);
            
            var clearButton = new ModernButton();
            clearButton.Text = "Clear";
            clearButton.Size = new Size(60, 24);
            clearButton.Location = new Point(1040, 310);
            clearButton.Font = new Font("Segoe UI", 8F);
            clearButton.Click += (s, e) => {
                proxyContainer.Controls.Clear();
                allProxies.Clear();
            };
            tab.Controls.Add(clearButton);
            
            proxyContainer = new FlowLayoutPanel();
            proxyContainer.Location = new Point(40, 350);
            proxyContainer.Size = new Size(1060, 330);
            proxyContainer.AutoScroll = true;
            proxyContainer.BackColor = DiscordColors.DarkerBackground;
            proxyContainer.Padding = new Padding(10);
            tab.Controls.Add(proxyContainer);
        }
        
        private void InitializeEligibleTab(TabPage tab)
        {
            var headerLabel = new Label();
            headerLabel.Text = "Eligible Proxies";
            headerLabel.Font = new Font("Segoe UI", 24F, FontStyle.Bold);
            headerLabel.ForeColor = DiscordColors.TextNormal;
            headerLabel.Location = new Point(40, 20);
            headerLabel.AutoSize = true;
            tab.Controls.Add(headerLabel);
            
            eligibleCountLabel = new Label();
            eligibleCountLabel.Text = "0 eligible proxies found";
            eligibleCountLabel.Font = new Font("Segoe UI", 11F);
            eligibleCountLabel.ForeColor = DiscordColors.TextMuted;
            eligibleCountLabel.Location = new Point(40, 55);
            eligibleCountLabel.AutoSize = true;
            tab.Controls.Add(eligibleCountLabel);
            
            var exportAllButton = new ModernButton();
            exportAllButton.Text = "Export All";
            exportAllButton.Size = new Size(100, 32);
            exportAllButton.Location = new Point(1000, 45);
            exportAllButton.Click += OnExportClick;
            tab.Controls.Add(exportAllButton);
            
            eligibleContainer = new FlowLayoutPanel();
            eligibleContainer.Location = new Point(40, 100);
            eligibleContainer.Size = new Size(1060, 580);
            eligibleContainer.AutoScroll = true;
            eligibleContainer.BackColor = DiscordColors.DarkerBackground;
            eligibleContainer.Padding = new Padding(10);
            tab.Controls.Add(eligibleContainer);
        }
        
        private void InitializeAnalyticsTab(TabPage tab)
        {
            var headerLabel = new Label();
            headerLabel.Text = "Analytics Dashboard";
            headerLabel.Font = new Font("Segoe UI", 24F, FontStyle.Bold);
            headerLabel.ForeColor = DiscordColors.TextNormal;
            headerLabel.Location = new Point(40, 20);
            headerLabel.AutoSize = true;
            tab.Controls.Add(headerLabel);
            
            // Analytics content
            var analyticsPanel = new FlowLayoutPanel();
            analyticsPanel.Location = new Point(40, 80);
            analyticsPanel.Size = new Size(1060, 600);
            analyticsPanel.AutoScroll = true;
            
            // Placeholder for analytics
            var placeholderLabel = new Label();
            placeholderLabel.Text = "Analytics data will appear here...";
            placeholderLabel.Font = new Font("Segoe UI", 12F);
            placeholderLabel.ForeColor = DiscordColors.TextMuted;
            placeholderLabel.AutoSize = true;
            analyticsPanel.Controls.Add(placeholderLabel);
            
            tab.Controls.Add(analyticsPanel);
        }
        
        private void InitializeLogsTab(TabPage tab)
        {
            var headerLabel = new Label();
            headerLabel.Text = "System Logs";
            headerLabel.Font = new Font("Segoe UI", 24F, FontStyle.Bold);
            headerLabel.ForeColor = DiscordColors.TextNormal;
            headerLabel.Location = new Point(40, 20);
            headerLabel.AutoSize = true;
            tab.Controls.Add(headerLabel);
            
            autoScrollCheckBox = new CheckBox();
            autoScrollCheckBox.Text = "Auto-scroll";
            autoScrollCheckBox.Checked = true;
            autoScrollCheckBox.ForeColor = DiscordColors.TextMuted;
            autoScrollCheckBox.Location = new Point(1000, 25);
            autoScrollCheckBox.AutoSize = true;
            tab.Controls.Add(autoScrollCheckBox);
            
            logBox = new RichTextBox();
            logBox.BackColor = DiscordColors.DarkestBackground;
            logBox.ForeColor = DiscordColors.TextNormal;
            logBox.Font = new Font("Consolas", 9F);
            logBox.BorderStyle = BorderStyle.None;
            logBox.ReadOnly = true;
            logBox.Location = new Point(40, 60);
            logBox.Size = new Size(1060, 620);
            tab.Controls.Add(logBox);
        }
        
        private void InitializeSettingsTab(TabPage tab)
        {
            var headerLabel = new Label();
            headerLabel.Text = "Settings";
            headerLabel.Font = new Font("Segoe UI", 24F, FontStyle.Bold);
            headerLabel.ForeColor = DiscordColors.TextNormal;
            headerLabel.Location = new Point(40, 20);
            headerLabel.AutoSize = true;
            tab.Controls.Add(headerLabel);
            
            // Version info
            var versionLabel = new Label();
            versionLabel.Text = "Version: " + VERSION + " (Auto-Update Enabled)";
            versionLabel.Font = new Font("Segoe UI", 10F);
            versionLabel.ForeColor = DiscordColors.Green;
            versionLabel.Location = new Point(40, 60);
            versionLabel.AutoSize = true;
            tab.Controls.Add(versionLabel);
            
            // Settings content
            var settingsPanel = new Panel();
            settingsPanel.Location = new Point(40, 100);
            settingsPanel.Size = new Size(500, 400);
            
            var autoUpdateLabel = new Label();
            autoUpdateLabel.Text = "Automatic updates are enabled and check every minute.";
            autoUpdateLabel.Font = new Font("Segoe UI", 10F);
            autoUpdateLabel.ForeColor = DiscordColors.TextNormal;
            autoUpdateLabel.Location = new Point(0, 20);
            autoUpdateLabel.AutoSize = true;
            settingsPanel.Controls.Add(autoUpdateLabel);
            
            tab.Controls.Add(settingsPanel);
        }
        
        private void AddMenuItem(Panel parent, string text, int y, bool selected, int tabIndex)
        {
            var item = new Panel();
            item.Size = new Size(224, 32);
            item.Location = new Point(8, y);
            item.BackColor = selected ? DiscordColors.ChannelBar : Color.Transparent;
            item.Cursor = Cursors.Hand;
            item.Tag = tabIndex;
            
            var label = new Label();
            label.Text = text;
            label.Font = new Font("Segoe UI", 10F);
            label.ForeColor = selected ? DiscordColors.TextNormal : DiscordColors.TextMuted;
            label.Location = new Point(12, 6);
            label.AutoSize = true;
            
            item.Controls.Add(label);
            parent.Controls.Add(item);
            
            item.Click += (s, e) => {
                foreach (Control c in parent.Controls)
                {
                    if (c is Panel p && p.Tag is int)
                    {
                        p.BackColor = Color.Transparent;
                        if (p.Controls.Count > 0 && p.Controls[0] is Label l)
                            l.ForeColor = DiscordColors.TextMuted;
                    }
                }
                item.BackColor = DiscordColors.ChannelBar;
                label.ForeColor = DiscordColors.TextNormal;
                tabControl.SelectedIndex = tabIndex;
            };
            
            label.Click += (s, e) => item.OnClick(e);
            
            item.MouseEnter += (s, e) => {
                if (item.BackColor != DiscordColors.ChannelBar)
                    item.BackColor = DiscordColors.DarkerBackground;
            };
            item.MouseLeave += (s, e) => {
                if (tabControl.SelectedIndex != tabIndex)
                    item.BackColor = Color.Transparent;
            };
        }
        
        private void AddStatCard(FlowLayoutPanel parent, string title, string value, Color color)
        {
            var card = new ProxyCard();
            card.Size = new Size(250, 100);
            card.Margin = new Padding(0, 0, 15, 0);
            
            var titleLabel = new Label();
            titleLabel.Text = title;
            titleLabel.Font = new Font("Segoe UI", 9F);
            titleLabel.ForeColor = DiscordColors.TextMuted;
            titleLabel.Location = new Point(16, 16);
            titleLabel.AutoSize = true;
            card.Controls.Add(titleLabel);
            
            var valueLabel = new Label();
            valueLabel.Text = value;
            valueLabel.Font = new Font("Segoe UI", 24F, FontStyle.Bold);
            valueLabel.ForeColor = color;
            valueLabel.Location = new Point(16, 35);
            valueLabel.AutoSize = true;
            valueLabel.Name = title;
            card.Controls.Add(valueLabel);
            
            parent.Controls.Add(card);
        }
        
        private void AnimateScanningLabel(object sender, EventArgs e)
        {
            if (isPaused) return;
            
            string[] frames = { "Lightning", "Globe", "Satellite", "Magnifying", "Sparkles", "Rocket" };
            animationStep = (animationStep + 1) % frames.Length;
            scanningLabel.Text = frames[animationStep] + " Scanning " + proxySources.Length + " sources...";
        }
        
        private void OnPauseClick(object sender, EventArgs e)
        {
            isPaused = !isPaused;
            pauseButton.Text = isPaused ? "Resume Scanning" : "Pause Scanning";
            scanProgress.Style = isPaused ? ProgressBarStyle.Blocks : ProgressBarStyle.Marquee;
            Log(isPaused ? "Scanning paused" : "Scanning resumed", DiscordColors.Yellow);
        }
        
        private void OnExportClick(object sender, EventArgs e)
        {
            try
            {
                var timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
                var filename = "eligible_proxies_" + timestamp + ".txt";
                
                var content = new StringBuilder();
                content.AppendLine("# ProxyAssessmentTool Export - " + DateTime.Now);
                content.AppendLine("# Eligible SOCKS5 Proxies (US Mobile Only)");
                content.AppendLine("# Format: IP:Port | Location | Carrier | Response Time");
                content.AppendLine();
                
                foreach (var proxy in eligibleProxies.Values.OrderBy(p => p.Country).ThenBy(p => p.City))
                {
                    content.AppendLine(string.Format("{0}:{1} | {2}, {3} | {4} | {5}ms",
                        proxy.IP, proxy.Port, proxy.City, proxy.Country, 
                        proxy.Carrier, proxy.ResponseTimeMs));
                }
                
                File.WriteAllText(filename, content.ToString());
                
                MessageBox.Show("Exported " + eligibleProxies.Count + " eligible proxies to:\n" + filename,
                    "Export Successful", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    
                Log("Exported " + eligibleProxies.Count + " proxies to " + filename, DiscordColors.Green);
            }
            catch (Exception ex)
            {
                MessageBox.Show("Export failed: " + ex.Message, "Error", 
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
                Log("Export error: " + ex.Message, DiscordColors.Red);
            }
        }
        
        private void AutoExportEligible()
        {
            if (eligibleProxies.Count == 0) return;
            
            try
            {
                var autoExportDir = Path.Combine(Environment.CurrentDirectory, "AutoExports");
                Directory.CreateDirectory(autoExportDir);
                
                var timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
                var filename = Path.Combine(autoExportDir, "auto_export_" + timestamp + ".txt");
                
                var content = string.Join(Environment.NewLine,
                    eligibleProxies.Values.Select(p => p.IP + ":" + p.Port));
                
                File.WriteAllText(filename, content);
                Log("Auto-exported " + eligibleProxies.Count + " proxies", DiscordColors.Green);
            }
            catch (Exception ex)
            {
                Log("Auto-export error: " + ex.Message, DiscordColors.Red);
            }
        }
        
        private void Log(string message, Color color)
        {
            if (logBox == null) return;
            
            BeginInvoke(new Action(() => {
                var timestamp = DateTime.Now.ToString("HH:mm:ss");
                logBox.SelectionStart = logBox.TextLength;
                logBox.SelectionLength = 0;
                logBox.SelectionColor = DiscordColors.TextMuted;
                logBox.AppendText("[" + timestamp + "] ");
                logBox.SelectionColor = color;
                logBox.AppendText(message + Environment.NewLine);
                
                if (autoScrollCheckBox.Checked)
                {
                    logBox.ScrollToCaret();
                }
            }));
        }
        
        private async void StartAutoScan()
        {
            scanCancellation = new CancellationTokenSource();
            await Task.Run(() => ScanProxiesAsync(scanCancellation.Token));
        }
        
        private async Task ScanProxiesAsync(CancellationToken cancellationToken)
        {
            var scanCount = 0;
            var startTime = DateTime.Now;
            
            while (!cancellationToken.IsCancellationRequested)
            {
                if (isPaused)
                {
                    await Task.Delay(1000, cancellationToken);
                    continue;
                }
                
                try
                {
                    var cycleStart = DateTime.Now;
                    var discoveredProxies = new HashSet<string>();
                    
                    // Parallel source fetching
                    var fetchTasks = proxySources.Select(async source => {
                        try
                        {
                            using (var client = new WebClient())
                            {
                                client.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");
                                client.Proxy = null;
                                var data = await client.DownloadStringTaskAsync(source);
                                
                                var matches = Regex.Matches(data, @"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{1,5}\b");
                                var found = matches.Cast<Match>().Select(m => m.Value).ToList();
                                
                                lock (discoveredProxies)
                                {
                                    foreach (var proxy in found)
                                        discoveredProxies.Add(proxy);
                                }
                                
                                Log("Fetched " + found.Count + " from " + new Uri(source).Host, DiscordColors.TextMuted);
                            }
                        }
                        catch (Exception ex)
                        {
                            Log("Source error (" + new Uri(source).Host + "): " + ex.Message, DiscordColors.Yellow);
                        }
                    }).ToArray();
                    
                    await Task.WhenAll(fetchTasks);
                    
                    BeginInvoke(new Action(() => {
                        UpdateStatCard("PROXIES FOUND", allProxies.Count.ToString());
                        foundCountLabel.Text = allProxies.Count + " proxies discovered";
                    }));
                    
                    var newProxies = discoveredProxies.Where(p => !allProxies.ContainsKey(p)).ToList();
                    
                    if (newProxies.Count > 0)
                    {
                        Log("Testing " + newProxies.Count + " new proxies...", DiscordColors.Blurple);
                        
                        var testTasks = newProxies.Select(async proxy => {
                            await testSemaphore.WaitAsync();
                            try
                            {
                                var parts = proxy.Split(':');
                                if (parts.Length == 2 && int.TryParse(parts[1], out int port))
                                {
                                    var info = await TestProxyAsync(parts[0], port);
                                    if (info != null)
                                    {
                                        allProxies.TryAdd(proxy, info);
                                        
                                        BeginInvoke(new Action(() => {
                                            AddProxyToUI(info, proxyContainer);
                                            
                                            if (info.IsEligible)
                                            {
                                                eligibleProxies.TryAdd(proxy, info);
                                                AddProxyToUI(info, eligibleContainer);
                                                Log("Eligible: " + proxy + " (" + info.Carrier + ")", DiscordColors.Green);
                                            }
                                        }));
                                    }
                                }
                            }
                            finally
                            {
                                testSemaphore.Release();
                            }
                        }).ToArray();
                        
                        await Task.WhenAll(testTasks);
                    }
                    
                    var successRate = allProxies.Count > 0 ? 
                        (eligibleProxies.Count * 100.0 / allProxies.Count).ToString("F1") : "0";
                    
                    BeginInvoke(new Action(() => {
                        UpdateStatCard("ELIGIBLE", eligibleProxies.Count.ToString());
                        UpdateStatCard("SUCCESS RATE", successRate + "%");
                        eligibleCountLabel.Text = eligibleProxies.Count + " eligible proxies found";
                    }));
                    
                    scanCount++;
                    var runtime = DateTime.Now - startTime;
                    statusLabel.Text = string.Format("Scan #{0} | Runtime: {1:hh\\:mm\\:ss} | Found: {2} | Eligible: {3}",
                        scanCount, runtime, allProxies.Count, eligibleProxies.Count);
                    
                    await Task.Delay(60000, cancellationToken);
                }
                catch (Exception ex)
                {
                    Log("Scan cycle error: " + ex.Message, DiscordColors.Red);
                    await Task.Delay(5000, cancellationToken);
                }
            }
        }
        
        private async Task<ProxyInfo> TestProxyAsync(string ip, int port)
        {
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                using (var client = new TcpClient())
                {
                    client.ReceiveTimeout = 5000;
                    client.SendTimeout = 5000;
                    
                    var connectTask = client.ConnectAsync(ip, port);
                    if (await Task.WhenAny(connectTask, Task.Delay(5000)) != connectTask)
                        return null;
                    
                    if (!client.Connected)
                        return null;
                    
                    var stream = client.GetStream();
                    var greeting = new byte[] { 0x05, 0x01, 0x00 };
                    await stream.WriteAsync(greeting, 0, greeting.Length);
                    
                    var response = new byte[2];
                    var read = await ReadExactAsync(stream, response, 0, 2);
                    
                    if (read != 2 || response[0] != 0x05 || response[1] != 0x00)
                        return null;
                    
                    stopwatch.Stop();
                    
                    var location = await GetLocationAsync(ip);
                    
                    var info = new ProxyInfo
                    {
                        IP = ip,
                        Port = port,
                        Country = location.Country,
                        City = location.City,
                        Carrier = location.ISP,
                        IsEligible = location.Country == "US" && location.IsMobile,
                        FraudScore = 0,
                        Protocol = "SOCKS5",
                        ResponseTime = DateTime.Now,
                        ResponseTimeMs = (int)stopwatch.ElapsedMilliseconds
                    };
                    
                    return info;
                }
            }
            catch
            {
                return null;
            }
        }
        
        private async Task<int> ReadExactAsync(NetworkStream stream, byte[] buffer, int offset, int count)
        {
            int totalRead = 0;
            while (totalRead < count)
            {
                var read = await stream.ReadAsync(buffer, offset + totalRead, count - totalRead);
                if (read == 0) break;
                totalRead += read;
            }
            return totalRead;
        }
        
        private async Task<LocationInfo> GetLocationAsync(string ip)
        {
            try
            {
                using (var client = new WebClient())
                {
                    client.Headers.Add("User-Agent", "ProxyAssessmentTool/2.2");
                    var json = await client.DownloadStringTaskAsync("http://ip-api.com/json/" + ip + "?fields=status,country,city,isp,org,as");
                    
                    var country = ExtractJsonValue(json, "country");
                    var city = ExtractJsonValue(json, "city");
                    var isp = ExtractJsonValue(json, "isp");
                    var org = ExtractJsonValue(json, "org");
                    var asn = ExtractJsonValue(json, "as");
                    
                    var detectedCarrier = DetectCarrier(isp + " " + org + " " + asn);
                    
                    return new LocationInfo
                    {
                        Country = country.Contains("United States") ? "US" : country.Substring(0, Math.Min(2, country.Length)).ToUpper(),
                        City = city,
                        ISP = detectedCarrier ?? isp,
                        IsMobile = detectedCarrier != null
                    };
                }
            }
            catch
            {
                return new LocationInfo { Country = "??", City = "Unknown", ISP = "Unknown", IsMobile = false };
            }
        }
        
        private string DetectCarrier(string text)
        {
            var lowerText = text.ToLower();
            
            foreach (var carrier in carrierPatterns)
            {
                if (carrier.Value.Any(pattern => lowerText.Contains(pattern)))
                {
                    return carrier.Key;
                }
            }
            
            if (lowerText.Contains("mobile") || lowerText.Contains("wireless") || 
                lowerText.Contains("cellular") || lowerText.Contains("4g") || lowerText.Contains("5g"))
            {
                return "Mobile Network";
            }
            
            return null;
        }
        
        private string ExtractJsonValue(string json, string key)
        {
            var pattern = "\"" + key + "\":\"([^\"]+)\"";
            var match = Regex.Match(json, pattern);
            return match.Success ? match.Groups[1].Value : "Unknown";
        }
        
        private void AddProxyToUI(ProxyInfo proxy, FlowLayoutPanel container)
        {
            var card = new ProxyCard();
            card.ProxyInfo = proxy;
            card.Size = new Size(250, 140);
            card.Margin = new Padding(5);
            
            var ipLabel = new Label();
            ipLabel.Text = proxy.IP + ":" + proxy.Port;
            ipLabel.Font = new Font("Consolas", 10F, FontStyle.Bold);
            ipLabel.ForeColor = DiscordColors.TextNormal;
            ipLabel.Location = new Point(16, 16);
            ipLabel.AutoSize = true;
            card.Controls.Add(ipLabel);
            
            var statusDot = new Label();
            statusDot.Text = "O";
            statusDot.Font = new Font("Segoe UI", 10F);
            statusDot.ForeColor = proxy.IsEligible ? DiscordColors.Green : DiscordColors.Red;
            statusDot.Location = new Point(16, 40);
            statusDot.AutoSize = true;
            card.Controls.Add(statusDot);
            
            var statusLabel = new Label();
            statusLabel.Text = proxy.IsEligible ? "Eligible" : "Ineligible";
            statusLabel.Font = new Font("Segoe UI", 9F);
            statusLabel.ForeColor = proxy.IsEligible ? DiscordColors.Green : DiscordColors.Red;
            statusLabel.Location = new Point(30, 41);
            statusLabel.AutoSize = true;
            card.Controls.Add(statusLabel);
            
            var locationLabel = new Label();
            locationLabel.Text = proxy.City + ", " + proxy.Country;
            locationLabel.Font = new Font("Segoe UI", 9F);
            locationLabel.ForeColor = DiscordColors.TextMuted;
            locationLabel.Location = new Point(16, 65);
            locationLabel.AutoSize = true;
            card.Controls.Add(locationLabel);
            
            var carrierLabel = new Label();
            carrierLabel.Text = proxy.Carrier;
            carrierLabel.Font = new Font("Segoe UI", 9F);
            carrierLabel.ForeColor = DiscordColors.TextMuted;
            carrierLabel.Location = new Point(16, 85);
            carrierLabel.Size = new Size(218, 20);
            carrierLabel.AutoEllipsis = true;
            card.Controls.Add(carrierLabel);
            
            var timeLabel = new Label();
            timeLabel.Text = proxy.ResponseTimeMs + "ms " + DateTime.Now.ToString("HH:mm");
            timeLabel.Font = new Font("Segoe UI", 8F);
            timeLabel.ForeColor = DiscordColors.TextMuted;
            timeLabel.Location = new Point(16, 110);
            timeLabel.AutoSize = true;
            card.Controls.Add(timeLabel);
            
            container.Controls.Add(card);
            
            if (container.Controls.Count > 100)
            {
                container.Controls.RemoveAt(0);
            }
        }
        
        private void UpdateStatCard(string title, string value)
        {
            foreach (Control control in tabControl.TabPages[0].Controls)
            {
                if (control is FlowLayoutPanel)
                {
                    foreach (Control card in control.Controls)
                    {
                        var label = card.Controls.Find(title, false).FirstOrDefault() as Label;
                        if (label != null)
                        {
                            label.Text = value;
                            break;
                        }
                    }
                }
            }
        }
        
        private Icon CreateIcon()
        {
            var bitmap = new Bitmap(32, 32);
            using (var g = Graphics.FromImage(bitmap))
            {
                g.SmoothingMode = SmoothingMode.AntiAlias;
                g.Clear(Color.Transparent);
                
                using (var brush = new LinearGradientBrush(
                    new Point(0, 0), new Point(32, 32),
                    DiscordColors.Blurple, DiscordColors.StreamingPurple))
                {
                    g.FillEllipse(brush, 2, 2, 28, 28);
                }
                
                using (var pen = new Pen(Color.White, 2))
                {
                    g.DrawLine(pen, 10, 16, 22, 16);
                    g.DrawLine(pen, 16, 10, 16, 22);
                }
            }
            return Icon.FromHandle(bitmap.GetHicon());
        }
        
        protected override void OnFormClosed(FormClosedEventArgs e)
        {
            scanCancellation?.Cancel();
            animationTimer?.Stop();
            autoExportTimer?.Stop();
            trayIcon?.Dispose();
            base.OnFormClosed(e);
        }
    }
    
    public class ProxyInfo
    {
        public string IP { get; set; }
        public int Port { get; set; }
        public string Country { get; set; }
        public string City { get; set; }
        public string Carrier { get; set; }
        public bool IsEligible { get; set; }
        public int FraudScore { get; set; }
        public string Protocol { get; set; }
        public DateTime ResponseTime { get; set; }
        public int ResponseTimeMs { get; set; }
    }
    
    public class LocationInfo
    {
        public string Country { get; set; }
        public string City { get; set; }
        public string ISP { get; set; }
        public bool IsMobile { get; set; }
    }
    
    public class Program
    {
        [STAThread]
        public static void Main()
        {
            ServicePointManager.DefaultConnectionLimit = 100;
            ServicePointManager.Expect100Continue = false;
            ServicePointManager.UseNagleAlgorithm = false;
            
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

    Write-Host "Compiling Auto-Update Edition..." -ForegroundColor Magenta
    
    & $cscPath /target:winexe /optimize+ /win32icon:"$iconPath" /reference:System.dll /reference:System.Drawing.dll /reference:System.Windows.Forms.dll /reference:System.Core.dll "/out:$OutputPath" "$sourceFile" 2>&1

    if ($LASTEXITCODE -eq 0 -and (Test-Path $OutputPath)) {
        Write-Host "`nSUCCESS! Built v2.2.0 Auto-Update Edition" -ForegroundColor Green
        Write-Host "File: $OutputPath" -ForegroundColor White
        Write-Host ""
        Write-Host "NEW FEATURES:" -ForegroundColor Cyan
        Write-Host "  [✓] Automatic update checking every minute" -ForegroundColor Gray
        Write-Host "  [✓] Silent background updates" -ForegroundColor Gray
        Write-Host "  [✓] Update notifications in app and system tray" -ForegroundColor Gray
        Write-Host "  [✓] Beautiful custom icon embedded" -ForegroundColor Gray
        Write-Host "  [✓] System tray integration" -ForegroundColor Gray
        Write-Host "  [✓] Fixed all special character encoding" -ForegroundColor Gray
        Write-Host ""
        Write-Host "AUTO-UPDATE MECHANISM:" -ForegroundColor Yellow
        Write-Host "  • Checks GitHub releases every 60 seconds" -ForegroundColor Gray
        Write-Host "  • Downloads and installs updates automatically" -ForegroundColor Gray
        Write-Host "  • Shows notification banner during update" -ForegroundColor Gray
        Write-Host "  • Restarts app with new version seamlessly" -ForegroundColor Gray
        Write-Host ""
        Write-Host "FROM NOW ON:" -ForegroundColor Magenta
        Write-Host "  • You never need to manually update again!" -ForegroundColor Gray
        Write-Host "  • Just push new releases to GitHub" -ForegroundColor Gray
        Write-Host "  • The app will update itself automatically" -ForegroundColor Gray
    }
    else {
        throw "Compilation failed"
    }
}
finally {
    Remove-Item -Path $buildDir -Recurse -Force -ErrorAction SilentlyContinue
}