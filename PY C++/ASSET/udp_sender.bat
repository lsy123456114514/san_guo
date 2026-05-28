@echo off
chcp 65001 >nul
echo UDP Packet Sender with Network Scanner
echo ======================================

setlocal enabledelayedexpansion

set "PACKET_COUNT=50"
set "PACKET_SIZE=1000"

:menu
echo.
echo 1. Scan Local Network
echo 2. Manual Input IP
echo 3. Exit
echo.
set /p choice="Select (1/2/3): "

if "%choice%"=="1" goto scan
if "%choice%"=="2" goto manual
if "%choice%"=="3" goto end
echo Invalid choice.
goto menu

:scan
echo.
echo Scanning local network, please wait...
echo.

set "FOUND_IPS="
set "COUNT=0"

for /f "tokens=2" %%a in ('arp -a ^| findstr "dynamic"') do (
    echo Found: %%a
    set "FOUND_IPS=!FOUND_IPS! %%a"
    set /a COUNT+=1
)

if "%COUNT%"=="0" (
    echo No active hosts found in ARP cache.
    echo.
    echo Please try option 2 to input IP manually.
    goto menu
)

echo.
echo Total found: %COUNT% hosts
echo.

set /p SELECTED_IP="Enter target IP from above list: "
echo.
set /p TARGET_PORT="Enter target port: "

goto send

:manual
echo.
set /p TARGET_IP="Enter target IP: "
echo.
set /p TARGET_PORT="Enter target port: "

:send
set "DATA_STR="
for /l %%i in (1,1,1000) do set "DATA_STR=!DATA_STR!A"

echo.
echo Target IP: %TARGET_IP%
echo Target Port: %TARGET_PORT%
echo Packet Count: %PACKET_COUNT%
echo Packet Size: %PACKET_SIZE% bytes
echo Sending packets...
echo.

for /l %%n in (1,1,%PACKET_COUNT%) do (
    echo [%%n/!PACKET_COUNT!] Sending packet...
    powershell -NoProfile -Command "Try { $udp = New-Object System.Net.Sockets.UdpClient; $udp.Connect('%TARGET_IP%', %TARGET_PORT%); $data = [System.Text.Encoding]::UTF8.GetBytes('%DATA_STR%'); $udp.Send($data) | Out-Null; $udp.Close(); Write-Host 'OK' } Catch { Write-Host 'Error:' $_.Exception.Message }"
)

echo.
echo Done! Sent %PACKET_COUNT% UDP packets.
pause
goto menu

:end
exit
