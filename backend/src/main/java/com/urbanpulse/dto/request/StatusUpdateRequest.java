package com.urbanpulse.dto.request;

import com.urbanpulse.enums.IncidentStatus;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class StatusUpdateRequest {
    @NotNull
    private IncidentStatus status;
    private String notes;
}
