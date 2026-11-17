What If API 명세

01 자산 시뮬레이션 계산
## **Request**

### **Header**

```
Content-Type: application/json
```

### **Parameter**

없음

### **Body**

| **필드** | **데이터 타입** | **필수** | **설명** |
| --- | --- | --- | --- |
| startMonth | String | Y | 계산 시작 월 `YYYY-MM` |
| periodMonths | Integer | Y | 계산 기간 6~120개월 |
| currentAsset | Integer | Y | 현재 자산 0~100,000만원 |
| monthlySaving | Integer | Y | 월 저축액 0~1,000만원 |
| events | Array | Y | 이벤트 목록 (공통 규칙 5-1) |
| goal | Object | N | 목표. 없으면 `null` |

### **Example**

```
POST /api/v1/simulations

{
  "startMonth": "2026-11",
  "periodMonths": 12,
  "currentAsset": 500,
  "monthlySaving": 40,
  "events": [
    { "id": "ev-1", "name": "성과급", "type": "income", "amount": 100, "month": "2027-02", "repeat": "once" },
    { "id": "ev-2", "name": "노트북 구입", "type": "expense", "amount": 150, "month": "2027-05", "repeat": "once" }
  ],
  "goal": { "name": "유럽 여행", "amount": 1000, "deadline": "2027-11" }
}
```

## **Response**

### **성공 예시**

```json
{
  "isSuccess": true,
  "code": "SIM200_1",
  "message": "계산에 성공했습니다.",
  "result": {
    "series": [500, 540, 580, 720, 760, 800, 690, 730, 770, 810, 850, 890, 930],
    "summary": {
      "finalAsset": 930,
      "increase": 430,
      "totalSaving": 480,
      "eventTotal": -50,
      "goal": {
        "assetAtDeadline": 930,
        "shortfall": 70,
        "achievementRate": 93,
        "extraSavingNeeded": 5.8,
        "reachedMonth": null,
        "alreadyAchieved": false
      },
      "negativeAsset": null,
      "milestones": { "after1Year": 930, "after5Years": 2850 }
    },
    "warnings": []
  }
}
```

### **에러 예시**

```json
{
  "isSuccess": false,
  "code": "CONDITION400_12",
  "message": "목표 기한이 계산 기간을 벗어나요.",
  "result": null
}
```

### **Response Field (result)**

| **필드** | **데이터 타입** | **설명** |
| --- | --- | --- |
| series | Integer[] | 월별 자산 (그래프 선) |
| summary | Object | 헤드라인·핵심 숫자용 값 |
| warnings | Array | 기간 밖이라 뺀 이벤트 |

### **Error Code**

| **HttpStatus** | **ResultCode** | **ErrorMessage** | **Description** |
| --- | --- | --- | --- |
| 400 | CONDITION400_1~12 | (공통 규칙 3장) | 계산 조건 검증 에러 |

### **비고**

- 설명: 조건으로 월별 자산과 결과 숫자를 계산. DB를 쓰지 않음
- 관련 기능: INP-07(실시간 미리보기), RES-03~06, RES-10, RES-11(슬라이더), 정책표 3·5·6장
- 계산식: A(0) = 현재 자산, A(m) = A(m−1) + 월 저축 + 그달 이벤트 합계. 저축은 1개월차부터. 이자·세금 미반영
- 같은 입력이면 항상 같은 결과. 골든 테스트: 위 예시 → 930·부족 70·달성률 93%·5.8 / 월 저축 50 → 1,050·도달 2027-10 / 자산 0·저축 0·지출 150(2027-05) → 음수 경고 2027-05 −150
- 기간 밖 이벤트는 에러가 아니라 `warnings`로 알림. 화면은 "N개 이벤트가 기간 밖이에요" 안내
- 슬라이더 점선 미리보기는 손을 뗄 때 또는 200ms 간격으로 부름

02 AI 대화
## **Request**

### **Header**

```
Content-Type: application/json
```

### **Parameter**

없음

### **Body**

| **필드** | **데이터 타입** | **필수** | **설명** |
| --- | --- | --- | --- |
| question | String | Y | 질문. 앞뒤 공백 제거 후 1~200자 |
| baseVersionNo | Integer | Y | 지금 보고 있는 버전 번호. `versions` 안에 있어야 함 |
| nextVersionNo | Integer | Y | 새 버전이 생기면 붙일 번호. 11 이상이면 `AI422_1` |
| versions | Array | Y | 이 대화의 버전 전체 1~10개. V1 필수 |
| versions[].no | Integer | Y | 버전 번호 |
| versions[].title | String | Y | 버전 제목 (V1은 "기존 플랜") |
| versions[].condition | Object | Y | 그 버전의 Condition (공통 규칙 5-1) |

### **Example**

```
POST /api/v1/ai/chat

{
  "question": "매달 10만원 더 모으면?",
  "baseVersionNo": 1,
  "nextVersionNo": 2,
  "versions": [
    { "no": 1, "title": "기존 플랜", "condition": { "startMonth": "2026-11", "periodMonths": 12, "currentAsset": 500, "monthlySaving": 40, "events": [ ... ], "goal": { ... } } }
  ]
}
```

## **Response**

응답은 `result.type`으로 구분.

### **성공 예시 — change (조건 변경, 새 버전)**

```json
{
  "isSuccess": true,
  "code": "AI200_1",
  "message": "답변을 만들었습니다.",
  "result": {
    "type": "change",
    "answerText": "다음 달부터 월 50만원씩 모으면 12개월 뒤 1,050만원이에요. 이자·세금은 반영하지 않았어요.",
    "summaryText": "월 저축을 10만원 늘리면 목표를 50만원 넘겨요.",
    "newCondition": { "startMonth": "2026-11", "periodMonths": 12, "currentAsset": 500, "monthlySaving": 50, "events": [... ], "goal": {... } },
    "result": { "series": [500, 550, 600, 750, 800, 850, 750, 800, 850, 900, 950, 1000, 1050], "summary": {... }, "warnings": [] },
    "v1Result": { "finalAsset": 930, "goalShortfall": 70 },
    "versionCard": { "no": 2, "title": "월 50만원", "baseVersionNo": 1 },
    "usedAssumptions": ["이자·세금 미반영", "가정 기반"]
  }
}
```

### **성공 예시 — explain (설명)**

```json
{
  "isSuccess": true,
  "code": "AI200_1",
  "message": "답변을 만들었습니다.",
  "result": {
    "type": "explain",
    "answerText": "5월에 노트북 구입 150만원이 빠져서 자산이 잠시 줄어요.",
    "highlightMonths": ["2027-05"]
  }
}
```

### **성공 예시 — clarify (되묻기)**

```json
{
  "isSuccess": true,
  "code": "AI200_1",
  "message": "답변을 만들었습니다.",
  "result": {
    "type": "clarify",
    "answerText": "몇 개월 앞당길까요?",
    "options": [
      { "label": "1개월", "question": "목표 기한을 1개월 앞당기면?" },
      { "label": "2개월", "question": "목표 기한을 2개월 앞당기면?" },
      { "label": "3개월", "question": "목표 기한을 3개월 앞당기면?" }
    ]
  }
}
```

### **성공 예시 — finance (예·적금 목록)**

```json
{
  "isSuccess": true,
  "code": "AI200_1",
  "message": "답변을 만들었습니다.",
  "result": {
    "type": "finance",
    "answerText": "지금 조건으로 가입할 수 있는 공시 상품을 정리했어요. 추천이 아니라 비교용 정보예요.",
    "productQuery": { "type": "deposit", "termMonths": 12, "amountMax": 500, "monthlyAmount": 40, "sort": "maxRate", "limit": 3 }
  }
}
```

### **성공 예시 — refuse (범위 밖 질문)**

```json
{
  "isSuccess": true,
  "code": "AI200_1",
  "message": "답변을 만들었습니다.",
  "result": {
    "type": "refuse",
    "answerText": "저는 입력하신 계획을 계산해서 설명해 드려요. 이런 질문은 어떠세요?",
    "examples": ["월 10만원 더 모으면?", "5년 뒤엔 얼마야?"]
  }
}
```

### **에러 예시**

```json
{
  "isSuccess": false,
  "code": "AI503_1",
  "message": "일시적인 오류로 요청을 처리하지 못했어요. 다시 한 번 물어봐 주시겠어요?",
  "result": null
}
```

### **Response Field (result)**

| **필드** | **데이터 타입** | **설명** |
| --- | --- | --- |
| type | String | `change` / `explain` / `clarify` / `finance` / `refuse` |
| answerText | String | 대화에 보여 줄 답변. `change`에서 설명 문장만 실패하면 `null` → 프론트가 기본 문장 |
| summaryText | String | (change) 새 버전의 AI 한줄요약. 실패하면 `null` |
| newCondition | Object | (change) 새 버전의 전체 조건. 프론트는 이걸 새 버전으로 보관 |
| result | Object | (change) 새 조건의 계산 결과 (SimulationResult) → 그래프 즉시 갱신 |
| v1Result | Object | (change) V1의 `finalAsset`, `goalShortfall` → 카드 "V1 대비 +120만원" |
| versionCard | Object | (change) `no`, `title`, `baseVersionNo` → 버전 카드 |
| usedAssumptions | String[] | (change) 답변에 쓴 가정 |
| highlightMonths | String[] | (explain) 그래프에서 강조할 달. 없으면 `[]` |
| options | Array | (clarify) 선택 칩. 누르면 `question`을 새 질문으로 보냄 |
| productQuery | Object | (finance) 13 공시 상품 목록 조회에 그대로 넣을 조건 |
| examples | String[] | (refuse) 대신 해 볼 수 있는 질문 칩 |

### **Error Code**

| **HttpStatus** | **ResultCode** | **ErrorMessage** | **Description** |
| --- | --- | --- | --- |
| 400 | AI400_1 | 질문을 입력해 주세요. | 질문이 비었거나 공백만 |
| 400 | AI400_2 | 질문은 200자까지 입력할 수 있어요. | 질문 200자 초과 |
| 400 | AI400_3 | 대화 버전 정보가 올바르지 않아요. | V1 없음, `baseVersionNo`가 `versions`에 없음, 버전 11개 이상 |
| 400 | CONDITION400_1~12 | (공통 규칙 3장) | 버전 조건 검증 에러 |
| 422 | AI422_1 | 버전이 너무 많아요. 저장하거나 정리해 주세요. | `nextVersionNo`가 11 이상 (정책표 10장) |
| 429 | AI429_1 | 잠시 후 다시 물어봐 주세요. | 요청 제한 초과 (제안) |
| 503 | AI503_1 | 일시적인 오류로 요청을 처리하지 못했어요. 다시 한 번 물어봐 주시겠어요? | AI 타임아웃·오류. 그래프·대화는 그대로 유지 |

### **비고**

- 설명: 질문을 조건 변경으로 해석해 새 버전을 만들거나, 설명·되묻기·거절
- 관련 기능: CHT-02~13, FIN-01, 정책표 9·10장
- 처리 순서: 질문 검증 → AI가 조건 변경으로 해석 → 서버가 기존 조건에 적용하고 범위 재검증 → 계산 엔진 → AI가 설명 → 숫자 대조·금지 표현 필터 → 응답
- AI가 바꾼 조건이 입력 범위를 벗어나면 버전을 만들지 않고 `clarify`로 답함
- AI가 새로 추가한 이벤트의 `id`는 서버가 제작
- 상대 날짜("내년 3월")는 서버가 오늘 날짜(KST)를 AI에 넘겨 해석
- "V2와 V3 차이 설명해줘" 같은 질문을 위해 대화의 모든 버전을 보냄
- 목표 역산("2개월 앞당기려면 매달 얼마?")도 `change`. 월 저축 숫자는 AI가 아니라 계산 엔진이 구함. 소수·상한 처리 규칙은 PM 확인 중
- 새 버전의 기준(보고 있는 버전 vs V1)은 PM·PD 확인 중. 지금은 보고 있는 버전(`baseVersionNo`) 기준
- 전체 처리 50초를 넘으면 `AI503_1` (Hosting 경유 요청 시간 제한 대비, 미확인)
- 캐시: no-store

03 AI 한줄요약
## **Request**

### **Header**

```
Content-Type: application/json
```

### **Parameter**

없음

### **Body**

| **필드** | **데이터 타입** | **필수** | **설명** |
| --- | --- | --- | --- |
| condition | Object | Y | 요약할 조건 (공통 규칙 5-1) |

### **Example**

```
POST /api/v1/ai/summary

{
  "condition": { "startMonth": "2026-11", "periodMonths": 12, "currentAsset": 500, "monthlySaving": 40, "events": [ ... ], "goal": { ... } }
}
```

## **Response**

### **성공 예시**

```json
{
  "isSuccess": true,
  "code": "AI200_2",
  "message": "요약을 만들었습니다.",
  "result": {
    "text": "5월 노트북 구입 때문에 목표에 70만원 모자라요.",
    "usedAssumptions": ["이자·세금 미반영", "가정 기반"]
  }
}
```

### **에러 예시**

```json
{
  "isSuccess": false,
  "code": "AI503_1",
  "message": "일시적인 오류로 요청을 처리하지 못했어요. 다시 한 번 물어봐 주시겠어요?",
  "result": null
}
```

### **Response Field (result)**

| **필드** | **데이터 타입** | **설명** |
| --- | --- | --- |
| text | String | 한줄요약 (1문장, 60자 안팎) |
| usedAssumptions | String[] | 요약에 쓴 가정 |

### **Error Code**

| **HttpStatus** | **ResultCode** | **ErrorMessage** | **Description** |
| --- | --- | --- | --- |
| 400 | CONDITION400_1~12 | (공통 규칙 3장) | 조건 검증 에러 |
| 429 | AI429_1 | 잠시 후 다시 물어봐 주세요. | 요청 제한 초과 (제안) |
| 503 | AI503_1 | 일시적인 오류로 요청을 처리하지 못했어요. 다시 한 번 물어봐 주시겠어요? | AI 타임아웃·오류 → 프론트가 기본 문장 표시 |

### **비고**

- 설명: 결과 화면의 AI 요약 (결과의 가장 큰 원인 한 문장)
- 관련 기능: RES-05, CHT-01, 정책표 9장
- 부르는 때: 결과 화면 진입, 슬라이더에서 손을 뗄 때, 조건 확정 때. 슬라이더를 움직이는 중에는 부르지 않음
- 서버는 프론트가 보낸 결과를 받지 않고 조건으로 다시 계산해서 AI에 넘김
- **실패하면 `AI503_1`만 내려감.** 프론트가 계산 값으로 기본 문장을 만듦 (정책표 9장 예시: "목표에 70만원 부족해요. 5월 지출이 가장 커요."). 화면에는 에러를 보여 주지 않음
- AI 대화의 `change` 응답에는 `summaryText`가 같이 와서 이 API를 다시 부르지 않아도 됨
- 캐시: no-store

04 상황 이름 제안
## **Request**

### **Header**

```
Content-Type: application/json
```

### **Parameter**

없음

### **Body**

| **필드** | **데이터 타입** | **필수** | **설명** |
| --- | --- | --- | --- |
| condition | Object | Y | 저장할 버전의 조건 (공통 규칙 5-1) |
| questions | String[] | Y | 저장할 버전을 만든 질문들. 1~~10개, 각 1~~200자 |
| currentName | String | Y | 지금 상황 이름 (1~30자) |

### **Example**

```
POST /api/v1/ai/scenario-name

{
  "condition": { ... },
  "questions": ["매달 10만원 더 모으면?"],
  "currentName": "상황 1 · 지금처럼"
}
```

## **Response**

### **성공 예시**

```json
{
  "isSuccess": true,
  "code": "AI200_3",
  "message": "이름을 제안했습니다.",
  "result": {
    "suggestedName": "월 10만원 더 모으기"
  }
}
```

### **에러 예시**

```json
{
  "isSuccess": false,
  "code": "AI503_1",
  "message": "일시적인 오류로 요청을 처리하지 못했어요. 다시 한 번 물어봐 주시겠어요?",
  "result": null
}
```

### **Response Field (result)**

| **필드** | **데이터 타입** | **설명** |
| --- | --- | --- |
| suggestedName | String | 제안 이름 1~30자 → 저장 화면 이름 입력창 기본값 |

### **Error Code**

| **HttpStatus** | **ResultCode** | **ErrorMessage** | **Description** |
| --- | --- | --- | --- |
| 400 | AI400_4 | 이름 제안 정보가 올바르지 않아요. | 질문이 없거나 10개 초과, 지금 이름이 비었음 |
| 400 | CONDITION400_1~12 | (공통 규칙 3장) | 조건 검증 에러 |
| 429 | AI429_1 | 잠시 후 다시 물어봐 주세요. | 요청 제한 초과 (제안) |
| 503 | AI503_1 | 일시적인 오류로 요청을 처리하지 못했어요. 다시 한 번 물어봐 주시겠어요? | AI 타임아웃·오류 → 프론트가 지금 이름을 그대로 채움 |

### **비고**

- 설명: 저장 화면에 들어올 때 대화 내용으로 상황 이름 제안
- 관련 기능: SAV-02, 정책표 12장
- 대화가 없으면(V1 저장) 부르지 않고 지금 이름을 씀
- 실패하면 화면에 에러를 보여 주지 않고 지금 이름을 그대로 채움
- 캐시: no-store

05 상황 목록 조회
## **Request**

### **Header**

```
Authorization: Bearer {Firebase ID 토큰}
```

### **Parameter**

없음

### **Body**

없음

### **Example**

```
GET /api/v1/scenarios
```

## **Response**

### **성공 예시**

```json
{
  "isSuccess": true,
  "code": "SCENARIO200_1",
  "message": "상황 목록 조회에 성공했습니다.",
  "result": {
    "totalCount": 2,
    "scenarios": [
      {
        "scenarioId": "3f6c9a2e-6b1d-4c1e-9a55-2d8f0e4b7c11",
        "name": "상황 2 · 월 10만원 더",
        "hasGoal": true,
        "goalName": "유럽 여행",
        "periodMonths": 12,
        "monthlySaving": 50,
        "eventCount": 2,
        "finalAsset": 1050,
        "increase": 550,
        "goalShortfall": -50,
        "sparkline": [500, 550, 600, 750, 800, 850, 750, 800, 850, 900, 950, 1000, 1050],
        "origin": { "scenarioId": "0b7d2c4e-1f3a-4e8b-9c6d-5a2e1f0b3c77", "name": "상황 1 · 지금처럼", "versionNo": 2 },
        "updatedAt": "2026-11-05T21:18:00+09:00"
      },
      {
        "scenarioId": "0b7d2c4e-1f3a-4e8b-9c6d-5a2e1f0b3c77",
        "name": "상황 1 · 지금처럼",
        "hasGoal": true,
        "goalName": "유럽 여행",
        "periodMonths": 12,
        "monthlySaving": 40,
        "eventCount": 2,
        "finalAsset": 930,
        "increase": 430,
        "goalShortfall": 70,
        "sparkline": [500, 540, 580, 720, 760, 800, 690, 730, 770, 810, 850, 890, 930],
        "origin": null,
        "updatedAt": "2026-11-05T21:10:00+09:00"
      }
    ]
  }
}
```

### **에러 예시**

```json
{
  "isSuccess": false,
  "code": "COMMON401_1",
  "message": "로그인이 필요해요.",
  "result": null
}
```

### **Response Field (result)**

| **필드** | **데이터 타입** | **설명** |
| --- | --- | --- |
| totalCount | Integer | 저장한 상황 수 → 새 상황 기본 이름 "상황 N"의 N(= totalCount + 1) |
| scenarios | Array | 최근 수정순 |
| scenarios[].scenarioId | String | 상황 ID (UUID) |
| scenarios[].name | String | 상황 이름 |
| scenarios[].hasGoal | Boolean | 목표 O/X 태그 |
| scenarios[].goalName | String | 목표 이름. 목표 없으면 `null` |
| scenarios[].periodMonths | Integer | 요약 줄 "12개월" |
| scenarios[].monthlySaving | Integer | 요약 줄 "월 40만원" |
| scenarios[].eventCount | Integer | 요약 줄 "이벤트 2개" |
| scenarios[].finalAsset | Integer | 결과 금액 "930만원" |
| scenarios[].increase | Integer | 목표 X 결과 문구 "+1,390만원" |
| scenarios[].goalShortfall | Integer | 목표 O 결과 문구. 양수 "유럽 여행까지 −70만원", 음수 "목표 달성 +50만원". 목표 없으면 `null` |
| scenarios[].sparkline | Integer[] | 미니 그래프 |
| scenarios[].origin | Object | AI 대화로 만든 상황이면 원래 상황 `scenarioId`·`name`·`versionNo` → "상황 1에서 AI 대화로 생성". 아니면 `null` |
| scenarios[].updatedAt | String | 수정 시각 "수정 11.05 21:10" |

### **Error Code**

| **HttpStatus** | **ResultCode** | **ErrorMessage** | **Description** |
| --- | --- | --- | --- |
| 401 | COMMON401_1 | 로그인이 필요해요. | 토큰 없음·만료 |

### **비고**

- 설명: 내가 저장한 미래(W03) 목록
- 관련 기능: LST-02, LST-03, LST-06, 정책표 12장
- 최대 20개(제안)라 페이지를 나누지 않음
- 저장한 상황이 없으면 `totalCount: 0`, `scenarios: []` → 빈 상태 화면
- 카드 문구는 서버가 만들지 않고 프론트가 숫자로 조립
- 원래 상황을 지웠으면 `origin`은 `null`이 됨.
- 캐시: no-store

06 새 상황으로 저장
## **Request**

### **Header**

```
Authorization: Bearer {Firebase ID 토큰}
Content-Type: application/json
Idempotency-Key: {UUID}
```

### **Parameter**

없음

### **Body**

| **필드** | **데이터 타입** | **필수** | **설명** |
| --- | --- | --- | --- |
| scenarioId | String | Y | 상황 ID. 프론트가 만든 UUID |
| name | String | Y | 상황 이름. 앞뒤 공백 제거 후 1~30자, 중복 허용 |
| memo | String | N | 메모 0~200자 |
| condition | Object | Y | 저장할 버전의 조건 (공통 규칙 5-1) |
| versionSnapshot | Object | Y | 저장하는 버전 정보 |
| versionSnapshot.no | Integer | Y | 버전 번호 1~10 |
| versionSnapshot.question | String | N | 그 버전을 만든 질문 1~200자. V1이거나 슬라이더만 바꿨으면 `null` |
| originScenarioId | String | N | 저장한 상황을 열어 대화하다가 V2 이상을 새 상황으로 저장할 때 원래 상황 ID |

### **Example**

```
POST /api/v1/scenarios
Idempotency-Key: 9b1d2f0e-4c3a-4e7b-8a6d-1f2e3d4c5b6a

{
  "scenarioId": "3f6c9a2e-6b1d-4c1e-9a55-2d8f0e4b7c11",
  "name": "월 10만원 더 모으기",
  "memo": "노트북은 5월에 그대로 사기로 함",
  "condition": { "startMonth": "2026-11", "periodMonths": 12, "currentAsset": 500, "monthlySaving": 50, "events": [ ... ], "goal": { ... } },
  "versionSnapshot": { "no": 2, "question": "매달 10만원 더 모으면?" },
  "originScenarioId": "0b7d2c4e-1f3a-4e8b-9c6d-5a2e1f0b3c77"
}
```

## **Response**

### **성공 예시 (201)**

```json
{
  "isSuccess": true,
  "code": "SCENARIO201_1",
  "message": "상황을 저장했습니다.",
  "result": {
    "scenarioId": "3f6c9a2e-6b1d-4c1e-9a55-2d8f0e4b7c11",
    "name": "월 10만원 더 모으기",
    "version": 0,
    "createdAt": "2026-11-15T17:30:00+09:00",
    "updatedAt": "2026-11-15T17:30:00+09:00",
    "warnings": []
  }
}
```

### **에러 예시**

```json
{
  "isSuccess": false,
  "code": "SCENARIO403_1",
  "message": "저장할 수 있는 상황은 20개예요. 쓰지 않는 상황을 삭제해 주세요.",
  "result": null
}
```

### **Response Field (result)**

| **필드** | **데이터 타입** | **설명** |
| --- | --- | --- |
| scenarioId | String | 상황 ID |
| name | String | 저장된 이름 → 토스트 "'{이름}'을 저장했어요" |
| version | Integer | 덮어쓰기 충돌 확인용 번호 (처음 0) |
| createdAt | String | 생성 시각 |
| updatedAt | String | 수정 시각 |
| warnings | Array | 기간 밖이라 계산에서 뺀 이벤트 |

### **Error Code**

| **HttpStatus** | **ResultCode** | **ErrorMessage** | **Description** |
| --- | --- | --- | --- |
| 400 | SCENARIO400_1 | 상황 이름을 입력해 주세요. | 이름이 비었거나 공백만 |
| 400 | SCENARIO400_2 | 상황 이름은 30자까지 입력할 수 있어요. | 이름 30자 초과 |
| 400 | SCENARIO400_3 | 메모는 200자까지 입력할 수 있어요. | 메모 200자 초과 |
| 400 | CONDITION400_1~12 | (공통 규칙 3장) | 조건 검증 에러 |
| 400 | COMMON400_2 | 요청 키가 필요해요. | `Idempotency-Key` 없음 |
| 401 | COMMON401_1 | 로그인이 필요해요. | 토큰 없음·만료 |
| 403 | SCENARIO403_1 | 저장할 수 있는 상황은 20개예요. 쓰지 않는 상황을 삭제해 주세요. | 저장한 상황이 이미 20개 (제안) |
| 409 | SCENARIO409_2 | 이미 저장된 상황이에요. | 같은 `scenarioId`가 이미 있음 |
| 422 | COMMON422_1 | 같은 요청 키로 다른 내용을 보냈어요. | 같은 키로 내용이 다른 요청 |

### **비고**

- 설명: 고른 버전 하나를 새 상황으로 저장 (나머지 버전은 저장하지 않음)
- 관련 기능: SAV-04(새 상황으로 저장), SAV-07~10, 정책표 12장
- 검증 순서는 이름 → 메모 → 조건이고, 첫 번째 에러 하나만 내려감
- 서버는 조건으로 다시 계산해서 목록 카드용 요약(결과 금액, 부족액, 미니 그래프)을 채움
- 기간 밖 이벤트가 있어도 저장은 되고 `warnings`로 알림
- 상황·이벤트·목표 저장은 한 트랜잭션. 중간에 실패하면 아무것도 저장되지 않음
- 재시도는 같은 `Idempotency-Key`로 보냄. 처음 성공했다면 같은 201 응답이 옴 (공통 규칙 7장)
- `originScenarioId`가 내 상황이 아니면 무시
- 캐시: no-store

07 상황 열기
## **Request**

### **Header**

```
Authorization: Bearer {Firebase ID 토큰}
```

### **Parameter**

| **파라미터** | **데이터 타입** | **필수** | **설명** |
| --- | --- | --- | --- |
| scenarioId | String | Y | 경로 변수. 상황 ID (UUID) |

### **Body**

없음

### **Example**

```
GET /api/v1/scenarios/3f6c9a2e-6b1d-4c1e-9a55-2d8f0e4b7c11
```

## **Response**

### **성공 예시**

```json
{
  "isSuccess": true,
  "code": "SCENARIO200_2",
  "message": "상황 조회에 성공했습니다.",
  "result": {
    "scenarioId": "3f6c9a2e-6b1d-4c1e-9a55-2d8f0e4b7c11",
    "name": "월 10만원 더 모으기",
    "memo": "노트북은 5월에 그대로 사기로 함",
    "condition": { "startMonth": "2026-11", "periodMonths": 12, "currentAsset": 500, "monthlySaving": 50, "events": [... ], "goal": {... } },
    "simulation": { "series": [... ], "summary": {... }, "warnings": [] },
    "sourceQuestions": ["매달 10만원 더 모으면?"],
    "version": 0,
    "createdAt": "2026-11-15T17:30:00+09:00",
    "updatedAt": "2026-11-15T17:30:00+09:00"
  }
}
```

### **에러 예시**

```json
{
  "isSuccess": false,
  "code": "SCENARIO404_1",
  "message": "상황을 찾을 수 없어요.",
  "result": null
}
```

### **Response Field (result)**

| **필드** | **데이터 타입** | **설명** |
| --- | --- | --- |
| scenarioId | String | 상황 ID |
| name | String | 상황 이름 |
| memo | String | 메모. 없으면 `null` |
| condition | Object | 저장한 조건 → 프론트는 이 조건을 V1로 시작 |
| simulation | Object | 저장한 조건으로 다시 계산한 결과 (SimulationResult) |
| sourceQuestions | String[] | 저장한 버전을 만든 질문 |
| version | Integer | 덮어쓰기·이름 변경 때 그대로 보낼 번호 |
| createdAt | String | 생성 시각 |
| updatedAt | String | 수정 시각 |

### **Error Code**

| **HttpStatus** | **ResultCode** | **ErrorMessage** | **Description** |
| --- | --- | --- | --- |
| 401 | COMMON401_1 | 로그인이 필요해요. | 토큰 없음·만료 |
| 404 | SCENARIO404_1 | 상황을 찾을 수 없어요. | 없는 상황, 다른 사람 상황 |

### **비고**

- 설명: 저장한 상황을 열어 결과 화면으로 (목표 O면 W07, 목표 X면 W08)
- 관련 기능: LST-04, 정책표 12장
- 저장 시점의 조건을 복원하고 대화는 V1부터 새로 시작 (이전 대화 버전은 저장되지 않음)
- 결과는 저장하지 않고 열 때마다 다시 계산. 같은 조건이면 결과도 같음
- 불러오기 실패 시 화면은 토스트 + 목록 유지
- 캐시: no-store

08 기존 상황에 덮어쓰기
## **Request**

### **Header**

```
Authorization: Bearer {Firebase ID 토큰}
Content-Type: application/json
Idempotency-Key: {UUID}
```

### **Parameter**

| **파라미터** | **데이터 타입** | **필수** | **설명** |
| --- | --- | --- | --- |
| scenarioId | String | Y | 경로 변수. 덮어쓸 상황 ID |

### **Body**

| **필드** | **데이터 타입** | **필수** | **설명** |
| --- | --- | --- | --- |
| name | String | Y | 상황 이름 1~30자 |
| memo | String | N | 메모 0~200자 |
| condition | Object | Y | 저장할 버전의 조건 (공통 규칙 5-1) |
| versionSnapshot | Object | Y | 저장하는 버전 정보 (06과 같음) |
| version | Integer | Y | 07 상황 열기에서 받은 `version` |

### **Example**

```
PUT /api/v1/scenarios/0b7d2c4e-1f3a-4e8b-9c6d-5a2e1f0b3c77
Idempotency-Key: 2c7e4a1b-9d3f-4b6e-8c2a-5f1d0e9b7a34

{
  "name": "상황 1 · 지금처럼",
  "memo": null,
  "condition": { ... },
  "versionSnapshot": { "no": 2, "question": "매달 10만원 더 모으면?" },
  "version": 0
}
```

## **Response**

### **성공 예시**

```json
{
  "isSuccess": true,
  "code": "SCENARIO200_3",
  "message": "상황을 덮어썼습니다.",
  "result": {
    "scenarioId": "0b7d2c4e-1f3a-4e8b-9c6d-5a2e1f0b3c77",
    "name": "상황 1 · 지금처럼",
    "version": 1,
    "createdAt": "2026-11-05T21:10:00+09:00",
    "updatedAt": "2026-11-15T17:40:00+09:00",
    "warnings": []
  }
}
```

### **에러 예시**

```json
{
  "isSuccess": false,
  "code": "SCENARIO409_1",
  "message": "다른 곳에서 이 상황이 바뀌었어요. 다시 열어 주세요.",
  "result": null
}
```

### **Response Field (result)**

06 새 상황으로 저장과 같아요. `version`은 1 올라간 값이에요.

| **필드** | **데이터 타입** | **설명** |
| --- | --- | --- |
| scenarioId | String | 상황 ID |
| name | String | 상황 이름 |
| version | Integer | 새 번호 |
| createdAt | String | 생성 시각 (그대로) |
| updatedAt | String | 수정 시각 |
| warnings | Array | 기간 밖 이벤트 |

### **Error Code**

| **HttpStatus** | **ResultCode** | **ErrorMessage** | **Description** |
| --- | --- | --- | --- |
| 400 | SCENARIO400_1~3 | (06과 같음) | 이름·메모 검증 에러 |
| 400 | CONDITION400_1~12 | (공통 규칙 3장) | 조건 검증 에러 |
| 400 | COMMON400_2 | 요청 키가 필요해요. | `Idempotency-Key` 없음 |
| 401 | COMMON401_1 | 로그인이 필요해요. | 토큰 없음·만료 |
| 404 | SCENARIO404_1 | 상황을 찾을 수 없어요. | 없는 상황, 다른 사람 상황 |
| 409 | SCENARIO409_1 | 다른 곳에서 이 상황이 바뀌었어요. 다시 열어 주세요. | `version`이 최신이 아님 (다른 탭·기기에서 먼저 바꿈) |
| 422 | COMMON422_1 | 같은 요청 키로 다른 내용을 보냈어요. | 같은 키로 내용이 다른 요청 |

### **비고**

- 설명: 저장 화면에서 "{기존 상황}에 덮어쓰기"를 고르고 확인 모달을 거친 뒤 호출
- 관련 기능: SAV-04, 정책표 12장
- 이벤트는 모두 지우고 새로 넣고, 요약·질문 원문도 새로 채움. 한 트랜잭션
- 재시도는 같은 `Idempotency-Key`로 보내요. 덮어쓰기는 성공했는데 응답만 잃어버린 경우에도 409가 아니라 처음 성공 응답이 옴.
- 캐시: no-store

09 상황 이름·메모 변경
## **Request**

### **Header**

```
Authorization: Bearer {Firebase ID 토큰}
Content-Type: application/json
```

### **Parameter**

| **파라미터** | **데이터 타입** | **필수** | **설명** |
| --- | --- | --- | --- |
| scenarioId | String | Y | 경로 변수. 상황 ID |

### **Body**

| **필드** | **데이터 타입** | **필수** | **설명** |
| --- | --- | --- | --- |
| name | String | N | 새 이름 1~30자. 안 보내면 그대로 |
| memo | String | N | 새 메모 0~200자. 안 보내면 그대로, `""`이면 지움 |
| version | Integer | Y | 07 상황 열기 또는 목록에서 받은 `version` |

### **Example**

```
PATCH /api/v1/scenarios/3f6c9a2e-6b1d-4c1e-9a55-2d8f0e4b7c11

{
  "name": "유럽 여행 플랜",
  "version": 0
}
```

## **Response**

### **성공 예시**

```json
{
  "isSuccess": true,
  "code": "SCENARIO200_4",
  "message": "상황 이름을 바꿨습니다.",
  "result": {
    "scenarioId": "3f6c9a2e-6b1d-4c1e-9a55-2d8f0e4b7c11",
    "name": "유럽 여행 플랜",
    "memo": "노트북은 5월에 그대로 사기로 함",
    "version": 1,
    "updatedAt": "2026-11-15T17:45:00+09:00"
  }
}
```

### **에러 예시**

```json
{
  "isSuccess": false,
  "code": "SCENARIO400_2",
  "message": "상황 이름은 30자까지 입력할 수 있어요.",
  "result": null
}
```

### **Response Field (result)**

| **필드** | **데이터 타입** | **설명** |
| --- | --- | --- |
| scenarioId | String | 상황 ID |
| name | String | 바뀐 이름 |
| memo | String | 메모 |
| version | Integer | 새 번호 |
| updatedAt | String | 수정 시각 (목록 맨 위로 올라감) |

### **Error Code**

| **HttpStatus** | **ResultCode** | **ErrorMessage** | **Description** |
| --- | --- | --- | --- |
| 400 | SCENARIO400_1 | 상황 이름을 입력해 주세요. | 이름이 공백만 |
| 400 | SCENARIO400_2 | 상황 이름은 30자까지 입력할 수 있어요. | 이름 30자 초과 |
| 400 | SCENARIO400_3 | 메모는 200자까지 입력할 수 있어요. | 메모 200자 초과 |
| 401 | COMMON401_1 | 로그인이 필요해요. | 토큰 없음·만료 |
| 404 | SCENARIO404_1 | 상황을 찾을 수 없어요. | 없는 상황, 다른 사람 상황 |
| 409 | SCENARIO409_1 | 다른 곳에서 이 상황이 바뀌었어요. 다시 열어 주세요. | `version`이 최신이 아님 |

### **비고**

- 설명: 상황 카드 ··· 메뉴의 이름 변경 (11/15 MVP 포함 결정)
- 관련 기능: LST-08 (디자인 화면 요청 중)
- 목록 응답에 `version`이 없으니, 카드에서 바로 바꾸려면 목록에 `version`을 추가해야 함. (프론트와 정할 것)
- 캐시: no-store

10 상황 삭제
## **Request**

### **Header**

```
Authorization: Bearer {Firebase ID 토큰}
```

### **Parameter**

| **파라미터** | **데이터 타입** | **필수** | **설명** |
| --- | --- | --- | --- |
| scenarioId | String | Y | 경로 변수. 상황 ID |

### **Body**

없음

### **Example**

```
DELETE /api/v1/scenarios/3f6c9a2e-6b1d-4c1e-9a55-2d8f0e4b7c11
```

## **Response**

### **성공 예시**

```json
{
  "isSuccess": true,
  "code": "SCENARIO200_5",
  "message": "상황을 삭제했습니다.",
  "result": null
}
```

### **에러 예시**

```json
{
  "isSuccess": false,
  "code": "SCENARIO404_1",
  "message": "상황을 찾을 수 없어요.",
  "result": null
}
```

### **Response Field (result)**

없음 (`null`)

### **Error Code**

| **HttpStatus** | **ResultCode** | **ErrorMessage** | **Description** |
| --- | --- | --- | --- |
| 401 | COMMON401_1 | 로그인이 필요해요. | 토큰 없음·만료 |
| 404 | SCENARIO404_1 | 상황을 찾을 수 없어요. | 없는 상황, 다른 사람 상황, 이미 삭제됨 |

### **비고**

- 설명: 상황 카드 ··· 메뉴의 삭제 (11/15 MVP 포함 결정). 휴지통 없이 바로 영구 삭제
- 관련 기능: LST-08 (디자인 화면 요청 중), 정책표 12장
- 프론트가 확인 모달("삭제하면 되돌릴 수 없어요")을 거친 뒤 호출
- 이벤트·목표도 같이 지워짐
- 이 상황에서 AI 대화로 만들어 저장한 다른 상황은 남고, 그 카드의 `origin`만 `null`이 됨
- 삭제 재시도 때 `SCENARIO404_1`이 오면 이미 지워진 것이라 성공으로 봐도 무방.
- 캐시: no-store

11 체험 모드 상황 가져오기
## **Request**

### **Header**

```
Authorization: Bearer {Firebase ID 토큰}
Content-Type: application/json
Idempotency-Key: {UUID}
```

### **Parameter**

없음

### **Body**

| **필드** | **데이터 타입** | **필수** | **설명** |
| --- | --- | --- | --- |
| scenarios | Array | Y | 이 브라우저(localStorage)의 상황 1~50개 |
| scenarios[] | Object | Y | 06 새 상황으로 저장 Body와 같은 모양 (`scenarioId`, `name`, `memo`, `condition`, `versionSnapshot`) |

### **Example**

```
POST /api/v1/scenarios/import
Idempotency-Key: 7a3e9c1d-2b4f-4d8a-9e6c-3f1b0a2d5c48

{
  "scenarios": [
    {
      "scenarioId": "a1b2c3d4-0000-4000-8000-000000000001",
      "name": "상황 1 · 지금처럼",
      "memo": null,
      "condition": { ... },
      "versionSnapshot": { "no": 1, "question": null }
    }
  ]
}
```

## **Response**

### **성공 예시**

```json
{
  "isSuccess": true,
  "code": "SCENARIO200_6",
  "message": "상황을 가져왔습니다.",
  "result": {
    "importedCount": 1,
    "skippedCount": 2,
    "imported": ["a1b2c3d4-0000-4000-8000-000000000001"],
    "skipped": [
      { "scenarioId": "a1b2c3d4-0000-4000-8000-000000000002", "reason": "ALREADY_EXISTS" },
      { "scenarioId": "a1b2c3d4-0000-4000-8000-000000000003", "reason": "LIMIT_EXCEEDED" }
    ]
  }
}
```

### **에러 예시**

```json
{
  "isSuccess": false,
  "code": "SCENARIO400_4",
  "message": "가져올 상황이 없어요.",
  "result": null
}
```

### **Response Field (result)**

| **필드** | **데이터 타입** | **설명** |
| --- | --- | --- |
| importedCount | Integer | 가져온 개수 → 토스트 "N개를 가져왔어요" |
| skippedCount | Integer | 건너뛴 개수 |
| imported | String[] | 가져온 상황 ID |
| skipped | Array | 건너뛴 상황과 이유 |
| skipped[].reason | String | `ALREADY_EXISTS` 이미 있음 / `LIMIT_EXCEEDED` 저장 개수 초과 / `INVALID` 값이 범위를 벗어남 |

### **Error Code**

| **HttpStatus** | **ResultCode** | **ErrorMessage** | **Description** |
| --- | --- | --- | --- |
| 400 | SCENARIO400_4 | 가져올 상황이 없어요. | 배열이 비었거나 50개 초과 |
| 400 | COMMON400_2 | 요청 키가 필요해요. | `Idempotency-Key` 없음 |
| 401 | COMMON401_1 | 로그인이 필요해요. | 토큰 없음·만료 |
| 422 | COMMON422_1 | 같은 요청 키로 다른 내용을 보냈어요. | 같은 키로 내용이 다른 요청 |

### **비고**

- 설명: 로그인 직후 "이 브라우저의 상황 N개를 가져올까요?"에 동의했을 때만 호출 (자동 이전 안 함)
- 관련 기능: LST-07, 정책표 12장 (가져오기 방식은 PM 확정 필요)
- 서버가 항목마다 다시 검증. 틀린 항목 하나 때문에 전체를 실패시키지 않고 `INVALID`로 건너뜀.
- 같은 ID가 이미 있으면 덮어쓰지 않고 건너뜀. 계정에 있던 상황은 건드리지 않음. 여러 번 보내도 중복되지 않음
- 개수 한도를 넘는 만큼은 배열 뒤쪽부터 `LIMIT_EXCEEDED`로 건너뜀
- 가져온 상황의 생성·수정 시각은 가져온 시각
- 가져온 뒤 브라우저 데이터를 지울지는 PM과 정할 것
- 캐시: no-store

12 회원 탈퇴 데이터 삭제
## **Request**

### **Header**

```
Authorization: Bearer {Firebase ID 토큰}
```

### **Parameter**

없음

### **Body**

없음

### **Example**

```
DELETE /api/v1/users/me
```

## **Response**

### **성공 예시**

```json
{
  "isSuccess": true,
  "code": "USER200_1",
  "message": "회원 데이터를 삭제했습니다.",
  "result": {
    "deletedScenarioCount": 3
  }
}
```

### **에러 예시**

```json
{
  "isSuccess": false,
  "code": "COMMON401_1",
  "message": "로그인이 필요해요.",
  "result": null
}
```

### **Response Field (result)**

| **필드** | **데이터 타입** | **설명** |
| --- | --- | --- |
| deletedScenarioCount | Integer | 지운 상황 수 (없으면 0) |

### **Error Code**

| **HttpStatus** | **ResultCode** | **ErrorMessage** | **Description** |
| --- | --- | --- | --- |
| 401 | COMMON401_1 | 로그인이 필요해요. | 토큰 없음·만료 |

### **비고**

- 설명: 회원 탈퇴 때 서버에 있는 내 데이터 전부 삭제 (11/15 MVP 포함 결정)
- 관련 기능: ACC-09 계정 메뉴 (디자인 화면 요청 중), 정책표 13장
- 지우는 것: 내 상황 전부(이벤트·목표 포함), 저장 요청 기록
- **순서**: 프론트가 확인 모달 → 이 API 호출 → 성공하면 Firebase 계정 삭제. 순서가 반대면 토큰이 무효가 돼서 서버 데이터를 지울 수 없음
- Firebase 계정 삭제는 최근에 로그인한 사용자만 가능해서, 오래된 로그인이면 다시 로그인을 요청해야 할 수 있음 (Firebase 동작, 미확인)
- 지울 데이터가 없어도 성공 (여러 번 불러도 결과가 같음)
- 닉네임 변경·비밀번호 재설정·로그아웃은 Firebase로 처리해서 서버 API가 없음
- 캐시: no-store

13 공시 상품 목록 조회
## **Request**

### **Header**

없음

### **Parameter**

| **파라미터** | **데이터 타입** | **필수** | **설명** |
| --- | --- | --- | --- |
| type | String | N | 쿼리 파라미터. `deposit` 정기예금(기본) / `saving` 적금 |
| termMonths | Integer | N | 쿼리 파라미터. 가입 기간(개월), 기본 12 |
| amountMax | Integer | N | 쿼리 파라미터. 현재 자산(만원). 최소 가입 금액이 이보다 큰 상품 제외 |
| monthlyAmount | Integer | N | 쿼리 파라미터. 적금일 때 월 저축액(만원). 월 한도가 이보다 작은 상품 제외 |
| sort | String | N | 쿼리 파라미터. `maxRate` 최고금리순(기본) / `baseRate` 기본금리순 / `term` 기간순 |
| limit | Integer | N | 쿼리 파라미터. 1~10, 기본 3. 더 보기는 `limit=10` |

### **Body**

없음

### **Example**

```
GET /api/v1/products?type=deposit&termMonths=12&amountMax=500&sort=maxRate&limit=3
```

## **Response**

### **성공 예시**

```json
{
  "isSuccess": true,
  "code": "PRODUCT200_1",
  "message": "상품 목록 조회에 성공했습니다.",
  "result": {
    "totalCount": 14,
    "asOfDate": "2026-11-01",
    "collectedAt": "2026-11-02T06:00:00+09:00",
    "stale": false,
    "source": "금융감독원 금융상품통합비교공시",
    "products": [
      {
        "productId": 101,
        "bank": "가나은행",
        "name": "예시 정기예금 A",
        "type": "deposit",
        "termMonths": 12,
        "interestType": "simple",
        "baseRate": 2.80,
        "maxRate": 3.20,
        "perks": "1. 급여이체 시 연 0.2%p 2. 비대면 가입 시 연 0.2%p",
        "perksItems": [
          { "condition": "급여이체", "rate": 0.2 },
          { "condition": "비대면 가입", "rate": 0.2 }
        ],
        "joinTarget": "실명의 개인",
        "joinWays": ["영업점", "인터넷", "스마트폰"],
        "minAmount": 100,
        "maxLimit": null,
        "depositProtected": true,
        "maturityRateNote": "만기일 기준 별도 적용",
        "link": "https://www.example-bank.co.kr",
        "asOfDate": "2026-11-01",
        "isSample": true
      }
    ]
  }
}
```

### **에러 예시**

```json
{
  "isSuccess": false,
  "code": "PRODUCT400_1",
  "message": "조회 조건이 올바르지 않아요.",
  "result": null
}
```

### **Response Field (result)**

| **필드** | **데이터 타입** | **설명** |
| --- | --- | --- |
| totalCount | Integer | 조건에 맞는 전체 개수. `limit`보다 크면 "더 보기" |
| asOfDate | String | 공시 기준일 |
| collectedAt | String | 수집 시각 |
| stale | Boolean | 기준일이 7일 넘게 지남 → "공시 기준일이 오래됐어요" |
| source | String | 출처 문구 |
| products[].productId | Long | 상품 ID |
| products[].bank | String | 금융사 |
| products[].name | String | 상품명 |
| products[].type | String | `deposit` / `saving` |
| products[].termMonths | Integer | 가입 기간 |
| products[].interestType | String | `simple` 단리 / `compound` 복리 |
| products[].baseRate | Number | 기본 금리 (연 %, 소수 둘째 자리) |
| products[].maxRate | Number | 최고 금리 (연 %) |
| products[].perks | String | 우대조건 원문 |
| products[].perksItems | Array | 우대조건 항목 `condition`·`rate`(%p). 개수 = "우대조건 2개". 우대조건 없으면 `[]`, 원문을 못 읽으면 `null` → 원문 표시 |
| products[].joinTarget | String | 가입 대상 |
| products[].joinWays | String[] | 가입 방법 → "비대면 가입 가능" |
| products[].minAmount | Integer | 최소 가입 금액(만원) → "100만원 이상". 못 읽으면 `null` → 숨김 |
| products[].maxLimit | Integer | 가입 한도(만원). `null`이면 한도 없음 |
| products[].depositProtected | Boolean | 예금자보호 여부. `null`이면 "예금자보호 여부는 금융사에서 확인하세요" |
| products[].maturityRateNote | String | 만기 후 이율 |
| products[].link | String | 금융사 홈페이지. `null`이면 버튼 숨김 |
| products[].asOfDate | String | 상품별 공시 기준일 |
| products[].isSample | Boolean | "예시 데이터" 태그 |

### **Error Code**

| **HttpStatus** | **ResultCode** | **ErrorMessage** | **Description** |
| --- | --- | --- | --- |
| 400 | PRODUCT400_1 | 조회 조건이 올바르지 않아요. | `termMonths`·금액이 음수, `limit`이 1~10 밖 |
| 400 | COMMON400_1 | 잘못된 요청이에요. | `type`·`sort` 값 오류 |

### **비고**

- 설명: 조건에 맞는 공시 예·적금 목록. AI가 아니라 서버 코드가 우리 DB에서 걸러서 정렬
- 관련 기능: FIN-01~12, MOB-03, 정책표 11장
- 결과가 없으면 `totalCount: 0`, `products: []` → "조건에 맞는 공시 상품이 없어요"
- 우대조건 항목·최소 가입 금액은 수집할 때 공시 원문을 코드(정규식)로 읽은 값. AI로 읽지 않음
- 예금자보호는 예금보험공사 데이터와 맞는 상품만 값이 있음. 보호 한도 금액은 문구에 넣지 않음
- 공시에 상품 페이지 주소가 없어서 `link`는 금융사 홈페이지. 버튼 문구는 "금융사 홈페이지에서 확인 ↗" 제안
- 최소 가입 금액을 못 읽은 상품을 `amountMax` 필터에서 뺄지는 PM 확인 중 (지금은 통과)
- 고지 문구("정보 제공용 목록이에요…")는 정책표 11장 확정 문구라 프론트에 고정
- 필드 이름은 금감원 인증키로 실제 응답을 받아 본 뒤 확정 (미확인)
- 캐시: 공개 데이터라 `Cache-Control: public, max-age=300` 가능


14 상품 수집 실행
## **Request**

### **Header**

```
X-Ingest-Token: {비밀 토큰}
```

### **Parameter**

없음

### **Body**

없음

### **Example**

```
POST /api/v1/internal/ingest
X-Ingest-Token: ********
```

## **Response**

### **성공 예시**

```json
{
  "isSuccess": true,
  "code": "INGEST200_1",
  "message": "상품 수집을 마쳤습니다.",
  "result": {
    "asOfDate": "2026-11-15",
    "collectedAt": "2026-11-15T06:00:12+09:00",
    "upsertedCount": 132,
    "failedCount": 0,
    "idempotencyKeysDeleted": 18
  }
}
```

### **에러 예시**

```json
{
  "isSuccess": false,
  "code": "INGEST409_1",
  "message": "수집이 이미 실행 중이에요.",
  "result": null
}
```

### **Response Field (result)**

| **필드** | **데이터 타입** | **설명** |
| --- | --- | --- |
| asOfDate | String | 이번 공시 기준일 |
| collectedAt | String | 수집 시각 |
| upsertedCount | Integer | 새로 넣거나 바꾼 상품 수 |
| failedCount | Integer | 실패한 상품 수 |
| idempotencyKeysDeleted | Integer | 같이 정리한 24시간 지난 저장 요청 기록 수 |

### **Error Code**

| **HttpStatus** | **ResultCode** | **ErrorMessage** | **Description** |
| --- | --- | --- | --- |
| 401 | INGEST401_1 | 수집 토큰이 올바르지 않아요. | 토큰 없음·불일치 |
| 409 | INGEST409_1 | 수집이 이미 실행 중이에요. | 다른 수집이 진행 중 |
| 502 | INGEST502_1 | 공시 데이터를 가져오지 못했어요. | 금감원·예금보험공사 API 오류 |

### **비고**

- 설명: GitHub Actions cron이 하루 한 번 호출. 프론트는 쓰지 않음
- 관련 기능: 정책표 11장 (하루 1회 수집, 기준일·수집 시각 저장)
- 금감원 상품 + 예금보험공사 데이터를 받아 우대조건·최소 가입 금액을 코드로 읽고 upsert. 두 번 불러도 결과가 같음
- Cloud Run은 응답 뒤 작업을 멈출 수 있어서, 수집을 끝낸 뒤 응답
- 토큰은 Secret Manager에 두고 코드에 X
- 캐시: no-store

15 헬스 체크
## **Request**

### **Header**

없음

### **Parameter**

없음

### **Body**

없음

### **Example**

```
GET /api/v1/health
```

## **Response**

### **성공 예시**

```json
{
  "isSuccess": true,
  "code": "COMMON200_1",
  "message": "정상입니다.",
  "result": { "status": "UP" }
}
```

### **에러 예시**

```json
{
  "isSuccess": false,
  "code": "COMMON500_1",
  "message": "서버에 문제가 생겼어요. 잠시 후 다시 시도해 주세요.",
  "result": null
}
```

### **Response Field (result)**

| **필드** | **데이터 타입** | **설명** |
| --- | --- | --- |
| status | String | `UP` |

### **Error Code**

| **HttpStatus** | **ResultCode** | **ErrorMessage** | **Description** |
| --- | --- | --- | --- |
| 500 | COMMON500_1 | 서버에 문제가 생겼어요. 잠시 후 다시 시도해 주세요. | 서버 이상 |

### **비고**

- 설명: 배포 확인·모니터링용
- 프론트가 실제 주소로 먼저 붙어 볼 수 있게 가장 먼저 배포
- DB까지 확인할지는 정할 것 (DB 절전을 깨우면 무료 사용량이 줄 수 있음, 미확인)
- 캐시: no-store






