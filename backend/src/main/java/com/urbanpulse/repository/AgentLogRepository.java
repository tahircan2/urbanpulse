package com.urbanpulse.repository;

import com.urbanpulse.entity.AgentLog;
import com.urbanpulse.enums.AgentName;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AgentLogRepository extends JpaRepository<AgentLog, Long> {

    /**
     * FIX: N+1 query problem.
     * The original findAllByOrderByTimestampDesc() triggered a separate query
     * for EACH log to load its incident (lazy). 100 logs = 101 queries.
     *
     * JOIN FETCH loads incident data in a single query.
     * CountQuery is required when using JOIN FETCH with pagination.
     */
    @Query(value = "SELECT l FROM AgentLog l JOIN FETCH l.incident ORDER BY l.timestamp DESC", countQuery = "SELECT COUNT(l) FROM AgentLog l")
    Page<AgentLog> findAllWithIncident(Pageable pageable);

    /**
     * FIX: Same N+1 fix for per-incident query.
     */
    @Query("SELECT l FROM AgentLog l JOIN FETCH l.incident WHERE l.incident.id = :incidentId ORDER BY l.timestamp DESC")
    List<AgentLog> findByIncidentIdWithIncident(@Param("incidentId") Long incidentId);

    @Query(value = "SELECT l FROM AgentLog l JOIN FETCH l.incident WHERE l.notificationsSent IS NOT NULL AND l.notificationsSent != '' ORDER BY l.timestamp DESC", countQuery = "SELECT COUNT(l) FROM AgentLog l WHERE l.notificationsSent IS NOT NULL AND l.notificationsSent != ''")
    Page<AgentLog> findWithNotifications(Pageable pageable);

    List<AgentLog> findByAgentName(AgentName agentName);

    long countBySuccessTrue();

    @Query("DELETE FROM AgentLog l WHERE l.incident.id = :incidentId")
    @org.springframework.data.jpa.repository.Modifying
    void deleteByIncidentId(@Param("incidentId") Long incidentId);
}
