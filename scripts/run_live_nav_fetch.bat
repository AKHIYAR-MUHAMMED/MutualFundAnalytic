# run_live_nav_fetch.bat

@echo off
REM Batch file to execute the live NAV fetch script
python "%~dp0..\scripts\live_nav_fetch.py"

REM You can schedule this batch file using Windows Task Scheduler to run daily.
