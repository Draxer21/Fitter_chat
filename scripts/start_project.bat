@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."
for %%I in ("%ROOT_DIR%") do set "ROOT_DIR=%%~fI"
set "CHATBOT_DIR=%ROOT_DIR%\Chatbot"
set "FRONTEND_DIR=%ROOT_DIR%\frontend"
set "DEFAULT_VENV=%ROOT_DIR%\.venv\Scripts\python.exe"
if not defined PYTHONWARNINGS (
    rem Silencia deprecations ruidosas en Rasa/TensorFlow/SQLAlchemy
    set "PYTHONWARNINGS=ignore::DeprecationWarning:pkg_resources,ignore::DeprecationWarning:sqlalchemy,ignore::sqlalchemy.exc.MovedIn20Warning,ignore::DeprecationWarning:jax"
)

if not defined PYTHON_BIN (
    if exist "%DEFAULT_VENV%" (
        set "PYTHON_BIN=%DEFAULT_VENV%"
    ) else (
        call :find_python
    )
)

if not defined PYTHON_BIN (
    echo [x] No se encontro ningun interprete de Python. Define la variable PYTHON_BIN o crea .venv.
    exit /b 1
)

call "%PYTHON_BIN%" -V >nul 2>&1
if errorlevel 1 (
    echo [x] No se pudo ejecutar "%PYTHON_BIN%".
    exit /b 1
)

call :require_cmd npm || exit /b 1

call "%PYTHON_BIN%" -m pip show rasa >nul 2>&1
if errorlevel 1 (
    echo [x] El paquete 'rasa' no esta instalado en el entorno de "%PYTHON_BIN%".
    echo     Ejecuta: pip install rasa
    exit /b 1
)

call "%PYTHON_BIN%" -m pip show flask >nul 2>&1
if errorlevel 1 (
    echo [x] Flask no esta instalado en el entorno de "%PYTHON_BIN%".
    echo     Ejecuta: pip install -r requirements.txt
    exit /b 1
)

if not exist "%CHATBOT_DIR%" (
    echo [x] No existe el directorio "%CHATBOT_DIR%".
    exit /b 1
)

if not exist "%FRONTEND_DIR%" (
    echo [x] No existe el directorio "%FRONTEND_DIR%".
    exit /b 1
)

set "HAS_MODEL="
for %%F in ("%CHATBOT_DIR%\models\*.tar.gz") do (
    set "HAS_MODEL=1"
    goto after_models
)
:after_models
if not defined HAS_MODEL (
    echo [!] No se detectaron modelos en Chatbot\models. Ejecuta "rasa train" antes de iniciar Rasa.
)

if not defined PROFILE_ENCRYPTION_KEY (
    echo [!] La variable PROFILE_ENCRYPTION_KEY no esta configurada. Usa una clave Fernet antes de trabajar con perfiles reales.
)

if not defined BACKEND_PORT set "BACKEND_PORT=5000"
if not defined CHATBOT_PORT set "CHATBOT_PORT=5005"
if not defined ACTION_PORT set "ACTION_PORT=5055"
if not defined FRONTEND_PORT set "FRONTEND_PORT=3000"

set START_BACKEND=1
set START_CHATBOT=1
set START_ACTIONS=1
set START_FRONTEND=1

:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="--skip-backend" (
    set START_BACKEND=0
    shift
    goto parse_args
)
if /I "%~1"=="--skip-chatbot" (
    set START_CHATBOT=0
    shift
    goto parse_args
)
if /I "%~1"=="--skip-actions" (
    set START_ACTIONS=0
    shift
    goto parse_args
)
if /I "%~1"=="--skip-frontend" (
    set START_FRONTEND=0
    shift
    goto parse_args
)
if /I "%~1"=="--help" (
    call :usage
    exit /b 0
)
echo [x] Opcion desconocida: %~1
call :usage
exit /b 1

:args_done
if "%START_BACKEND%%START_CHATBOT%%START_ACTIONS%%START_FRONTEND%"=="0000" (
    echo [x] No hay servicios seleccionados para iniciar.
    exit /b 1
)

echo.
echo === Iniciando servicios desde %ROOT_DIR% ===

if "%START_BACKEND%"=="1" call :launch_backend
if "%START_CHATBOT%"=="1" call :launch_rasa
if "%START_ACTIONS%"=="1" call :launch_actions
if "%START_FRONTEND%"=="1" call :launch_frontend

echo.
echo Todos los servicios solicitados fueron lanzados en nuevas ventanas de terminal.
echo Usa Ctrl+C o cierra cada ventana para detenerlos.
exit /b 0

:launch_backend
echo -> Backend Flask (puerto %BACKEND_PORT%)
start "backend" cmd /K "cd /d ^"%ROOT_DIR%^" && set FLASK_APP=backend.app:create_app && set FLASK_ENV=development && set FLASK_RUN_PORT=%BACKEND_PORT% && ^"%PYTHON_BIN%^" -m flask run --host 0.0.0.0 --port %BACKEND_PORT% --debug"
exit /b 0

:launch_rasa
echo -> Servidor Rasa (puerto %CHATBOT_PORT%)
start "rasa" cmd /K "cd /d ^"%CHATBOT_DIR%^" && ^"%PYTHON_BIN%^" -m rasa run --enable-api --cors "*" --endpoints endpoints.yml --credentials credentials.yml --port %CHATBOT_PORT%"
exit /b 0

:launch_actions
echo -> Servidor de acciones (puerto %ACTION_PORT%)
start "actions" cmd /K "cd /d ^"%ROOT_DIR%^" && ^"%PYTHON_BIN%^" -m rasa run actions --actions actions.actions --port %ACTION_PORT% --debug"
exit /b 0

:launch_frontend
echo -> Frontend React (puerto %FRONTEND_PORT%)
start "frontend" cmd /K "cd /d ^"%FRONTEND_DIR%^" && set PORT=%FRONTEND_PORT% && set BROWSER=none && npm start"
exit /b 0

:usage
echo.
echo Uso: scripts\start_project.bat [opciones]
echo.
echo   --skip-backend     No inicia el backend Flask
echo   --skip-chatbot     No inicia el servidor principal de Rasa
echo   --skip-actions     No inicia el servidor de acciones
echo   --skip-frontend    No inicia el frontend React
echo   --help             Muestra este mensaje
echo.
echo Variables utiles:
echo   PYTHON_BIN       Ruta al interprete de Python (por defecto .venv\Scripts\python.exe)
echo   BACKEND_PORT     Puerto de Flask (5000)
echo   CHATBOT_PORT     Puerto HTTP de Rasa (5005)
echo   ACTION_PORT      Puerto del servidor de acciones (5055)
echo   FRONTEND_PORT    Puerto del frontend React (3000)
echo.
exit /b 0

:require_cmd
where %~1 >nul 2>&1
if errorlevel 1 (
    echo [x] El comando "%~1" no esta disponible en el PATH. Instala la herramienta correspondiente.
    exit /b 1
)
exit /b 0

:find_python
for %%P in (python3 python py) do (
    where %%P >nul 2>&1 && (
        set "PYTHON_BIN=%%P"
        goto :eof
    )
)
goto :eof
