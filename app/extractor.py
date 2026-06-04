from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL

from .formatters import natural_paragraphs, plain_text, srt_text, timed_text

Progress = Callable[[str], None]


class ExtractionError(RuntimeError):
    pass


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _is_probably_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def scrape_page_text(url: str) -> str:
    if not _is_probably_url(url):
        return ""
    try:
        response = requests.get(
            url,
            timeout=12,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36",
            },
        )
        response.raise_for_status()
    except requests.RequestException:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    candidates: list[str] = []
    for selector in [
        "title",
        'meta[name="description"]',
        'meta[property="og:title"]',
        'meta[property="og:description"]',
        "h1",
        "article",
    ]:
        for node in soup.select(selector):
            if node.name == "meta":
                text = node.get("content", "")
            else:
                text = node.get_text(" ", strip=True)
            text = _clean_text(text)
            if text and text not in candidates:
                candidates.append(text)
    return "\n".join(candidates[:8])


def _ydl_base_opts() -> dict[str, Any]:
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "socket_timeout": 20,
        "extract_flat": False,
    }


def extract_info(url: str) -> dict[str, Any]:
    with YoutubeDL(_ydl_base_opts()) as ydl:
        return ydl.extract_info(url, download=False)


def pick_caption(info: dict[str, Any]) -> dict[str, str] | None:
    subtitles = info.get("subtitles") or {}
    automatic = info.get("automatic_captions") or {}
    lang_priority = [
        "zh-Hans",
        "zh-CN",
        "zh",
        "zh-Hant",
        "zh-TW",
        "en",
        "en-US",
        "en-GB",
    ]

    for pool_name, pool in [("公开字幕", subtitles), ("自动字幕", automatic)]:
        ordered_langs = [lang for lang in lang_priority if lang in pool]
        ordered_langs.extend(lang for lang in pool.keys() if lang not in ordered_langs)
        for lang in ordered_langs:
            tracks = pool.get(lang) or []
            preferred = sorted(
                tracks,
                key=lambda item: 0 if item.get("ext") in {"vtt", "srt", "json3"} else 1,
            )
            for track in preferred:
                url = track.get("url")
                if url:
                    return {"url": url, "lang": lang, "type": pool_name, "ext": track.get("ext", "")}
    return None


def _parse_timestamp(value: str) -> float:
    value = value.replace(",", ".")
    parts = value.split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
    except ValueError:
        return 0.0
    return 0.0


def parse_subtitle_text(raw: str) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    blocks = re.split(r"\n\s*\n", raw.replace("\r\n", "\n").replace("\r", "\n"))
    timing_re = re.compile(r"(?P<start>\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}|\d{1,2}:\d{2}[.,]\d{1,3})\s+-->\s+(?P<end>\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}|\d{1,2}:\d{2}[.,]\d{1,3})")
    seen: set[tuple[float, str]] = set()

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines or lines[0].startswith("WEBVTT") or lines[0].startswith("Kind:"):
            continue
        timing_index = next((i for i, line in enumerate(lines) if "-->" in line), -1)
        if timing_index < 0:
            continue
        match = timing_re.search(lines[timing_index])
        if not match:
            continue
        text_lines = lines[timing_index + 1 :]
        text = " ".join(
            re.sub(r"<[^>]+>", "", line)
            for line in text_lines
            if not line.startswith(("NOTE", "STYLE"))
        )
        text = _clean_text(text)
        if not text:
            continue
        start = _parse_timestamp(match.group("start"))
        key = (round(start, 2), text)
        if key in seen:
            continue
        seen.add(key)
        segments.append({"start": start, "end": _parse_timestamp(match.group("end")), "text": text})
    return segments


def download_caption(track: dict[str, str]) -> list[dict[str, Any]]:
    response = requests.get(track["url"], timeout=20)
    response.raise_for_status()
    return parse_subtitle_text(response.text)


def download_audio(url: str, work_dir: Path, progress: Progress) -> Path:
    progress("未找到可直接提取的字幕，开始下载公开视频音频")
    output_template = str(work_dir / "source.%(ext)s")
    opts = {
        **_ydl_base_opts(),
        "skip_download": False,
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
                "preferredquality": "192",
            }
        ],
    }
    try:
        with YoutubeDL(opts) as ydl:
            ydl.extract_info(url, download=True)
    except Exception as exc:
        raise ExtractionError(
            "无法下载公开视频音频。可能需要登录、平台限制、DRM、链接不是公开视频，或 yt-dlp 暂不支持。请改用手动上传视频/音频。"
        ) from exc

    candidates = sorted(work_dir.glob("source.*"), key=lambda p: p.stat().st_size, reverse=True)
    if not candidates:
        raise ExtractionError("音频下载后没有找到可用文件，请改用手动上传。")
    return candidates[0]


def transcribe_media(media_path: Path, progress: Progress) -> list[dict[str, Any]]:
    if shutil.which("ffmpeg") is None:
        raise ExtractionError("没有检测到 ffmpeg。请先安装：brew install ffmpeg")
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise ExtractionError("没有安装 faster-whisper。请先运行：pip install -r requirements.txt") from exc

    model_size = os.getenv("WHISPER_MODEL", "small")
    progress(f"加载本地 Whisper 模型：{model_size}")
    model = WhisperModel(model_size, device="auto", compute_type="int8")
    progress("开始语音识别，这一步会根据视频长度花一些时间")
    segments_iter, _info = model.transcribe(str(media_path), vad_filter=True, beam_size=5)
    segments = []
    for segment in segments_iter:
        text = _clean_text(segment.text)
        if text:
            segments.append({"start": float(segment.start), "end": float(segment.end), "text": text})
    if not segments:
        raise ExtractionError("Whisper 没有识别到可用文字。")
    return segments


def assemble_result(
    *,
    title: str,
    method: str,
    segments: list[dict[str, Any]],
    metadata_text: str = "",
    source_url: str = "",
    source_file: str = "",
) -> dict[str, Any]:
    raw_plain = plain_text(segments)
    return {
        "title": title or "未命名视频",
        "method": method,
        "source_url": source_url,
        "source_file": source_file,
        "metadata_text": metadata_text,
        "segments": segments,
        "timed_text": timed_text(segments),
        "plain_text": raw_plain,
        "paragraph_text": natural_paragraphs(raw_plain),
        "srt_text": srt_text(segments),
    }


def extract_from_url(url: str, progress: Progress) -> dict[str, Any]:
    if not _is_probably_url(url):
        raise ExtractionError("请输入 http 或 https 开头的视频网址。")

    with tempfile.TemporaryDirectory(prefix="video-copy-") as temp:
        work_dir = Path(temp)
        progress("读取视频公开信息")
        try:
            info = extract_info(url)
        except Exception as exc:
            raise ExtractionError(
                "无法读取该链接的公开视频信息。若平台需要登录、限制解析或不是公开视频，请使用手动上传。"
            ) from exc

        title = _clean_text(info.get("title")) or "未命名视频"
        meta_parts = [
            _clean_text(info.get("title")),
            _clean_text(info.get("description")),
            scrape_page_text(url),
        ]
        metadata_text = "\n".join(part for part in meta_parts if part)

        progress("检查公开视频字幕/自动字幕")
        caption = pick_caption(info)
        if caption:
            try:
                segments = download_caption(caption)
                if segments:
                    method = f"{caption['type']}：{caption['lang']}"
                    return assemble_result(
                        title=title,
                        method=method,
                        segments=segments,
                        metadata_text=metadata_text,
                        source_url=url,
                    )
            except Exception:
                progress("字幕下载或解析失败，改用音频转写")

        audio_path = download_audio(url, work_dir, progress)
        segments = transcribe_media(audio_path, progress)
        return assemble_result(
            title=title,
            method="本地 Whisper 音频转写",
            segments=segments,
            metadata_text=metadata_text,
            source_url=url,
        )


def extract_from_file(file_path: Path, progress: Progress) -> dict[str, Any]:
    if not file_path.exists():
        raise ExtractionError("上传文件不存在。")
    segments = transcribe_media(file_path, progress)
    return assemble_result(
        title=file_path.stem,
        method="手动上传文件 + 本地 Whisper 转写",
        segments=segments,
        source_file=file_path.name,
    )
