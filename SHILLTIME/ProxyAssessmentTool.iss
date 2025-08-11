; ProxyAssessmentTool Installer Script
; Requires Inno Setup 6.2.0 or later

#define MyAppName "ProxyAssessmentTool"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Security Assessment Solutions"
#define MyAppURL "https://github.com/yourusername/ProxyAssessmentTool"
#define MyAppExeName "ProxyAssessmentTool.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{A7F3B9D5-4E8C-4D2A-9F1E-6C8B3A2D5E7F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE.txt
OutputDir=.
OutputBaseFilename=ProxyAssessmentTool_Setup_v{#MyAppVersion}
SetupIconFile=installer\icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}
VersionInfoDescription=ProxyAssessmentTool Setup
VersionInfoCompany={#MyAppPublisher}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main executable (will be assembled from parts during install)
Source: "publish\ProxyAssessmentTool.exe.part*"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "installer\AssembleExe.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

; Configuration files
Source: "publish\appsettings.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "publish\default.yaml"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: "publish\ProxyAssessmentTool.xml"; DestDir: "{app}"; Flags: ignoreversion
Source: "publish\ProxyAssessmentTool.Core.xml"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "BUILD_AND_RUN.md"; DestDir: "{app}"; Flags: ignoreversion

; Create necessary directories
[Dirs]
Name: "{app}\logs"
Name: "{app}\data"
Name: "{app}\config"

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Assemble the exe from parts during installation
Filename: "{tmp}\AssembleExe.exe"; Parameters: """{tmp}"" ""{app}\{#MyAppExeName}"""; StatusMsg: "Assembling application files..."; Flags: runhidden

; Launch application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  
  // Check for .NET 8 Desktop Runtime
  if not RegKeyExists(HKLM, 'SOFTWARE\dotnet\Setup\InstalledVersions\x64\windowsdesktop') then
  begin
    if MsgBox('The Microsoft .NET Desktop Runtime 8.0 is required but not installed.' + #13#10 + #13#10 +
              'Would you like to download it now?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      ShellExec('open', 'https://dotnet.microsoft.com/download/dotnet/8.0/runtime', '', '', SW_SHOW, ewNoWait, ResultCode);
      Result := False;
    end
    else
    begin
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Set up Windows Defender exclusion for better performance (optional)
    // This is commented out by default for security reasons
    // Exec('powershell.exe', '-Command "Add-MpPreference -ExclusionPath ''' + ExpandConstant('{app}') + '''"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\data"