package com.whatif.support;

import org.springframework.boot.test.context.TestComponent;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.whatif.global.exception.BusinessException;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

/** 전역 예외 처리 검증용 컨트롤러. 컴포넌트 스캔에서 빠지고 IntegrationTestSupport가 직접 등록한다. */
@TestComponent
@RestController
@RequestMapping("/api/v1/test")
public class TestExceptionController {

	@GetMapping("/business")
	public void business() {
		throw new BusinessException(TestErrorCode.CONFLICT);
	}

	@PostMapping("/validation")
	public void validation(@Valid @RequestBody ValidationRequest request) {
	}

	@GetMapping("/unexpected")
	public void unexpected() {
		throw new IllegalStateException("예상하지 못한 오류");
	}

	// 선언 순서: name → amount
	public record ValidationRequest(
		@NotBlank(message = "TEST400_1") String name,
		@NotNull(message = "TEST400_2") Integer amount
	) {
	}

}
