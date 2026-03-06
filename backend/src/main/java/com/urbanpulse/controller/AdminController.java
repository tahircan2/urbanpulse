package com.urbanpulse.controller;

import com.urbanpulse.dto.response.ApiResponse;
import com.urbanpulse.dto.response.UserResponse;
import com.urbanpulse.entity.User;
import com.urbanpulse.enums.UserRole;
import com.urbanpulse.exception.ResourceNotFoundException;
import com.urbanpulse.repository.IncidentRepository;
import com.urbanpulse.repository.AgentLogRepository;
import com.urbanpulse.repository.UserRepository;
import jakarta.validation.constraints.NotNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * Admin-only controller for user management and bulk data operations.
 * All endpoints require ADMIN role.
 */
@RestController
@RequestMapping("/admin")
@RequiredArgsConstructor
@PreAuthorize("hasRole('ADMIN')")
@Slf4j
public class AdminController {

    private final UserRepository userRepository;
    private final IncidentRepository incidentRepository;
    private final AgentLogRepository agentLogRepository;

    // ── Users ──────────────────────────────────────────────────────────────────

    @GetMapping("/users")
    @Transactional(readOnly = true)
    public ResponseEntity<ApiResponse<List<UserResponse>>> getAllUsers() {
        List<UserResponse> users = userRepository.findAll().stream()
                .map(this::toUserResponse)
                .toList();
        return ResponseEntity.ok(ApiResponse.ok(users));
    }

    @GetMapping("/users/{id}")
    @Transactional(readOnly = true)
    public ResponseEntity<ApiResponse<UserResponse>> getUser(@PathVariable Long id) {
        User user = userRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + id));
        return ResponseEntity.ok(ApiResponse.ok(toUserResponse(user)));
    }

    @PatchMapping("/users/{id}/role")
    @Transactional
    public ResponseEntity<ApiResponse<UserResponse>> updateRole(
            @PathVariable Long id,
            @RequestParam @NotNull UserRole role) {
        User user = userRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + id));
        UserRole prev = user.getRole();
        user.setRole(role);
        userRepository.save(user);
        log.info("Admin updated user {} role: {} -> {}", id, prev, role);
        return ResponseEntity.ok(ApiResponse.ok("Role updated", toUserResponse(user)));
    }

    @PatchMapping("/users/{id}/toggle")
    @Transactional
    public ResponseEntity<ApiResponse<UserResponse>> toggleEnabled(@PathVariable Long id) {
        User user = userRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + id));
        user.setEnabled(!user.isEnabled());
        userRepository.save(user);
        log.info("Admin toggled user {} enabled: {}", id, user.isEnabled());
        return ResponseEntity.ok(ApiResponse.ok(
                user.isEnabled() ? "User enabled" : "User disabled", toUserResponse(user)));
    }

    @DeleteMapping("/users/{id}")
    @Transactional
    public ResponseEntity<ApiResponse<String>> deleteUser(@PathVariable Long id) {
        if (!userRepository.existsById(id))
            throw new ResourceNotFoundException("User not found: " + id);
        userRepository.deleteById(id);
        log.info("Admin deleted user: {}", id);
        return ResponseEntity.ok(ApiResponse.ok("User deleted"));
    }

    // ── Agent Logs ─────────────────────────────────────────────────────────────

    @DeleteMapping("/agent-logs/{id}")
    @Transactional
    public ResponseEntity<ApiResponse<String>> deleteAgentLog(@PathVariable Long id) {
        if (!agentLogRepository.existsById(id))
            throw new ResourceNotFoundException("Agent log not found: " + id);
        agentLogRepository.deleteById(id);
        return ResponseEntity.ok(ApiResponse.ok("Agent log deleted"));
    }

    @DeleteMapping("/agent-logs/incident/{incidentId}")
    @Transactional
    public ResponseEntity<ApiResponse<String>> deleteLogsForIncident(@PathVariable Long incidentId) {
        agentLogRepository.deleteByIncidentId(incidentId);
        log.info("Admin deleted all agent logs for incident {}", incidentId);
        return ResponseEntity.ok(ApiResponse.ok("Agent logs deleted for incident " + incidentId));
    }

    // ── Helpers ────────────────────────────────────────────────────────────────

    private UserResponse toUserResponse(User u) {
        return UserResponse.builder()
                .id(u.getId())
                .name(u.getName())
                .email(u.getEmail())
                .role(u.getRole())
                .district(u.getDistrict())
                .enabled(u.isEnabled())
                .createdAt(u.getCreatedAt())
                .incidentCount(u.getIncidents() != null ? u.getIncidents().size() : 0L)
                .build();
    }
}
