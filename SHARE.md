# 视频文案提取器：群友使用说明

这是一个本地运行的小工具，用来把视频里的口播、字幕、脚本文案提取成可复制的文字稿。

项目地址：

https://github.com/versense84-cmd/video-copy-extractor

## 它能做什么

你粘贴一个公开视频链接，工具会按顺序尝试：

1. 优先读取视频平台公开字幕或自动字幕。
2. 顺手整理网页标题、简介、描述等明显文字信息。
3. 如果没有字幕，就下载公开视频音频，用本地 Whisper 自动转写。
4. 如果平台限制解析，就支持你手动上传自己有权处理的视频或音频文件。

最后会输出：

- 带时间点的文字稿
- 去掉时间码的纯文字
- 自动整理过的自然段文案
- `.txt`、`.srt`、`.md`、`.json` 下载文件

## 适合谁用

适合这些场景：

- 学习视频口播结构
- 整理自己的视频脚本
- 分析公开视频的表达方式
- 把课程、访谈、播客、演讲转成文字
- 给剪辑、复盘、笔记做参考

不适合这些用途：

- 搬运别人内容
- 破解付费内容
- 抓取私密视频
- 绕过平台登录或 DRM 限制

## 使用前准备

这个工具目前主要面向 Mac 用户。

需要安装：

- Python 3.10 到 3.12
- ffmpeg
- 项目依赖包

如果你有 Homebrew，可以先运行：

```bash
brew install python@3.12 ffmpeg
```

## 一键下载项目

打开终端，运行：

```bash
git clone https://github.com/versense84-cmd/video-copy-extractor.git
cd video-copy-extractor
```

## 安装依赖

推荐用 Python 3.12：

```bash
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

如果你的电脑没有 `/opt/homebrew/bin/python3.12`，可以试：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 启动工具

```bash
./run.sh
```

启动后，在浏览器打开：

```text
http://127.0.0.1:8787
```

## 怎么用

1. 打开本地网页。
2. 粘贴视频链接。
3. 点击“开始提取”。
4. 等待进度完成。
5. 复制整理好的文案，或者下载 `txt` / `srt` / `md` / `json` 文件。

如果链接提取失败：

1. 切换到“手动上传”。
2. 上传你有权处理的视频或音频文件。
3. 等待 Whisper 本地转写。

## 常见问题

### 第一次运行很慢正常吗？

正常。第一次用 Whisper 时会下载模型文件，后面会快一些。

### 小红书、抖音、B 站链接都能直接提取吗？

不保证。平台规则会变化，有些链接需要登录、权限或平台侧限制。工具不会绕过这些限制。失败时可以改用手动上传。

### 能不能转写英文？

可以。Whisper 支持多语言。中文、英文、日文等常见语言都可以试。

### 识别不准怎么办？

可以换更大的 Whisper 模型，比如：

```bash
WHISPER_MODEL=medium ./run.sh
```

模型越大通常越准，但也更慢。

### 会把视频上传到云端吗？

不会。工具是在本地运行，Whisper 转写也在本地执行。

## 给群友的一句话介绍

这是一个开源的本地“视频文案提取器”：粘贴公开视频链接，优先提取字幕；没有字幕就用本地 Whisper 转写音频，最后生成可复制、可下载的文字稿。

项目地址：

https://github.com/versense84-cmd/video-copy-extractor
