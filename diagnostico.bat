@echo off
setlocal
cd /d "%~dp0"

echo Ejecutando la aplicacion desde Python con consola visible...
where py >nul 2>&1
if %errorlevel%==0 (
    py launcher.py
) else (
    python launcher.py
)

echo.
echo Si aparecio un error arriba, copia el texto completo.
pause
