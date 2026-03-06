package com.urbanpulse.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.client.SimpleClientHttpRequestFactory;

import java.util.concurrent.Executor;

@Configuration
@EnableAsync
// BUG FIX: @EnableScheduling removed — already declared in UrbanPulseApplication
public class AppConfig {

    /**
     * RestTemplate for calling the Python AI service.
     * BUG FIX: Added connect + read timeouts.
     * Without timeouts, a slow/down AI service hangs the async thread indefinitely.
     */
    @Bean
    public RestTemplate restTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5_000);   // 5s to establish connection
        factory.setReadTimeout(30_000);     // 30s to read response (pipeline can be slow)
        return new RestTemplate(factory);
    }

    /**
     * Dedicated thread pool for @Async AI pipeline calls.
     * Isolates AI work from Tomcat request threads.
     */
    @Bean(name = "taskExecutor")
    public Executor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(4);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(50);
        executor.setThreadNamePrefix("ai-pipeline-");
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(30);
        executor.initialize();
        return executor;
    }
}
