package com.whatif.global.exception;

import org.springframework.http.HttpStatus;

import com.whatif.global.response.ResultCode;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/** 명세 공통 규칙 3장의 공통 에러. */
@Getter
@RequiredArgsConstructor
public enum CommonErrorCode implements ResultCode {

	BAD_REQUEST(HttpStatus.BAD_REQUEST, "COMMON400_1", "잘못된 요청이에요."),
	IDEMPOTENCY_KEY_REQUIRED(HttpStatus.BAD_REQUEST, "COMMON400_2", "요청 키가 필요해요."),
	UNAUTHORIZED(HttpStatus.UNAUTHORIZED, "COMMON401_1", "로그인이 필요해요."),
	NOT_FOUND(HttpStatus.NOT_FOUND, "COMMON404_1", "요청한 주소를 찾을 수 없어요."),
	METHOD_NOT_ALLOWED(HttpStatus.METHOD_NOT_ALLOWED, "COMMON405_1", "지원하지 않는 요청 방식이에요."),
	IDEMPOTENCY_KEY_REUSED(HttpStatus.UNPROCESSABLE_CONTENT, "COMMON422_1", "같은 요청 키로 다른 내용을 보냈어요."),
	INTERNAL_SERVER_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "COMMON500_1", "서버에 문제가 생겼어요. 잠시 후 다시 시도해 주세요.");

	private final HttpStatus httpStatus;
	private final String code;
	private final String message;

}
