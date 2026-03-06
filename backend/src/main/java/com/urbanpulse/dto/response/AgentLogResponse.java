package com.urbanpulse.dto.response;

import com.urbanpulse.enums.AgentAction;
import com.urbanpulse.enums.AgentName;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data @Builder @NoArgsConstructor @AllArgsConstructor
public class AgentLogResponse {
    private Long id;
    private Long incidentId;
    private String incidentTitle;
    private AgentName agentName;
    private AgentAction action;
    private String inputSummary;
    private String outputSummary;
    private Double confidence;
    private long processingMs;
    private LocalDateTime timestamp;
    private boolean success;
    private String toolsCalled;
    private String notificationsSent;
}
