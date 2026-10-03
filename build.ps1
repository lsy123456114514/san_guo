# build.ps1 — 一键出货：全量测试通过 → 自动打包游戏 + 测试工具
# 用法:
#   .\build.ps1              # 测试 + 打两个包（默认）
#   .\build.ps1 -SkipTest    # 跳过测试直接打包
#   .\build.ps1 -TestOnly    # 只跑全量测试，不打包
param(
    [switch]$SkipTest,
    [switch]$TestOnly
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

function Fail([string]$msg) {
    Write-Host "[build] 失败: $msg" -ForegroundColor Red
    exit 1
}

# ── 1/3 源码全量测试（33 模块，约 2 分钟） ──
if (-not $SkipTest) {
    Write-Host "[build] 1/3 源码全量测试 ..." -ForegroundColor Cyan
    py auto_test.py --all
    if ($LASTEXITCODE -ne 0) { Fail "全量测试未通过 (exit=$LASTEXITCODE)" }
    Write-Host "[build] 测试全绿 (33/33)" -ForegroundColor Green
}
if ($TestOnly) { exit 0 }

# ── 2/3 两个包（spec 内含瘦身与依赖收集规则） ──
Write-Host "[build] 2/3 打包游戏 (complete_game.spec) ..." -ForegroundColor Cyan
py -m PyInstaller complete_game.spec --noconfirm
if ($LASTEXITCODE -ne 0) { Fail "游戏打包失败 (exit=$LASTEXITCODE)" }

Write-Host "[build] 3/3 打包测试工具 (auto_test.spec) ..." -ForegroundColor Cyan
py -m PyInstaller auto_test.spec --noconfirm
if ($LASTEXITCODE -ne 0) { Fail "测试工具打包失败 (exit=$LASTEXITCODE)" }

# ── 出货清单 ──
Write-Host ""
Write-Host "==== 出货清单 ====" -ForegroundColor Yellow
Get-ChildItem dist -Directory | ForEach-Object {
    $exe = Get-ChildItem $_.FullName -Filter *.exe -File -ErrorAction SilentlyContinue |
           Select-Object -First 1
    if ($exe) {
        $mb = (Get-ChildItem $_.FullName -Recurse -File |
               Measure-Object Length -Sum).Sum / 1MB
        "{0}   {1,7:N1} MB   {2}" -f $exe.Name, $mb, $_.FullName
    }
}
Write-Host "[build] 完成" -ForegroundColor Green
