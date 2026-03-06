package com.urbanpulse.dto.request;

import com.urbanpulse.enums.UserRole;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class RegisterRequest {
    @NotBlank @Size(min = 2, max = 100)
    private String name;

    @Email @NotBlank
    private String email;

    @NotBlank @Size(min = 6, max = 50)
    private String password;

    private UserRole role = UserRole.CITIZEN;
    private String district;
}
