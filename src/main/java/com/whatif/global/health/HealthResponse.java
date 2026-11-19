package com.whatif.global.health;

public record HealthResponse(String status) {

	public static HealthResponse up() {
		return new HealthResponse("UP");
	}

}
