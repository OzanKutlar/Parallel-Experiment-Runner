@echo off
echo [Experiment Proxy] Starting Proxy

:retry
echo [Experiment Proxy] Experiment Server Available at : 171.22.173.112:3753
ssh -N -R 0.0.0.0:3753:127.0.0.1:3753 -p 51821 evo@171.22.173.112
echo [Experiment Proxy] Proxy disconnected. Retrying in 5 seconds...
timeout /t 5
goto retry
