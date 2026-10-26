[Setup]
AppName=VaultApp
AppVersion=2.0.0
AppPublisher=VaultApp
AppPublisherURL=https://github.com/ton-compte/vaultapp
AppSupportURL=https://github.com/ton-compte/vaultapp
AppUpdatesURL=https://github.com/ton-compte/vaultapp
DefaultDirName={autopf}\VaultApp
DefaultGroupName=VaultApp
OutputDir=Output
OutputBaseFilename=VaultApp_Setup_2.0.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=assets\logo.ico
LicenseFile=LICENSE.txt
WizardSizePercent=110
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
AllowNoIcons=yes

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"
Name: "startmenuicon"; Description: "Créer un raccourci dans le Menu Démarrer"; GroupDescription: "Raccourcis :"

[Files]
Source: "dist\VaultApp.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\VaultApp"; Filename: "{app}\VaultApp.exe"; Tasks: desktopicon
Name: "{group}\VaultApp"; Filename: "{app}\VaultApp.exe"; Tasks: startmenuicon
Name: "{group}\Désinstaller VaultApp"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\VaultApp.exe"; Description: "Lancer VaultApp"; Flags: nowait postinstall skipifsilent

[Messages]
WelcomeLabel1=Bienvenue dans l'installation de VaultApp !
WelcomeLabel2=Cet assistant va installer VaultApp 2.0 sur ton ordinateur.%n%nVaultApp est un gestionnaire de mots de passe sécurisé qui protège tes comptes avec un chiffrement AES-256.%n%nClique sur Suivant pour continuer.
FinishedHeadingLabel=Installation terminée !
FinishedLabel=VaultApp 2.0 a été installé avec succès sur ton ordinateur.%n%nTu peux maintenant lancer l'application depuis le raccourci sur le Bureau.
