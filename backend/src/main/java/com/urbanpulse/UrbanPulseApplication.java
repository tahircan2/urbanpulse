package com.urbanpulse;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

// @EnableAsync lives in AppConfig (alongside the executor bean it configures)
// @EnableScheduling lives here — one clear place
@SpringBootApplication
@EnableScheduling
public class UrbanPulseApplication {
    public static void main(String[] args) {
        SpringApplication.run(UrbanPulseApplication.class, args);
    }
}
