package com.whatif.global.exception;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;

import com.whatif.support.IntegrationTestSupport;

@WithMockUser
class GlobalExceptionHandlerTest extends IntegrationTestSupport {

	@Test
	@DisplayName("도메인 에러는 담긴 결과 코드로 응답한다")
	void businessException() throws Exception {
		mockMvc.perform(get("/api/v1/test/business"))
			.andExpect(status().isConflict())
			.andExpect(jsonPath("$.isSuccess").value(false))
			.andExpect(jsonPath("$.code").value("TEST409_1"));
	}

	@Test
	@DisplayName("검증 에러가 여러 개면 필드 선언 순서상 첫 번째 코드 하나만 응답한다")
	void firstValidationError() throws Exception {
		mockMvc.perform(post("/api/v1/test/validation")
				.contentType(MediaType.APPLICATION_JSON)
				.content("{}"))
			.andExpect(status().isBadRequest())
			.andExpect(jsonPath("$.code").value("TEST400_1"));
	}

	@Test
	@DisplayName("JSON이 깨지면 COMMON400_1로 응답한다")
	void malformedJson() throws Exception {
		mockMvc.perform(post("/api/v1/test/validation")
				.contentType(MediaType.APPLICATION_JSON)
				.content("{"))
			.andExpect(status().isBadRequest())
			.andExpect(jsonPath("$.code").value("COMMON400_1"));
	}

	@Test
	@DisplayName("없는 경로는 COMMON404_1로 응답한다")
	void notFound() throws Exception {
		mockMvc.perform(get("/api/v1/test/missing"))
			.andExpect(status().isNotFound())
			.andExpect(jsonPath("$.code").value("COMMON404_1"));
	}

	@Test
	@DisplayName("지원하지 않는 메서드는 COMMON405_1로 응답한다")
	void methodNotAllowed() throws Exception {
		mockMvc.perform(post("/api/v1/health"))
			.andExpect(status().isMethodNotAllowed())
			.andExpect(jsonPath("$.code").value("COMMON405_1"));
	}

	@Test
	@DisplayName("예상하지 못한 오류는 내부 내용을 숨기고 COMMON500_1로 응답한다")
	void unexpected() throws Exception {
		mockMvc.perform(get("/api/v1/test/unexpected"))
			.andExpect(status().isInternalServerError())
			.andExpect(jsonPath("$.code").value("COMMON500_1"))
			.andExpect(jsonPath("$.message").value("서버에 문제가 생겼어요. 잠시 후 다시 시도해 주세요."));
	}

}
