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

[Code]
var
  ErrorCount: Integer;
  EasterEggTriggered: Boolean;

function InitializeSetup(): Boolean;
begin
  ErrorCount := 0;
  EasterEggTriggered := False;
  Result := True;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  // 模拟错误触发机制
  if CurPageID = wpSelectDir then
  begin
    // 随机触发错误（10%的概率）
    if Random(10) = 0 then
    begin
      ErrorCount := ErrorCount + 1;
      // 显示错误消息
      MsgBox('安装过程中遇到问题：无法创建目录。', mbError, MB_OK);
      
      // 检查是否触发彩蛋
      if ErrorCount >= 3 then
      begin
        EasterEggTriggered := True;
        MsgBox('恭喜你发现了彩蛋！作为奖励，游戏将获得特殊能力。', mbInformation, MB_OK);
        MsgBox('彩蛋提示：在游戏中输入 "threekingdoms" 解锁隐藏角色。', mbInformation, MB_OK);
      end;
      
      Result := False; // 阻止继续安装
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    // 检查文件是否存在
    if not FileExists(ExpandConstant('{src}\dist\三国名将传完整版\三国名将传完整版.exe')) then
    begin
      ErrorCount := ErrorCount + 1;
      MsgBox('错误：找不到游戏主程序文件。', mbError, MB_OK);
      
      // 检查是否触发彩蛋
      if ErrorCount >= 3 then
      begin
        EasterEggTriggered := True;
        MsgBox('恭喜你发现了彩蛋！作为奖励，游戏将获得特殊能力。', mbInformation, MB_OK);
        MsgBox('彩蛋提示：在游戏中输入 "threekingdoms" 解锁隐藏角色。', mbInformation, MB_OK);
      end;
    end;
  end;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  // 彩蛋触发后，跳过某些页面作为奖励
  if EasterEggTriggered and (PageID = wpSelectComponents) then
  begin
    Result := True;
  end;
end;
