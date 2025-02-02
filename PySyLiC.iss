
;This file is part of pySyLiC.
;
; Copyright (C) 2009-2025 Cédrick FAURY
;
;pySyLiC is free software; you can redistribute it and/or modify
;it under the terms of the GNU General Public License as published by
;the Free Software Foundation; either version 2 of the License, or
;(at your option) any later version.
;
;pySyLiC is distributed in the hope that it will be useful,
;but WITHOUT ANY WARRANTY; without even the implied warranty of
;MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;GNU General Public License for more details.
;
;You should have received a copy of the GNU General Public License
;along with pySyLiC; if not, write to the Free Software
;Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

[ISPP]
#define AppName "pySyLiC"
#define AppVersion "1.0"
#define AppVersionInfo "1.0.0"
#define AppVersionBase "1.0"

#define AppURL "https://github.com/cedrick-f/pySyLiC"

[Setup]
;Informations générales sur l'application
AppName={#AppName}
AppVerName={#AppName} {#AppVersion}
AppVersion={#AppVersion}
AppPublisher=Cédrick Faury
AppCopyright=Copyright © 2009-2025 Cédrick Faury
VersionInfoVersion = {#AppVersionInfo}

;Répertoire de base contenant les fichiers
SourceDir=D:\Developpement\PySyLiC\PySyLiC 1.0

;Repertoire d'installation
DefaultDirName={pf}\{#AppName}
DefaultGroupName={#AppName}
LicenseFile=LICENSE.txt

;Paramètres de compression
;lzma ou zip
Compression=lzma/max
SolidCompression=yes

;Par défaut, pas besoin d'être administrateur pour installer
PrivilegesRequired=none

;Nom du fichier généré et répertoire de destination
OutputBaseFilename=setup_{#AppName}_{#AppVersion}_win32
OutputDir=releases

;Dans le panneau de configuration de Windows2000/NT/XP, c'est l'icone de pyMotion.exe qui
;apparaît à gauche du nom du fichier pour la désinstallation
UninstallDisplayIcon={app}\icone.ico

;Fenêtre en background
WindowResizable=false
WindowStartMaximized=true
WindowShowCaption=true
BackColorDirection=lefttoright
;WizardImageFile = D:\Documents\Developpement\PyVot 0.6\Images\grand_logo.bmp
;WizardSmallImageFile = D:\Documents\Developpement\PyVot 0.6\Images\petit_logo.bmp

AlwaysUsePersonalGroup=no

[Languages]
Name: en; MessagesFile: "compiler:Default.isl"
Name: fr; MessagesFile: "compiler:Languages\French.isl"

;Name: fr; MessagesFile: "compiler:Languages\French.isl"

[Messages]
BeveledLabel={#AppName} {#AppVersion} installation


[CustomMessages]
;
; French
;
fr.uninstall=Désinstaller
fr.gpl_licence=Prendre connaissance du contrat de licence pour le logiciel
fr.fdl_licence=Prendre connaissance du contrat de licence pour la documentation associée
fr.CreateDesktopIcon=Créer un raccourci sur le bureau vers
fr.AssocFileExtension=&Associer le programme PySyLic à l'extension .syl
fr.CreateQuickLaunchIcon=Créer un icône dans la barre de lancement rapide
fr.FileExtensionName=Système PySyLiC
fr.FileExtension=pySyLiC.system
fr.InstallFor=Installer pour :
fr.AllUsers=Tous les utilisateurs
fr.JustMe=Seulement moi
fr.ShortCut=Raccourcis :
fr.Association=Association de fichier :

;
; English
;
en.uninstall=Uninstall
en.gpl_licence=Read the GNU GPL
en.fdl_licence=Read the GNU FDL
en.AssocFileExtension=&Associate PySyLic with .syl extension
en.CreateDesktopIcon=Create Desktop shortcut to
en.CreateQuickLaunchIcon=Create a &Quick Launch icon to
en.FileExtensionName=PySyLiC System
en.FileExtension=pySyLiC.system
en.InstallFor=Install for :
en.AllUsers=All users
en.JustMe=Just me
en.ShortCut=Short cuts :
en.Association=File association :

[Files]
;
; Fichiers de la distribution
;
Source: src\build\*.*; DestDir: {app}; Flags : ignoreversion recursesubdirs;
;Source: *.txt; DestDir: {app}; Flags : ignoreversion;
;Source: Images\*.ico; DestDir: {app}\Images; Flags : ignoreversion;
;Source: Images\*.png; DestDir: {app}\Images; Flags : ignoreversion;
;Source: locale\en\LC_MESSAGES\*.mo; DestDir: {app}\locale\en\LC_MESSAGES; Flags : ignoreversion;

;
; Fichiers exemples
;
;Source: Exemples\*.syl; DestDir: {app}\Exemples; Flags : ignoreversion;
;Source: Exemples\*.csv; DestDir: {app}\Exemples; Flags : ignoreversion;


; les dll C++
;Source: src\msvcr90.dll; DestDir: {app}\bin; Flags : ignoreversion;
;Source: src\*.manifest; DestDir: {app}\bin; Flags : ignoreversion;

; peut-être utile avec Win2000 ???
;Source: gdiplus.dll; DestDir: {app}\bin; Flags : ignoreversion;

; des fichiers à mettre dans le dossier "Application data"
;Source: {src};  DestDir: {code:DefAppDataFolder}\Test\;

[Tasks]
Name: desktopicon2; Description: {cm:CreateDesktopIcon} {#AppName} ;GroupDescription: {cm:ShortCut}; MinVersion: 4,4
Name: fileassoc; Description: {cm:AssocFileExtension};GroupDescription: {cm:Association};
Name: common; Description: {cm:AllUsers}; GroupDescription: {cm:InstallFor}; Flags: exclusive
Name: local;  Description: {cm:JustMe}; GroupDescription: {cm:InstallFor}; Flags: exclusive unchecked

[Icons]
Name: {group}\{#AppName};Filename: {app}\bin\{#AppName}.exe; WorkingDir: {app}\bin; IconFileName: {app}\bin\{#AppName}.exe
Name: {group}\{cm:uninstall} {#AppName}; Filename: {app}\unins000.exe;IconFileName: {app}\unins000.exe
;
; On ajoute sur le Bureau l'icône PySyLic
;
Name: {code:DefDesktop}\{#AppName} {#AppVersion};   Filename: {app}\bin\{#AppName}.exe; WorkingDir: {app}\bin; MinVersion: 4,4; Tasks: desktopicon2; IconFileName: {app}\bin\{#AppName}.exe


[_ISTool]
Use7zip=true


[Registry]
; Tout ce qui concerne les fichiers .syl
Root: HKCR; SubKey: .syl; ValueType: string; ValueData: {cm:FileExtension}; Flags: uninsdeletekey
Root: HKCR; SubKey: {cm:FileExtension}; ValueType: string; Flags: uninsdeletekey; ValueData: {cm:FileExtensionName}
Root: HKCR; SubKey: {cm:FileExtension}\Shell\Open\Command; ValueType: string; ValueData: """{app}\bin\{#AppName}.exe"" ""%1"""; Flags: uninsdeletekey;
Root: HKCR; Subkey: {cm:FileExtension}\DefaultIcon; ValueType: string; ValueData: {app}\images\pySyLiC.ico,0; Flags: uninsdeletekey;

; Pour stocker le style d'installation : "All users" ou "Current user"
Root: HKLM; Subkey: Software\{#AppName}; ValueType: string; ValueName: DataFolder; ValueData: {code:DefAppDataFolder}\{#AppName} ; Flags: uninsdeletekey;

; Pour stocker le dossier d'installation de pySyLiC (pour vérification si "install" ou "portable")
;Root: HKLM; Subkey: Software\{#AppName}; ValueType: string; ValueName: InstallFolder; ValueData: {app} ; Flags: uninsdeletekey;



[Code]
Procedure URLLabelOnClick(Sender: TObject);
var
  ErrorCode: Integer;
begin
  ShellExec('open', 'http://fauryc.free.fr/spip.php?rubrique1', '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode);
end;

{*** INITIALISATION ***}
Procedure InitializeWizard;
var
  URLLabel: TNewStaticText;
begin
  URLLabel := TNewStaticText.Create(WizardForm);
  URLLabel.Caption := 'http://fauryc.free.fr';
  URLLabel.Cursor := crHand;
  URLLabel.OnClick := @URLLabelOnClick;
  URLLabel.Parent := WizardForm;
  { Alter Font *after* setting Parent so the correct defaults are inherited first }
  URLLabel.Font.Style := URLLabel.Font.Style + [fsUnderline];
  URLLabel.Font.Color := clBlue;
  URLLabel.Top := WizardForm.ClientHeight - URLLabel.Height - 15;
  URLLabel.Left := ScaleX(20);
end;


{ Renvoie le dossier "Application Data" à utiliser }
function DefAppDataFolder(Param: String): String;
begin
  if IsTaskSelected('common') then
    Result := ExpandConstant('{commonappdata}')
  else
    Result := ExpandConstant('{localappdata}')
end;


{ Renvoie le bureau sur lequel placer le raccourci de pySyLiC }
function DefDesktop(Param: String): String;
begin
  if IsTaskSelected('common') then
    Result := ExpandConstant('{commondesktop}')
  else
    Result := ExpandConstant('{userdesktop}')
end;






















