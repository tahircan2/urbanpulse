package com.urbanpulse;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.data.web.config.EnableSpringDataWebSupport;

// @EnableAsync lives in AppConfig (alongside the executor bean it configures)
// @EnableScheduling lives here — one clear place
@SpringBootApplication
@EnableScheduling
@EnableSpringDataWebSupport(pageSerializationMode = EnableSpringDataWebSupport.PageSerializationMode.VIA_DTO)
public class UrbanPulseApplication {
    public static void main(String[] args) {
        SpringApplication.run(UrbanPulseApplication.class, args);
    }
}
