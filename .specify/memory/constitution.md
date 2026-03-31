<!--
Sync Impact Report
- Version change: 0.0.0 → 1.0.0 (initial constitution)
- Added principles:
  1. Pipeline-First Architecture
  2. Source Traceability (NON-NEGOTIABLE)
  3. Human-in-the-Loop Review
  4. Local-First Execution
  5. Simplicity & Minimal Dependencies
  6. Policy-Domain Awareness
- Added sections:
  - Technology Constraints
  - Data Processing Workflow
  - Governance
- Templates requiring updates:
  - .specify/templates/plan-template.md ✅ no changes needed (generic)
  - .specify/templates/spec-template.md ✅ no changes needed (generic)
  - .specify/templates/tasks-template.md ✅ no changes needed (generic)
  - No command files exist — N/A
- Follow-up TODOs: none
-->

# 플랫폼 산업 모니터링 시스템 Constitution

## Core Principles

### I. Pipeline-First Architecture

모든 기능은 명확한 파이프라인 단계로 구성되어야 한다.

- 전체 처리 흐름은 반드시 **수집 → 중복 제거/클러스터링 → 정책 태깅 → 리스크 점수 산출 → 브리핑 생성** 순서를 따라야 한다
- 각 단계는 독립적으로 실행·테스트 가능해야 하며, 단계 간 데이터는 명확한 인터페이스(파일 또는 데이터 구조)로 전달되어야 한다
- 새로운 기능 추가 시 기존 파이프라인 단계에 통합하거나, 명확한 이유와 함께 새 단계를 정의해야 한다

### II. Source Traceability (NON-NEGOTIABLE)

모든 분석 결과는 반드시 원문 출처를 추적할 수 있어야 한다.

- 요약문·브리핑·리포트에는 반드시 **원문 링크**를 첨부해야 한다
- 원문에 없는 내용이 AI 생성 결과에 포함되어서는 안 된다 (hallucination 방지)
- 수집된 모든 데이터는 수집 시각, 출처 URL, 원문 제목을 메타데이터로 보존해야 한다

### III. Human-in-the-Loop Review

AI 분석 결과의 오류 가능성을 인정하고, 고위험 판단에는 사람의 검토를 보장해야 한다.

- 리스크 점수가 임계값 이상인 이슈는 반드시 사람이 확인하는 단계를 거쳐야 한다
- 자동 생성된 정책 분류·감성 분석 결과에는 신뢰도 점수를 함께 제공해야 한다
- 최종 브리핑 리포트는 자동 생성 후 검토·수정이 가능한 형태로 제공되어야 한다

### IV. Local-First Execution

KISDI 연구원의 Windows 랩탑에서 직접 구동 가능해야 한다.

- 서버 배포나 클라우드 인프라 없이 로컬 환경에서 완전히 실행 가능해야 한다
- 설치 및 실행 절차는 Python 환경 설정과 API 키 구성만으로 완료되어야 한다
- 외부 서비스 의존은 API 호출(Naver Search API, Google Gemini API, RSS 피드)로 제한한다

### V. Simplicity & Minimal Dependencies

6주 자문 기간 내 완성 가능한 수준의 단순함을 유지해야 한다.

- Python 표준 라이브러리와 최소한의 서드파티 패키지만 사용한다
- 불필요한 추상화, 프레임워크 도입, 과도한 설계를 지양한다
- 파일 기반 데이터 저장(JSON, CSV)을 기본으로 하며, 별도 DB 서버를 요구하지 않는다

### VI. Policy-Domain Awareness

플랫폼 산업 정책의 7대 영역을 시스템 전반에서 일관되게 적용해야 한다.

- 7대 정책 영역: **공정거래, 소비자보호, 개인정보, 노동, 콘텐츠/저작권, 안전, AI/자동화**
- 정책 태깅은 멀티라벨 분류를 지원해야 한다 (하나의 이슈가 복수 영역에 해당 가능)
- 리스크 히트맵은 **플랫폼 × 정책영역** 매트릭스 형태를 따라야 한다

## Technology Constraints

- **Language**: Python 3.10+
- **LLM API**: Google Gemini API (분석, 태깅, 요약 용도)
- **Data Sources**: Naver Search API (뉴스 검색), RSS 피드 (전문지·기관 발표), 웹 크롤링 (보도자료·의안)
- **Storage**: 로컬 파일 시스템 (JSON, CSV)
- **Target Platform**: Windows 10/11 (KISDI 랩탑)
- **External Dependencies**: 최소화 — requests, feedparser 등 경량 패키지 위주

## Data Processing Workflow

전체 시스템은 다음 워크플로우를 따른다:

1. **수집 (Collection)**: Naver Search API, RSS 피드, 웹 크롤링으로 뉴스·공식 발표 수집
2. **전처리 (Preprocessing)**: 중복 제거, 이슈 클러스터링
3. **분석 (Analysis)**: 핵심 키워드 추출, 감성 분석(긍정/부정), 정책 프레임 자동 분류 (7대 영역)
4. **평가 (Scoring)**: 리스크 스코어링, 급상승 이슈 탐지 (언급량 급증, 규제기관 동반 언급, 여론 급변)
5. **리포트 (Reporting)**: 주간 이슈 브리핑 (TOP 10), 리스크 히트맵, 정책 질문 자동 도출

각 단계의 출력은 다음 단계의 입력으로 사용되며, 중간 결과는 파일로 저장하여 재실행·디버깅이 가능해야 한다.

## Governance

- 이 Constitution은 프로젝트의 모든 설계·구현 결정에 우선한다
- 원칙 변경 시 변경 사유, 영향 범위, 마이그레이션 계획을 문서화해야 한다
- 모든 코드 리뷰는 Source Traceability(원칙 II)와 Human-in-the-Loop(원칙 III) 준수 여부를 확인해야 한다
- 버전 관리는 Semantic Versioning(MAJOR.MINOR.PATCH)을 따른다

**Version**: 1.0.0 | **Ratified**: 2026-03-31 | **Last Amended**: 2026-03-31
