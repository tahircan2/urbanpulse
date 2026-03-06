package com.urbanpulse.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data @Builder @NoArgsConstructor @AllArgsConstructor
public class DashboardStatsResponse {
    private long total;
    private long pending;
    private long inProgress;
    private long resolved;
    private long closed;
    private long critical;
    private long aiProcessed;
    private long agentLogsTotal;
    // FIX: Use double for percentage precision (was long - integer division lost precision)
    private double agentSuccessRate;
}
