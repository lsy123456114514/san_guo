; 游戏安装程序脚本
; 使用Inno Setup制作

[Setup]
AppName=三国游戏
AppVersion=1.0
AppPublisher=游戏开发团队
AppPublisherURL=https://example.com
AppSupportURL=https://example.com
AppUpdatesURL=https://example.com
DefaultDirName={pf}\三国游戏
DefaultGroupName=三国游戏
OutputBaseFilename=三国游戏安装程序
; SetupIconFile=ASSET\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "dist\ThreeKingdomsGame.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "ASSET\*"; DestDir: "{app}\ASSET"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\三国游戏"; Filename: "{app}\ThreeKingdomsGame.exe"
Name: "{group}\卸载三国游戏"; Filename: "{uninstallexe}"
Name: "{commondesktop}\三国游戏"; Filename: "{app}\ThreeKingdomsGame.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Run]
Filename: "{app}\ThreeKingdomsGame.exe"; Description: "{cm:LaunchProgram,三国游戏}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\ASSET"
Type: filesandordirs; Name: "{app}\data"
Type: files; Name: "{app}\ThreeKingdomsGame.exe"

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
    if not FileExists(ExpandConstant('{src}\dist\ThreeKingdomsGame.exe')) then
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
