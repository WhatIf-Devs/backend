package com.whatif.global.response;

import org.springframework.http.HttpStatus;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/** 명세의 공통 성공 코드. */
@Getter
@RequiredArgsConstructor
public enum CommonSuccessCode implements ResultCode {

	HEALTH_OK(HttpStatus.OK, "COMMON200_1", "정상입니다.");

	private final HttpStatus httpStatus;
	private final String code;
	private final String message;

}
