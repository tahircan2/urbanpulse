package com.urbanpulse.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "departments")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Department {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 100)
    private String name;

    @Column(length = 60)
    private String type;

    @Builder.Default
    @Column(nullable = false)
    private int capacity = 10;

    @Builder.Default
    @Column(nullable = false)
    private int currentLoad = 0;

    @Column(length = 200)
    private String contactEmail;
}
