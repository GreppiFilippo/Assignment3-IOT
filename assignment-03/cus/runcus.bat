@echo off
echo Checking for uv command...
where uv >nul 2>&1
if %errorlevel%==0 (
  echo uv is installed. Starting with uv...
  set PYTHONPATH=%CD%\src
  uv run uvicorn src.main:app --host 127.0.0.1 --port 8000
  exit /b
)

echo uv not found. Installing dependencies and running...
where python >nul 2>&1
if %errorlevel%==0 (
  python -m pip install --user fastapi uvicorn paho-mqtt pyserial pydantic requests
  set PYTHONPATH=%CD%\src
  python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
) else (
  echo Python not found. Please install Python 3.
  exit /b 1
)
