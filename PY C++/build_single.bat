@echo off
cd /d "%~dp0"
echo Cleaning old build...
if exist build rmdir /s /q build
if exist dist\SangoHeroes.exe del /q dist\SangoHeroes.exe
echo Building single-file exe...
pyinstaller --onefile --name SangoHeroes --add-data "ASSET;ASSET" --add-data "data;data" --hidden-import=pkg_resources --exclude-module=tkinter --exclude-module=PyQt5 --exclude-module=wx --exclude-module=numpy --exclude-module=scipy --exclude-module=matplotlib --exclude-module=pandas --exclude-module=tensorflow --exclude-module=torch --exclude-module=sklearn --noconfirm main.py
echo Done!
pause