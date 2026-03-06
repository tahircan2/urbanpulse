package com.urbanpulse.dto.request;

import com.urbanpulse.enums.IncidentCategory;
import jakarta.validation.constraints.*;
import lombok.Data;

@Data
public class IncidentRequest {

    @NotBlank @Size(min = 5, max = 200)
    private String title;

    @NotBlank @Size(min = 10, max = 2000)
    private String description;

    @NotNull
    private IncidentCategory category;

    @Min(1) @Max(5)
    private int priority = 3;

    @NotNull
    private Double latitude;

    @NotNull
    private Double longitude;

    @NotBlank
    private String district;

    private String photoUrl;
}
