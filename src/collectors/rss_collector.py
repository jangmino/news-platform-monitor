"""RSS 보도자료 수집기 — korea.kr 정책브리핑 RSS 피드."""

from __future__ import annotations

from datetime import datetime

import feedparser
import requests

from src.config import load_config
from src.collectors.hwpx_parser import extract_hwpx_text
from src.models.article import Article, FileInfo
from src.utils.file_io import load_json, save_json, raw_rss_dir
from src.utils.text_utils import generate_id, normalize_text


def _parse_feed_entry(entry, source_name: str) -> Article:
    """RSS 피드 항목을 Article 객체로 변환한다."""
    url = entry.get("link", "")
    title = entry.get("title", "")
    summary = entry.get("summary", "")
    published = entry.get("published", "")
    content = normalize_text(summary)

    # 첨부파일 확인 (enclosures)
    file_info = None
    enclosures = entry.get("enclosures", [])
    for enc in enclosures:
        href = enc.get("href", "")
        if href and href.endswith(".hwpx"):
            file_info = FileInfo(
                name=href.split("/")[-1],
                url=href,
                parse_status="pending",
            )
            break

    # links에서도 hwpx 파일 찾기
    if not file_info:
        for link in entry.get("links", []):
            href = link.get("href", "")
            if href and ".hwpx" in href:
                file_info = FileInfo(
                    name=href.split("/")[-1],
                    url=href,
                    parse_status="pending",
                )
                break

    return Article(
        id=generate_id(url),
        title=title,
        content=content,
        url=url,
        source_type="rss",
        source_name=source_name,
        published_at=published,
        file_info=file_info,
    )


def _try_extract_hwpx(article: Article) -> Article:
    """첨부파일이 있으면 HWPX 텍스트 추출을 시도한다."""
    if not article.file_info or article.file_info.parse_status != "pending":
        return article

    try:
        hwpx_text = extract_hwpx_text(article.file_info.url)
        if hwpx_text:
            article.content = hwpx_text
            article.file_info.parse_status = "success"
        else:
            article.file_info.parse_status = "failed"
    except Exception as e:
        article.file_info.parse_status = "failed"
        print(f"  HWPX 파싱 실패 ({article.title}): {e}")

    return article


def collect_rss(config: dict | None = None) -> list[Article]:
    """모든 RSS 소스에서 보도자료를 수집한다."""
    if config is None:
        config = load_config()

    rss_sources = config.get("rss_sources", {})
    if not rss_sources:
        print("RSS 소스가 설정되지 않았습니다.")
        return []

    all_articles = []

    for source_name, feed_url in rss_sources.items():
        print(f"  [{source_name}] 수집 중... ", end="")
        try:
            feed = feedparser.parse(feed_url)
            if feed.bozo and not feed.entries:
                print(f"피드 파싱 실패, 건너뜀")
                continue

            # 기존 데이터 로드 (중복 체크)
            save_path = raw_rss_dir() / f"{source_name}.json"
            existing_data = load_json(save_path)
            existing_urls = {a["url"] for a in existing_data} if isinstance(existing_data, list) else set()

            new_articles = []
            for entry in feed.entries:
                article = _parse_feed_entry(entry, source_name)
                if article.url in existing_urls:
                    continue
                article = _try_extract_hwpx(article)
                new_articles.append(article)

            # 기존 + 신규 합쳐서 저장
            all_data = existing_data if isinstance(existing_data, list) else []
            all_data.extend([a.to_dict() for a in new_articles])
            save_json(all_data, save_path)

            print(f"신규 {len(new_articles)}건 (전체 {len(all_data)}건)")
            all_articles.extend(new_articles)

        except Exception as e:
            print(f"오류 발생, 건너뜀: {e}")

    print(f"\nRSS 수집 완료: 총 {len(all_articles)}건 신규 수집")
    return all_articles
