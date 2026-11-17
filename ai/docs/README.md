# docs 

| 파일 | 내용 |
| --- | --- |
| `ai-api-mapping.md` | **AI 파트 기준 문서.** API 명세 02·03·04와 AI 입출력의 대응, 생성 주체, 검증, BE 확인 사항 |
| `api-spec.md` | BE가 전달한 What If API 명세 원문 (01~15) |
| `api-common-rules.md` | API 공통 규칙 중 공통 응답 형태 (성공·에러·검증 에러) |
| `meeting-prep.md` | (직접 저장) 회의 준비 자료를 Markdown으로 내보낸 파일 |


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
