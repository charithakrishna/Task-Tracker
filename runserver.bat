@echo OFF

:: VENV Activation
call .\venv\Scripts\activate.bat

:: Change to the project directory (optional but recommended)
cd /d "%~dp0"

:: Run Django server
python manage.py runserver

pause