# Implementation Plan: press_data.py RSS 수집 코드 통합

**Branch**: `002-integrate-press-data` | **Date**: 2026-04-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-integrate-press-data/spec.md`

## Summary

press_data.py에서 검증된 RSS 수집 로직(웹 크롤링 기반 본문 추출, PDF/ODT 첨부파일 파싱, dept_name 자동 추출)을 현재 레포의 `collectors/` 모듈 구조에 통합한다. 신규 `web_scraper.py` 모듈을 추가하고, `hwpx_parser.py`를 `doc_extractor.py`로 확장하며, `rss_collector.py`에서 두 모듈을 조합한다. 기존 Article 데이터 모델과 파이프라인 호환성은 완전히 유지된다.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: feedparser, requests, beautifulsoup4 (신규), pymupdf (신규), odfpy (신규), pyyaml (기존 유지)
**Storage**: 로컬 파일 시스템 (JSON) — 기존 방식 유지
**Testing**: pytest
**Target Platform**: Windows 10/11 (KISDI 랩탑), macOS/Linux 호환
**Project Type**: CLI 파이프라인 도구
**Performance Goals**: 7개 기관 전체 수집 시 기관당 1~2분 이내 (딜레이 1.2초 포함)
**Constraints**: requests 타임아웃 20초 (웹), 10초 (첨부파일); 서버 부하 방지를 위한 1.2초 딜레이
**Scale/Scope**: 7개 기관 × 최대 50건, 일 1회 실행, 단일 사용자

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Pipeline-First | PASS | collectors/ 단계만 변경. 전처리→분석→평가→리포트 단계는 Article 인터페이스를 통해 분리되어 있어 영향 없음 |
| II. Source Traceability | PASS | Article.url 보존 유지, file_info.url에 첨부파일 원본 URL 저장. FR-010 |
| III. Human-in-the-Loop | PASS | 수집 단계 변경이므로 직접 해당 없음. 기존 risk_score 임계값 로직 변경 없음 |
| IV. Local-First | PASS | 신규 의존성(beautifulsoup4, pymupdf, odfpy) 모두 로컬 설치 패키지. 외부 서비스 추가 없음 |
| V. Simplicity | PASS* | 패키지 3개 추가. 모두 press_data.py에서 검증된 단일 목적 라이브러리. 불필요한 추상화 없음 |
| VI. Policy-Domain | PASS | 변경 없음 — 수집 단계이며 정책 영역 분류 로직 미관여 |

*V. Simplicity 주석: 기존 requirements.txt 6개 → 9개로 증가. 각 패키지가 단일 문제(HTML파싱/PDF파싱/ODT파싱) 해결에 필수적이므로 허용.

**Gate result**: ALL PASS — Phase 0 진행 가능

## Project Structure

### Documentation (this feature)

```text
specs/002-integrate-press-data/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (변경/추가 대상)

```text
src/
├── collectors/
│   ├── rss_collector.py      # 수정: 웹 크롤링 통합, dept_name 추출, _try_extract_attachments 확장
│   ├── hwpx_parser.py        # 유지 (하위 호환성)
│   ├── doc_extractor.py      # 신규: PDF/ODT 추출 + HWPX 위임. press_data.py 추출 함수 통합
│   └── web_scraper.py        # 신규: 상세 페이지 크롤링 + 본문 추출. press_data.py 크롤링 로직 통합
│
config.yaml.example            # 수정: RSS URL → dept_xxx.xml 형식으로 교체
requirements.txt               # 수정: beautifulsoup4, pymupdf, odfpy 추가
```

**변경 없는 파일 (하위 호환성 유지)**

```text
src/models/article.py          # 변경 없음 — FileInfo 구조 그대로 사용
src/utils/file_io.py           # 변경 없음
src/utils/text_utils.py        # 변경 없음
src/processors/                # 변경 없음
src/analyzers/                 # 변경 없음
src/scorers/                   # 변경 없음
src/reporters/                 # 변경 없음
src/cli.py                     # 변경 없음
```

**Structure Decision**: 기존 `collectors/` 모듈 구조 유지. `web_scraper.py`를 별도 모듈로 분리하여 단일 책임 원칙 적용. `hwpx_parser.py`는 하위 호환을 위해 유지하되, `doc_extractor.py`가 HWPX 포함 모든 첨부파일 추출을 담당.

## Complexity Tracking

> No Constitution Check violations — this section is not applicable.
