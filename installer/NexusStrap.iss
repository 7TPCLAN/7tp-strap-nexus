#ifndef NexusVersion
  #define NexusVersion "0.1.0"
#endif

[Setup]
AppId={{6D4AB4E2-7F2B-4C29-9D8B-7C7D7A1C7E31}
AppName=7TP Nexus Strap
AppVersion={#NexusVersion}
AppPublisher=7TPCLAN
DefaultDirName={autopf}\7TPCLAN\7TP Nexus Strap
DefaultGroupName=7TP Nexus Strap
OutputDir=..\dist-installer
OutputBaseFilename=7TP-Nexus-Strap-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\nexus-icon.ico
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
UninstallDisplayIcon={app}\7TP Nexus Strap.exe
SetupLogging=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\7TP Nexus Strap\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\7TP Nexus Strap"; Filename: "{app}\7TP Nexus Strap.exe"
Name: "{autodesktop}\7TP Nexus Strap"; Filename: "{app}\7TP Nexus Strap.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\7TP Nexus Strap.exe"; Description: "Launch 7TP Nexus Strap"; Flags: postinstall nowait skipifsilent
