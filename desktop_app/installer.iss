[Setup]
AppName=三条IM自动化测试控制台
AppVersion=0.9.9
DefaultDirName={autopf}\SantiaoAntiDesktop
DefaultGroupName=三条IM自动化测试控制台
OutputDir=d:\projects\santiao-anti\dist\SetupInstaller
OutputBaseFilename=Santiao_IM_Native_Setup_v0.9.9
Compression=lzma2/fast
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
; 显式开启路径选择页面，允许用户在安装向导中点击【浏览】自由选择安装到任意磁盘目录
DisableDirPage=no
; 严禁静默复用历史安装路径，确保每次安装均可自定义新位置
UsePreviousAppDir=no
DirExistsWarning=auto
AlwaysShowDirOnReadyPage=yes
; 绑定应用程序专属品牌高清图标 (应用于安装向导主程序与卸载器)
SetupIconFile=d:\projects\santiao-anti\desktop_app\resources\app_icon.ico

; 强制关闭正在运行的应用程序，避免卸载或覆盖安装时文件被占用无法删除
CloseApplications=yes
CloseApplicationsFilter=*.exe
RestartApplications=no

[Files]
; 1. 桌面端应用主程序与运行库
Source: "d:\projects\santiao-anti\dist\三条IM自动化测试控制台\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; 2. 核心自动化测试工程（动态收纳所有业务目录与核心配置，二进制加密/机器码发布）
Source: "d:\projects\santiao-anti\dist\encrypted_release\common\*"; DestDir: "{app}\common"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "d:\projects\santiao-anti\dist\encrypted_release\config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "d:\projects\santiao-anti\dist\encrypted_release\core\*"; DestDir: "{app}\core"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "d:\projects\santiao-anti\dist\encrypted_release\data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "d:\projects\santiao-anti\dist\encrypted_release\locators\*"; DestDir: "{app}\locators"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "d:\projects\santiao-anti\dist\encrypted_release\pages\*"; DestDir: "{app}\pages"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "d:\projects\santiao-anti\dist\encrypted_release\tests\*"; DestDir: "{app}\tests"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "d:\projects\santiao-anti\dist\encrypted_release\utils\*"; DestDir: "{app}\utils"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "d:\projects\santiao-anti\dist\encrypted_release\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

; 3. Appium 批处理启动脚本与测试说明文档 (安装释放至程序安装目录 {app})
Source: "d:\projects\santiao-anti\start_appium_batch.bat"; DestDir: "{app}"; DestName: "start_appium_batch.bat"; Flags: ignoreversion
Source: "d:\projects\santiao-anti\test_docs\*"; DestDir: "{app}\test_docs"; Flags: ignoreversion recursesubdirs createallsubdirs

; 3. 内置独立免安装 Python 运行环境
Source: "D:\data\Python313\*"; DestDir: "{app}\python_runtime"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pdb,Doc,include,tcl,__pycache__,paddle*,scipy*,sympy*,wandb*,modelscope*,*polars*,Lib\test"

; 4. 内置 Allure CLI 命令行工具 (开箱即用支持生成全维度可视化测试报告)
Source: "d:\projects\santiao-anti\allure-cli\*"; DestDir: "{app}\allure-cli"; Flags: ignoreversion recursesubdirs createallsubdirs


[Icons]
Name: "{autoprograms}\三条IM自动化测试控制台"; Filename: "{app}\三条IM自动化测试控制台.exe"
Name: "{autodesktop}\三条IM自动化测试控制台"; Filename: "{app}\三条IM自动化测试控制台.exe"

[Run]
Filename: "{app}\三条IM自动化测试控制台.exe"; Description: "运行 三条IM自动化测试控制台"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 显式指示卸载程序彻底清除运行期间动态产生的测试报告、日志、缓存及主目录
Type: filesandordirs; Name: "{app}\reports"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\python_runtime"
Type: filesandordirs; Name: "{app}\allure-cli"
Type: filesandordirs; Name: "{app}"

[Code]
// 卸载初始化阶段：强制终止正在运行的主程序与后台任务，彻底解除 Windows 独占文件锁
function InitializeUninstall(): Boolean;
var
  ErrorCode: Integer;
begin
  Exec('taskkill.exe', '/F /IM 三条IM自动化测试控制台.exe', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
  Sleep(500);
  Result := True;
end;

// 卸载收尾阶段：确保整个应用安装根目录连根拔起彻底清除，做到 0 字节残留
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DelTree(ExpandConstant('{app}'), True, True, True);
  end;
end;
