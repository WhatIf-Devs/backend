package com.whatif;

import java.util.TimeZone;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class WhatIfApplication {

	public static void main(String[] args) {
		// 계산 시작 월과 응답 시각의 기준을 한국 시간으로 고정한다
		TimeZone.setDefault(TimeZone.getTimeZone("Asia/Seoul"));
		SpringApplication.run(WhatIfApplication.class, args);
	}

}
