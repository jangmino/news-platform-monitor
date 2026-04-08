# Data Model: press_data.py RSS 수집 코드 통합

**Branch**: `002-integrate-press-data` | **Date**: 2026-04-05

## 변경 범위

이번 통합은 **수집(collectors) 단계만 변경**한다. 데이터 모델(`Article`, `FileInfo`)은 변경하지 않는다. 아래는 기존 모델의 필드 활용 방식 변경 사항만 기술한다.

---

## 기존 모델 (변경 없음)

### Article

| 필드 | 타입 | 변경 전 활용 | 변경 후 활용 |
|------|------|------------|------------|
| `id` | str (SHA-256[:16]) | URL 해시 | 동일 |
| `title` | str | RSS entry.title | 동일 |
| `content` | str | RSS entry.summary (정규화) | **우선순위**: 첨부파일 텍스트 > 웹 크롤링 본문 > RSS summary |
| `url` | str | RSS entry.link | 동일 (중복 판별 기준) |
| `source_type` | str | `"rss"` 고정 | 동일 |
| `source_name` | str | config 키 이름 | **변경**: RSS feed.feed.title에서 기관명 자동 추출, 실패 시 config 키 이름 fallback |
| `published_at` | str | RSS entry.published | 동일 |
| `collected_at` | str | datetime.now().isoformat() | 동일 |
| `file_info` | FileInfo? | RSS enclosures에서 HWPX만 탐지 | **변경**: 웹 페이지 HTML 파싱으로 HWPX/PDF/ODT 탐지 |

### FileInfo

| 필드 | 타입 | 변경 전 활용 | 변경 후 활용 |
|------|------|------------|------------|
| `name` | str | href에서 파일명 추출 | 동일 (a태그 텍스트 lower() 또는 href 파일명) |
| `url` | str | 첨부파일 절대 URL | 동일 (상대 경로 → 절대 URL 변환 추가) |
| `parse_status` | str | `"pending"` / `"success"` / `"failed"` | 동일 |

---

## 신규 모듈 인터페이스

### `src/collectors/web_scraper.py`

```
crawl_page(url: str) -> tuple[str, list[dict]]
  - 반환: (web_text, file_list)
  - web_text: 추출된 본문 텍스트 (50자 미만이면 빈 문자열 반환)
  - file_list: [{"name": str, "url": str}, ...] — 페이지에서 발견된 첨부파일 목록

extract_web_text(soup: BeautifulSoup, url: str) -> str
  - 내부 함수. selector 우선순위:
    1. pressReleaseView → div.view-cont
    2. policyNewsView → div.news-content | #articleBody
    3. 범용 → div.view-cont | div.news-content | div.article-content | #articleBodyContents
    4. Fallback → p태그 수가 가장 많은 div
```

### `src/collectors/doc_extractor.py`

```
extract_doc_text(url: str, file_name: str) -> tuple[str | None, str]
  - 반환: (extracted_text, parse_status)
  - file_name 확장자 기반으로 파서 분기:
    .hwpx → hwpx_parser.extract_hwpx_text(url)
    .pdf  → _extract_pdf(url) [pymupdf, ImportError 시 None]
    .odt  → _extract_odt(url) [odfpy, ImportError 시 None]
    .hwp  → None (지원 불가, status="unsupported")
```

### `src/collectors/rss_collector.py` 변경 사항

**`_parse_feed_entry` 시그니처 변경**:
```
기존: _parse_feed_entry(entry, source_name: str) -> Article
변경: _parse_feed_entry(entry, source_name: str, dept_name: str) -> Article
  - dept_name: RSS feed.feed.title에서 추출한 기관명
  - Article.source_name = dept_name (config 키 대신 피드 타이틀 기반)
```

**`_try_extract_hwpx` → `_try_extract_content` 교체**:
```
기존: _try_extract_hwpx(article) → HWPX만 처리
변경: _try_extract_content(article) → web 크롤링 후 첨부파일 처리
  처리 순서:
  1. crawl_page(article.url) → web_text, file_list
  2. 우선순위 순서로 첨부파일 텍스트 추출 시도 (.hwpx > .pdf > .odt)
  3. 추출 성공 시 article.content = doc_text, file_info 설정
  4. 추출 실패 시 web_text 사용 (50자 이상이면)
  5. web_text도 불충분하면 기존 RSS summary 유지
```

---

## 데이터 흐름 (변경 후)

```
RSS 피드 (feedparser)
    │
    ▼
feed.feed.title → dept_name 추출
    │
    ▼
entry → Article (title, url, published_at, source_name=dept_name)
    │
    ▼
crawl_page(article.url)
    ├── web_text (HTML 파싱)
    └── file_list (첨부파일 링크 목록)
         │
         ▼
    우선순위 순회 (.hwpx > .pdf > .odt)
         ├── 성공: article.content = doc_text, file_info.parse_status = "success"
         └── 실패: article.content = web_text or RSS summary
    │
    ▼
Article (content 풍부해짐, file_info 정확해짐)
    │
    ▼
JSON 저장 (기존 방식 동일)
    │
    ▼
하위 파이프라인 (processors → analyzers → scorers → reporters) — 변경 없음
```

---

## 하위 호환성 보증

- `Article.to_dict()` / `Article.from_dict()` — 변경 없음
- JSON 스키마 — 변경 없음 (필드 추가 없음)
- `hwpx_parser.py` — import path 유지, 내부 로직 변경 없음
- `collect_rss()` 반환 타입 — `list[Article]` 유지
