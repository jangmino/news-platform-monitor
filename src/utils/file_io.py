"""JSON 파일 I/O 유틸리티."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path


DATA_DIR = Path("data")


def ensure_dir(path: Path) -> None:
    """디렉토리가 없으면 생성한다."""
    path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> list | dict:
    """JSON 파일을 로드한다. 파일이 없으면 빈 리스트를 반환한다."""
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(data: list | dict, path: Path) -> None:
    """데이터를 JSON 파일로 저장한다."""
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_text(text: str, path: Path) -> None:
    """텍스트를 파일로 저장한다."""
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def atomic_write(data: list | dict, path: Path) -> None:
    """데이터를 JSON으로 원자적으로 저장한다 (tmpfile → os.replace)."""
    ensure_dir(path.parent)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def copy_to_dashboard(src: Path, filename: str) -> None:
    """분석 결과를 대시보드 public/data/ 에 복사한다.

    dashboard 디렉토리 자체가 없으면 조용히 건너뛴다.
    dashboard/public/data 하위 디렉토리는 없으면 생성한다.
    """
    project_root = Path(__file__).resolve().parents[2]
    dashboard_root = project_root / "dashboard"
    if not dashboard_root.exists():
        return
    dst_dir = dashboard_root / "public" / "data"
    ensure_dir(dst_dir)
    dst = dst_dir / filename
    shutil.copy2(src, dst)
    print(f"대시보드 복사 완료: {dst}")


# 데이터 경로 헬퍼
def raw_rss_dir() -> Path:
    return DATA_DIR / "raw" / "rss"


def raw_news_dir() -> Path:
    return DATA_DIR / "raw" / "news"


def processed_dir() -> Path:
    return DATA_DIR / "processed"


def analyzed_dir() -> Path:
    return DATA_DIR / "analyzed"


def scored_dir() -> Path:
    return DATA_DIR / "scored"


def reports_dir() -> Path:
    return DATA_DIR / "reports"
