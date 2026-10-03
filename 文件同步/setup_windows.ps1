# setup_windows.ps1 — 在 Windows 上一键部署“文件同步服务端”
# 用法（管理员 PowerShell）:
#   .\setup_windows.ps1 -Config .\config.server.json
param(
    [string]$Config = (Join-Path $PSScriptRoot "config.server.json")
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Config)) {
    Write-Host "[错误] 找不到配置文件: $Config" -ForegroundColor Red
    Write-Host "请先把 config.server.example.json 复制成 config.server.json 并填写。" -ForegroundColor Yellow
    exit 1
}

$cfg = Get-Content -LiteralPath $Config -Raw -Encoding UTF8 | ConvertFrom-Json
$port = [int]$cfg.server.port
$shareFile = $cfg.server.share_file
$backupDir = $cfg.server.backup_dir
$scriptDir = $PSScriptRoot

# 1) 备份目录
if (-not (Test-Path -LiteralPath $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Write-Host "[OK] 已创建备份目录: $backupDir" -ForegroundColor Green
}

# 2) 防火墙放行端口
$ruleName = "FileSync Server $port"
if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP `
        -LocalPort $port -Action Allow | Out-Null
    Write-Host "[OK] 已放行防火墙 TCP $port" -ForegroundColor Green
} else {
    Write-Host "[跳过] 防火墙规则已存在: $ruleName" -ForegroundColor Yellow
}

# 3) 找到无窗口的 pythonw
$py = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = (Get-Command pyw.exe -ErrorAction SilentlyContinue).Source }
if (-not $py) { $py = (Get-Command python.exe -ErrorAction SilentlyContinue).Source }
if (-not $py) {
    Write-Host "[错误] 未找到 Python，请先安装并确保 py/pyw 在 PATH。" -ForegroundColor Red
    exit 1
}

# 4) 注册开机自启计划任务
$taskName = "FileSyncServer"
$serverScript = Join-Path $scriptDir "sync_server.py"
$action = New-ScheduledTaskAction -Execute $py `
    -Argument "`"$serverScript`" --config `"$Config`""
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Days 0)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
    -Settings $settings -RunLevel Highest -Force | Out-Null
Write-Host "[OK] 已注册开机自启任务: $taskName" -ForegroundColor Green

Start-ScheduledTask -TaskName $taskName
Write-Host "[OK] 服务已启动" -ForegroundColor Green

# 5) 打印地址，供 Linux 端填写
Write-Host ""
Write-Host "==== 服务端信息 ====" -ForegroundColor Cyan
Write-Host ("共享文件 : " + $shareFile)
Write-Host ("备份目录 : " + $backupDir)
$ip = $null
if (Get-Command tailscale -ErrorAction SilentlyContinue) {
    $ip = (tailscale ip -4 2>$null | Select-Object -First 1)
}
if ($ip) {
    Write-Host ("Tailscale IP : " + $ip)
    Write-Host ("client.server_url 填: http://" + $ip + ":" + $port)
} else {
    Write-Host "未检测到 Tailscale。局域网内可填本机 IP；跨网建议安装 Tailscale。" -ForegroundColor Yellow
    Write-Host ("当前内网 IP: " + ((Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -ne 'WellKnown' } |
        Select-Object -First 1).IPAddress))
}
