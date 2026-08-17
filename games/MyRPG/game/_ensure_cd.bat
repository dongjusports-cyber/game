@echo off
REM Dam bao co Sango2_disc.cue + .bin (khong can Python)
setlocal
set "CDDIR=%~dp0CD-ROM"
set "REST=%CDDIR%\restored"

if not exist "%CDDIR%\Sango2.img" (
  echo LOI: Thieu CD-ROM\Sango2.img — chay: git lfs pull
  exit /b 1
)

if not exist "%REST%" mkdir "%REST%"

if not exist "%REST%\Sango2_disc.cue" (
  echo LOI: Thieu restored\Sango2_disc.cue — git pull
  exit /b 1
)

if not exist "%REST%\Sango2_disc.bin" (
  echo Dang tao Sango2_disc.bin tu Sango2.img ^(~611 MB, doi 1-2 phut^)...
  copy /Y "%CDDIR%\Sango2.img" "%REST%\Sango2_disc.bin"
)

echo OK: CD PIONEERV01 san sang
exit /b 0
