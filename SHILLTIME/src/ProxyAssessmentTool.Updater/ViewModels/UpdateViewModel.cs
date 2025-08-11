using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using System.Windows.Input;
using CommunityToolkit.Mvvm.Input;
using ProxyAssessmentTool.Updater.Models;
using ProxyAssessmentTool.Updater.Services;

namespace ProxyAssessmentTool.Updater.ViewModels
{
    public class UpdateViewModel : INotifyPropertyChanged
    {
        private readonly SignatureValidator _validator;
        private readonly AtomicInstaller _installer;
        private readonly string _packagePath;
        
        private string _status = "Preparing...";
        private double _progress;
        private bool _canInstall;
        private bool _isInstalling;
        private UpdateManifest? _manifest;
        private string? _errorMessage;

        public UpdateViewModel(string packagePath)
        {
            _packagePath = packagePath;
            _validator = new SignatureValidator(GetConfiguredThumbprint());
            _installer = new AtomicInstaller(new Progress<InstallProgress>(OnInstallProgress));
            
            InstallCommand = new AsyncRelayCommand(InstallAsync, () => CanInstall && !IsInstalling);
            CancelCommand = new RelayCommand(() => Environment.Exit(0));
            
            _ = ValidatePackageAsync();
        }

        public string Status
        {
            get => _status;
            set { _status = value; OnPropertyChanged(); }
        }

        public double Progress
        {
            get => _progress;
            set { _progress = value; OnPropertyChanged(); }
        }

        public bool CanInstall
        {
            get => _canInstall;
            set { _canInstall = value; OnPropertyChanged(); ((AsyncRelayCommand)InstallCommand).NotifyCanExecuteChanged(); }
        }

        public bool IsInstalling
        {
            get => _isInstalling;
            set { _isInstalling = value; OnPropertyChanged(); ((AsyncRelayCommand)InstallCommand).NotifyCanExecuteChanged(); }
        }

        public UpdateManifest? Manifest
        {
            get => _manifest;
            set { _manifest = value; OnPropertyChanged(); }
        }

        public string? ErrorMessage
        {
            get => _errorMessage;
            set { _errorMessage = value; OnPropertyChanged(); }
        }

        public ICommand InstallCommand { get; }
        public ICommand CancelCommand { get; }

        private async Task ValidatePackageAsync()
        {
            Status = "Validating update package...";
            Progress = 0;
            
            var result = await _validator.ValidateUpdatePackageAsync(_packagePath);
            
            if (result.IsValid)
            {
                Manifest = result.Manifest;
                Status = $"Ready to install version {Manifest?.Version}";
                CanInstall = true;
            }
            else
            {
                ErrorMessage = result.ErrorMessage;
                Status = "Validation failed";
                CanInstall = false;
            }
        }

        private async Task InstallAsync()
        {
            if (Manifest == null) return;
            
            IsInstalling = true;
            ErrorMessage = null;
            
            var result = await _installer.InstallUpdateAsync(_packagePath, Manifest);
            
            if (result.Success)
            {
                Status = "Installation complete!";
                Progress = 100;
                
                // Launch the updated application
                await Task.Delay(1000);
                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                {
                    FileName = System.IO.Path.Combine(result.InstallPath!, "ProxyAssessmentTool.exe"),
                    UseShellExecute = true
                });
                
                Environment.Exit(0);
            }
            else
            {
                ErrorMessage = result.Error;
                Status = "Installation failed";
                IsInstalling = false;
            }
        }

        private void OnInstallProgress(InstallProgress progress)
        {
            Status = progress.Status;
            Progress = progress.Percentage;
        }

        private static string GetConfiguredThumbprint()
        {
            // TODO: Load from config or embed
            return "YOUR_CERTIFICATE_THUMBPRINT_HERE";
        }

        public event PropertyChangedEventHandler? PropertyChanged;
        
        protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}