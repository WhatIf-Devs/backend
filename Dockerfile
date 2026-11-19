# syntax=docker/dockerfile:1
# What If API 서버 이미지 (Cloud Run, linux/amd64)
# 기본 이미지는 태그와 다이제스트를 함께 고정한다. 올릴 때는 두 값을 같이 바꾼다.

FROM eclipse-temurin:21-jdk-noble@sha256:114cabb73033ca4ce7ceec3deb62396bc1b716282bae051ed3c1d82e38fcab2d AS build
WORKDIR /workspace

# 의존성 내려받기를 소스와 분리해 캐시한다
COPY gradlew settings.gradle build.gradle ./
COPY gradle gradle
RUN --mount=type=cache,target=/root/.gradle ./gradlew dependencies --no-daemon -q > /dev/null

# 테스트는 CI(./gradlew build)에서 이미 돌리므로 여기서는 실행 가능한 jar만 만든다
COPY src src
RUN --mount=type=cache,target=/root/.gradle ./gradlew bootJar --no-daemon -q \
 && cp "$(find build/libs -name '*.jar' ! -name '*-plain.jar')" app.jar \
 && java -Djarmode=tools -jar app.jar extract --layers --launcher --destination extracted

FROM eclipse-temurin:21-jre-noble@sha256:0eda5830ed7b669abc246a8dc520ea8a23cab06f9a8d4b6964109e2f2394e46f
ENV TZ=Asia/Seoul
WORKDIR /app

# 기본 이미지에 있는 일반 사용자(ubuntu, uid 1000)로 실행한다
COPY --from=build --chown=1000:1000 /workspace/extracted/dependencies/ ./
COPY --from=build --chown=1000:1000 /workspace/extracted/spring-boot-loader/ ./
COPY --from=build --chown=1000:1000 /workspace/extracted/snapshot-dependencies/ ./
COPY --from=build --chown=1000:1000 /workspace/extracted/application/ ./
USER 1000:1000

EXPOSE 8080
ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
