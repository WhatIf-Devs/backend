package com.whatif.global.health;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.whatif.global.response.ApiResponse;
import com.whatif.global.response.CommonSuccessCode;

/** 배포 확인과 모니터링용. DB 절전을 깨우지 않도록 DB는 확인하지 않는다. */
@RestController
@RequestMapping("/api/v1/health")
public class HealthController {

	@GetMapping
	public ResponseEntity<ApiResponse<HealthResponse>> health() {
		return ApiResponse.success(CommonSuccessCode.HEALTH_OK, HealthResponse.up());
	}

}
