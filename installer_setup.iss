[Setup]
AppName=Web Ceph Auto Processor
AppVersion=1.0.0
AppPublisher=Web Ceph Auto Team
AppPublisherURL=https://github.com/webcephauto
DefaultDirName={autopf}\WebCephAuto
DefaultGroupName=Web Ceph Auto
UninstallDisplayIcon={app}\WebCephAuto.exe
Compression=lzma2
SolidCompression=yes
OutputDir=installer
OutputBaseFilename=WebCephAuto_Setup_v1.0.0

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "바탕화면에 아이콘 만들기"; GroupDescription: "추가 아이콘:"; Flags: unchecked

[Files]
Source: "dist\WebCephAuto.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Web Ceph Auto"; Filename: "{app}\WebCephAuto.exe"
Name: "{group}\제거"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Web Ceph Auto"; Filename: "{app}\WebCephAuto.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\WebCephAuto.exe"; Description: "프로그램 실행"; Flags: nowait postinstall skipifsilent
