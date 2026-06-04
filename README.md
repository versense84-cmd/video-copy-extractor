# 视频文案提取器

一个本地网页工具：输入公开视频网址，优先提取平台公开字幕；没有字幕时下载公开视频音频并用本地 Whisper 转写。也支持手动上传视频/音频文件。

如果你只是想快速了解这个工具、发给群友或朋友，请看：[群友使用说明](./SHARE.md)。

## 技术方案

处理优先级：

1. 用 `yt-dlp` 读取公开视频信息，查找公开字幕、自动字幕、caption 或 transcript，并优先提取。
2. 同时整理标题、简介、网页 `title`、`description`、`h1`、`article` 等明显文字内容。
3. 如果没有可用字幕，下载公开视频音频，用 `faster-whisper` 在本地转写。
4. 如果链接需要登录、付费、DRM、私密权限，工具不会绕过限制，会提示改用手动上传。

输出内容：

- 原始字幕 / 原始转写稿
- 去掉时间码后的纯文字
- 按自然段整理后的文案
- 带大概时间点的句子
- 可下载 `.txt`、`.srt`、`.md`、`.json`

## 项目结构

```text
video-copy-extractor/
  app/
    main.py          # FastAPI 接口、任务队列、下载接口
    extractor.py     # 字幕提取、网页文字提取、音频下载、Whisper 转写
    formatters.py    # txt/srt/md/json 格式化
  static/
    index.html       # 本地网页
    styles.css       # 页面样式
    app.js           # 提交任务、轮询进度、复制和下载
  data/
    uploads/         # 上传文件临时目录
    outputs/         # 输出文件目录
  requirements.txt
  README.md
```

## Mac 安装

建议使用 Python 3.10 到 3.12。`faster-whisper` 的底层依赖通常不适合太新的 Python 版本。如果你的 `python3 --version` 是 3.14，建议用 Homebrew 安装 3.12：

```bash
brew install python@3.12 ffmpeg
```

进入项目目录：

```bash
cd /Users/luyuxi/Documents/视频类/video-copy-extractor
```

创建虚拟环境并安装依赖：

```bash
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

如果你没有 Homebrew 的 Python 3.12，也可以先试：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 运行

```bash
cd /Users/luyuxi/Documents/视频类/video-copy-extractor
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8787
```

或者直接运行：

```bash
cd /Users/luyuxi/Documents/视频类/video-copy-extractor
./run.sh
```

打开：

```text
http://127.0.0.1:8787
```

## Whisper 模型

默认模型是 `small`，速度和准确率比较平衡。第一次使用会自动下载模型文件。

可以临时指定更快或更准的模型：

```bash
WHISPER_MODEL=base uvicorn app.main:app --reload --host 127.0.0.1 --port 8787
WHISPER_MODEL=medium uvicorn app.main:app --reload --host 127.0.0.1 --port 8787
```

常用选择：

- `base`：更快，准确率一般
- `small`：默认，适合日常口播
- `medium`：更准，但更慢、占用更高

## 平台备用方案

YouTube、B 站、抖音、小红书等平台的可解析性会随平台规则变化。如果链接失败，常见原因是：

- 视频需要登录或会员权限
- 视频不是公开内容
- 平台限制了网页解析
- 链接里没有公开视频文件或公开字幕
- 内容有 DRM 或区域限制

备用方案：

1. 用你有权处理的方式保存视频或音频文件。
2. 打开工具的“手动上传”。
3. 上传 `.mp4`、`.mov`、`.m4a`、`.mp3`、`.wav` 等文件。
4. 工具会跳过平台解析，直接本地转写。

## 使用边界

这个工具只用于学习、分析、整理你有权处理的公开或自有内容。它不会做登录绕过、付费破解、DRM 绕过或私密内容爬取。

## 发布到 GitHub

如果已经安装并登录 GitHub CLI：

```bash
cd /Users/luyuxi/Documents/视频类/video-copy-extractor
gh repo create video-copy-extractor --public --source=. --remote=origin --push
```

如果没有 GitHub CLI，可以在 GitHub 网页新建一个空仓库，然后运行：

```bash
cd /Users/luyuxi/Documents/视频类/video-copy-extractor
git remote add origin https://github.com/你的用户名/video-copy-extractor.git
git push -u origin main
```

发布前确认 `.venv`、上传文件、输出文件不会被提交，项目里的 `.gitignore` 已经处理了这些本地文件。
