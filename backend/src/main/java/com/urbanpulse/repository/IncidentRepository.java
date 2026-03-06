package com.urbanpulse.repository;

import com.urbanpulse.entity.Incident;
import com.urbanpulse.enums.IncidentCategory;
import com.urbanpulse.enums.IncidentStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface IncidentRepository extends JpaRepository<Incident, Long> {

        Page<Incident> findByStatus(IncidentStatus status, Pageable pageable);

        Page<Incident> findByCategory(IncidentCategory category, Pageable pageable);

        Page<Incident> findByStatusAndCategory(IncidentStatus status, IncidentCategory category, Pageable pageable);

        List<Incident> findByStatusIn(List<IncidentStatus> statuses);

        long countByStatus(IncidentStatus status);

        long countByPriorityGreaterThanEqual(int priority);

        long countByAgentProcessedTrue();

        @Query("SELECT i FROM Incident i WHERE " +
                        "(:status IS NULL OR i.status = :status) AND " +
                        "(:category IS NULL OR i.category = :category) AND " +
                        "(:district IS NULL OR i.district = :district) AND " +
                        "(:agentProcessed IS NULL OR i.agentProcessed = :agentProcessed)")
        Page<Incident> findWithFilters(
                        @Param("status") IncidentStatus status,
                        @Param("category") IncidentCategory category,
                        @Param("district") String district,
                        @Param("agentProcessed") Boolean agentProcessed,
                        Pageable pageable);

        @Query("SELECT i FROM Incident i WHERE i.agentProcessed = false ORDER BY i.createdAt ASC")
        List<Incident> findUnprocessedByAgent();

        @Query("SELECT i FROM Incident i WHERE i.status = :status AND i.priority >= 4")
        List<Incident> findActiveCritical(@Param("status") IncidentStatus status);

        default List<Incident> findActiveCritical() {
                return findActiveCritical(IncidentStatus.IN_PROGRESS);
        }

        /**
         * FIX: Single-query dashboard stats to replace 7 separate count() calls.
         * Returns Object[] with indices:
         * [0] total, [1] pending, [2] inProgress, [3] resolved,
         * [4] closed, [5] critical (priority >= 4), [6] aiProcessed
         *
         * Reduces 7 round-trips to 1.
         */
        @Query("SELECT " +
                        "COUNT(i), " +
                        "SUM(CASE WHEN i.status = 'PENDING'     THEN 1 ELSE 0 END), " +
                        "SUM(CASE WHEN i.status = 'IN_PROGRESS' THEN 1 ELSE 0 END), " +
                        "SUM(CASE WHEN i.status = 'RESOLVED'    THEN 1 ELSE 0 END), " +
                        "SUM(CASE WHEN i.status = 'CLOSED'      THEN 1 ELSE 0 END), " +
                        "SUM(CASE WHEN i.priority >= 4           THEN 1 ELSE 0 END), " +
                        "SUM(CASE WHEN i.agentProcessed = true   THEN 1 ELSE 0 END) " +
                        "FROM Incident i")
        List<Object[]> fetchDashboardCounts();
}
