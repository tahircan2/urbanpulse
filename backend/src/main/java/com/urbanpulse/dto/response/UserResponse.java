package com.urbanpulse.dto.response;

import com.urbanpulse.enums.UserRole;
import lombok.*;
import java.time.LocalDateTime;

@Data @Builder @NoArgsConstructor @AllArgsConstructor
public class UserResponse {
    private Long          id;
    private String        name;
    private String        email;
    private UserRole      role;
    private String        district;
    private boolean       enabled;
    private LocalDateTime createdAt;
    private long          incidentCount;
}
