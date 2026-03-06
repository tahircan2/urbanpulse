package com.urbanpulse.repository;

import com.urbanpulse.entity.Department;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface DepartmentRepository extends JpaRepository<Department, Long> {
    Optional<Department> findByName(String name);

    @Query("SELECT d FROM Department d WHERE d.currentLoad < d.capacity ORDER BY d.currentLoad ASC")
    List<Department> findAvailableDepartments();
}
