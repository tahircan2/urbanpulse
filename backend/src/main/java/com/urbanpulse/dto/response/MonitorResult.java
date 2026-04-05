package com.urbanpulse.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class MonitorResult {
    @JsonProperty("incident_id")
    private Long incidentId;
    private String action;
    private String notes;
    private boolean escalate;
}
