[Setup]
AppName=三条IM自动化测试控制台
AppVersion=2.5.0
DefaultDirName={autopf}\SantiaoAntiDesktop
DefaultGroupName=三条IM自动化测试控制台
OutputDir=D:\projects\santiao-anti\dist\SetupInstaller
OutputBaseFilename=Santiao_IM_Native_Setup_v2.5.0
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest

[Files]
Source: "D:\projects\santiao-anti\dist\三条IM自动化测试控制台\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\三条IM自动化测试控制台"; Filename: "{app}\三条IM自动化测试控制台.exe"
Name: "{autodesktop}\三条IM自动化测试控制台"; Filename: "{app}\三条IM自动化测试控制台.exe"

[Run]
Filename: "{app}\三条IM自动化测试控制台.exe"; Description: "运行 三条IM自动化测试控制台"; Flags: nowait postinstall skipifsilent
