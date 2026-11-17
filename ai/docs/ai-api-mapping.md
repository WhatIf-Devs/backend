# AI 파트 기준: API 명세 반영본

기준일: 2026-11-16 · 출처: What If API 명세(BE 전달, 01~15), API 공통 규칙(공통 응답 형태), 정책표, PRD, 기능명세서

AI 파트가 맡는 API는 **02 AI 대화, 03 AI 한줄요약, 04 상황 이름 제안** 세 개입니다. 13 공시 상품 목록은 AI가 조회 조건(`productQuery`)의 일부만 정하고, 목록은 서버 코드가 만듭니다. 나머지 API(01, 05~12, 14, 15)는 AI와 무관하지만, 01의 계산 결과(`SimulationResult`)가 AI 입력의 근거가 됩니다.

## 0. 공통 응답 형태 (API 공통 규칙)

모든 응답은 `{isSuccess, code, message, result}` 네 필드입니다. 스키마는 `schema/api-response.schema.json`, 예시는 `schema/examples/api-responses.json`에 있습니다.

| 구분 | 규칙 | AI API 예 |
| --- | --- | --- |
| 성공 | `isSuccess: true`, code는 `{도메인}{HTTP 상태}_{번호}`, 데이터 없으면 `result: null` | `AI200_1` 대화, `AI200_2` 요약, `AI200_3` 이름 |
| 도메인 에러 | 규칙 위반. 각 API의 에러 코드 | `AI400_1~4`, `AI422_1`, `AI429_1`, `AI503_1` |
| 검증 에러 | 입력 범위·형식 위반. **필드별 코드, 여러 개가 틀려도 첫 번째 하나만**. code로 입력창을 찾아 에러 표시·포커스 | `CONDITION400_1~12` |
| 형식 오류 | JSON 깨짐, 타입 불일치, 필수값 누락 | `COMMON400_1` "잘못된 요청이에요." |
| 모든 에러 | `isSuccess: false`, `result: null`, `message`는 화면에 그대로 띄우는 문구 | |

AI 파트가 지킬 점은 세 가지입니다.

- **AI가 만든 조건이 틀린 것은 에러가 아닙니다.** 1단계 해석 결과를 적용한 조건이 범위를 벗어나면 `CONDITION400`이 아니라 성공 응답(`type: clarify`)으로 되묻습니다. `CONDITION400`은 프론트가 보낸 `versions[].condition` 자체가 틀렸을 때만 내려갑니다.
- **AI 답변이 검증에 실패한 것도 에러가 아닙니다.** change는 성공 응답 안에서 `answerText`·`summaryText`를 `null`로 보냅니다. 03·04는 `AI503_1`이 내려가지만, 프론트는 에러를 띄우지 않고 폴백(기본 문장, 지금 이름)을 씁니다.
- **에러 문구는 서버 `message`가 기준입니다.** AI 파트 문서의 오류 문구(`fallback/templates.json` `errors_api`)는 명세에 적힌 값을 옮긴 참고본입니다.

검증 에러 코드는 `CONDITION400_3`(현재 자산)과 `CONDITION400_12`(목표 기한)만 확인됐습니다. 나머지는 Condition 필드 순서(startMonth → periodMonths → currentAsset → monthlySaving → 이벤트 이름·유형·금액·시점·반복 → 목표 이름·금액·기한)로 추정해 `tests/reference/simulate.py`의 `CONDITION_CODES`와 `tests/condition.errors.json`에 넣었습니다. 두 확인값과 12개라는 개수가 이 순서와 맞아떨어지지만, 공통 규칙 3장으로 확인해야 합니다.

## 1. 공통 데이터: Condition (공통 규칙 5-1)

```json
{
  "startMonth": "2026-11", "periodMonths": 12, "currentAsset": 500, "monthlySaving": 40,
  "events": [
    { "id": "ev-1", "name": "성과급", "type": "income", "amount": 100, "month": "2027-02", "repeat": "once" },
    { "id": "ev-2", "name": "노트북 구입", "type": "expense", "amount": 150, "month": "2027-05", "repeat": "once" }
  ],
  "goal": { "name": "유럽 여행", "amount": 1000, "deadline": "2027-11" }
}
```

| 필드 | 범위 | 비고 |
| --- | --- | --- |
| `currentAsset` | 0~100,000만원 | 이전 파일의 `assets`에서 이름 변경. AI는 바꾸지 않음 |
| `monthlySaving` | 0~1,000만원 | 슬라이더 대상 |
| `periodMonths` | 6~120 | |
| `events[].id` | 서버가 생성 | AI는 수정·삭제 때 id로 지칭, 추가 때 id 없음 |
| `events[].repeat` | `once` / `monthly` | monthly = 그달부터 기간 끝까지 매달 |
| `goal` | 없으면 `null` | 기한이 기간 밖이면 `CONDITION400_12` |

계산식(01 비고): A(0) = 현재 자산, A(m) = A(m−1) + 월 저축 + 그달 이벤트 합계. 저축은 1개월차부터, 이자·세금 미반영.

골든 값: 명세 예시 → 930 · 부족 70 · 93% · 5.8 / 월 저축 50 → 1,050 · 도달 2027-10 / 자산 0·저축 0·지출 150(2027-05) → 음수 경고 2027-05 −150. 참조 구현 `tests/reference/simulate.py`가 모두 재현합니다.

## 2. API 02 AI 대화: 두 단계 구조

처리 순서(명세 비고): 질문 검증 → **AI 해석(1단계)** → 서버가 기준 조건에 적용·범위 재검증 → 계산 엔진 → **AI 답변(2단계)** → 숫자 대조·금지 표현 필터 → 응답.

### 1단계 해석: 입력과 출력

- 입력: 요청 body(`question`, `baseVersionNo`, `nextVersionNo`, `versions[]`) + 서버가 붙이는 `today`(KST).
- 출력: `schema/ai-interpret.output.schema.json`. `type`과 그 유형의 객체 하나만 채움.
- 프롬프트: `prompts/interpret.system.txt`, Gemini 스키마: `schema/gemini/interpret.response-schema.json`.

### 응답 필드별 생성 주체

| `result.type` | 응답 필드 | 만드는 곳 |
| --- | --- | --- |
| change | `newCondition` | 서버: 1단계 `change`를 기준 버전에 적용. 새 이벤트 id 생성 |
| change | `result`, `v1Result` | 서버 계산 엔진 |
| change | `answerText`, `summaryText` | **AI 2단계** (mode `change`). 실패하면 각각 `null` |
| change | `versionCard` (`title` 포함) | 서버 코드. 제목에 숫자가 들어가므로 AI가 만들지 않음 (제안) |
| change | `usedAssumptions` | 서버 고정값 `["이자·세금 미반영", "가정 기반"]` |
| explain | `answerText`, `highlightMonths` | **AI 2단계** (mode `explainResult` 또는 `explainTerm`) |
| clarify | `answerText`, `options[{label, question}]` | **AI 1단계**. 범위 초과로 서버가 바꾼 clarify는 서버 문구 |
| finance | `productQuery.type`, `termMonths`, `sort` | **AI 1단계** (언급 없으면 `null` → 서버 기본값) |
| finance | `productQuery.amountMax`, `monthlyAmount`, `limit` | 서버: `currentAsset`, `monthlySaving`(적금일 때), 3 |
| finance | `answerText` | 서버 고정 문구 |
| refuse | `answerText`, `examples` | 서버 고정 문구·칩 (AI는 `refuse.reason`만, 로그용) |

### 2단계 답변 입력 (서버가 계산해서 넘김)

- mode `change`: `changes`(바뀐 항목의 from·to·delta), `base`·`new` 결과 요약, `diff.vsBase`·`diff.vsV1`, `solved`(목표 역산 때 엔진이 구한 월 저축).
- mode `explainResult`: 대상 버전들의 조건 요약, 결과 요약, `declines`(자산이 줄어든 달과 변화량), `diffs`(버전 간 차이).
- mode `explainTerm`: `term`만. 숫자·금리·상품명 금지.
- 예시: `schema/examples/explain.inputs.json` (숫자는 모두 참조 엔진으로 계산).

AI가 차이 값을 직접 빼지 않도록, 서버가 `delta`와 `diff`를 미리 계산해 넘기는 것이 핵심입니다.

## 3. API 03 한줄요약

- 서버가 조건으로 다시 계산한 뒤 AI에 `situation`, `summary`, `topDriver`를 넘깁니다. 프롬프트는 `prompts/summary.system.txt`입니다.
- `topDriver` 규칙(제안, `simulate.py top_driver`): 목표 부족이거나 자산이 음수가 되면 영향이 가장 큰 지출 이벤트, 그 외에는 월 저축 누적과 수입 이벤트 중 영향이 가장 큰 것입니다. 명세 예시 "5월 노트북 구입 때문에 목표에 70만원 모자라요."와 일치합니다.
- 실패하면 `AI503_1`만 내려가고, 프론트가 `fallback/templates.json`의 문장을 씁니다.
- change 응답의 `summaryText`가 있으면 이 API를 다시 부르지 않습니다.

## 4. API 04 상황 이름 제안

- 입력: `condition`, `questions[]`, `currentName`. 출력: `suggestedName`(1~30자). 프롬프트는 `prompts/scenario-name.system.txt`입니다.
- 숫자는 질문과 조건에 있는 값만 허용합니다. 실패하면 프론트가 `currentName`을 그대로 씁니다. V1 저장 때는 부르지 않습니다.

## 5. 검증 (2단계 답변, 03, 04 공통)

- 허용 숫자 집합 = AI에 넘긴 입력 안의 금액·달·달성률·기간·버전 번호(`validate_answer.allowed_from_input`)입니다.
- 실패 사유는 금액·비율·달·연도·기간·버전 불일치, 분류 불가 숫자, 금지 표현, 지시형("~세요"), 이자 언급, 문장 수·길이 초과, 해요체 아님입니다.
- 실패하면 재생성(최대 2회)하고, 그래도 실패하면 해당 필드를 `null`로 보냅니다. 프론트가 폴백 문장을 씁니다.
- 가정 안내 "이자·세금은 반영하지 않았어요."는 **검증을 통과한 뒤 서버가 `answerText` 끝에 붙이는 것을 제안**합니다. AI가 쓰면 누락되거나 이자 언급 검사에 걸립니다.

## 6. 응답 시간

명세는 전체 50초 초과 시 `AI503_1`입니다. 정책표 목표는 평균 10초, 20초 타임아웃입니다. change는 Gemini 호출이 최소 2회이고, 재생성까지 하면 최대 4회입니다. 1단계는 빠른 모델과 낮은 온도로 처리하는 것을 권합니다.

## 7. BE에 확인할 것 (11/16 기준)

| # | 질문 | 제안 |
| --- | --- | --- |
| 1 | 공통 규칙 3장 `CONDITION400_1~12` 목록과 문구 | 3·12번만 확인. 나머지는 필드 순서로 추정(0장). 범위 재검증 실패를 clarify 문구로 바꿀 때도 필요 |
| 2 | 목표 역산 신호 | 1단계 출력 `change.solveFor: "monthlySaving"`. 올림 정수(참조 구현) vs 소수는 PM 확인 중 |
| 3 | 다른 버전 기준 변경("V2에서 ~") | 1단계 출력 `change.fromVersionNo`. 미채택이면 항상 `baseVersionNo` |
| 4 | 용어 설명 질문의 type | `explain` + `highlightMonths: []` |
| 5 | `productQuery` 채우는 주체 | AI는 `type`·`termMonths`·`sort`, 서버는 금액·`limit` |
| 6 | 가정 안내 문장 | 서버가 검증 후 붙임 |
| 7 | `versionCard.title` | 서버 코드가 변경 내용으로 생성 (예: "월 50만원") |
| 8 | refuse의 `examples` | 서버 고정 칩(목표 O/X 별), AI는 `reason`만 |
| 9 | 슬라이더 값 | 정책표 8장대로 보고 있는 버전의 `condition.monthlySaving`에 반영돼 전송되는지 |
| 10 | `negativeAsset`, `warnings[]`, `extraSavingNeeded`(부족 없을 때) 모양 | 참조 구현은 `{month, asset}`, `{eventId, name, month}`, `null`로 가정 |
| 11 | `milestones` 계산 방식 | 명세 예시(기간 12개월인데 `after5Years` 2850)로 보아 기간과 무관하게 연장 계산하는 것으로 추정 |
| 12 | "5년 뒤엔 얼마야?" | 새 버전(`periodMonths` 60) vs `milestones.after5Years`로 explain. 버전 정책상 전자 |
| 13 | 상황 이름 접두어 | 목록 예시는 "상황 2 · 월 10만원 더", 제안 예시는 "월 10만원 더 모으기". 접두어를 누가 붙이나 |

## 8. 파일 대응표

| 파일 | 대응 API |
| --- | --- |
| `prompts/interpret.system.txt` | 02 1단계 |
| `prompts/explain.system.txt` | 02 2단계 |
| `prompts/summary.system.txt` | 03 |
| `prompts/scenario-name.system.txt` | 04 |
| `schema/condition.schema.json` | 01·02·03·04·06·08 공통 Condition |
| `schema/api-response.schema.json` | 02·03·04 응답 (공통 응답 형태) |
| `schema/examples/api-responses.json` | 02 다섯 유형, 03, 04의 성공·에러 응답 예시 |
| `tests/condition.errors.json` | 검증 에러 코드(첫 번째 하나만) 테스트 |
| `schema/ai-*.output.schema.json` | AI 출력 (내부, 서버가 응답 필드로 옮김) |
| `schema/gemini/*.response-schema.json` | Google AI Studio·Gemini `responseSchema` |
| `schema/fixtures/chat-requests.json` | 02 요청 모양 시험 데이터 |
| `schema/examples/*.json` | 1·2단계, 03, 04 입출력 예시 |
| `tests/questions.json` | 1단계 시험 질문 30개 |
| `tests/golden.simulation.json` | 01 골든 테스트 |
| `tests/validator.cases.json` | 검증기 단위 테스트 15개 |
| `tests/reference/*.py` | 계산·적용·검증 참조 구현과 자체 검사 |
| `fallback/templates.json` | FE 폴백 문장, 서버 고정 문구, 표기 규칙 |
