package com.urbanpulse.entity;

import com.urbanpulse.enums.IncidentCategory;
import com.urbanpulse.enums.IncidentStatus;
import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "incidents", indexes = {
    @Index(name = "idx_incidents_status",     columnList = "status"),
    @Index(name = "idx_incidents_category",   columnList = "category"),
    @Index(name = "idx_incidents_priority",   columnList = "priority"),
    @Index(name = "idx_incidents_district",   columnList = "district"),
    // BUG FIX: Hibernate maps camelCase to snake_case in DDL.
    // columnList must use the actual DB column name, not the Java field name.
    @Index(name = "idx_incidents_created_at", columnList = "created_at"),
    @Index(name = "idx_incidents_agent",      columnList = "agent_processed")
})
@EntityListeners(AuditingEntityListener.class)
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class Incident {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank @Size(min = 5, max = 200)
    @Column(nullable = false, length = 200)
    private String title;

    @NotBlank @Size(min = 10, max = 2000)
    @Column(nullable = false, columnDefinition = "TEXT")
    private String description;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    private IncidentCategory category;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private IncidentStatus status;

    @Min(1) @Max(5)
    @Column(nullable = false)
    private int priority;

    @Column(nullable = false)
    private double latitude;

    @Column(nullable = false)
    private double longitude;

    @NotBlank
    @Column(nullable = false, length = 80)
    private String district;

    @Column(length = 500)
    private String photoUrl;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "reporter_id")
    private User reporter;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "department_id")
    private Department assignedDepartment;

    @Column(nullable = false)
    @Builder.Default
    private boolean agentProcessed = false;

    @Column(columnDefinition = "TEXT")
    private String agentNotes;

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(nullable = false)
    private LocalDateTime updatedAt;

    private LocalDateTime resolvedAt;

    @OneToMany(mappedBy = "incident", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<AgentLog> agentLogs;
}
