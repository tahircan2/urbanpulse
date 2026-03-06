package com.urbanpulse.dto.response;

import com.urbanpulse.enums.IncidentCategory;
import com.urbanpulse.enums.IncidentStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data @Builder @NoArgsConstructor @AllArgsConstructor
public class IncidentResponse {
    private Long id;
    private String title;
    private String description;
    private IncidentCategory category;
    private IncidentStatus status;
    private int priority;
    private double latitude;
    private double longitude;
    private String district;
    private String photoUrl;
    private String reporterName;
    private String assignedDepartment;
    private boolean agentProcessed;
    private String agentNotes;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private LocalDateTime resolvedAt;
}
