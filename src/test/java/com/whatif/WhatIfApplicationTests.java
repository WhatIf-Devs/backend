package com.whatif;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.whatif.support.IntegrationTestSupport;

class WhatIfApplicationTests extends IntegrationTestSupport {

	@Test
	@DisplayName("테스트컨테이너 PostgreSQL로 스프링 컨텍스트가 뜬다")
	void contextLoads() {
		assertThat(mockMvc).isNotNull();
	}

}
