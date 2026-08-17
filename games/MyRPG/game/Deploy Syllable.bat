@echo off
REM Deploy syllable — copy EXE + FONT (khong can Python)
setlocal
cd /d "%~dp0"
set "GAMEDIR=%~dp0"
set "MYRPG=%~dp0.."
set "SANGO=%GAMEDIR%SANGO2"
set "TOOLKIT=%~dp0..\..\.."

echo === Deploy Sango II Syllable ===

if not exist "%MYRPG%\patch\SAN2-SYLLABLE.EXE" (
  echo LOI: Thieu patch\SAN2-SYLLABLE.EXE — git pull
  exit /b 1
)
if not exist "%SANGO%\FONT16-SYLLABLE.PAT" (
  echo LOI: Thieu FONT16-SYLLABLE.PAT — git pull
  exit /b 1
)

copy /Y "%MYRPG%\patch\SAN2-SYLLABLE.EXE" "%SANGO%\SAN2-VN.EXE" >nul
copy /Y "%SANGO%\FONT16-SYLLABLE.PAT" "%SANGO%\FONT16.PAT" >nul
copy /Y "%SANGO%\FONT16-SYLLABLE.PAT" "%SANGO%\FONT16-VN.PAT" >nul
copy /Y "%SANGO%\FONT24-SYLLABLE.PAT" "%SANGO%\FONT24.PAT" >nul
copy /Y "%SANGO%\FONT24-SYLLABLE.PAT" "%SANGO%\FONT24-VN.PAT" >nul

echo OK: SAN2-VN.EXE + FONT16/24.PAT
exit /b 0
