@echo off
cd /d "%~dp0"
if not exist "D:\Game\SAN" mkdir "D:\Game\SAN"
set SDL_AUDIODRIVER=winmm
"C:\DOSBox-X\dosbox-x.exe" -conf "%~dp0install.conf"
