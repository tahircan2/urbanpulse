package com.urbanpulse.service;

import com.urbanpulse.dto.request.IncidentRequest;
import com.urbanpulse.dto.request.StatusUpdateRequest;
import com.urbanpulse.dto.response.IncidentResponse;
import com.urbanpulse.entity.Incident;
import com.urbanpulse.entity.User;
import com.urbanpulse.enums.IncidentCategory;
import com.urbanpulse.enums.IncidentStatus;
import com.urbanpulse.exception.ResourceNotFoundException;
import com.urbanpulse.repository.IncidentRepository;
import com.urbanpulse.repository.UserRepository;
import com.urbanpulse.websocket.WebSocketEventPublisher;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
public class IncidentService {

    private final IncidentRepository incidentRepository;
    private final UserRepository userRepository;
    private final WebSocketEventPublisher wsPublisher;
    private final AiPipelineService aiPipelineService;

    @Transactional
    public IncidentResponse createIncident(IncidentRequest req) {
        String email = SecurityContextHolder.getContext().getAuthentication().getName();
        User reporter = userRepository.findByEmail(email)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + email));

        Incident incident = Incident.builder()
                .title(req.getTitle().trim())
                .description(req.getDescription().trim())
                .category(req.getCategory())
                .status(IncidentStatus.PENDING)
                .priority(req.getPriority())
                .latitude(req.getLatitude())
                .longitude(req.getLongitude())
                .district(req.getDistrict().trim())
                .photoUrl(req.getPhotoUrl())
                .reporter(reporter)
                .agentProcessed(false)
                .build();

        incident = incidentRepository.save(incident);
        log.info("Incident created: id={}, category={}, district={}",
                incident.getId(), incident.getCategory(), incident.getDistrict());

        IncidentResponse response = toResponse(incident);
        wsPublisher.publishNewIncident(response);

        // Trigger AI pipeline asynchronously, but ONLY after transaction commits
        final Long incidentId = incident.getId();
        if (org.springframework.transaction.support.TransactionSynchronizationManager.isSynchronizationActive()) {
            org.springframework.transaction.support.TransactionSynchronizationManager.registerSynchronization(
                    new org.springframework.transaction.support.TransactionSynchronization() {
                        @Override
                        public void afterCommit() {
                            aiPipelineService.triggerPipeline(incidentId);
                        }
                    });
        } else {
            aiPipelineService.triggerPipeline(incidentId);
        }

        return response;
    }

    @Transactional(readOnly = true)
    public Page<IncidentResponse> getIncidents(IncidentStatus status, IncidentCategory category,
            String district, Boolean agentProcessed, int page, int size) {
        // Clamp page size to prevent abuse
        int clampedSize = Math.min(size, 100);
        Pageable pageable = PageRequest.of(page, clampedSize, Sort.by("createdAt").descending());
        return incidentRepository
                .findWithFilters(status, category, district, agentProcessed, pageable)
                .map(this::toResponse);
    }

    @Transactional(readOnly = true)
    public IncidentResponse getById(Long id) {
        return toResponse(incidentRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Incident not found: " + id)));
    }

    @Transactional
    public IncidentResponse updateStatus(Long id, StatusUpdateRequest req) {
        Incident incident = incidentRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Incident not found: " + id));

        IncidentStatus previous = incident.getStatus();
        incident.setStatus(req.getStatus());

        if (req.getStatus() == IncidentStatus.RESOLVED || req.getStatus() == IncidentStatus.CLOSED) {
            incident.setResolvedAt(LocalDateTime.now());
        }
        if (req.getNotes() != null && !req.getNotes().isBlank()) {
            incident.setAgentNotes(req.getNotes().trim());
        }

        incident = incidentRepository.save(incident);
        log.info("Incident {} status changed: {} -> {}", id, previous, req.getStatus());

        IncidentResponse response = toResponse(incident);
        wsPublisher.publishStatusUpdate(response);
        return response;
    }

    @Transactional(readOnly = true)
    public List<IncidentResponse> getActiveCritical() {
        return incidentRepository.findActiveCritical().stream()
                .map(this::toResponse)
                .toList();
    }

    @Transactional
    public void deleteIncident(Long id) {
        if (!incidentRepository.existsById(id))
            throw new ResourceNotFoundException("Incident not found: " + id);
        incidentRepository.deleteById(id);
        log.info("Incident deleted: id={}", id);
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
                .photoUrl(i.getPhotoUrl())
                .reporterName(i.getReporter() != null ? i.getReporter().getName() : "Anonymous")
                .assignedDepartment(i.getAssignedDepartment() != null
                        ? i.getAssignedDepartment().getName()
                        : null)
                .agentProcessed(i.isAgentProcessed())
                .agentNotes(i.getAgentNotes())
                .createdAt(i.getCreatedAt())
                .updatedAt(i.getUpdatedAt())
                .resolvedAt(i.getResolvedAt())
                .build();
    }
}
