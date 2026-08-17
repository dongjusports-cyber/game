@echo off
REM Chay trong DOSBox — mount CD + khoi dong Sango II syllable
setlocal

cd /d C:\

REM --- Mount CD-ROM: restored disc (uu tien) > cue > ccd ---
if exist C:\CD-ROM\restored\Sango2_disc.cue (
  imgmount d C:\CD-ROM\restored\Sango2_disc.cue -t cdrom
  goto :cd_ok
)
if exist C:\CD-ROM\Sango2.cue (
  imgmount d C:\CD-ROM\Sango2.cue -t cdrom
  goto :cd_ok
)
if exist C:\CD-ROM\Sango2.ccd (
  imgmount d C:\CD-ROM\Sango2.ccd -t cdrom
  goto :cd_ok
)
if exist C:\CD-ROM\ (
  mount d C:\CD-ROM -t cdrom -label PIONEERV.01
  goto :cd_ok
)

echo.
echo CANH BAO: Khong tim thay CD image!
echo Dat vao C:\CD-ROM\ :
echo   Sango2.cue + Sango2.img   (CloneCD — co nhac CD day du)
echo   hoac Sango2.ccd + .img + .sub
echo.
goto :play

:cd_ok
echo CD-ROM mounted as D:

:play
cd SANGO2
if not exist SAN2-VN.EXE (
  echo LOI: Chua co SAN2-VN.EXE — chay Deploy Syllable.bat tren Windows
  pause
  exit /b 1
)
if not exist FONT16.PAT (
  echo LOI: Chua co FONT16.PAT — chay Deploy Syllable.bat tren Windows
  pause
  exit /b 1
)
C:\UNIVBE
SAN2-VN
