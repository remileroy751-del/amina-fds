; ============================================================
;  AMINA FDS - Script Inno Setup
;  Génère un installateur Windows (Setup.exe) qui installe le
;  logiciel et crée une icône de lancement sur le Bureau et
;  dans le Menu Démarrer.
;  Compilation : ISCC.exe installer.iss  (voir workflow GitHub Actions)
; ============================================================

#define MyAppName "AMINA FDS"
#define MyAppVersion "1.0"
#define MyAppPublisher "Ecom Academy"
#define MyAppURL "https://ecomacademytg.netlify.app"
#define MyAppExeName "AMINA_FDS.exe"

[Setup]
AppId={{6B6C0F0A-6B7B-4E7A-9D2F-AMINAFDS0001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=AMINA_FDS_Setup
SetupIconFile=assets\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer une icône sur le Bureau"; GroupDescription: "Icônes supplémentaires :"; Flags: checkedonce

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer {#MyAppName} maintenant"; Flags: nowait postinstall skipifsilent
