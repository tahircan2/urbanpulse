package com.urbanpulse.controller;

import com.urbanpulse.dto.response.AgentLogResponse;
import com.urbanpulse.dto.response.ApiResponse;
import com.urbanpulse.service.AgentLogService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/agent-logs")
@RequiredArgsConstructor
@PreAuthorize("isAuthenticated()")
public class AgentLogController {

    private final AgentLogService agentLogService;

    @GetMapping
    public ResponseEntity<ApiResponse<Page<AgentLogResponse>>> getAll(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {
        return ResponseEntity.ok(ApiResponse.ok(agentLogService.getAll(page, size)));
    }

    @GetMapping("/notifications")
    public ResponseEntity<ApiResponse<Page<AgentLogResponse>>> getNotifications(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(ApiResponse.ok(agentLogService.getWithNotifications(page, size)));
    }

    @GetMapping("/incident/{incidentId}")
    public ResponseEntity<ApiResponse<List<AgentLogResponse>>> getByIncident(
            @PathVariable Long incidentId) {
        return ResponseEntity.ok(ApiResponse.ok(agentLogService.getByIncident(incidentId)));
    }
}
