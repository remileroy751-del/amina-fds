; ============================================================================
;  Script Inno Setup - AMINA FDS (Gestion de Stock)
;  Ce script transforme l'executable PyInstaller (dist\AMINA_FDS.exe) en un
;  vrai programme d'installation Windows :
;    - installation dans "Program Files"
;    - raccourci cree automatiquement sur le Bureau
;    - raccourci dans le menu Demarrer
;    - desinstalleur propre (visible dans "Applications" / "Programmes")
; ============================================================================

#define MyAppName "AMINA FDS - Gestion de Stock"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "AMINA FDS"
#define MyAppExeName "AMINA_FDS.exe"

[Setup]
; Identifiant unique de l'application (ne JAMAIS changer entre deux versions,
; sinon Windows considere que c'est un logiciel different).
AppId={{8511FF83-283B-4847-8D97-E00A73230C31}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\AMINA_FDS
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Necessite les droits administrateur (installation dans Program Files)
PrivilegesRequired=admin
OutputDir=Output
OutputBaseFilename=AMINA_FDS_Setup
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Interdit d'installer une ancienne version d'exe par-dessus sans prevenir
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
; Case a cocher (activee par defaut) pour creer le raccourci sur le Bureau
Name: "desktopicon"; Description: "Créer une icône sur le Bureau"; GroupDescription: "Icônes supplémentaires :"; Flags: checkedonce

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Raccourci dans le menu Demarrer
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Désinstaller {#MyAppName}"; Filename: "{uninstallexe}"
; Raccourci sur le Bureau (seulement si la case est cochee)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Propose de lancer le logiciel une fois l'installation terminee
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer {#MyAppName} maintenant"; Flags: nowait postinstall skipifsilent shellexec

; Remarque : la base de donnees de l'utilisateur est stockee dans %APPDATA%,
; donc elle n'est jamais touchee par l'installation ni la desinstallation :
; les donnees sont toujours conservees meme apres desinstallation du logiciel.
