@echo off
:loop
REM Python
python "main.py"

REM 10분 대기 (600초)
timeout /t 600 /nobreak >nul
goto loop
