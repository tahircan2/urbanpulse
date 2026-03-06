package com.urbanpulse.dto.request;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.List;

/**
 * Received from the Python AI service at POST /agent-logs/batch
 */
@Data
public class BatchAgentLogRequest {

    @NotNull @Valid
    private List<AgentResultRequest.AgentLogEntry> logs;
}
