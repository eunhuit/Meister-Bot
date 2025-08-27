@echo off
:loop
REM Python 스크립트 실행 (경로는 실제로 바꿔주세요)
python "main.py"

REM 10분 대기 (600초)
timeout /t 600 /nobreak >nul
goto loop
