; 游戏安装程序脚本
; 使用Inno Setup制作

[Setup]
AppName=三国游戏
AppVersion=1.0
AppPublisher=游戏开发团队
AppPublisherURL=https://example.com
AppSupportURL=https://example.com
AppUpdatesURL=https://example.com
DefaultDirName={commonpf}\三国游戏
DefaultGroupName=三国游戏
OutputBaseFilename=三国游戏安装程序
; SetupIconFile=ASSET\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Files]
; 游戏是 onedir 布局：exe + _internal\（ASSET/DLL 都在里面），整目录安装
Source: "dist\三国名将传完整版\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; game_map_enhanced 从 _internal\ASSET\..\data\maps 读地图，包里没带，安装时补上
Source: "data\*"; DestDir: "{app}\_internal\data"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\三国游戏"; Filename: "{app}\三国名将传完整版.exe"
Name: "{group}\卸载三国游戏"; Filename: "{uninstallexe}"
Name: "{commondesktop}\三国游戏"; Filename: "{app}\三国名将传完整版.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Run]
Filename: "{app}\三国名将传完整版.exe"; Description: "{cm:LaunchProgram,三国游戏}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
Type: files; Name: "{app}\三国名将传完整版.exe"

