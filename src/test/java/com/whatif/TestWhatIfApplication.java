package com.whatif;

import org.springframework.boot.SpringApplication;

/** 도커 컴포즈 없이 테스트컨테이너 DB로 서버를 띄울 때 쓴다. */
public class TestWhatIfApplication {

	public static void main(String[] args) {
		SpringApplication.from(WhatIfApplication::main).with(TestcontainersConfiguration.class).run(args);
	}

}
