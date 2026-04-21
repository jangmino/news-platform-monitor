# Gemini LLM 분석 병렬화

## Context

현재 `press_analyzer.py`, `news_analyzer.py`는 보도자료/뉴스를 **1건씩 순차 호출**한다. 각 호출 뒤 `time.sleep(1.0)`도 하드코딩되어 있어 ([press_analyzer.py:292](src/analyzers/press_analyzer.py#L292), [news_analyzer.py:316](src/analyzers/news_analyzer.py#L316)), 250건 기준 최소 `N × (API latency + 1.0s) ≈ 7~10분`이 소요된다.

- 발표 시연(재실행 포함) 속도가 현재 가장 큰 병목
- `google-genai` SDK는 `client.aio.models.generate_content(...)` 비동기 API를 제공하므로 코드 구조 변경 없이 동시성 도입 가능
- OpenAI처럼 단순 동시 요청 + 서버 측 레이트 리밋 준수 + 지수 백오프로 처리하는 것이 표준 패턴

**목표**: Gemini API 호출을 동시성 `N`건으로 병렬화해 처리 시간을 약 `1/N`로 단축하되, 기존의 증분 캐시·원자적 저장·재시도·로깅 의미는 그대로 유지한다.

## Approach — asyncio + client.aio + Semaphore

동기 `genai.Client` + `ThreadPoolExecutor` 대안 대비 장점: Google 공식 권장 경로이고, 기존 `time.sleep` 기반 retry를 `await asyncio.sleep`로 그대로 치환 가능, GIL·스레드 세이프티 고민 불필요.

### 변경 파일

1. **`src/analyzers/press_analyzer.py`** — 병렬화 도입 (핵심)
2. **`src/analyzers/news_analyzer.py`** — 동일 패턴 적용
3. **`config.yaml.example`** — `api.gemini.max_workers: 5` 항목 추가
4. **`src/cli.py`** — 변경 없음 (CLI 플래그 없이 config만으로 조절)
5. **`src/analyzers/recommendation_generator.py`** — 변경 없음 (집계 기반 단일 호출)

### 구조 변경 (press_analyzer.py 기준, news_analyzer.py도 동일 패턴)

현재 구조:
```
for i, article in enumerate(articles, 1):
    if cached: append & continue
    if too_short: append skipped & continue
    try: analysis = _analyze_single(...)    # 동기 호출 + 내부 재시도 루프
    except: failed 기록
    time.sleep(1.0)
```

신규 구조:
```
# 1. pre-filter: cached / skipped / to_analyze 세 갈래 분류
# 2. to_analyze는 asyncio.gather 로 동시 실행, Semaphore(max_workers)로 동시성 제한
# 3. 순서 보존하며 최종 analyzed_articles 조립 → atomic_write
```

### 구현 포인트

- `genai.Client(api_key=...)` 동일하게 생성, 호출은 `await client.aio.models.generate_content(...)` 로 교체 ([press_analyzer.py:145](src/analyzers/press_analyzer.py#L145), [news_analyzer.py:166](src/analyzers/news_analyzer.py#L166))
- `_analyze_single` → `_analyze_single_async` 비동기 버전 추가 (내부 재시도 루프의 `time.sleep` → `asyncio.sleep`)
- 기존 `_is_transient_error`, `_RETRY_DELAYS`, `_parse_response`, `_validate_result` 는 순수 함수라 그대로 재사용
- `run_press_analysis` / `run_news_analysis`: 기존 시그니처(`def ... -> dict`) 유지. 내부에서 `asyncio.run(_run_async(...))` 호출하여 CLI 진입점은 무변경
- **동시성 제어**: `semaphore = asyncio.Semaphore(max_workers)` — per-article worker 내부에서 `async with semaphore:` 로 감싼다
- **하드코딩 1.0s sleep 제거**: 세마포어 + Gemini 서버 레이트 리밋 + 429/503 재시도 백오프로 충분
- **결과 수집**: `results = await asyncio.gather(*tasks)` — 순서 보존. `(index, result_article)` 튜플로 모아 원래 articles 순서대로 analyzed_articles 조립
- **진행 로그**: 동시성하에서는 per-article 1줄 프린트가 뒤섞인다. 완료 시 원자적 한 줄(`[done/total] title... 완료|재시도|오류`)로 축약. `asyncio.Lock()`으로 print 동시 호출 보호
- **재시도 간 대기**: 기존 `_RETRY_DELAYS = [5, 15, 45]` 유지 (이미 [press_analyzer.py:28](src/analyzers/press_analyzer.py#L28), [news_analyzer.py:28](src/analyzers/news_analyzer.py#L28)에 도입됨)
- **카운트/스킵/실패 집계**: 기존 변수(`new_count`, `fail_count`, `skip_count`)는 `asyncio.Lock` 또는 단일 이벤트 루프 내 순차 업데이트로 보호 (이벤트 루프 단일 스레드이므로 락 불요, 각 태스크가 자체 증분 후 결과에 태깅해 최종 집계)

### 설정

`config.yaml.example` (api.gemini 블록 확장):
```yaml
api:
  gemini:
    api_key: "YOUR_GEMINI_API_KEY"
    model: "gemini-2.5-flash-lite"
    max_workers: 5   # 동시 호출 수 (무료 티어 권장: 3, 유료 Tier1: 5~8)
```

analyzer 쪽:
```python
max_workers = int(gemini_cfg.get("max_workers", 5))
```

### 안전성·상태 불변성

- `existing` 캐시 dict: 병렬 구간에서는 읽기 전용(신규 분석 대상 판별용). 동시 읽기 안전
- `analyzed_articles` 리스트: 병렬 구간에서는 append 하지 않음. `asyncio.gather` 결과로 원자적 조립
- `atomic_write`: 기존대로 루프 종료 후 1회 호출 (변경 없음) — [file_io.py:42](src/utils/file_io.py#L42)
- 진행 중 Ctrl+C: 이벤트 루프가 `CancelledError`로 깨짐. 기존처럼 파일 저장 없이 종료 (이전 `press_analysis.json` 유지). 재실행 시 `analyzed`/`skipped` 캐시로부터 이어서 진행
- `failed` 상태는 지금과 동일하게 캐시 제외([press_analyzer.py:208](src/analyzers/press_analyzer.py#L208)) → 재실행 시 자동 재시도

### 재사용할 기존 함수/유틸

- `_is_transient_error()` — press/news 양쪽 ([press_analyzer.py:32](src/analyzers/press_analyzer.py#L32), [news_analyzer.py:32](src/analyzers/news_analyzer.py#L32))
- `_parse_response()`, `_validate_result()` — 순수 함수, 무변경
- `atomic_write()`, `copy_to_dashboard()` ([file_io.py](src/utils/file_io.py))
- `_RETRY_DELAYS` 상수

## Verification

1. **단위 동작 검증**
   - `python -m src.cli analyze-press` 단독 실행
   - 기대: 로그가 완료 순으로 `[done/total]` 형태로 흐르고, 이전보다 눈에 띄게 빨리 채워짐
   - `data/analyzed/press_analysis.json` 의 `analyzed_count`, `total_count`, `articles` 필드 이전 순차 실행 결과와 개수·status 일치
   - `dashboard/public/data/press_analysis.json` 자동 복사 확인

2. **증분 캐시 검증**
   - 한 번 실행 후 즉시 재실행 → 거의 모든 항목이 `캐시됨`으로 스킵, API 호출은 `failed` 건만 재시도되어야 함

3. **에러 복원력 검증**
   - `max_workers: 10` 로 과도하게 올려서 429/503 유발 → 콘솔에 재시도 로그 발생, 최종적으로 대부분 `analyzed`로 수렴

4. **뉴스 분석도 동일 검증**
   - `python -m src.cli analyze-news`

5. **엔드투엔드**
   - `python -m src.cli run-all`
   - 대시보드(`cd dashboard && bun run dev`)에서 결과 렌더링 정상 확인 — 특히 `press_analysis.json` 스키마가 변경되지 않았음을 확인

6. **실패 시 롤백**
   - 파일 편집 한정 변경이므로 `git checkout src/analyzers/press_analyzer.py src/analyzers/news_analyzer.py config.yaml.example` 로 즉시 복원 가능

## Out of Scope

- `recommendation_generator.py` 병렬화 — 단일 집계 호출이라 의미 없음
- `asyncio` 대신 `ThreadPoolExecutor` 구현 — 기각 (async가 더 간결)
- CLI `--workers` 플래그 — 기각 (config 한 곳에서 관리)
- 배치 API(`client.batches`) 도입 — 별도 주제, 이 변경 범위 밖
