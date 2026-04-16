# Quickstart: LLM 분석 및 대시보드 뉴스 데이터 확장

## 전제 조건

- Python 3.10+ 환경 설치 완료 (`pip install -r requirements.txt`)
- `config.yaml`에 `api.gemini.api_key` 설정 완료
- `data/raw/news/news_data.json` 존재 (spec-001 파이프라인 실행 후)
- `data/raw/rss/press_data.json` 존재 (spec-002 파이프라인 실행 후)

## 뉴스 분석 실행

```bash
# 뉴스 기사 LLM 분석 (증분 — 이미 분석된 항목은 건너뜀)
python -m src analyze-news

# 강제 재분석 (모든 항목 재호출)
python -m src analyze-news --force
```

결과 파일:
- `data/analyzed/news_analysis.json`
- `dashboard/public/data/news_analysis.json` (자동 복사)

## 보도자료 분석 실행 (기존, 변경 없음)

```bash
python -m src analyze-press
```

## 통합 정책 제언 생성

```bash
# 보도자료 + 뉴스 분석 결과를 합산하여 정책 제언 3개 생성
python -m src generate-recommendations
```

결과 파일:
- `data/analyzed/combined_recommendations.json`
- `dashboard/public/data/combined_recommendations.json` (자동 복사)

## 대시보드 실행

```bash
cd dashboard
bun run dev
```

브라우저에서 `http://localhost:5173` 접속.
- 상단 소스 필터 버튼(전체 / 보도자료 / 뉴스)으로 데이터 전환
- 뉴스 필터 선택 시 섹션 1에 언론사별 파이차트 추가 표시
- 섹션 4 이슈 카드에 출처 뱃지(보도자료/뉴스) 표시

## 전형적인 실행 순서

```bash
# 1. 뉴스 수집 (이미 완료된 경우 건너뜀)
python -m src collect --news

# 2. 보도자료 분석 (spec-003)
python -m src analyze-press

# 3. 뉴스 분석 (신규)
python -m src analyze-news

# 4. 통합 정책 제언 (신규)
python -m src generate-recommendations

# 5. 대시보드 확인
cd dashboard && bun run dev
```

## 파일 경로 참조

| 커맨드 | 입력 | 출력 |
|--------|------|------|
| `analyze-press` | `data/raw/rss/press_data.json` | `data/analyzed/press_analysis.json` |
| `analyze-news` | `data/raw/news/news_data.json` | `data/analyzed/news_analysis.json` |
| `generate-recommendations` | 위 두 파일 | `data/analyzed/combined_recommendations.json` |

## 트러블슈팅

**`news_data.json`이 없다는 오류**
```
뉴스 데이터가 없습니다. 먼저 collect-news를 실행하세요.
```
→ `python -m src collect --news` 실행 후 재시도

**대시보드에 뉴스 데이터가 표시되지 않음**
- `dashboard/public/data/news_analysis.json` 파일 존재 여부 확인
- `analyze-news` 완료 후 자동 복사됨 — 없으면 수동 복사: `copy data\analyzed\news_analysis.json dashboard\public\data\`

**소스 필터가 보이지 않음**
- 대시보드 빌드가 구버전일 수 있음: `bun run build` 후 재실행
