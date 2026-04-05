package com.urbanpulse.service;

import com.urbanpulse.dto.request.AgentResultRequest;
import com.urbanpulse.dto.request.AgentResultRequest.AgentLogEntry;
import com.urbanpulse.dto.response.IncidentResponse;
import com.urbanpulse.entity.AgentLog;

import com.urbanpulse.entity.Department;
import com.urbanpulse.entity.Incident;
import com.urbanpulse.enums.IncidentStatus;
import com.urbanpulse.exception.ResourceNotFoundException;
import com.urbanpulse.repository.AgentLogRepository;
import com.urbanpulse.repository.DepartmentRepository;
import com.urbanpulse.repository.IncidentRepository;
import com.urbanpulse.websocket.WebSocketEventPublisher;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.scheduling.annotation.Async;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class AiPipelineService {

    private final IncidentRepository incidentRepository;
    private final AgentLogRepository agentLogRepository;
    private final DepartmentRepository departmentRepository;
    private final WebSocketEventPublisher wsPublisher;
    private final RestTemplate restTemplate;

    @Value("${ai.service.url:http://localhost:8000/api}")
    private String aiServiceUrl;

    @Value("${ai.service.secret:change_this_in_production_please}")
    private String internalSecret;

    // ── 1. Trigger pipeline (called async after incident creation) ────────────

    /**
     * FIX: @Transactional added so that lazy-loaded associations (reporter)
     * are accessible within the async thread's own transaction.
     * Without it: LazyInitializationException when accessing
     * incident.getReporter().
     */
    @Async("taskExecutor")
    @Transactional(readOnly = true)
    public void triggerPipeline(Long incidentId) {
        Incident incident = incidentRepository.findById(incidentId).orElse(null);
        if (incident == null) {
            log.warn("triggerPipeline: incident {} not found", incidentId);
            return;
        }

        log.info("Triggering AI pipeline for incident {}", incidentId);

        // FIX: Map.of() only supports up to 10 key-value pairs.
        // With 12+ entries this causes a compile error. Use HashMap instead.
        Map<String, Object> incidentPayload = new HashMap<>();
        incidentPayload.put("id", incident.getId());
        incidentPayload.put("title", incident.getTitle());
        incidentPayload.put("description", incident.getDescription());
        incidentPayload.put("category", incident.getCategory().name());
        incidentPayload.put("status", incident.getStatus().name());
        incidentPayload.put("priority", incident.getPriority());
        incidentPayload.put("latitude", incident.getLatitude());
        incidentPayload.put("longitude", incident.getLongitude());
        incidentPayload.put("district", incident.getDistrict());
        incidentPayload.put("neighbourhood", incident.getNeighbourhood());
        incidentPayload.put("street", incident.getStreet());
        // FIX: reporter is LAZY — safe to access here because we're @Transactional
        incidentPayload.put("reporter_name", incident.getReporter() != null
                ? incident.getReporter().getName()
                : "Anonymous");
        // BUG FIX: reporter_email was missing — Planner agent needs it to send
        // confirmation email
        incidentPayload.put("reporter_email", incident.getReporter() != null
                ? incident.getReporter().getEmail()
                : null);
        incidentPayload.put("created_at", incident.getCreatedAt().toString());
        incidentPayload.put("agent_processed", false);

        Map<String, Object> body = new HashMap<>();
        body.put("incident", incidentPayload);

        try {
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, buildHeaders());
            ResponseEntity<String> response = restTemplate.postForEntity(
                    aiServiceUrl + "/pipeline/process", entity, String.class);
            if (response.getStatusCode().is2xxSuccessful()) {
                log.info("AI pipeline triggered for incident {}", incidentId);
            } else {
                log.warn("AI pipeline returned {} for incident {}", response.getStatusCode(), incidentId);
            }
        } catch (Exception e) {
            // Non-fatal: incident is already saved, AI is best-effort
            log.error("AI pipeline trigger failed for incident {}: {}", incidentId, e.getMessage());
        }
    }

    // ── 2. Apply agent result (callback from Python) ──────────────────────────

    @Transactional
    public void applyAgentResult(Long incidentId, AgentResultRequest req) {
        Incident incident = incidentRepository.findById(incidentId)
                .orElseThrow(() -> new ResourceNotFoundException("Incident not found: " + incidentId));

        if (incident.getStatus() == IncidentStatus.CLOSED || incident.getStatus() == IncidentStatus.RESOLVED) {
            log.info("Incident {} is already {}, ignoring agent result", incidentId, incident.getStatus());
            return;
        }

        if (!req.isSuccess()) {
            incident.setAgentProcessed(false);
            incident.setAgentNotes(req.getAgentNotes());
            incidentRepository.save(incident);
            log.error("AI processing failed for incident {}: {}", incidentId, req.getError());
            wsPublisher.publishAgentActivity("AI processing failed for Incident #" + incidentId);
            return;
        }

        incident.setCategory(req.getCategory());
        incident.setPriority(req.getPriority());
        incident.setAgentNotes(req.getAgentNotes());
        incident.setAgentProcessed(true);

        if (req.getAssignedDepartment() != null && !req.getAssignedDepartment().isBlank()) {
            Department dept = departmentRepository
                    .findByName(req.getAssignedDepartment().trim())
                    .orElseGet(() -> departmentRepository.save(
                            Department.builder()
                                    .name(req.getAssignedDepartment().trim())
                                    .type("MUNICIPAL")
                                    .capacity(20)
                                    .currentLoad(0)
                                    .build()));
            incident.setAssignedDepartment(dept);
        }

        incidentRepository.save(incident);

        // NOTE: Logs are NOT saved here. Python sends them separately via
        // POST /agent-logs/batch to avoid double insertion.
        // applyAgentResult only updates the incident record itself.

        try {
            wsPublisher.publishAgentActivity(
                    "Incident #" + incidentId + " processed — " +
                            req.getCategory().name() + " P" + req.getPriority());

            // Push exact updated status/details to the UI so it Auto-Updates
            wsPublisher.publishStatusUpdate(toResponse(incident));
        } catch (Exception e) {
            log.warn("WebSocket notification failed: {}", e.getMessage());
        }

        log.info("Agent result applied to incident {}: cat={}, pri={}, dept={}",
                incidentId, req.getCategory(), req.getPriority(), req.getAssignedDepartment());
    }

    private IncidentResponse toResponse(Incident i) {
        return IncidentResponse.builder()
                .id(i.getId())
                .title(i.getTitle())
                .description(i.getDescription())
                .category(i.getCategory())
                .status(i.getStatus())
                .priority(i.getPriority())
                .latitude(i.getLatitude())
                .longitude(i.getLongitude())
                .district(i.getDistrict())
                .neighbourhood(i.getNeighbourhood())
                .street(i.getStreet())
                .photoUrl(i.getPhotoUrl())
                .reporterName(i.getReporter() != null ? i.getReporter().getName() : "Anonymous")
                .assignedDepartment(i.getAssignedDepartment() != null
                        ? i.getAssignedDepartment().getName()
                        : null)
                .agentProcessed(i.isAgentProcessed())
                .agentNotes(i.getAgentNotes())
                .createdAt(i.getCreatedAt())
                .resolvedAt(i.getResolvedAt())
                .build();
    }

    // ── 3. Batch save logs (separate callback from Python) ────────────────────

    @Transactional
    public void batchSaveLogs(Long incidentId, List<AgentLogEntry> entries) {
        Incident incident = incidentRepository.findById(incidentId)
                .orElseThrow(() -> new ResourceNotFoundException("Incident not found: " + incidentId));

        saveLogs(incident, entries);
        log.info("Saved {} agent logs for incident {}", entries.size(), incidentId);

        try {
            // Notify UI so 'AI Pipeline' and 'Raw Log' tabs refresh immediately
            wsPublisher.publishAgentActivity("New agent logs stored for Incident #" + incidentId);
        } catch (Exception e) {
            log.warn("WebSocket notification failed during log save: {}", e.getMessage());
        }
    }
    // ── Helpers ───────────────────────────────────────────────────────────────

    private void saveLogs(Incident incident, List<AgentLogEntry> entries) {
        List<AgentLog> logs = entries.stream().map(entry -> {
            // Join list fields from Python to comma-separated strings
            String toolsCalled = (entry.getToolsCalled() != null && !entry.getToolsCalled().isEmpty())
                    ? String.join(",", entry.getToolsCalled())
                    : null;
            String notifSent = (entry.getNotificationsSent() != null && !entry.getNotificationsSent().isEmpty())
                    ? String.join(",", entry.getNotificationsSent())
                    : null;
            return AgentLog.builder()
                    .incident(incident)
                    .agentName(entry.getAgentName())
                    .action(entry.getAction())
                    .inputSummary(entry.getInputSummary())
                    .outputSummary(entry.getOutputSummary())
                    .confidence(entry.getConfidence())
                    .processingMs(entry.getProcessingMs())
                    .success(entry.isSuccess())
                    .toolsCalled(toolsCalled)
                    .notificationsSent(notifSent)
                    .timestamp(LocalDateTime.now())
                    .build();
        }).toList();
        agentLogRepository.saveAll(logs);
    }

    private HttpHeaders buildHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("X-Internal-Secret", internalSecret);
        return headers;
    }
}
