using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace ProxyAssessmentTool.Updater.Models
{
    public class UpdateManifest
    {
        [JsonPropertyName("version")]
        public string Version { get; set; } = "";
        
        [JsonPropertyName("releaseDate")]
        public DateTime ReleaseDate { get; set; }
        
        [JsonPropertyName("minimumVersion")]
        public string? MinimumVersion { get; set; }
        
        [JsonPropertyName("publisherThumbprint")]
        public string PublisherThumbprint { get; set; } = "";
        
        [JsonPropertyName("files")]
        public List<UpdateFile> Files { get; set; } = new();
        
        [JsonPropertyName("changelog")]
        public string? Changelog { get; set; }
        
        [JsonPropertyName("signature")]
        public string? Signature { get; set; }
    }

    public class UpdateFile
    {
        [JsonPropertyName("path")]
        public string Path { get; set; } = "";
        
        [JsonPropertyName("sha256")]
        public string Sha256 { get; set; } = "";
        
        [JsonPropertyName("size")]
        public long Size { get; set; }
        
        [JsonPropertyName("executable")]
        public bool Executable { get; set; }
    }
}