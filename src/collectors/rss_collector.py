"""RSS 보도자료 수집기 — korea.kr 정책브리핑 RSS 피드."""

from __future__ import annotations

import time

import feedparser

from src.config import load_config
from src.collectors.doc_extractor import extract_doc_text
from src.collectors.web_scraper import crawl_page
from src.models.article import Article, FileInfo
from src.utils.file_io import load_json, save_json, raw_rss_dir
from src.utils.text_utils import generate_id, normalize_text


_DEPT_PREFIX = "대한민국 정책브리핑"
_ATTACHMENT_PRIORITY = [".hwpx", ".pdf", ".odt"]
_CRAWL_DELAY = 1.2  # 서버 부하 방지용 딜레이 (초)
_SAVE_FILE = "press_data.json"  # 전 카테고리 통합 저장 파일


def _extract_dept_name(feed, fallback: str) -> str:
    """RSS 피드 타이틀에서 기관명을 추출한다.

    "대한민국 정책브리핑 - 공정거래위원회" → "공정거래위원회"
    추출 실패 시 config 키 이름(fallback)을 반환한다.
    """
    if not hasattr(feed.feed, "title"):
        return fallback
    extracted = feed.feed.title.replace(_DEPT_PREFIX, "").strip(" -–—")
    return extracted if extracted else fallback


def _parse_feed_entry(entry, dept_name: str) -> Article:
    """RSS 피드 항목을 Article 객체로 변환한다."""
    url = entry.get("link", "")
    title = entry.get("title", "")
    summary = entry.get("summary", "")
    published = entry.get("published", "")

    return Article(
        id=generate_id(url),
        title=title,
        content=normalize_text(summary),
        url=url,
        source_type="rss",
        source_name=dept_name,
        published_at=published,
    )


def _try_extract_content(article: Article) -> Article:
    """웹 페이지 크롤링 후 첨부파일 또는 웹 본문으로 content를 보강한다.

    처리 순서:
    1. 상세 페이지 크롤링 → web_text, 첨부파일 목록
    2. 우선순위 순서로 첨부파일 텍스트 추출 시도 (.hwpx > .pdf > .odt)
    3. 성공 시 article.content = doc_text
    4. 실패 시 web_text 사용 (50자 이상이면)
    5. web_text도 불충분하면 RSS summary 유지
    """
    web_text, file_list = crawl_page(article.url)

    selected_file: dict | None = None
    doc_content: str | None = None
    parse_status = "failed"

    for ext in _ATTACHMENT_PRIORITY:
        for f in file_list:
            if f["name"].endswith(ext):
                selected_file = f
                text, status = extract_doc_text(f["url"], f["name"])
                if text:
                    doc_content = text
                    parse_status = status
                else:
                    parse_status = status
                break
        if selected_file:
            break

    if doc_content and selected_file:
        article.content = doc_content
        article.file_info = FileInfo(
            name=selected_file["name"],
            url=selected_file["url"],
            parse_status="success",
        )
    elif web_text and len(web_text) > 50:
        article.content = web_text
        if selected_file:
            article.file_info = FileInfo(
                name=selected_file["name"],
                url=selected_file["url"],
                parse_status=parse_status,
            )
    # else: 원본 RSS summary 유지, file_info는 None

    return article


def _to_press_dict(article: Article, category: str) -> dict:
    """Article을 저장용 press 스키마 딕셔너리로 변환한다."""
    file_info = None
    if article.file_info:
        file_info = {
            "name": article.file_info.name,
            "url": article.file_info.url,
        }
    return {
        "title": article.title,
        "date": article.published_at,
        "source_type": "press",
        "category": category,
        "dept": article.source_name,
        "link": article.url,
        "content": article.content,
        "file_info": file_info,
    }


def collect_rss(config: dict | None = None) -> list[dict]:
    """모든 RSS 소스에서 보도자료를 수집하여 단일 JSON 파일로 저장한다."""
    if config is None:
        config = load_config()

    rss_sources = config.get("rss_sources", {})
    if not rss_sources:
        print("RSS 소스가 설정되지 않았습니다.")
        return []

    # 단일 파일 로드 — 전 카테고리 통합 중복 체크
    save_path = raw_rss_dir() / _SAVE_FILE
    existing_data: list[dict] = load_json(save_path) or []
    existing_urls: set[str] = {a["link"] for a in existing_data if "link" in a}

    all_new: list[dict] = []

    for category, feed_url in rss_sources.items():
        print(f"  [{category}] 수집 중... ", end="", flush=True)
        try:
            feed = feedparser.parse(feed_url)
            if feed.bozo and not feed.entries:
                print("피드 파싱 실패, 건너뜀")
                continue

            dept_name = _extract_dept_name(feed, fallback=category)

            new_in_category = 0
            for entry in feed.entries:
                article = _parse_feed_entry(entry, dept_name)
                if article.url in existing_urls:
                    continue

                article = _try_extract_content(article)
                press_dict = _to_press_dict(article, category=category)
                all_new.append(press_dict)
                existing_urls.add(article.url)  # 실행 중 중복 방지
                new_in_category += 1
                time.sleep(_CRAWL_DELAY)

            print(f"신규 {new_in_category}건")

        except Exception as e:
            print(f"오류 발생, 건너뜀: {e}")

    # 기존 + 신규 합쳐서 단일 파일 저장
    save_json(existing_data + all_new, save_path)

    print(f"\nRSS 수집 완료: 총 {len(all_new)}건 신규 수집 → {save_path}")
    return all_new
