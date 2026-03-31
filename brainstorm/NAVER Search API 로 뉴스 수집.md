# 03.25

## 검색 전략

- 기관명으로 조회→관련 키워드로 필터링
- 관련 키워드로 조회 → 기관명으로 필터링

→ 관련 키워드 중심 조회 + 기관명/플랫폼명 분류 태깅
: 기관명만으로 시작하면 포괄성이 낮고 정책 키워드만으로 시작하면 노이즈는 많지만 놓치는 이슈가 덜하기 때문에 이 방식으로 하는 게 나을 것 같다.

- 예시
    
    ### 1차 수집
    
    관련 정책 키워드 중심으로 조회
    
    예:
    
    - 플랫폼/시장 이슈: 플랫폼 규제, 온라인 플랫폼법, 배달앱 수수료, 플랫폼 독과점, 플랫폼 노동, 수수료, 입점업체, 갑질, 정산지연….
    - 공정거래/독점: 독점, 시장지배력, 끼워팔기, 자사우대, 불공정, 공정거래, 경쟁제한…
    - 소비자보호: 환불, 청약철회, 소비자 피해, 분쟁, 허위광고, 과장광고, 다크패턴, 기만광고, 리뷰조작, 허위리뷰, AI 리뷰, AI 생성 리뷰…
    - 개인정보/보안: 개인정보, 개인정보 유출, 위치정보, 동의, 보안사고, 해킹, 프라이버시, 정보보호, 프로파일링, 맞춤형 광고…
    - 알고리즘/AI: 알고리즘, 추천, 자동화, 생성형 AI, AI 요약, AI 추천, 알고리즘 투명성, 차별, 편향, 설명가능성, 생성형 AI 저작권…
    - 규제/입법: 규제, 법안, 입법, 가이드라인, 제재, 시정명령, 과징금, 조사, 행정처분, 정책토론회…
    
    ### 2차 후처리
    
    수집된 기사에서 아래 예시를 태깅
    
    - 기관명 포함 여부
        - 공정거래위원회
        - 개인정보보호위원회
        - 방송통신위원회
        - 국회
        - 과기정통부
    - 플랫폼명 포함 여부
        - 네이버, 카카오, 쿠팡, 배달의민족, 요기요, 당근, 토스, 야놀자, 무신사, 직방, 오늘의집, 카카오모빌리티, 네이버쇼핑
        - 구글, 유튜브, 메타, 인스타그램, 페이스북, 틱톡, 아마존, 테무, 알리익스프레스, 우버, 넷플릭스, 오픈AI
        - 플랫폼, 온라인플랫폼, 디지털플랫폼, 중개플랫폼, 앱마켓, 마켓플레이스

### AND/OR 같은 연산자 직접 사용

뉴스 API 검색어에 대해 통합검색 주소창의 상세검색 연산자를 활용할 수 있지만 제외 검색이 제대로 동작하지 않는다는 문의 언급이 보임. → 연산자 전반을 핵심 설계 축으로 두기엔 불확실성이 있다

원칙적으로는 연산자 사용 가능하다고 안내되지만 실무적으로는 연산자를 보조 수단으로 보는 것 추천

- `""`(구문 검색), `|`(OR)

### 키워드 반영 아이디어

1. 검색어 생성
    1. 기관명 사전
    2. 플랫폼명 사전
    3. 정책 키워드 사전
    
    → 이를 바탕으로
    
    - 기관명 + 정책 키워드
    - 플랫폼명 + 정책 키워드
    - 정책 키워드 단독
    
    같은 조합을 자동화.. → 조합 수 너무 많아짐
    
2. 넓게 수집 후 후처리
    1. 정책 키워드로 넓게 수집
    2. 기사 `title`이나 `description` 안에
        1. 기관명 포함 여부
        2. 특정 플랫폼명 포함 여부 등을 체크
    3. 중복 제거

## 네이버 뉴스 검색 API 문서

https://developers.naver.com/docs/serviceapi/search/news/news.md

- 요청 URL: `https://openapi.naver.com/v1/search/news.json` 또는 `.xml`
- HTTP 메서드: `GET`
- 인증 방식: 비로그인 오픈 API이며, 요청 헤더에 `X-Naver-Client-Id`, `X-Naver-Client-Secret`를 넣어야 함
- 필수 파라미터: `query`(UTF-8 인코딩)
- 선택 파라미터:
    - `display`: 한 번에 가져올 결과 수, 기본 10 / 최대 100
    - `start`: 시작 위치, 기본 1 / 최대 1000
    - `sort`: `sim`(정확도순, 기본) 또는 `date`(최신순)
- 응답 필드:
    
    
    | **요소** | **타입** | **설명** |
    | --- | --- | --- |
    | rss | - | RSS 컨테이너. RSS 리더기를 사용해 검색 결과를 확인할 수 있습니다. |
    | rss/channel | - | 검색 결과를 포함하는 컨테이너. `channel` 요소의 하위 요소인 `title`, `link`, `description`은 RSS에서 사용하는 정보이며, 검색 결과와는 상관이 없습니다. |
    | rss/channel/lastBuildDate | dateTime | 검색 결과를 생성한 시간 |
    | rss/channel/total | Integer | 총 검색 결과 개수 |
    | rss/channel/start | Integer | 검색 시작 위치 |
    | rss/channel/display | Integer | 한 번에 표시할 검색 결과 개수 |
    | rss/channel/item | - | 개별 검색 결과. JSON 형식의 결괏값에서는 `items` 속성의 JSON 배열로 개별 검색 결과를 반환합니다. |
    | rss/channel/item/title | String | 뉴스 기사의 제목. 제목에서 검색어와 일치하는 부분은 `<b>` 태그로 감싸져 있습니다. |
    | rss/channel/item/originallink | String | 뉴스 기사 원문의 URL |
    | rss/channel/item/link | String | 뉴스 기사의 네이버 뉴스 URL. 네이버에 제공되지 않은 기사라면 기사 원문의 URL을 반환합니다. |
    | rss/channel/item/description | String | 뉴스 기사의 내용을 요약한 패시지 정보. 패시지 정보에서 검색어와 일치하는 부분은 `<b>` 태그로 감싸져 있습니다. |
    | rss/channel/item/pubDate | dateTime | 뉴스 기사가 네이버에 제공된 시간. 네이버에 제공되지 않은 기사라면 기사 원문이 제공된 시간을 반환합니다. |
- 호출 한도: 검색 API 전체 기준 하루 25,000회

### 최신순 조회

`sort=date`를 쓰면 날짜 내림차순, 즉 최신순으로 가져올 수 있음

한 번 요청할 때 `display`는 최대 100개, `start`는 최대 1000까지 가능하다. 그래서 이론적으로 한 query당 1~1000 위치까지, 최대 1000건 범위 내에서 최신순으로 페이지네이션 조회 가능

예를 들면:

- 1페이지: `display=100&start=1`
- 2페이지: `display=100&start=101`
- ...
- 10페이지: `display=100&start=901`

이렇게 하면 한 검색어에 대해 최신 기사 최대 1000건까지 수집 가능. 

API가 반환하는 건 네이버 뉴스 검색 결과이기 때문에, 실제로 `total`이 더 크더라도 `start` 상한 때문에 1000개 이후는 직접 순회할 수 없다 (기간을 나눠서 설정하는 방식으로는 가능하지만, 최신 자료만 모니터링 할 것이기 때문에 괜찮을 듯 합니다.)

### 여러 query 돌리기

```python
queries = [
     "공정거래",
    "개인정보",
    "플랫폼 규제",
    "저작권"
]

for query in queries:
    params = {
        "query": query,
        "display": 10,
        "start": 1,
        "sort": "date"
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    print(f"\n=== {query} ===")

    for item in data['items']:
        print(item['title'])
```

### 페이지 넘기기

```python
for start in range(1, 1000, 100):  # 1,101,201,...
    params = {
        "query": "공정거래",
        "display": 100,
        "start": start,
        "sort": "date"
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    print(f"=== start={start} ===")

    for item in data['items']:
        print(item['title'])
```

### 플랫폼 / 기관 필터링 예시

```python
platforms = ["쿠팡", "네이버", "카카오", "배달의민족", "유튜브"]
institutions = ["공정거래위원회", "개인정보보호위원회", "방송통신위원회", "국회"]

for item in data['items']:
    # HTML 태그 제거
    title = item['title'].replace("<b>", "").replace("</b>", "")
    desc = item['description'].replace("<b>", "").replace("</b>", "")
    
    text = title + " " + desc

    platform_tags = []
    institution_tags = []

    # 플랫폼 태깅
    for p in platforms:
        if p in text:
            platform_tags.append(p)

    # 기관 태깅
    for inst in institutions:
        if inst in text:
            institution_tags.append(inst)

    # 하나라도 태그 있으면 출력
    if platform_tags or institution_tags:
        print(f"[플랫폼: {platform_tags}] [기관: {institution_tags}] {title}")
```