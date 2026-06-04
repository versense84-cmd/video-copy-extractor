import html
import json
import re
from pathlib import Path
from typing import Any


def format_timestamp(seconds: float, srt: bool = False) -> str:
    seconds = max(0.0, float(seconds or 0))
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    sep = "," if srt else "."
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{sep}{millis:03d}"


def plain_text(segments: list[dict[str, Any]]) -> str:
    return "\n".join(s["text"].strip() for s in segments if s.get("text", "").strip())


def natural_paragraphs(text: str, max_chars: int = 260) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return ""

    parts = re.split(r"(?<=[。！？!?；;])\s*|(?<=[.])\s+", compact)
    paragraphs: list[str] = []
    current = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if current and len(current) + len(part) > max_chars:
            paragraphs.append(current.strip())
            current = part
        else:
            current = f"{current}{part}" if re.search(r"[\u4e00-\u9fff]$", current) else f"{current} {part}".strip()
    if current:
        paragraphs.append(current.strip())
    return "\n\n".join(paragraphs)


def timed_text(segments: list[dict[str, Any]]) -> str:
    lines = []
    for segment in segments:
        text = segment.get("text", "").strip()
        if text:
            lines.append(f"[{format_timestamp(segment.get('start', 0))}] {text}")
    return "\n".join(lines)


def srt_text(segments: list[dict[str, Any]]) -> str:
    blocks = []
    for idx, segment in enumerate(segments, 1):
        text = html.unescape(segment.get("text", "")).strip()
        if not text:
            continue
        start = format_timestamp(segment.get("start", 0), srt=True)
        end = format_timestamp(segment.get("end", segment.get("start", 0) + 2), srt=True)
        blocks.append(f"{idx}\n{start} --> {end}\n{text}")
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def markdown_text(result: dict[str, Any]) -> str:
    title = result.get("title") or "视频文案提取结果"
    sections = [
        f"# {title}",
        "## 来源",
        result.get("source_url") or result.get("source_file") or "",
        "## 提取方式",
        result.get("method", ""),
    ]
    metadata_text = result.get("metadata_text", "").strip()
    if metadata_text:
        sections.extend(["## 页面/视频文字", metadata_text])
    sections.extend(
        [
            "## 带时间点文本",
            result.get("timed_text", ""),
            "## 纯文字版本",
            result.get("plain_text", ""),
            "## 自然段整理版本",
            result.get("paragraph_text", ""),
        ]
    )
    return "\n\n".join(part for part in sections if part is not None)


def write_outputs(output_dir: Path, job_id: str, result: dict[str, Any]) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "txt": result.get("paragraph_text", ""),
        "srt": result.get("srt_text", ""),
        "md": markdown_text(result),
        "json": json.dumps(result, ensure_ascii=False, indent=2),
    }
    saved: dict[str, str] = {}
    for ext, content in files.items():
        path = output_dir / f"{job_id}.{ext}"
        path.write_text(content, encoding="utf-8")
        saved[ext] = path.name
    return saved
