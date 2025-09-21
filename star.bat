@echo off
echo Iniciando todo el sistema FITTER...

REM === Levantar Action Server ===
start "Rasa Actions" cmd /k "cd /d G:\Fitter && .venv\Scripts\activate && rasa run actions"

REM === Levantar Rasa Core/NLU ===
start "Rasa Server" cmd /k "cd /d G:\Fitter && .venv\Scripts\activate && rasa run --enable-api --cors * -p 5005 --endpoints .\Chatbot\endpoints.yml"

REM === Levantar Backend (Flask/FastAPI) ===
start "Backend" cmd /k "cd /d G:\Fitter\backend && .venv\Scripts\activate && python app.py"

REM === Levantar Frontend (React) ===
start "Frontend" cmd /k "cd /d G:\Fitter\frontend && npm start"

echo Todo se está levantando en consolas separadas.
pause
