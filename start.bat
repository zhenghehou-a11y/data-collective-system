@echo off
echo Starting Project Evaluation System API service...
start /min cmd /c "uvicorn main:app --host 0.0.0.0 --port 8000"
echo [SUCCESS] Service started in the background!
echo [INFO] API Docs: http://localhost:8000/docs
pause