@echo off
REM ===== SANGO II — CLICK AND PLAY (co dau + nhac CD) =====
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set "G=%CD%"
set "G=%G:\=/%"
set "G=%G:/=\%"

title Sango II — Play

echo.
echo  Sango II — Khoi dong...
echo  Thu muc: %G%
echo.

REM --- CD ---
call "%~dp0_ensure_cd.bat"
if errorlevel 1 pause & exit /b 1

REM --- Deploy font + EXE ---
call "%~dp0Deploy Syllable.bat"
if errorlevel 1 pause & exit /b 1

REM --- Tim DOSBox-X ---
set "DBX="
if exist "C:\DOSBox-X\dosbox-x.exe" set "DBX=C:\DOSBox-X\dosbox-x.exe"
if exist "%ProgramFiles%\DOSBox-X\dosbox-x.exe" set "DBX=%ProgramFiles%\DOSBox-X\dosbox-x.exe"
if exist "%ProgramFiles(x86)%\DOSBox-X\dosbox-x.exe" set "DBX=%ProgramFiles(x86)%\DOSBox-X\dosbox-x.exe"
if exist "%LocalAppData%\Programs\DOSBox-X\dosbox-x.exe" set "DBX=%LocalAppData%\Programs\DOSBox-X\dosbox-x.exe"

if "%DBX%"=="" (
  echo LOI: Khong tim thay DOSBox-X
  echo Cai tu: https://dosbox-x.com/
  echo Dat vao C:\DOSBox-X\dosbox-x.exe
  pause
  exit /b 1
)

REM --- Tao conf runtime (duong dan tuyet doi, auto mount CD) ---
set "CONF=%G%\_runtime.conf"
set "CUE=%G%\CD-ROM\restored\Sango2_disc.cue"

(
echo [sdl]
echo output=default
echo fullscreen=false
echo.
echo [dosbox]
echo machine=svga_s3
echo memsize=64
echo.
echo [cpu]
echo core=auto
echo cycles=max
echo.
echo [render]
echo scaler=normal2x
echo.
echo [mixer]
echo nosound=false
echo rate=44100
echo.
echo [midi]
echo mpu401=intelligent
echo mididevice=win32
echo.
echo [sblaster]
echo sbtype=sbpro2
echo sbbase=220
echo irq=7
echo dma=1
echo hdma=5
echo oplmode=opl3
echo.
echo [cdrom]
echo cdrom = enable
echo.
echo [dos]
echo xms=true
echo ems=true
echo umb=true
echo.
echo [autoexec]
echo @echo off
echo mount c "%G%"
echo imgmount d "%CUE%" -t cdrom
echo SET BLASTER=A220 I7 D1 H5 T6
echo echo.
echo echo CD-ROM mounted as D: — nhac CD bat
echo echo.
echo c:
echo cd SANGO2
echo C:\UNIVBE
echo SAN2-VN
) > "%CONF%"

echo Mo DOSBox-X...
echo   C: = game
echo   D: = CD PIONEERV01 ^(nhac^)
echo.
start "" /wait "%DBX%" -conf "%CONF%"
endlocal
