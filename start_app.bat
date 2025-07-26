@echo off
REM Script de inicio para DataApp1 en Windows
REM Análisis Exploratorio de Datos con IA

echo.
echo ========================================
echo 🚀 DataApp1 - Iniciando aplicación
echo ========================================
echo.

REM Verificar si existe el entorno virtual
if not exist "venv" (
    echo ❌ Entorno virtual no encontrado
    echo 🔧 Ejecuta primero: python setup.py
    pause
    exit /b 1
)

REM Activar entorno virtual
echo 🔄 Activando entorno virtual...
call venv\Scripts\activate

REM Verificar si Flask está instalado
python -c "import flask" 2>nul
if errorlevel 1 (
    echo ❌ Flask no está instalado
    echo 🔧 Ejecuta: pip install -r backend\requirements.txt
    pause
    exit /b 1
)

REM Cambiar al directorio backend
cd backend

REM Iniciar servidor Flask
echo 🌐 Iniciando servidor Flask...
echo 📍 Servidor disponible en: http://localhost:5000
echo 🌍 Frontend disponible en: ..\frontend\index.html
echo.
echo 🛑 Presiona Ctrl+C para detener el servidor
echo.

python app.py

echo.
echo 👋 Servidor detenido
pause
