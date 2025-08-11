using System;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace ProxyAssessmentTool.Core
{
    public class StartupHealthTracker
    {
        private readonly string _healthFilePath;
        private StartupHealth _currentHealth;

        public StartupHealthTracker()
        {
            var appData = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "ProxyAssessmentTool");
            
            Directory.CreateDirectory(appData);
            _healthFilePath = Path.Combine(appData, "StartupHealth.json");
            
            _currentHealth = new StartupHealth();
        }

        public void RecordStartupBegin()
        {
            _currentHealth = new StartupHealth
            {
                Timestamp = DateTime.UtcNow,
                Status = StartupStatus.InProgress,
                MachineName = Environment.MachineName,
                Version = GetType().Assembly.GetName().Version?.ToString() ?? "Unknown"
            };
            
            SaveHealth();
        }

        public void RecordStartupSuccess(TimeSpan elapsed)
        {
            _currentHealth.Status = StartupStatus.Success;
            _currentHealth.ElapsedMilliseconds = (long)elapsed.TotalMilliseconds;
            SaveHealth();
        }

        public void RecordStartupFailure(Exception exception, TimeSpan elapsed)
        {
            _currentHealth.Status = StartupStatus.Failed;
            _currentHealth.ElapsedMilliseconds = (long)elapsed.TotalMilliseconds;
            _currentHealth.ExceptionType = exception.GetType().FullName;
            _currentHealth.ExceptionMessage = exception.Message;
            SaveHealth();
        }

        public StartupHealth? GetLastHealth()
        {
            try
            {
                if (File.Exists(_healthFilePath))
                {
                    var json = File.ReadAllText(_healthFilePath);
                    return JsonSerializer.Deserialize<StartupHealth>(json);
                }
            }
            catch
            {
                // Ignore deserialization errors
            }
            
            return null;
        }

        private void SaveHealth()
        {
            try
            {
                var json = JsonSerializer.Serialize(_currentHealth, new JsonSerializerOptions
                {
                    WriteIndented = true,
                    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
                });
                
                File.WriteAllText(_healthFilePath, json);
            }
            catch
            {
                // Don't fail startup due to health tracking
            }
        }
    }

    public class StartupHealth
    {
        public DateTime Timestamp { get; set; }
        public StartupStatus Status { get; set; }
        public long ElapsedMilliseconds { get; set; }
        public string? ExceptionType { get; set; }
        public string? ExceptionMessage { get; set; }
        public string? MachineName { get; set; }
        public string? Version { get; set; }
    }

    public enum StartupStatus
    {
        InProgress,
        Success,
        Failed
    }
}