# Quickstart: press_data.py 통합 후 설정 및 사용 가이드

**Branch**: `002-integrate-press-data` | **Date**: 2026-04-05

## 변경 사항 요약

이번 업데이트로 RSS 수집 시 다음이 개선됩니다:
- 보도자료 상세 페이지 전체 본문 자동 수집 (기존: RSS 요약문만)
- PDF, ODT 첨부파일 텍스트 추출 지원 (기존: HWPX만)
- RSS 피드에서 기관명 자동 추출 (기존: config 키 이름 그대로 사용)
- 검증된 RSS URL 적용

---

## 설치

### 신규 의존성 설치

```bash
# 가상환경 활성화 후
pip install -r requirements.txt
```

추가된 패키지:
- `beautifulsoup4` — 보도자료 웹 페이지 HTML 파싱
- `pymupdf` — PDF 첨부파일 텍스트 추출
- `odfpy` — ODT 첨부파일 텍스트 추출

> **참고**: pymupdf 또는 odfpy 설치에 실패해도 시스템은 정상 동작합니다. 해당 파일 형식만 건너뜁니다.

### Windows에서 pymupdf 설치 문제 시

```bash
pip install --upgrade pip
pip install pymupdf
```

---

## 설정 업데이트

### config.yaml 갱신 (기존 사용자)

기존 `config.yaml`을 사용 중이라면 `rss_sources` 섹션을 아래와 같이 업데이트하세요:

```yaml
rss_sources:
  공정거래: "https://www.korea.kr/rss/dept_ftc.xml"
  소비자보호: "https://www.korea.kr/rss/dept_mfds.xml"
  개인정보: "https://www.korea.kr/rss/dept_pipc.xml"
  노동: "https://www.korea.kr/rss/dept_moel.xml"
  콘텐츠/저작권: "https://www.korea.kr/rss/dept_mcst.xml"
  안전: "https://www.korea.kr/rss/dept_mois.xml"
  AI/자동화: "https://www.korea.kr/rss/dept_msit.xml"
```

### 신규 설치

```bash
cp config.yaml.example config.yaml
# API 키 설정 후 바로 사용 가능
```

---

## 사용법 (변경 없음)

```bash
# RSS 보도자료 수집 (이제 웹 본문도 자동 수집)
python -m src.cli collect --rss

# 전체 파이프라인
python -m src.cli run-all
```

---

## 수집 속도 변화

웹 크롤링 추가로 수집 속도가 느려집니다:

| 기준 | 기존 | 변경 후 |
|------|------|---------|
| 항목당 소요 시간 | ~0.5초 | ~2~3초 (크롤링 + 딜레이 1.2초) |
| 7개 기관 전체 (기관당 50건) | ~3분 | ~15~20분 |

> 수집은 백그라운드 실행을 권장합니다. 일 1회 스케줄로 설정하면 문제 없습니다.

---

## 수집 결과 확인

```bash
# 수집된 기사 본문 길이 샘플 확인 (macOS/Linux)
python -c "
import json
from pathlib import Path
for f in Path('data/raw/rss').glob('*.json'):
    data = json.loads(f.read_text(encoding='utf-8'))
    if data:
        avg = sum(len(a.get('content','')) for a in data) / len(data)
        print(f'{f.stem}: 평균 본문 {avg:.0f}자 ({len(data)}건)')
"
```

---

## 트러블슈팅

### RSS 수집이 이전과 다르게 느린 경우

정상입니다. 상세 페이지 크롤링으로 인해 수집 시간이 길어졌습니다.

### 특정 기관 보도자료 본문이 여전히 짧은 경우

korea.kr 페이지 구조가 변경되었을 수 있습니다. `data/raw/rss/[기관명].json`에서 `content` 필드를 확인하고, 필요 시 `web_scraper.py`의 선택자를 업데이트하세요.

### PDF/ODT 추출 실패

`file_info.parse_status == "failed"`인 항목은 웹 본문으로 대체됩니다. pymupdf 또는 odfpy 재설치로 해결 가능합니다.
