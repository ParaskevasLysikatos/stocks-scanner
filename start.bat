@echo off
echo === Stock Speculation Scanner ===
echo.
echo Stopping old containers...
docker-compose down
echo.
echo Removing old images...
docker rmi stock-scanner-frontend stock-scanner-backend 2>nul
echo.
echo Building fresh images (no cache)...
docker-compose build --no-cache
echo.
echo Starting containers...
docker-compose up -d
echo.
echo === Ready! Open http://localhost in your browser ===
pause
