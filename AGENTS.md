# What If 백엔드

현재 자산, 월 저축, 이벤트, 목표를 입력하면 월별 자산을 계산하고, 조건을 바꿔 비교하는 자산 시뮬레이터의 API 서버예요.
Claude, Codex 등 모든 AI 도구와 사람이 함께 따르는 규칙이에요.

## 명령어

```bash
docker compose up -d                                       # 로컬 PostgreSQL
./gradlew bootRun --args='--spring.profiles.active=local'  # 로컬 서버
./gradlew build                                            # 빌드 + 전체 테스트 (도커 실행 필요)
./gradlew test --tests "com.whatif.global.*"               # 일부 테스트
```

작업이 끝났다고 말하기 전에 `./gradlew build` 통과를 확인해요.

## 기술 스택

- 자바 21, 스프링 부트 4.1, 그래들(그루비 문법)
- JSON은 잭슨 3(`tools.jackson`)을 써요. `com.fasterxml.jackson.databind` 예제를 그대로 가져오지 않아요.
- JPA, PostgreSQL, 플라이웨이
- 로그인: Firebase Authentication. 서버는 ID 토큰만 검증해요.
- AI: Gemini API. 서버가 호출을 중계해요.
- 배포: Cloud Run, GitHub Actions
- 테스트: JUnit 5, AssertJ, Mockito, 테스트컨테이너(PostgreSQL), ArchUnit

## 기준 문서

구현 전에 해당 부분을 먼저 읽어요. 문서와 코드가 다르면 임의로 고르지 말고 물어봐요.

- `docs/api-spec.md`: API 경로, 요청·응답 필드, 결과 코드, 에러 문구
- `docs/erd.md`: 테이블, 컬럼, 인덱스, DDL
- `docs/review-checklist.md`: PR 전 점검표
- `ai/`: 프롬프트, 출력 스키마, 시험 자료 (AI 파트 관리)

"제안", "미정", "미확인"으로 표시된 내용은 확정이 아니에요. 구현 전에 확인해요.
API나 DB가 바뀌면 코드와 문서를 같은 PR에서 고쳐요.

## 패키지 구조

```
com.whatif
├── domain
│   ├── simulation   # 계산 엔진, 계산 API
│   ├── ai           # AI 대화, 한줄요약, 이름 제안
│   ├── scenario     # 상황 저장, 목록, 열기, 수정, 삭제, 가져오기
│   ├── product      # 공시 상품 조회, 수집
│   └── user         # 회원 탈퇴 시 데이터 삭제
└── global
    ├── client       # Gemini, 금감원 등 외부 호출
    ├── config       # 공통 설정
    ├── exception    # 전역 예외 처리, 공통 에러 코드
    ├── health       # 헬스 체크
    ├── response     # 공통 응답, 결과 코드
    └── security     # 보안 설정, 토큰 검증
```

도메인 내부:

```
domain/{도메인}/
├── controller/      # {도메인}SuccessCode
│   └── dto/         # {도메인}{행위}Request · {도메인}{행위}Response
├── service/         # {도메인}CommandService (쓰기) · {도메인}QueryService (조회)
│   └── dto/
│       ├── command/ # {도메인}{행위}Command
│       ├── query/   # {도메인}{행위}Query (파라미터 2개 이상일 때)
│       └── result/  # {도메인}{행위}Result
├── repository/
├── entity/
└── exception/       # {도메인}ErrorCode
```

- 의존 방향은 `controller → service → repository · entity`예요.
- 다른 도메인은 그 도메인의 서비스만 불러요. 남의 레포지토리와 엔티티를 직접 쓰지 않아요.
- 도메인 호출 방향은 `ai → simulation`, `scenario → simulation`, `user → scenario`예요.
- `global`은 `domain`을 참조하지 않아요.
- 계산 조건(`Condition`)과 계산 엔진은 `domain/simulation/engine`에 두고, 스프링·DB·다른 도메인에 의존하지 않아요.
- 의존 규칙은 ArchUnit 테스트가 강제해요. 테스트가 깨지면 구조를 고치고, 테스트를 느슨하게 고치지 않아요.

## 코드 규칙

- 요청·응답·명령·결과 객체는 `record`로 작성해요.
- 엔티티는 세터 금지, 기본 생성자는 `protected`, 연관관계는 지연 로딩이에요. 생성은 `create`로 시작하는 정적 팩토리로만 해요.
- 엔티티를 응답으로 내보내지 않아요.
- 조회 서비스는 클래스에 `@Transactional(readOnly = true)`, 명령 서비스는 쓰기 메서드마다 `@Transactional`을 붙여요.
- 형식 검증은 요청 객체, 업무 규칙 검증은 서비스에서 해요.
- 현재 시각은 `Clock` 빈에서 얻어요.
- 롬복 허용: `@Getter`, `@NoArgsConstructor(access = PROTECTED)`, `@Builder(access = PRIVATE)`, `@RequiredArgsConstructor`, `@Slf4j`
- 롬복 금지: `@Setter`, `@Data`, `@AllArgsConstructor`

## 응답·예외

```json
{ "isSuccess": true, "code": "SCENARIO200_1", "message": "...", "result": { } }
```

- 결과 코드는 `{도메인}{HTTP 상태}_{번호}` 형식이고, 코드와 문구는 `docs/api-spec.md` 그대로 써요.
- 에러이거나 돌려줄 데이터가 없으면 `result`는 `null`이에요.
- 검증 에러가 여러 개여도 첫 번째 하나만 내려줘요. 검증 어노테이션의 `message`에 결과 코드를 적어요.
- 도메인 에러는 `BusinessException`으로 던져요. 컨트롤러에서 에러 응답을 직접 만들지 않아요.
- 남의 리소스를 요청하면 403이 아니라 404로 응답해요. 조회·수정·삭제는 항상 본인 소유 조건으로 찾아요.

## 계산 규칙

- 금액은 만원 단위 정수예요. 예외는 `extraSavingNeeded`(소수 첫째 자리)뿐이에요.
- `A(0) = 현재 자산`, `A(m) = A(m-1) + 월 저축 + 그달 이벤트 합계`이고, 저축은 1개월차부터 반영해요.
- 이자와 세금은 반영하지 않아요.
- 반올림은 `HALF_UP`이고, 소수 계산에는 `double`을 쓰지 않아요.
- 같은 입력이면 항상 같은 결과가 나와야 해요. 골든 테스트: 930만원, 70만원 부족, 달성률 93%, 추가 저축 5.8, 월 50만원이면 1,050만원.
- 프론트가 보낸 계산 결과는 믿지 않고, 서버가 조건으로 다시 계산해요.

## AI 규칙

- **AI는 숫자를 만들지 않아요.** 모든 숫자는 계산 엔진 값이에요.
- AI의 역할은 질문을 조건 변경 JSON으로 해석하고, 계산 결과를 설명하는 것뿐이에요.
- AI 출력은 스키마로 검증하고, 적용한 조건은 입력 범위로 다시 검증해요.
- 답변 속 숫자를 엔진 값과 대조하고, 금지 표현을 걸러요.
- 트랜잭션 안에서 Gemini를 호출하지 않아요. 외부 호출에는 시간 제한을 걸어요.
- AI에 이메일, 닉네임, 회원 ID를 보내지 않아요.
- 질문 원문과 AI 답변을 로그에 남기지 않아요. 추적 번호와 글자 수만 남겨요.
- 금융상품 목록은 AI가 아니라 서버 코드가 만들어요. "추천" 표현을 쓰지 않아요.

## DB·마이그레이션

- `ddl-auto`는 `validate`예요. 스키마는 플라이웨이로만 바꿔요.
- 파일 이름은 `V{yyyyMMddHHmm}__{설명}.sql`이에요.
- **이미 병합된 마이그레이션 파일은 고치지 않아요.** 새 파일을 추가해요.
- 테이블·컬럼은 스네이크 표기, 인덱스는 `uk_`, `idx_`, `fk_` 접두어를 써요.

## 보안·개인정보

- 비밀 값은 환경 변수로만 읽어요. `.env`와 실제 키를 커밋하지 않아요.
- 이 레포는 Public이에요. API 키, 개인정보, 키가 찍힌 노트북 출력을 올리지 않아요.
- 토큰, 이메일, 입력 금액을 로그와 예외 메시지에 남기지 않아요.

## 테스트

- 기능과 테스트를 같은 PR에 넣어요.
- 테스트 이름은 `@DisplayName`에 한국어로 써요.
- 통합 테스트는 테스트컨테이너 PostgreSQL을 쓰고 H2는 쓰지 않아요.
- 꼭 검증할 것: 골든 값, 입력 범위 경계, 본인 소유가 아니면 404, 덮어쓰기 충돌, 같은 저장 요청 재시도

## 깃·PR

- 브랜치: `main`(운영), `develop`(개발), `feat/이슈번호-이름`, `fix/...`, `refactor/...`, `chore/...`, `docs/...`
- 커밋: `feat|fix|refactor|test|docs|chore: 한국어 설명 (#이슈번호)`
- PR은 `develop` 대상이고, 머지는 일반 merge commit으로 해요.
- 서버 코드 변경은 400줄 안팎으로 유지해요. 테스트와 `ai/`의 데이터는 줄 수에서 제외해요.
- `main`과 `develop`에 직접 커밋하지 않아요.
- AI가 작성한 코드도 PR 작성자가 설명할 수 있어야 머지해요.

## 작업할 때 지킬 것

- 답변, 문서, 주석, 커밋 메시지는 한국어로 써요.
- 명세에 없는 API, 필드, 에러 코드를 임의로 만들지 않아요.
- 실패하는 테스트를 지우거나 건너뛰게 만들어 통과시키지 않아요.
- 새 의존성을 추가할 때는 이유를 먼저 말해요.
