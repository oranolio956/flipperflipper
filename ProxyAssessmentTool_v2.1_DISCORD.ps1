# ProxyAssessmentTool v2.1.0 - Discord UI with Auto Internet Scanning
param([string]$OutputPath = "ProxyAssessmentTool.exe")

$ErrorActionPreference = "Stop"
Write-Host "Building ProxyAssessmentTool v2.1.0 (Discord UI)..." -ForegroundColor Cyan

$buildDir = Join-Path $env:TEMP "PAT_Build_$(Get-Random)"
New-Item -ItemType Directory -Path $buildDir -Force | Out-Null

try {
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
using System.Threading.Tasks;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;

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

    public class ModernButton : Button
    {
        private bool isHovered = false;
        private Color normalColor;
        private Color hoverColor;
        
        public ModernButton()
        {
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.DoubleBuffer, true);
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
        public ProxyCard()
        {
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.DoubleBuffer, true);
            BackColor = DiscordColors.DarkestBackground;
            Size = new Size(280, 120);
            Padding = new Padding(16);
        }
        
        protected override void OnPaint(PaintEventArgs e)
        {
            e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            
            using (var path = GetRoundedRect(new Rectangle(0, 0, Width - 1, Height - 1), 8))
            {
                e.Graphics.FillPath(new SolidBrush(BackColor), path);
                e.Graphics.DrawPath(new Pen(DiscordColors.ChannelBar, 1), path);
            }
            
            base.OnPaint(e);
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
        private const string VERSION = "2.1.0";
        private Panel sidePanel;
        private Panel contentPanel;
        private Label statusLabel;
        private FlowLayoutPanel proxyContainer;
        private Label scanningLabel;
        private ProgressBar scanProgress;
        private Label foundCountLabel;
        private System.Windows.Forms.Timer animationTimer;
        private int animationStep = 0;
        private CancellationTokenSource scanCancellation;
        private List<ProxyInfo> foundProxies = new List<ProxyInfo>();
        
        // Proxy sources
        private readonly string[] proxySources = new string[]
        {
            "https://www.proxy-list.download/api/v1/get?type=socks5",
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
            "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt"
        };
        
        public MainForm()
        {
            InitializeUI();
            StartAutoScan();
        }
        
        private void InitializeUI()
        {
            Text = "ProxyAssessmentTool v" + VERSION + " - Discord Edition";
            Size = new Size(1280, 720);
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
            titleLabel.Text = "PROXY SCANNER";
            titleLabel.Font = new Font("Segoe UI", 12F, FontStyle.Bold);
            titleLabel.ForeColor = DiscordColors.TextNormal;
            titleLabel.Location = new Point(16, 16);
            titleLabel.AutoSize = true;
            logoPanel.Controls.Add(titleLabel);
            
            sidePanel.Controls.Add(logoPanel);
            
            // Menu items
            AddMenuItem(sidePanel, "🏠 Dashboard", 60, true);
            AddMenuItem(sidePanel, "🔍 Auto Scanner", 100, false);
            AddMenuItem(sidePanel, "✅ Eligible Proxies", 140, false);
            AddMenuItem(sidePanel, "⚙️ Settings", 180, false);
            
            Controls.Add(sidePanel);
            
            // Content panel
            contentPanel = new Panel();
            contentPanel.BackColor = DiscordColors.Background;
            contentPanel.Dock = DockStyle.Fill;
            contentPanel.Padding = new Padding(40);
            
            // Header
            var headerLabel = new Label();
            headerLabel.Text = "Automatic Proxy Scanner";
            headerLabel.Font = new Font("Segoe UI", 24F, FontStyle.Bold);
            headerLabel.ForeColor = DiscordColors.TextNormal;
            headerLabel.Location = new Point(40, 20);
            headerLabel.AutoSize = true;
            contentPanel.Controls.Add(headerLabel);
            
            var subLabel = new Label();
            subLabel.Text = "Scanning the internet for eligible SOCKS5 proxies";
            subLabel.Font = new Font("Segoe UI", 11F);
            subLabel.ForeColor = DiscordColors.TextMuted;
            subLabel.Location = new Point(40, 55);
            subLabel.AutoSize = true;
            contentPanel.Controls.Add(subLabel);
            
            // Stats cards
            var statsPanel = new FlowLayoutPanel();
            statsPanel.Location = new Point(40, 100);
            statsPanel.Size = new Size(900, 130);
            statsPanel.AutoScroll = false;
            
            AddStatCard(statsPanel, "PROXIES FOUND", "0", DiscordColors.Blurple);
            AddStatCard(statsPanel, "ELIGIBLE", "0", DiscordColors.Green);
            AddStatCard(statsPanel, "SCANNING", "ACTIVE", DiscordColors.Yellow);
            
            contentPanel.Controls.Add(statsPanel);
            
            // Scanning status
            scanningLabel = new Label();
            scanningLabel.Text = "⚡ Scanning proxy sources...";
            scanningLabel.Font = new Font("Segoe UI", 10F);
            scanningLabel.ForeColor = DiscordColors.Yellow;
            scanningLabel.Location = new Point(40, 250);
            scanningLabel.AutoSize = true;
            contentPanel.Controls.Add(scanningLabel);
            
            scanProgress = new ProgressBar();
            scanProgress.Location = new Point(40, 280);
            scanProgress.Size = new Size(900, 6);
            scanProgress.Style = ProgressBarStyle.Marquee;
            contentPanel.Controls.Add(scanProgress);
            
            // Found proxies container
            var proxyLabel = new Label();
            proxyLabel.Text = "Live Proxies";
            proxyLabel.Font = new Font("Segoe UI", 14F, FontStyle.Bold);
            proxyLabel.ForeColor = DiscordColors.TextNormal;
            proxyLabel.Location = new Point(40, 320);
            proxyLabel.AutoSize = true;
            contentPanel.Controls.Add(proxyLabel);
            
            foundCountLabel = new Label();
            foundCountLabel.Text = "0 proxies found";
            foundCountLabel.Font = new Font("Segoe UI", 9F);
            foundCountLabel.ForeColor = DiscordColors.TextMuted;
            foundCountLabel.Location = new Point(160, 326);
            foundCountLabel.AutoSize = true;
            contentPanel.Controls.Add(foundCountLabel);
            
            proxyContainer = new FlowLayoutPanel();
            proxyContainer.Location = new Point(40, 360);
            proxyContainer.Size = new Size(900, 280);
            proxyContainer.AutoScroll = true;
            proxyContainer.BackColor = DiscordColors.DarkerBackground;
            proxyContainer.Padding = new Padding(10);
            contentPanel.Controls.Add(proxyContainer);
            
            Controls.Add(contentPanel);
            
            // Status bar
            var statusBar = new Panel();
            statusBar.Height = 22;
            statusBar.BackColor = DiscordColors.DarkestBackground;
            statusBar.Dock = DockStyle.Bottom;
            
            statusLabel = new Label();
            statusLabel.Text = "Ready - v" + VERSION;
            statusLabel.ForeColor = DiscordColors.TextMuted;
            statusLabel.Font = new Font("Segoe UI", 9F);
            statusLabel.Location = new Point(10, 3);
            statusLabel.AutoSize = true;
            statusBar.Controls.Add(statusLabel);
            
            Controls.Add(statusBar);
            
            // Animation timer
            animationTimer = new System.Windows.Forms.Timer();
            animationTimer.Interval = 500;
            animationTimer.Tick += AnimateScanningLabel;
            animationTimer.Start();
        }
        
        private void AddMenuItem(Panel parent, string text, int y, bool selected)
        {
            var item = new Panel();
            item.Size = new Size(224, 32);
            item.Location = new Point(8, y);
            item.BackColor = selected ? DiscordColors.ChannelBar : Color.Transparent;
            item.Cursor = Cursors.Hand;
            
            var label = new Label();
            label.Text = text;
            label.Font = new Font("Segoe UI", 10F);
            label.ForeColor = selected ? DiscordColors.TextNormal : DiscordColors.TextMuted;
            label.Location = new Point(12, 6);
            label.AutoSize = true;
            
            item.Controls.Add(label);
            parent.Controls.Add(item);
            
            item.MouseEnter += (s, e) => {
                if (!selected) item.BackColor = DiscordColors.DarkerBackground;
            };
            item.MouseLeave += (s, e) => {
                if (!selected) item.BackColor = Color.Transparent;
            };
        }
        
        private void AddStatCard(FlowLayoutPanel parent, string title, string value, Color color)
        {
            var card = new ProxyCard();
            card.Size = new Size(280, 100);
            card.Margin = new Padding(0, 0, 20, 0);
            
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
            string[] frames = { "⚡", "🔄", "🌐", "📡" };
            animationStep = (animationStep + 1) % frames.Length;
            scanningLabel.Text = frames[animationStep] + " Scanning proxy sources...";
        }
        
        private async void StartAutoScan()
        {
            scanCancellation = new CancellationTokenSource();
            await Task.Run(() => ScanProxiesAsync(scanCancellation.Token));
        }
        
        private async Task ScanProxiesAsync(CancellationToken cancellationToken)
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                try
                {
                    // Fetch proxies from multiple sources
                    var allProxies = new HashSet<string>();
                    
                    foreach (var source in proxySources)
                    {
                        if (cancellationToken.IsCancellationRequested) break;
                        
                        try
                        {
                            using (var client = new WebClient())
                            {
                                client.Headers.Add("User-Agent", "ProxyAssessmentTool/2.1");
                                var data = await client.DownloadStringTaskAsync(source);
                                
                                // Extract IP:Port patterns
                                var matches = Regex.Matches(data, @"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{1,5}\b");
                                foreach (Match match in matches)
                                {
                                    allProxies.Add(match.Value);
                                }
                            }
                        }
                        catch { /* Ignore individual source failures */ }
                    }
                    
                    // Update UI with found count
                    BeginInvoke(new Action(() => {
                        UpdateStatCard("PROXIES FOUND", allProxies.Count.ToString());
                        foundCountLabel.Text = allProxies.Count + " proxies found";
                    }));
                    
                    // Test each proxy
                    int eligible = 0;
                    var tasks = allProxies.Select(proxy => Task.Run(async () =>
                    {
                        var parts = proxy.Split(':');
                        if (parts.Length == 2 && int.TryParse(parts[1], out int port))
                        {
                            var info = await TestProxyAsync(parts[0], port);
                            if (info != null && info.IsEligible)
                            {
                                Interlocked.Increment(ref eligible);
                                BeginInvoke(new Action(() => AddProxyToUI(info)));
                            }
                        }
                    })).ToArray();
                    
                    await Task.WhenAll(tasks);
                    
                    // Update eligible count
                    BeginInvoke(new Action(() => {
                        UpdateStatCard("ELIGIBLE", eligible.ToString());
                    }));
                    
                    // Wait before next scan cycle
                    await Task.Delay(60000, cancellationToken); // Scan every minute
                }
                catch (Exception ex)
                {
                    BeginInvoke(new Action(() => {
                        statusLabel.Text = "Scan error: " + ex.Message;
                    }));
                }
            }
        }
        
        private async Task<ProxyInfo> TestProxyAsync(string ip, int port)
        {
            try
            {
                // Basic SOCKS5 connectivity test
                using (var client = new TcpClient())
                {
                    var connectTask = client.ConnectAsync(ip, port);
                    if (await Task.WhenAny(connectTask, Task.Delay(3000)) != connectTask)
                        return null;
                    
                    if (!client.Connected)
                        return null;
                    
                    // Send SOCKS5 greeting
                    var stream = client.GetStream();
                    var greeting = new byte[] { 0x05, 0x01, 0x00 }; // SOCKS5, 1 method, no auth
                    await stream.WriteAsync(greeting, 0, greeting.Length);
                    
                    var response = new byte[2];
                    var read = await stream.ReadAsync(response, 0, 2);
                    
                    if (read == 2 && response[0] == 0x05 && response[1] == 0x00)
                    {
                        // Get location info (simplified - in production use proper geolocation API)
                        var location = await GetLocationAsync(ip);
                        
                        return new ProxyInfo
                        {
                            IP = ip,
                            Port = port,
                            Country = location.Country,
                            City = location.City,
                            Carrier = location.ISP,
                            IsEligible = location.Country == "US" && location.IsMobile,
                            FraudScore = 0, // Would need real fraud detection API
                            Protocol = "SOCKS5",
                            ResponseTime = DateTime.Now
                        };
                    }
                }
            }
            catch { }
            
            return null;
        }
        
        private async Task<LocationInfo> GetLocationAsync(string ip)
        {
            // Simplified - in production use proper IP geolocation service
            try
            {
                using (var client = new WebClient())
                {
                    var json = await client.DownloadStringTaskAsync("http://ip-api.com/json/" + ip);
                    
                    // Basic parsing
                    var country = ExtractJsonValue(json, "country");
                    var city = ExtractJsonValue(json, "city");
                    var isp = ExtractJsonValue(json, "isp");
                    
                    return new LocationInfo
                    {
                        Country = country.Contains("United States") ? "US" : country,
                        City = city,
                        ISP = isp,
                        IsMobile = isp.Contains("Mobile") || isp.Contains("Wireless") || 
                                  isp.Contains("Cellular") || isp.Contains("Verizon") || 
                                  isp.Contains("AT&T") || isp.Contains("T-Mobile")
                    };
                }
            }
            catch
            {
                return new LocationInfo { Country = "Unknown", City = "Unknown", ISP = "Unknown" };
            }
        }
        
        private string ExtractJsonValue(string json, string key)
        {
            var pattern = "\"" + key + "\":\"([^\"]+)\"";
            var match = Regex.Match(json, pattern);
            return match.Success ? match.Groups[1].Value : "Unknown";
        }
        
        private void AddProxyToUI(ProxyInfo proxy)
        {
            var card = new ProxyCard();
            card.Size = new Size(280, 140);
            card.Margin = new Padding(5);
            
            var ipLabel = new Label();
            ipLabel.Text = proxy.IP + ":" + proxy.Port;
            ipLabel.Font = new Font("Consolas", 11F, FontStyle.Bold);
            ipLabel.ForeColor = DiscordColors.TextNormal;
            ipLabel.Location = new Point(16, 16);
            ipLabel.AutoSize = true;
            card.Controls.Add(ipLabel);
            
            var statusDot = new Label();
            statusDot.Text = "●";
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
            carrierLabel.Size = new Size(248, 20);
            carrierLabel.AutoEllipsis = true;
            card.Controls.Add(carrierLabel);
            
            var timeLabel = new Label();
            timeLabel.Text = "Found " + DateTime.Now.ToString("HH:mm:ss");
            timeLabel.Font = new Font("Segoe UI", 8F);
            timeLabel.ForeColor = DiscordColors.TextMuted;
            timeLabel.Location = new Point(16, 110);
            timeLabel.AutoSize = true;
            card.Controls.Add(timeLabel);
            
            proxyContainer.Controls.Add(card);
            
            // Keep only recent proxies (max 50)
            if (proxyContainer.Controls.Count > 50)
            {
                proxyContainer.Controls.RemoveAt(0);
            }
        }
        
        private void UpdateStatCard(string title, string value)
        {
            foreach (Control control in contentPanel.Controls)
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
                
                using (var brush = new SolidBrush(DiscordColors.Blurple))
                {
                    g.FillEllipse(brush, 2, 2, 28, 28);
                }
                
                using (var pen = new Pen(Color.White, 3))
                {
                    g.DrawArc(pen, 8, 8, 16, 16, 0, 360);
                }
            }
            return Icon.FromHandle(bitmap.GetHicon());
        }
        
        protected override void OnFormClosed(FormClosedEventArgs e)
        {
            scanCancellation?.Cancel();
            animationTimer?.Stop();
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

    Write-Host "Compiling Discord-style UI..." -ForegroundColor Magenta
    
    & $cscPath /target:winexe /optimize+ /reference:System.dll /reference:System.Drawing.dll /reference:System.Windows.Forms.dll /reference:System.Core.dll "/out:$OutputPath" "$sourceFile" 2>&1

    if ($LASTEXITCODE -eq 0 -and (Test-Path $OutputPath)) {
        Write-Host "`n✨ SUCCESS! Built v2.1.0 with Discord UI" -ForegroundColor Green
        Write-Host "📁 File: $OutputPath" -ForegroundColor White
        Write-Host ""
        Write-Host "Features:" -ForegroundColor Cyan
        Write-Host "  ✓ Beautiful Discord-inspired dark UI" -ForegroundColor Gray
        Write-Host "  ✓ Automatic internet proxy scanning" -ForegroundColor Gray
        Write-Host "  ✓ Real-time proxy discovery from 5 sources" -ForegroundColor Gray
        Write-Host "  ✓ Automatic eligibility checking" -ForegroundColor Gray
        Write-Host "  ✓ Live proxy cards with status" -ForegroundColor Gray
        Write-Host "  ✓ No manual input required!" -ForegroundColor Gray
        Write-Host ""
        Write-Host "The app will automatically:" -ForegroundColor Yellow
        Write-Host "  • Scan the internet for SOCKS5 proxies" -ForegroundColor Gray
        Write-Host "  • Test each proxy for connectivity" -ForegroundColor Gray
        Write-Host "  • Check location and carrier info" -ForegroundColor Gray
        Write-Host "  • Display eligible US mobile proxies" -ForegroundColor Gray
    }
    else {
        throw "Compilation failed"
    }
}
finally {
    Remove-Item -Path $buildDir -Recurse -Force -ErrorAction SilentlyContinue
}