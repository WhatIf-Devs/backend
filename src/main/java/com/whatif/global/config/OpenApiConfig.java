package com.whatif.global.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;

/** 스웨거 문서 설정. Authorize 버튼에 Firebase ID 토큰을 넣으면 요청에 Bearer 헤더가 붙는다. 운영에서는 꺼져 있다. */
@Configuration
public class OpenApiConfig {

	private static final String BEARER_SCHEME = "bearerAuth";

	@Bean
	public OpenAPI openApi() {
		return new OpenAPI()
			.info(new Info().title("What If API").version("v1"))
			.components(new Components().addSecuritySchemes(BEARER_SCHEME, new SecurityScheme()
				.type(SecurityScheme.Type.HTTP)
				.scheme("bearer")
				.bearerFormat("JWT")))
			.addSecurityItem(new SecurityRequirement().addList(BEARER_SCHEME));
	}

}
