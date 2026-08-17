@echo off
REM Build ban Sango II tieng Viet (ASCII) — chay trong thu muc clone repo
REM Can: Python 3, game goc tai GAME_DIR

setlocal
set "GAME_DIR=D:\Game\SAN\SANGO2"
set "REPO=%~dp0.."
cd /d "%REPO%"

echo === SANGO2-VN build ===
echo Game: %GAME_DIR%
echo.

if not exist "%GAME_DIR%\SAN2.EXE" (
  echo ERROR: Khong tim thay SAN2.EXE tai %GAME_DIR%
  exit /b 1
)

echo [1/5] Trich city/panel/ui_menu...
python tools\extract_city_panel.py
if errorlevel 1 exit /b 1

echo.
echo [2/5] Kiem tra dich...
python tools\build_patch.py --dry-run
if errorlevel 1 exit /b 1

echo.
echo [3/5] Patch SAN2.EXE...
python tools\build_patch.py "%GAME_DIR%\SAN2.EXE" -o "%GAME_DIR%\SAN2-VN.EXE"
if errorlevel 1 exit /b 1

echo.
echo [4/5] Patch font Latin...
if exist "%GAME_DIR%\FONT16.PAT" (
  python tools\patch_font_latin.py --all --game-dir "%GAME_DIR%"
) else (
  echo WARN: Khong thay FONT16.PAT — bo qua buoc font
)

echo.
echo [5/5] Copy font VN neu co...
if exist "%GAME_DIR%\FONT16-VN.PAT" copy /Y "%GAME_DIR%\FONT16-VN.PAT" "%GAME_DIR%\FONT16.PAT"
if exist "%GAME_DIR%\FONT24-VN.PAT" copy /Y "%GAME_DIR%\FONT24-VN.PAT" "%GAME_DIR%\FONT24.PAT"

echo.
echo === Xong ===
echo Chay: scripts\test_dosbox.bat
echo Hoac: D:\Game\SAN\Play Sango2 VN.bat
endlocal
