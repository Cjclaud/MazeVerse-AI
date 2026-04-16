#define MyAppName "Mazeverse AI"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Mazeverse"
#define MyAppDevelopers "CJ (Munotida) & Paradise (Rutendo)"
#define MyAppExeName "MazeverseAI.exe"

[Setup]
AppId={{1D466D82-7E66-4551-A93A-9BE77900A4A2}
AppName={#MyAppName}
AppVerName={#MyAppName} {#MyAppVersion}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppCopyright=Created by {#MyAppDevelopers}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer-dist
OutputBaseFilename=MazeverseAI-Setup
SetupIconFile=assets\icon.ico
WizardImageFile=assets\installer_wizard.png
WizardSmallImageFile=assets\installer_small.png
Compression=lzma
SolidCompression=yes
WizardStyle=modern
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoCopyright=Created by {#MyAppDevelopers}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\MazeverseAI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
