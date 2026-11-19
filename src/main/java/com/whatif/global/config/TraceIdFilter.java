package com.whatif.global.config;

import java.io.IOException;
import java.util.UUID;

import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

/**
 * 요청마다 추적 번호를 만들어 로그와 응답 헤더에 넣는다.
 * 클라이언트가 보낸 값은 로그 위조를 막기 위해 쓰지 않는다. 시큐리티 에러 응답에도 붙도록 가장 먼저 실행한다.
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class TraceIdFilter extends OncePerRequestFilter {

	public static final String TRACE_ID_HEADER = "X-Trace-Id";
	private static final String TRACE_ID_KEY = "traceId";

	@Override
	protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
		throws ServletException, IOException {
		String traceId = UUID.randomUUID().toString().replace("-", "").substring(0, 16);
		MDC.put(TRACE_ID_KEY, traceId);
		response.setHeader(TRACE_ID_HEADER, traceId);
		try {
			filterChain.doFilter(request, response);
		} finally {
			MDC.remove(TRACE_ID_KEY);
		}
	}

}
