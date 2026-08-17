@echo off
REM DEPRECATED — dung Play Sango2 Syllable.bat cho ban co dau
cd /d "%~dp0"
echo.
echo *** CANH BAO ***
echo File nay tro D:\Game\SAN (repo cu, ASCII khong dau).
echo Ban syllable CO DAU: Play Sango2 Syllable.bat
echo.
choice /C YN /M "Chuyen sang Play Sango2 Syllable.bat"
if errorlevel 2 exit /b 0
call "%~dp0Play Sango2 Syllable.bat"
