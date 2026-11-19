package com.whatif.global.config;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.whatif.support.IntegrationTestSupport;

class TraceIdFilterTest extends IntegrationTestSupport {

	@Test
	@DisplayName("성공 응답에 서버가 만든 추적 번호를 넣고 클라이언트가 보낸 값은 쓰지 않는다")
	void generatesTraceId() throws Exception {
		String traceId = mockMvc.perform(get("/api/v1/health").header(TraceIdFilter.TRACE_ID_HEADER, "forged"))
			.andReturn().getResponse().getHeader(TraceIdFilter.TRACE_ID_HEADER);

		assertThat(traceId).hasSize(16).isNotEqualTo("forged");
	}

	@Test
	@DisplayName("시큐리티가 거절한 401 응답에도 추적 번호를 넣는다")
	void addsTraceIdToSecurityError() throws Exception {
		String traceId = mockMvc.perform(get("/api/v1/scenarios"))
			.andReturn().getResponse().getHeader(TraceIdFilter.TRACE_ID_HEADER);

		assertThat(traceId).hasSize(16);
	}

}
