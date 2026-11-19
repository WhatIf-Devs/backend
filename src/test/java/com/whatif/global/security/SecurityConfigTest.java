package com.whatif.global.security;

import static org.hamcrest.Matchers.nullValue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.whatif.support.IntegrationTestSupport;

class SecurityConfigTest extends IntegrationTestSupport {

	@Test
	@DisplayName("허용 목록에 없는 경로를 로그인 없이 호출하면 COMMON401_1로 응답한다")
	void unauthorized() throws Exception {
		mockMvc.perform(get("/api/v1/scenarios"))
			.andExpect(status().isUnauthorized())
			.andExpect(jsonPath("$.isSuccess").value(false))
			.andExpect(jsonPath("$.code").value("COMMON401_1"))
			.andExpect(jsonPath("$.message").value("로그인이 필요해요."))
			.andExpect(jsonPath("$.result").value(nullValue()));
	}

}
