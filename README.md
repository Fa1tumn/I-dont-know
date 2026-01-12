# 基于Deepseek生成文案工具


## 快速开始

1. 克隆项目并安装依赖：

```bash
pip install -r requirements.txt
```

2. 在环境变量中设置 API Key：

在.env.example中输入api key后将.example删除

3. 使用 video_tool 生成文案：

以下是 `video_tool.py` 的命令行参数及其中文说明：

- `brief`：简短的产品或视频创意描述（必填）
- `-p, --platform`：目标平台（例如：`douyin`, `tiktok`, `youtube`），默认 `short-video`
- `-f, --format`（`--fmt`）：输出格式，`script`（脚本）或 `caption`（标题/字句），默认 `script`
- `-t, --tone`：文案语气（例如：`energetic`, `professional`）
- `-l, --length`：文案长度（`short`, `medium`, `long`）
- `-n, --number`：生成变体数量（整数），默认 `1`
- `--out`：输出文件路径（JSON）。若不指定，则打印到标准输出（终端）
- `--mock`：离线模拟模式（不开网络，返回 mock 文案），用于本地测试

示例：

```bash
python context/video_tool.py "一款面向中小企业的社交媒体管理工具" -p douyin -f caption -t energetic -l short -n 3 --mock
```


## 文件说明

- `deepseek_client.py`：Deepseek API 客户端封装，包含重试与错误处理。
- `generator.py`：`CopyGenerator` 类，构建 prompt 并调用客户端生成多个文案变体。
- `video_tool.py`：简单命令行工具示例。

