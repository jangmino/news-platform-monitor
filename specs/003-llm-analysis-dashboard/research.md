# Research: Gemini LLM 분석 + 웹 대시보드

## Python 파이프라인 — 기존 코드 현황

### `src/analyzers/gemini_analyzer.py`
- Gemini API 호출 로직 존재. `press_analyzer.py` 작성 시 재사용 방향 확인 필요.

### `src/cli.py`
- 기존 CLI 커맨드 구조 확인 후 `analyze-press` 커맨드 추가.

### `data/raw/rss/press_data.json`
- 실제 필드: `title`, `date`, `source_type`, `category`, `dept`, `link`, `content`, `file_info`
- `content` 필드 존재 확인 완료.

---

## React 대시보드 — 기술 조사

### Recharts 차트 선택 기준

| 섹션 | 차트 | Recharts 컴포넌트 |
|------|------|------------------|
| 섹션 1 히트맵 | HTML table + Tailwind | (Recharts 미사용) |
| 섹션 2 트렌드 | 일별 라인 차트 | `LineChart` |
| 섹션 2 버블 | 클러스터 버블차트 | `ScatterChart` (z축: 버블 크기) |
| 섹션 3 클라우드 | 키워드 태그 | (Recharts 미사용, span 기반) |
| 섹션 3 타임라인 | 고위험 이슈 테이블 | shadcn/ui `Table` |

**히트맵**: Recharts는 네이티브 히트맵 없음. `ScatterChart`로 흉내낼 수 있으나 셀 클릭 이벤트 처리가 복잡하다. HTML `<table>` + Tailwind `bg-opacity` 색상 강도 방식이 구현이 명확하고 클릭 이벤트도 단순하다.

**ScatterChart 버블**: `<Scatter>` 에 `r` 속성을 데이터 포인트로 전달하거나, 커스텀 `shape` prop으로 원 크기를 제어한다.

### shadcn/ui 컴포넌트 활용 계획

- `Card`, `CardHeader`, `CardContent` → 섹션 1 요약 카드, 섹션 4 플랫폼 카드
- `Table`, `TableHeader`, `TableRow`, `TableCell` → 섹션 3 타임라인
- `Badge` → 감성 레이블(긍정/부정/중립), 정책영역 태그
- `Separator` → 섹션 구분선

shadcn/ui 컴포넌트는 `bunx --bun shadcn@latest add card table badge separator` 로 개별 설치.

### Bun + Vite 환경 특이사항

- `bun create vite` 로 React TypeScript 템플릿 생성
- `bunx --bun shadcn@latest init` : `--bun` 플래그로 Bun 런타임 강제
- Windows에서 Bun 1.x 이상 필요 (PowerShell 설치 스크립트 사용)
- Vite dev server 기본 포트: 5173

### 데이터 브리지: 왜 `dashboard/public/data/` 복사 방식인가

**대안 비교:**

| 방식 | 장점 | 단점 |
|------|------|------|
| `dashboard/public/data/` 복사 | 백엔드 서버 불필요, 완전한 분리 | Python이 dashboard 경로를 알아야 함 |
| Vite proxy → Python HTTP server | 경로 결합 없음 | 동시에 2개 프로세스 실행 필요 |
| 환경변수로 데이터 경로 설정 | 유연성 높음 | 설정 복잡성 증가 |

→ **복사 방식 채택**: 로컬 단일 사용자 환경에서 설정이 가장 단순하다. Python `cli.py`에서 `shutil.copy2`로 복사.

### Gemini structured output

- `response_mime_type: "application/json"` + `response_schema` 파라미터
- `gemini-2.5-flash-lite`에서 지원 확인 필요. 미지원 시 프롬프트에 JSON 예시 삽입 후 `json.loads()` 파싱.

### 이슈 클러스터링 (버블차트용, 간소화)

- 각 `keyword`를 클러스터 ID로 사용
- 동일 keyword를 가진 기사들을 같은 클러스터로 묶음
- 클러스터 속성: `keyword`, `firstDate`, `avgRiskScore`, `articleCount`, `dominantDomain`
- 고도화(임베딩 기반 유사도 클러스터링)는 추후 spec
