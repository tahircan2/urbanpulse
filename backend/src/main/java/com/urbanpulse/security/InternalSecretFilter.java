package com.urbanpulse.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/**
 * Validates the X-Internal-Secret header on AI callback routes.
 * Uses constant-time comparison to prevent timing attacks.
 *
 * Applied only to:
 *   POST /incidents/ * /agent-result
 *   POST /agent-logs/batch
 */
@Component
@Slf4j
public class InternalSecretFilter extends OncePerRequestFilter {

    @Value("${ai.service.secret:change_this_in_production_please}")
    private String internalSecret;

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI();
        // Only intercept the two AI-callback routes
        return !(path.contains("/agent-result") || path.endsWith("/agent-logs/batch"));
    }

    @Override
    protected void doFilterInternal(
            @NonNull HttpServletRequest request,
            @NonNull HttpServletResponse response,
            @NonNull FilterChain chain) throws ServletException, IOException {

        String provided = request.getHeader("X-Internal-Secret");

        if (provided == null || !constantTimeEquals(provided, internalSecret)) {
            log.warn("Rejected AI callback — invalid or missing X-Internal-Secret from {}",
                request.getRemoteAddr());
            response.setStatus(HttpServletResponse.SC_FORBIDDEN);
            // FIX: Set Content-Type so the client can parse the JSON error body
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write("{\"success\":false,\"message\":\"Forbidden\"}");
            return;
        }

        chain.doFilter(request, response);
    }

    /** Constant-time string comparison (prevents timing side-channel). */
    private static boolean constantTimeEquals(String a, String b) {
        byte[] aBytes = a.getBytes(StandardCharsets.UTF_8);
        byte[] bBytes = b.getBytes(StandardCharsets.UTF_8);
        return MessageDigest.isEqual(aBytes, bBytes);
    }
}
