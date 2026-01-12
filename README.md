# 基于Deepseek生成文案工具


## 快速开始

1. 克隆项目并安装依赖：

```bash
pip install -r requirements.txt
```

2. 在环境变量中设置 API Key：

在.env.example中输入api key后将.example删除
3. 使用 video_tool 生成文案：

```bash
python video_tool.py "一款面向中小企业的社交媒 体管理工具" -p douyin -f caption -t energetic -l short -n 3
```

## 文件说明

- `deepseek_client.py`：Deepseek API 客户端封装，包含重试与错误处理。
- `generator.py`：`CopyGenerator` 类，构建 prompt 并调用客户端生成多个文案变体。
- `video_tool.py`：简单命令行工具示例。

