package com.urbanpulse.service;

import com.urbanpulse.dto.response.AgentLogResponse;
import com.urbanpulse.repository.AgentLogRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
public class AgentLogService {

    private final AgentLogRepository agentLogRepository;

    /**
     * FIX: Use findAllWithIncident() (JOIN FETCH) instead of
     * findAllByOrderByTimestampDesc() which caused N+1 queries.
     */
    @Transactional(readOnly = true)
    public Page<AgentLogResponse> getAll(int page, int size) {
        int clampedSize = Math.min(size, 100);
        Pageable pageable = PageRequest.of(page, clampedSize);
        return agentLogRepository.findAllWithIncident(pageable)
                .map(this::toResponse);
    }

    @Transactional(readOnly = true)
    public Page<AgentLogResponse> getWithNotifications(int page, int size) {
        int clampedSize = Math.min(size, 100);
        Pageable pageable = PageRequest.of(page, clampedSize);
        return agentLogRepository.findWithNotifications(pageable)
                .map(this::toResponse);
    }

    /**
     * FIX: Use findByIncidentIdWithIncident() (JOIN FETCH).
     */
    @Transactional(readOnly = true)
    public List<AgentLogResponse> getByIncident(Long incidentId) {
        return agentLogRepository.findByIncidentIdWithIncident(incidentId)
                .stream()
                .map(this::toResponse)
                .toList();
    }

    private AgentLogResponse toResponse(com.urbanpulse.entity.AgentLog log) {
        return AgentLogResponse.builder()
                .id(log.getId())
                .incidentId(log.getIncident().getId())
                .incidentTitle(log.getIncident().getTitle())
                .agentName(log.getAgentName())
                .action(log.getAction())
                .inputSummary(log.getInputSummary())
                .outputSummary(log.getOutputSummary())
                .confidence(log.getConfidence())
                .processingMs(log.getProcessingMs())
                .timestamp(log.getTimestamp())
                .success(log.isSuccess())
                .toolsCalled(log.getToolsCalled())
                .notificationsSent(log.getNotificationsSent())
                .build();
    }
}
