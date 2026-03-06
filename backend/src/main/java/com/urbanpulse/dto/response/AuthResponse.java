package com.urbanpulse.dto.response;

import com.urbanpulse.enums.UserRole;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data @NoArgsConstructor @AllArgsConstructor @Builder
public class AuthResponse {
    private String token;
    // FIX: @Builder.Default to ensure "Bearer" is set when using builder pattern
    @Builder.Default
    private String type = "Bearer";
    private Long userId;
    private String name;
    private String email;
    private UserRole role;
}
