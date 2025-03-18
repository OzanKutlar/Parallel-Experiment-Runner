@echo off
echo [Webserver Proxy] Starting Proxy

:retry
echo [Webserver Proxy] Web Server Available at : 171.22.173.112:33000
ssh -N -R 0.0.0.0:33000:127.0.0.1:33000 -p 51821 evo@171.22.173.112
echo [Webserver Proxy] Proxy disconnected. Retrying in 5 seconds...
timeout /t 5
goto retry
