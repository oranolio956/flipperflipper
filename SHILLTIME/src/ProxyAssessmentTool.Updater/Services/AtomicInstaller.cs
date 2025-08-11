using System;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using ProxyAssessmentTool.Updater.Models;

namespace ProxyAssessmentTool.Updater.Services
{
    public class AtomicInstaller
    {
        private readonly string _baseDirectory;
        private readonly IProgress<InstallProgress> _progress;
        
        public AtomicInstaller(IProgress<InstallProgress> progress)
        {
            _baseDirectory = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "ProxyAssessmentTool");
            _progress = progress;
        }

        public async Task<InstallResult> InstallUpdateAsync(string packagePath, UpdateManifest manifest)
        {
            var version = Version.Parse(manifest.Version);
            var versionDir = Path.Combine(_baseDirectory, $"app-{version}");
            var tempDir = Path.Combine(_baseDirectory, $"temp-{Guid.NewGuid()}");
            
            try
            {
                _progress.Report(new InstallProgress("Preparing installation...", 0));
                
                // Step 1: Extract to temp directory
                Directory.CreateDirectory(tempDir);
                await ExtractPackageAsync(packagePath, tempDir, manifest);
                
                // Step 2: Stop running application
                _progress.Report(new InstallProgress("Stopping application...", 30));
                await StopApplicationAsync();
                
                // Step 3: Atomic move
                _progress.Report(new InstallProgress("Installing files...", 60));
                
                if (Directory.Exists(versionDir))
                {
                    // Version already exists - move to backup
                    var backupDir = $"{versionDir}.backup-{DateTime.Now:yyyyMMddHHmmss}";
                    Directory.Move(versionDir, backupDir);
                }
                
                Directory.Move(tempDir, versionDir);
                
                // Step 4: Update symlink/launcher
                _progress.Report(new InstallProgress("Updating launcher...", 80));
                await UpdateLauncherAsync(version);
                
                // Step 5: Update history
                _progress.Report(new InstallProgress("Finalizing...", 90));
                await UpdateHistoryAsync(manifest, true);
                
                _progress.Report(new InstallProgress("Installation complete!", 100));
                return InstallResult.Success(versionDir);
            }
            catch (Exception ex)
            {
                // Rollback
                if (Directory.Exists(tempDir))
                    Directory.Delete(tempDir, true);
                
                await UpdateHistoryAsync(manifest, false, ex.Message);
                return InstallResult.Failure(ex.Message);
            }
        }

        private async Task ExtractPackageAsync(string packagePath, string targetDir, UpdateManifest manifest)
        {
            await Task.Run(() =>
            {
                using var archive = System.IO.Compression.ZipFile.OpenRead(packagePath);
                
                foreach (var file in manifest.Files)
                {
                    var entry = archive.GetEntry(file.Path);
                    if (entry == null) continue;
                    
                    var targetPath = Path.Combine(targetDir, file.Path);
                    Directory.CreateDirectory(Path.GetDirectoryName(targetPath)!);
                    
                    entry.ExtractToFile(targetPath, true);
                    
                    if (file.Executable && OperatingSystem.IsWindows())
                    {
                        // File is already executable on Windows
                    }
                }
            });
        }

        private async Task StopApplicationAsync()
        {
            var processes = Process.GetProcessesByName("ProxyAssessmentTool");
            if (processes.Length == 0) return;
            
            // Try graceful shutdown first
            foreach (var process in processes)
            {
                try
                {
                    process.CloseMainWindow();
                }
                catch { }
            }
            
            // Wait up to 10 seconds
            await Task.Delay(TimeSpan.FromSeconds(10));
            
            // Force kill if still running
            processes = Process.GetProcessesByName("ProxyAssessmentTool");
            foreach (var process in processes)
            {
                try
                {
                    process.Kill();
                    process.WaitForExit(5000);
                }
                catch { }
            }
        }

        private async Task UpdateLauncherAsync(Version version)
        {
            var launcherPath = Path.Combine(_baseDirectory, "ProxyAssessmentTool.exe");
            var versionedExe = Path.Combine(_baseDirectory, $"app-{version}", "ProxyAssessmentTool.exe");
            
            // Simple approach: copy the exe to root
            if (File.Exists(launcherPath))
            {
                File.Delete(launcherPath);
            }
            
            File.Copy(versionedExe, launcherPath);
            
            // Update desktop shortcut if exists
            var desktopShortcut = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.Desktop),
                "ProxyAssessmentTool.lnk");
            
            if (File.Exists(desktopShortcut))
            {
                // Update shortcut target (requires COM interop or WshShell)
                await Task.CompletedTask;
            }
        }

        private async Task UpdateHistoryAsync(UpdateManifest manifest, bool success, string? error = null)
        {
            var historyPath = Path.Combine(_baseDirectory, "UpdateHistory.json");
            var history = new UpdateHistory();
            
            if (File.Exists(historyPath))
            {
                try
                {
                    var json = await File.ReadAllTextAsync(historyPath);
                    history = System.Text.Json.JsonSerializer.Deserialize<UpdateHistory>(json) ?? new UpdateHistory();
                }
                catch { }
            }
            
            history.Entries.Insert(0, new UpdateHistoryEntry
            {
                Version = manifest.Version,
                Timestamp = DateTime.UtcNow,
                Success = success,
                Error = error
            });
            
            // Keep last 50 entries
            if (history.Entries.Count > 50)
                history.Entries.RemoveRange(50, history.Entries.Count - 50);
            
            var updatedJson = System.Text.Json.JsonSerializer.Serialize(history, new System.Text.Json.JsonSerializerOptions
            {
                WriteIndented = true
            });
            
            await File.WriteAllTextAsync(historyPath, updatedJson);
        }
    }

    public class InstallProgress
    {
        public string Status { get; }
        public double Percentage { get; }
        
        public InstallProgress(string status, double percentage)
        {
            Status = status;
            Percentage = percentage;
        }
    }

    public class InstallResult
    {
        public bool Success { get; }
        public string? InstallPath { get; }
        public string? Error { get; }
        
        private InstallResult(bool success, string? installPath = null, string? error = null)
        {
            Success = success;
            InstallPath = installPath;
            Error = error;
        }
        
        public static InstallResult Success(string installPath) => new(true, installPath);
        public static InstallResult Failure(string error) => new(false, null, error);
    }
}