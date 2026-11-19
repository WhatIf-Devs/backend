package com.whatif.global.health;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.whatif.support.IntegrationTestSupport;

class HealthControllerTest extends IntegrationTestSupport {

	@Test
	@DisplayName("로그인 없이 헬스 체크를 호출하면 공통 응답 형식으로 UP을 돌려준다")
	void health() throws Exception {
		mockMvc.perform(get("/api/v1/health"))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.isSuccess").value(true))
			.andExpect(jsonPath("$.code").value("COMMON200_1"))
			.andExpect(jsonPath("$.message").value("정상입니다."))
			.andExpect(jsonPath("$.result.status").value("UP"));
	}

}
