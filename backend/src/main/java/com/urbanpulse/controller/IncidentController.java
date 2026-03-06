package com.urbanpulse.controller;

import com.urbanpulse.dto.request.IncidentRequest;
import com.urbanpulse.dto.request.StatusUpdateRequest;
import com.urbanpulse.dto.response.ApiResponse;
import com.urbanpulse.dto.response.IncidentResponse;
import com.urbanpulse.enums.IncidentCategory;
import com.urbanpulse.enums.IncidentStatus;
import com.urbanpulse.service.IncidentService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/incidents")
@RequiredArgsConstructor
public class IncidentController {

    private final IncidentService incidentService;

    @PostMapping
    public ResponseEntity<ApiResponse<IncidentResponse>> create(
            @Valid @RequestBody IncidentRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.ok("Incident submitted successfully", incidentService.createIncident(req)));
    }

    @GetMapping
    public ResponseEntity<ApiResponse<Page<IncidentResponse>>> getAll(
            @RequestParam(required = false) IncidentStatus status,
            @RequestParam(required = false) IncidentCategory category,
            @RequestParam(required = false) String district,
            @RequestParam(required = false) Boolean agentProcessed,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(ApiResponse.ok(
                incidentService.getIncidents(status, category, district, agentProcessed, page, size)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<IncidentResponse>> getById(@PathVariable Long id) {
        return ResponseEntity.ok(ApiResponse.ok(incidentService.getById(id)));
    }

    @PatchMapping("/{id}/status")
    @PreAuthorize("hasAnyRole('STAFF', 'ADMIN')")
    public ResponseEntity<ApiResponse<IncidentResponse>> updateStatus(
            @PathVariable Long id,
            @Valid @RequestBody StatusUpdateRequest req) {
        return ResponseEntity.ok(ApiResponse.ok("Status updated", incidentService.updateStatus(id, req)));
    }

    @GetMapping("/critical")
    @PreAuthorize("hasAnyRole('STAFF', 'ADMIN')")
    public ResponseEntity<ApiResponse<List<IncidentResponse>>> getCritical() {
        return ResponseEntity.ok(ApiResponse.ok(incidentService.getActiveCritical()));
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<String>> delete(@PathVariable Long id) {
        incidentService.deleteIncident(id);
        return ResponseEntity.ok(ApiResponse.ok("Incident deleted"));
    }
}
