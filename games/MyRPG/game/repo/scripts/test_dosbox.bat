@echo off
REM Test Sango II VN trong DOSBox — Windows local
setlocal
set "GAME_DIR=D:\Game\SAN\SANGO2"
set "REPO=%~dp0.."
set "CONF=%REPO%\scripts\dosbox_sango2.conf"

if not exist "%GAME_DIR%\SAN2-VN.EXE" (
  echo Chua co SAN2-VN.EXE — chay scripts\build_vn_release.bat truoc
  set "EXE=SAN2.EXE"
) else (
  set "EXE=SAN2-VN.EXE"
)

where dosbox >nul 2>&1
if errorlevel 1 (
  echo Cai DOSBox hoac them vao PATH: https://www.dosbox.com/
  exit /b 1
)

echo Launch DOSBox: %GAME_DIR%\%EXE%
dosbox -conf "%CONF%" -c "mount c \"%GAME_DIR%\"" -c "c:" -c "%EXE%"
endlocal
