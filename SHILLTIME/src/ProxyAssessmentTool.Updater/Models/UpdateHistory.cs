using System;
using System.Collections.Generic;

namespace ProxyAssessmentTool.Updater.Models
{
    public class UpdateHistory
    {
        public List<UpdateHistoryEntry> Entries { get; set; } = new();
    }

    public class UpdateHistoryEntry
    {
        public string Version { get; set; } = "";
        public DateTime Timestamp { get; set; }
        public bool Success { get; set; }
        public string? Error { get; set; }
    }
}