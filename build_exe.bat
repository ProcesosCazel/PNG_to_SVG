@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo  CREANDO ConvertidorImagenSVG - FINAL
echo  Loading screen + una sola instancia
echo ==============================================
echo.

where py >nul 2>&1
if %errorlevel%==0 (
    set "PY=py"
) else (
    where python >nul 2>&1
    if errorlevel 1 goto :no_python
    set "PY=python"
)

%PY% --version
if errorlevel 1 goto :no_python

echo.
echo Instalando dependencias...
%PY% -m pip install --upgrade pip
if errorlevel 1 goto :install_error
%PY% -m pip install --only-binary=:all: -r requirements.txt
if errorlevel 1 goto :install_error

echo.
echo Limpiando compilaciones anteriores y archivos temporales...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist build_onefile rmdir /s /q build_onefile
if exist dist_onefile rmdir /s /q dist_onefile
if exist __pycache__ rmdir /s /q __pycache__
if exist ConvertidorImagenSVG.spec del /q ConvertidorImagenSVG.spec
if exist ConvertidorImagenSVG_OneFile.spec del /q ConvertidorImagenSVG_OneFile.spec

echo.
echo Generando ejecutable recomendado...
rem ONEDIR evita la extraccion completa a TEMP de ONEFILE y abre mas rapido.
rem SPLASH muestra inmediatamente que la aplicacion se esta cargando.
%PY% -m PyInstaller --noconfirm --clean --onedir --windowed --splash splash.png --name ConvertidorImagenSVG launcher.py
if errorlevel 1 goto :build_error

echo.
echo ==============================================
echo  LISTO
echo.
echo  Comparte TODA esta carpeta:
echo  %CD%\dist\ConvertidorImagenSVG
echo.
echo  Los tecnicos abren:
echo  ConvertidorImagenSVG.exe
echo ==============================================
echo.
pause
exit /b 0

:no_python
echo ERROR: No se encontro Python.
pause
exit /b 1

:install_error
echo ERROR: No fue posible instalar las dependencias.
pause
exit /b 1

:build_error
echo ERROR: Fallo la creacion del ejecutable.
pause
exit /b 1
