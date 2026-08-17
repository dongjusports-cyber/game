@echo off
REM Xoa D:\Game\Sango2 sau khi da chuyen sang D:\Game\SAN
echo Dong DOSBox / Cursor neu dang mo game hoac repo cu.
pause
if exist "D:\Game\Sango2\Installed" rmdir /S /Q "D:\Game\Sango2\Installed" 2>nul
if exist "D:\Game\Sango2\sango2" rmdir /S /Q "D:\Game\Sango2\sango2" 2>nul
if exist "D:\Game\Sango2" rmdir /S /Q "D:\Game\Sango2" 2>nul
if exist "D:\Game\Sango2" (
  echo Con file bi khoa trong D:\Game\Sango2 — thu lai sau khi dong IDE.
) else (
  echo Da xoa D:\Game\Sango2
)
pause
