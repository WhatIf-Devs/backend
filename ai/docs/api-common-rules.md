# API 공통 규칙: 공통 응답 형태

BE 전달 (2026-11-16). 원문: Notion "API 공통 규칙"

## 성공 응답 (데이터 유/무)

- 모든 성공은 `isSuccess: true`, code는 `{도메인}{HTTP 상태}_{번호}`
- 데이터 있음: `result`에 객체

```json
{
  "isSuccess": true,
  "code": "SCENARIO200_1",
  "message": "상황 목록 조회에 성공했습니다.",
  "result": { "totalCount": 0, "scenarios": [] }
}
```

- 데이터 없음: `result: null` (예: 상황 삭제)

```json
{
  "isSuccess": true,
  "code": "SCENARIO200_5",
  "message": "상황을 삭제했습니다.",
  "result": null
}
```

## 에러 응답 (도메인 에러/검증 에러)

- 모든 에러는 `isSuccess: false`, `result: null`
- 에러 `message`는 화면에 그대로 띄우는 문구
- 도메인 에러: 규칙 위반(저장 개수 초과, 덮어쓰기 충돌, 없는 상황 등) → 각 API의 에러 코드

```json
{
  "isSuccess": false,
  "code": "SCENARIO409_1",
  "message": "다른 곳에서 이 상황이 바뀌었어요. 다시 열어 주세요.",
  "result": null
}
```

- 검증 에러: 입력값 범위·형식 위반 → 필드별 에러 코드, 여러 필드가 틀려도 첫 번째 하나만
- code만 보면 어느 입력창인지 알 수 있음 (해당 입력창에 에러 + 포커스)

```json
{
  "isSuccess": false,
  "code": "CONDITION400_3",
  "message": "현재 자산은 0~100,000만원으로 입력해 주세요.",
  "result": null
}
```

- JSON 깨짐·타입 불일치·필수값 누락 등 필드별 코드가 없는 형식 오류는 `COMMON400_1`
