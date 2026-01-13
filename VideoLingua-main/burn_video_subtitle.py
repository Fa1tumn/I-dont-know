#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
单独运行视频字幕烧录功能
"""

import os
import sys
from subtitle_burner import burn_subtitles_to_video

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    # 设置实际测试文件路径
    video_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output/test/test_demo.mp4")
    subtitle_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output/test/test_demo.bilingual.srt")
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output/test")

    # 检查输入文件是否存在
    if not os.path.exists(video_path):
        print(f"测试视频文件不存在: {video_path}")
        return
    if not os.path.exists(subtitle_path):
        print(f"测试字幕文件不存在: {subtitle_path}")
        return

    # 预期的输出路径
    expected_output = os.path.join(output_dir, "test_demo.bilingual.hardcoded.mp4")

    # 如果输出文件已存在，先删除
    if os.path.exists(expected_output):
        os.remove(expected_output)
        print(f"已删除已存在的输出文件: {expected_output}")

    # 调用被测试函数
    output_video = burn_subtitles_to_video(
        video_path,
        subtitle_path,
        font_size=16,  # 使用较小的字体大小
        position="bottom",
        font_color="white",
        outline_color="black",
        shadow_radius=0.3  # 设置阴影半径为3
    )

    # 验证结果
    if output_video:
        print(f"字幕烧录成功！输出视频路径: {output_video}")
        file_size = os.path.getsize(output_video)
        print(f"输出视频文件大小: {file_size / (1024 * 1024):.2f} MB")
        assert file_size > 1024 * 1024, "输出视频文件过小，可能未正确生成"
    else:
        print("字幕烧录失败")

if __name__ == '__main__':
    main()
