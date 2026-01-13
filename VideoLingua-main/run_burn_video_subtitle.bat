@echo off
REM 单独运行视频字幕烧录功能

REM 设置Python解释器路径，如果Python不在系统路径中，需要指定完整路径
set PYTHON_PATH=python

REM 运行Python脚本
%PYTHON_PATH% burn_video_subtitle.py

REM 暂停以便查看输出
pause
