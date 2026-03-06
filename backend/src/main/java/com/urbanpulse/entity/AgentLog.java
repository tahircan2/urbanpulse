package com.urbanpulse.entity;

import com.urbanpulse.enums.AgentAction;
import com.urbanpulse.enums.AgentName;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Table(name = "agent_logs", indexes = {
    @Index(name = "idx_agent_logs_incident",  columnList = "incident_id"),
    // BUG FIX: Hibernate maps agentName → agent_name in DDL.
    // Using the actual snake_case column name so the index is actually created.
    @Index(name = "idx_agent_logs_agent",     columnList = "agent_name"),
    @Index(name = "idx_agent_logs_timestamp", columnList = "timestamp")
})
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class AgentLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "incident_id", nullable = false)
    private Incident incident;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private AgentName agentName;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    private AgentAction action;

    @Column(columnDefinition = "TEXT")
    private String inputSummary;

    @Column(columnDefinition = "TEXT")
    private String outputSummary;

    private Double confidence;

    @Column(nullable = false)
    private long processingMs;

    @Column(nullable = false)
    private LocalDateTime timestamp;

    @Column(nullable = false)
    @Builder.Default
    private boolean success = true;

    @Column(length = 500)
    private String toolsCalled;

    @Column(length = 300)
    private String notificationsSent;

    @PrePersist
    public void prePersist() {
        if (this.timestamp == null) {
            this.timestamp = LocalDateTime.now();
        }
    }
}
