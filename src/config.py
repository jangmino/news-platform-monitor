"""설정 로더 — config.yaml + 환경 변수 오버라이드."""

from __future__ import annotations

import os
from pathlib import Path

import yaml


_DEFAULT_CONFIG_PATH = Path("config.yaml")


def load_config(config_path: str | Path | None = None) -> dict:
    """YAML 설정 파일을 로드하고 환경 변수로 오버라이드한다."""
    path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(
            f"설정 파일을 찾을 수 없습니다: {path}\n"
            "config.yaml.example을 복사하여 config.yaml을 생성하세요."
        )

    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 환경 변수 오버라이드
    env_overrides = {
        "NAVER_CLIENT_ID": ("api", "naver", "client_id"),
        "NAVER_CLIENT_SECRET": ("api", "naver", "client_secret"),
        "GEMINI_API_KEY": ("api", "gemini", "api_key"),
    }

    for env_var, key_path in env_overrides.items():
        value = os.environ.get(env_var)
        if value:
            d = config
            for key in key_path[:-1]:
                d = d.setdefault(key, {})
            d[key_path[-1]] = value

    return config
