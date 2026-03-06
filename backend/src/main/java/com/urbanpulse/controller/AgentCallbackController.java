package com.urbanpulse.controller;

import com.urbanpulse.dto.request.AgentResultRequest;
import com.urbanpulse.dto.request.AgentResultRequest.AgentLogEntry;
import com.urbanpulse.dto.request.BatchAgentLogRequest;
import com.urbanpulse.dto.response.ApiResponse;
import com.urbanpulse.service.AiPipelineService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Internal endpoint — only callable by the Python AI service.
 * Protected by X-Internal-Secret header (InternalSecretFilter).
 */
@RestController
@RequiredArgsConstructor
@Slf4j
public class AgentCallbackController {

    private final AiPipelineService aiPipelineService;

    /**
     * Called by Python after the full pipeline completes for an incident.
     */
    @PostMapping("/incidents/{id}/agent-result")
    public ResponseEntity<ApiResponse<String>> agentResult(
            @PathVariable Long id,
            @Valid @RequestBody AgentResultRequest req) {

        log.info("Agent result received for incident {}: cat={}, pri={}",
                id, req.getCategory(), req.getPriority());
        aiPipelineService.applyAgentResult(id, req);
        return ResponseEntity.ok(ApiResponse.ok("Agent result applied"));
    }

    /**
     * Called by Python to bulk-insert agent log entries.
     *
     * FIX: Previously extracted incidentId from only the first element, then passed
     * all
     * logs to batchSaveLogs() assuming they all belong to the same incident —
     * silently
     * incorrect if the batch contained logs from different incidents.
     *
     * Now: group logs by incidentId and call batchSaveLogs() once per group.
     * Each group is saved in its own transaction.
     */
    @PostMapping("/agent-logs/batch")
    public ResponseEntity<ApiResponse<String>> batchLogs(
            @Valid @RequestBody BatchAgentLogRequest req) {

        List<AgentLogEntry> logs = req.getLogs();
        if (logs == null || logs.isEmpty()) {
            return ResponseEntity.ok(ApiResponse.ok("No logs to save"));
        }

        // Group by incidentId so each incident's logs are persisted correctly
        Map<Long, List<AgentLogEntry>> byIncident = logs.stream()
                .collect(Collectors.groupingBy(AgentLogEntry::getIncidentId));

        byIncident.forEach((incidentId, entries) -> {
            log.info("Saving {} agent logs for incident {}", entries.size(), incidentId);
            aiPipelineService.batchSaveLogs(incidentId, entries);
        });

        return ResponseEntity.ok(ApiResponse.ok("Logs saved: " + logs.size()));
    }
}
