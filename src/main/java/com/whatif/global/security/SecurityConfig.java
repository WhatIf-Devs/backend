package com.whatif.global.security;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;

import lombok.RequiredArgsConstructor;

/**
 * 보안 설정. 허용 목록에 없는 경로는 모두 로그인이 필요하다.
 * Firebase ID 토큰 검증은 인증 이슈에서 추가한다. 그 전까지 로그인이 필요한 경로는 401로 응답한다.
 */
@Configuration
@RequiredArgsConstructor
public class SecurityConfig {

	private static final String[] SWAGGER_PATHS = {"/swagger-ui.html", "/swagger-ui/**", "/v3/api-docs/**"};

	private final ApiAuthenticationEntryPoint authenticationEntryPoint;

	// 스웨거가 꺼진 환경(운영)에서는 경로도 허용하지 않는다
	@Value("${springdoc.api-docs.enabled:true}")
	private boolean swaggerEnabled;

	@Bean
	public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
		http
			.csrf(AbstractHttpConfigurer::disable)
			.formLogin(AbstractHttpConfigurer::disable)
			.httpBasic(AbstractHttpConfigurer::disable)
			.logout(AbstractHttpConfigurer::disable)
			.requestCache(AbstractHttpConfigurer::disable)
			.sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
			.exceptionHandling(exception -> exception.authenticationEntryPoint(authenticationEntryPoint))
			.authorizeHttpRequests(auth -> {
				if (swaggerEnabled) {
					auth.requestMatchers(SWAGGER_PATHS).permitAll();
				}
				auth
					.requestMatchers("/api/v1/health").permitAll()
					.anyRequest().authenticated();
			});
		return http.build();
	}

}
