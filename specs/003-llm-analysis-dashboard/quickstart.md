# Quickstart: Gemini LLM 분석 + 웹 대시보드

## 전제 조건

- spec-002 완료: `data/raw/rss/press_data.json` 존재
- `GEMINI_API_KEY` 환경변수 설정
- Python venv 활성화 상태
- [Bun 설치](https://bun.sh) 완료

---

## 1. Python 분석 실행

```bash
cd news-platform-monitor

# 보도자료 LLM 분석 + 정책 제언 생성
python -m src analyze-press
```

완료 후 생성 파일:
```
data/analyzed/press_analysis.json           ← canonical
dashboard/public/data/press_analysis.json   ← 대시보드용 복사본
```

---

## 2. 대시보드 초기 설정 (최초 1회)

```bash
cd dashboard
bun install
```

---

## 3. 대시보드 실행

```bash
cd dashboard
bun run dev
# → http://localhost:5173 에서 접속
```

---

## 4. 분석 결과 업데이트 후 대시보드 반영

```bash
# 1. 분석 재실행 (증분 — 이미 분석된 항목은 API 재호출 없음)
python -m src analyze-press

# 2. 브라우저에서 새로고침 (자동 갱신 없음)
```

---

## 프로덕션 빌드

```bash
cd dashboard
bun run build
# → dashboard/dist/ 에 정적 파일 생성
# dist/data/press_analysis.json 은 public/에서 자동 포함됨
```

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `GEMINI_API_KEY not set` | 환경변수 미설정 | `export GEMINI_API_KEY=...` |
| 분석 완료율 낮음 | API 할당량 초과 | 잠시 후 `analyze-press` 재실행 (증분 재개) |
| 대시보드 "데이터 없음" | JSON 미생성 또는 미복사 | `analyze-press` 먼저 실행, `dashboard/public/data/press_analysis.json` 확인 |
| 히트맵 빈 셀만 표시 | `platforms` 추출 실패 | `press_analysis.json` 내 `platforms` 필드 확인 |
| `bun: command not found` | Bun 미설치 | https://bun.sh 에서 설치 |
| TypeScript 빌드 오류 | 타입 불일치 | `analysis.ts` 타입 정의와 실제 JSON 스키마 비교 |
