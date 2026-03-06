package com.urbanpulse.service;

import com.urbanpulse.dto.response.DashboardStatsResponse;
import com.urbanpulse.repository.AgentLogRepository;
import com.urbanpulse.repository.IncidentRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class DashboardService {

    private final IncidentRepository incidentRepository;
    private final AgentLogRepository agentLogRepository;

    /**
     * FIX: Replaced 7 separate COUNT queries with a single JPQL projection.
     * Original code made 7 individual DB round-trips; now it's 2 (incidents +
     * logs).
     *
     * fetchDashboardCounts() returns Object[] with SUM(CASE WHEN ...) aggregates.
     * toLong() helper handles null (no rows exist) safely.
     */
    @Transactional(readOnly = true)
    public DashboardStatsResponse getStats() {
        java.util.List<Object[]> results = incidentRepository.fetchDashboardCounts();
        if (results == null || results.isEmpty()) {
            return DashboardStatsResponse.builder().build();
        }
        Object[] counts = results.get(0);

        long total = toLong(counts[0]);
        long pending = toLong(counts[1]);
        long inProgress = toLong(counts[2]);
        long resolved = toLong(counts[3]);
        long closed = toLong(counts[4]);
        long critical = toLong(counts[5]);
        long aiProcessed = toLong(counts[6]);

        // Still 2 separate queries for agent logs (different table)
        long logsTotal = agentLogRepository.count();
        long logsSuccess = agentLogRepository.countBySuccessTrue();

        double successRate = logsTotal > 0
                ? Math.round((double) logsSuccess / logsTotal * 10000.0) / 100.0
                : 0.0;

        return DashboardStatsResponse.builder()
                .total(total)
                .pending(pending)
                .inProgress(inProgress)
                .resolved(resolved)
                .closed(closed)
                .critical(critical)
                .aiProcessed(aiProcessed)
                .agentLogsTotal(logsTotal)
                .agentSuccessRate(successRate)
                .build();
    }

    /** Safely convert Number|null from JPQL aggregation to long. */
    private long toLong(Object value) {
        if (value == null)
            return 0L;
        return ((Number) value).longValue();
    }
}
