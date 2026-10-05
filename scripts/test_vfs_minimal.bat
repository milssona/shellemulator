@echo off
cd /d "%~dp0.."
python tools\make_vfs.py
python src\main.py --vfs build\vfs_minimal.zip