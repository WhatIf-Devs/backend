# WhatIf_v0: AI 파트 작업 폴더

What If? 프로젝트(GDG G-Sprint)에서 AI 파트가 맡는 API **02 AI 대화, 03 AI 한줄요약, 04 상황 이름 제안**의 프롬프트, 스키마, 시험 자료, 참조 구현을 모아 둔 폴더입니다.
기준: What If API 명세와 API 공통 규칙(2026-11-16), 정책표, PRD, 기능명세서. 자세한 대응 관계는 `docs/ai-api-mapping.md`를 보세요.

## 구조
# 진행하면서 수정 및 조정 필요
## 파일 설명

### prompts/ — Gemini 시스템 지시문

| 파일 | 설명 |
| --- | --- |
| `interpret.system.txt` | API 02 1단계. 질문을 5가지 유형(change, explain, clarify, finance, refuse)으로 나누고 조건 변경을 JSON으로 바꾸는 규칙 |
| `explain.system.txt` | API 02 2단계. 계산이 끝난 값으로 답변 문장을 쓰는 규칙 (change, explainResult, explainTerm 세 모드) |
| `summary.system.txt` | API 03. 서버가 고른 원인으로 결과 화면 한줄요약(1문장, 60자 안팎)을 쓰는 규칙 |
| `scenario-name.system.txt` | API 04. 저장할 버전을 만든 질문들로 1~30자 상황 이름을 제안하는 규칙 |

### schema/ — 데이터 형식

| 파일 | 설명 |
| --- | --- |
| `condition.schema.json` | 모든 API가 함께 쓰는 Condition(현재 자산, 월 저축, 기간, 이벤트, 목표)의 형식과 허용 범위 |
| `ai-interpret.output.schema.json` | 1단계 해석 출력 형식. 유형별 객체 중 하나만 채움 |
| `ai-explain.output.schema.json` | 2단계 답변 출력 형식 (`answerText` + `summaryText` 또는 `highlightMonths`) |
| `ai-summary.output.schema.json` | 한줄요약 출력 형식 (`text`) |
| `ai-scenario-name.output.schema.json` | 이름 제안 출력 형식 (`suggestedName`) |
| `api-response.schema.json` | API 02·03·04 최종 응답 형식 (공통 응답 규칙 반영) |

#### schema/gemini/ — AI Studio·Gemini `responseSchema`에 그대로 넣는 스키마

| 파일 | 설명 |
| --- | --- |
| `interpret.response-schema.json` | 1단계 해석용 |
| `explain-change.response-schema.json` | 2단계 change용 (`answerText`, `summaryText`) |
| `explain-answer.response-schema.json` | 2단계 explain용 (`answerText`, `highlightMonths`) |
| `summary.response-schema.json` | 한줄요약용 |
| `scenario-name.response-schema.json` | 이름 제안용 |

#### schema/fixtures/

| 파일 | 설명 |
| --- | --- |
| `chat-requests.json` | API 02 요청 모양의 시험 데이터 4종: 목표 있음, 목표 없음, 버전 3개, 이벤트 이름에 지시문이 숨은 경우 |

#### schema/examples/ — 입출력 예시 (숫자는 참조 엔진으로 계산)

| 파일 | 설명 |
| --- | --- |
| `interpret.examples.json` | 1단계 해석 정답지 10개 (질문 → 기대 JSON) |
| `explain.inputs.json` | 2단계 입력 예시 5개, 예시 답변, 검증 결과 |
| `summary.inputs.json` | 한줄요약 입력 예시 3개(목표 부족, 초과, 목표 없음)와 예시 문장 |
| `scenario-name.inputs.json` | 이름 제안 입력 예시 3개와 예시 이름 |
| `api-responses.json` | API 02·03·04 최종 응답 예시 13개 (성공, 답변 검증 실패, 에러 포함) |

### tests/ — 시험 자료와 참조 구현

| 파일 | 설명 |
| --- | --- |
| `questions.json` | 1단계 해석 시험 질문 30개. 기대 결과와 기록 칸(`record`) 포함 |
| `golden.simulation.json` | 계산 엔진 골든 테스트: 930만원·부족 70만원·93%·5.8 / 1,050만원·2027-10 도달 / 음수 −150 / 역산 월 55만원 |
| `validator.cases.json` | 답변 검증기 단위 테스트 15개 (숫자 불일치, 금지 표현, 지시형, 이자 언급 등) |
| `condition.errors.json` | 검증 에러 코드 테스트 7개 (여러 필드가 틀려도 첫 번째 하나만) |

#### tests/reference/ — Python 참조 구현 (표준 라이브러리만 사용)

| 파일 | 설명 |
| --- | --- |
| `simulate.py` | 계산 엔진, 조건 검증, 해석 결과 적용, 목표 역산, 한줄요약 원인 선택(`topDriver`)의 기준 구현 |
| `validate_answer.py` | 답변 검증기 기준 구현. 허용 숫자 집합, 금지 표현, 문체·길이 검사 |
| `run_all.py` | 위 테스트를 한 번에 돌리는 자체 검사 스크립트. 실행: `python tests/reference/run_all.py` |

### fallback/

| 파일 | 설명 |
| --- | --- |
| `templates.json` | AI 실패 시 프론트가 쓰는 기본 문장, 서버 고정 문구(finance·refuse·가정 안내), 에러 문구, 금액·기간·날짜 표기 규칙 |




## Gemini 시험

1. Google AI Studio에서 `prompts/interpret.system.txt`를 System instructions에 넣고, `schema/gemini/interpret.response-schema.json`을 Structured output에 넣습니다. 온도는 0~0.2를 권합니다.
2. 입력은 `schema/fixtures/chat-requests.json`의 fixture에 `today`와 `question`을 더한 JSON입니다.
3. `tests/questions.json`의 질문을 차례로 넣고 `record`에 결과와 응답 시간을 적습니다.
4. 2단계·03·04는 `schema/examples/`의 `input`을 그대로 넣고 `sampleOutput`과 비교합니다.

## 자체 검사

```
python tests/reference/run_all.py
```

골든 계산, 검증기 단위 테스트, 질문 30개의 서버 적용 결과, 예시 답변 검증, 공통 응답 형태, 검증 에러 코드를 한 번에 확인합니다. 표준 라이브러리만 씁니다.

## 주의

- `examples`와 `questions`의 expected는 설계 의도이지 Gemini 실제 출력이 아닙니다.
- `tests/reference`는 BE 구현을 대신하지 않습니다. 기대값과 규칙을 코드로 고정하는 기준입니다. 명세에 없는 부분은 `ASSUMPTION` 주석으로 표시했습니다.
- `*.schema.json`(JSON Schema 2020-12)은 이 환경에 검증 라이브러리가 없어 자동 검증을 돌리지 못했습니다. VS Code나 Ajv로 확인하세요.
- `fromVersionNo`, `solveFor`, `explain.kind`, `topDriver`, 서버 고정 문구 분담은 BE와 합의 전의 제안입니다(`docs/ai-api-mapping.md` 7장).
