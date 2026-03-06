package com.urbanpulse.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.urbanpulse.enums.AgentAction;
import com.urbanpulse.enums.AgentName;
import com.urbanpulse.enums.IncidentCategory;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import lombok.Data;

import java.util.List;

/**
 * Received from the Python AI service at POST /incidents/{id}/agent-result
 *
 * FIX: Python sends snake_case JSON. Added @JsonProperty for every field that
 * doesn't match camelCase so deserialization is correct without changing the
 * global Jackson config (which would break the Angular frontend).
 */
@Data
public class AgentResultRequest {

    @NotNull(message = "category is required")
    private IncidentCategory category;

    @Min(value = 1, message = "priority must be between 1 and 5")
    @Max(value = 5, message = "priority must be between 1 and 5")
    private int priority;

    @JsonProperty("assigned_department")
    @Size(max = 200, message = "assignedDepartment must be under 200 characters")
    private String assignedDepartment;

    @JsonProperty("sla_hours")
    @Min(value = 1, message = "slaHours must be at least 1")
    @Max(value = 720, message = "slaHours must not exceed 720")
    private int slaHours;

    @JsonProperty("agent_notes")
    @Size(max = 500, message = "agentNotes must be under 500 characters")
    private String agentNotes;

    @JsonProperty("agent_processed")
    private boolean agentProcessed = true;

    @Valid
    private List<AgentLogEntry> logs;

    @Data
    public static class AgentLogEntry {

        @JsonProperty("incident_id")
        @NotNull(message = "incidentId is required in log entry")
        private Long incidentId;

        @JsonProperty("incident_title")
        private String incidentTitle;

        @JsonProperty("agent_name")
        @NotNull(message = "agentName is required")
        private AgentName agentName;

        @NotNull(message = "action is required")
        private AgentAction action;

        @JsonProperty("input_summary")
        @Size(max = 1000, message = "inputSummary must be under 1000 characters")
        private String inputSummary;

        @JsonProperty("output_summary")
        @Size(max = 1000, message = "outputSummary must be under 1000 characters")
        private String outputSummary;

        private Double confidence;

        @JsonProperty("processing_ms")
        @Min(value = 0, message = "processingMs must not be negative")
        private long processingMs;

        private boolean success;

        /**
         * FIX: Python sends snake_case "tools_called" as a List<String>.
         * Use @JsonProperty to map correctly. Removed conflicting manual getters.
         */
        @JsonProperty("tools_called")
        @Size(max = 10)
        private List<String> toolsCalledList;

        @JsonProperty("notifications_sent")
        @Size(max = 10)
        private List<String> notificationsSentList;

        // Clean accessors used by AiPipelineService.saveLogs()
        public List<String> getToolsCalled() {
            return toolsCalledList != null ? toolsCalledList : List.of();
        }

        public List<String> getNotificationsSent() {
            return notificationsSentList != null ? notificationsSentList : List.of();
        }
    }
}
