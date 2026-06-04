from __future__ import annotations

import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .extractor import ExtractionError, extract_from_file, extract_from_url
from .formatters import write_outputs

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
OUTPUT_DIR = BASE_DIR / "data" / "outputs"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="视频文案提取器")
executor = ThreadPoolExecutor(max_workers=2)
jobs: dict[str, dict[str, Any]] = {}


def set_progress(job_id: str, message: str) -> None:
    jobs[job_id]["progress"].append(message)
    jobs[job_id]["message"] = message


def run_job(job_id: str, mode: str, value: str) -> None:
    jobs[job_id].update({"status": "running", "message": "开始处理"})
    try:
        if mode == "url":
            result = extract_from_url(value, lambda msg: set_progress(job_id, msg))
        else:
            result = extract_from_file(Path(value), lambda msg: set_progress(job_id, msg))

        files = write_outputs(OUTPUT_DIR, job_id, result)
        jobs[job_id].update(
            {
                "status": "done",
                "message": "提取完成",
                "result": result,
                "files": files,
            }
        )
    except ExtractionError as exc:
        jobs[job_id].update({"status": "error", "message": str(exc)})
    except Exception as exc:
        jobs[job_id].update({"status": "error", "message": f"处理失败：{exc}"})


@app.post("/api/extract")
def start_extract(url: str = Form("")) -> dict[str, str]:
    url = url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="请粘贴一个视频网址。")
    job_id = uuid.uuid4().hex
    jobs[job_id] = {"status": "queued", "message": "排队中", "progress": []}
    executor.submit(run_job, job_id, "url", url)
    return {"job_id": job_id}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)) -> dict[str, str]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".mp3", ".m4a", ".wav", ".aac"}:
        raise HTTPException(status_code=400, detail="请上传常见视频或音频文件。")

    job_id = uuid.uuid4().hex
    safe_name = f"{job_id}{suffix}"
    target = UPLOAD_DIR / safe_name
    with target.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    jobs[job_id] = {"status": "queued", "message": "排队中", "progress": ["文件上传完成"]}
    executor.submit(run_job, job_id, "file", str(target))
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="没有找到这个任务。")
    return job


@app.get("/api/download/{job_id}/{ext}")
def download_file(job_id: str, ext: str) -> FileResponse:
    if ext not in {"txt", "srt", "md", "json"}:
        raise HTTPException(status_code=400, detail="不支持的文件格式。")
    path = OUTPUT_DIR / f"{job_id}.{ext}"
    if not path.exists():
        raise HTTPException(status_code=404, detail="文件还没有生成。")
    return FileResponse(path, filename=f"video-copy-{job_id}.{ext}")


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
