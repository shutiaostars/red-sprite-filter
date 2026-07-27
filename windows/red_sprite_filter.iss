#ifndef MyAppVersion
#define MyAppVersion "1.0.6"
#endif

[Setup]
AppId={{2A3AB61D-9341-46D7-B50D-5B760CFF3C74}
AppName=Red Sprite Filter
AppVersion={#MyAppVersion}
AppPublisher=shutiaostars
AppPublisherURL=https://github.com/shutiaostars/red-sprite-filter
AppSupportURL=https://github.com/shutiaostars/red-sprite-filter/issues
AppUpdatesURL=https://github.com/shutiaostars/red-sprite-filter/releases
DefaultDirName={autopf}\Red Sprite Filter
DefaultGroupName=Red Sprite Filter
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=red-sprite-filter-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\red-sprite-filter.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\red-sprite-filter.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Red Sprite Filter"; Filename: "{app}\red-sprite-filter.exe"
Name: "{autodesktop}\Red Sprite Filter"; Filename: "{app}\red-sprite-filter.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\red-sprite-filter.exe"; Description: "{cm:LaunchProgram,Red Sprite Filter}"; Flags: nowait postinstall skipifsilent
