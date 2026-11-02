#define AppName "CapCut Keyframe Studio"
[Setup]
AppId={{8F7AA107-5243-47B9-907B-D54F9BA52726}
AppName={#AppName}
AppVersion=0.2.0
DefaultDirName={localappdata}\Programs\CapCutKeyframeStudio
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=CapCut-Keyframe-Studio-Windows-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\CapCut Keyframe Studio.exe

[Files]
Source: "..\dist\CapCut Keyframe Studio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\CapCut Keyframe Studio.exe"
Name: "{group}\{#AppName} Web"; Filename: "{app}\CapCut Keyframe Studio.exe"; Parameters: "--web"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\CapCut Keyframe Studio.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Run]
Filename: "{app}\CapCut Keyframe Studio.exe"; Description: "Launch CapCut Keyframe Studio"; Flags: nowait postinstall skipifsilent
