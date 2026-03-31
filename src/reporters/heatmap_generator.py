"""리스크 히트맵 생성기 — matplotlib + seaborn."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # 비GUI 백엔드
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import numpy as np

from src.models.cluster import IssueCluster


# 한글 폰트 설정
def _setup_korean_font():
    """시스템에서 사용 가능한 한글 폰트를 찾아 설정한다."""
    korean_fonts = [
        "Malgun Gothic",      # Windows
        "맑은 고딕",           # Windows (한글명)
        "AppleGothic",        # macOS
        "Apple SD Gothic Neo", # macOS
        "NanumGothic",        # Linux/설치형
        "DejaVu Sans",        # 폴백
    ]

    for font_name in korean_fonts:
        fonts = fm.findSystemFonts()
        for f in fm.fontManager.ttflist:
            if font_name in f.name:
                plt.rcParams["font.family"] = f.name
                plt.rcParams["axes.unicode_minus"] = False
                return

    # 폴백
    plt.rcParams["axes.unicode_minus"] = False


_POLICY_DOMAINS = [
    "공정거래", "소비자보호", "개인정보", "노동",
    "콘텐츠/저작권", "안전", "AI/자동화",
]


def build_heatmap_data(clusters: list[IssueCluster]) -> dict:
    """플랫폼 x 정책영역 매트릭스 데이터를 생성한다."""
    matrix: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for cluster in clusters:
        for platform in cluster.platform_tags:
            for domain in cluster.policy_domains:
                if domain in _POLICY_DOMAINS:
                    matrix[platform][domain] += cluster.risk_score

    return dict(matrix)


def generate_heatmap_image(
    heatmap_data: dict,
    output_path: Path,
) -> str:
    """히트맵 PNG 이미지를 생성한다."""
    _setup_korean_font()

    if not heatmap_data:
        print("  히트맵: 데이터 없음 (플랫폼 태그가 부착된 클러스터 없음)")
        return ""

    platforms = sorted(heatmap_data.keys())
    domains = _POLICY_DOMAINS

    # 매트릭스 생성
    data = np.zeros((len(platforms), len(domains)))
    for i, platform in enumerate(platforms):
        for j, domain in enumerate(domains):
            data[i][j] = heatmap_data.get(platform, {}).get(domain, 0)

    # 히트맵 생성
    fig, ax = plt.subplots(figsize=(12, max(6, len(platforms) * 0.5)))
    sns.heatmap(
        data,
        xticklabels=domains,
        yticklabels=platforms,
        annot=True,
        fmt=".0f",
        cmap="YlOrRd",
        cbar_kws={"label": "Risk Score"},
        ax=ax,
    )
    ax.set_title("Platform x Policy Domain Risk Heatmap", fontsize=14, pad=15)
    ax.set_xlabel("정책 영역", fontsize=11)
    ax.set_ylabel("플랫폼", fontsize=11)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"  히트맵: {output_path} 저장")
    return str(output_path)


def generate_heatmap_markdown_table(heatmap_data: dict) -> str:
    """히트맵 데이터를 Markdown 테이블로 변환한다."""
    if not heatmap_data:
        return "*플랫폼 태그가 부착된 클러스터가 없어 히트맵을 생성할 수 없습니다.*\n"

    platforms = sorted(heatmap_data.keys())
    domains = _POLICY_DOMAINS

    # 헤더
    header = "| 플랫폼 | " + " | ".join(domains) + " |"
    separator = "|" + "|".join(["---"] * (len(domains) + 1)) + "|"

    rows = [header, separator]
    for platform in platforms:
        values = []
        for domain in domains:
            score = heatmap_data.get(platform, {}).get(domain, 0)
            values.append(f"{score:.0f}" if score > 0 else "-")
        rows.append(f"| {platform} | " + " | ".join(values) + " |")

    return "\n".join(rows) + "\n"
