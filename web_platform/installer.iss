[Setup]
AppName=三条IM自动化测试控制台
AppVersion=1.0.0
DefaultDirName={autopf}\SantiaoAntiPlatform
DefaultGroupName=三条IM自动化测试控制台
OutputDir=d:\projects\santiao-anti\dist\SetupInstaller
OutputBaseFilename=Santiao_IM_Console_Setup_v1.0.0
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest

[Files]
Source: "d:\projects\santiao-anti\dist\三条IM自动化测试控制台\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\三条IM自动化测试控制台"; Filename: "{app}\三条IM自动化测试控制台.exe"
Name: "{autodesktop}\三条IM自动化测试控制台"; Filename: "{app}\三条IM自动化测试控制台.exe"

[Run]
Filename: "{app}\三条IM自动化测试控制台.exe"; Description: "运行 三条IM自动化测试控制台"; Flags: nowait postinstall skipifsilent
