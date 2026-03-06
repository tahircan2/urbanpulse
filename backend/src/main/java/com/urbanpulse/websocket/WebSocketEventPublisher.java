package com.urbanpulse.websocket;

import com.urbanpulse.dto.response.IncidentResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class WebSocketEventPublisher {

    private final SimpMessagingTemplate messagingTemplate;

    public void publishNewIncident(IncidentResponse incident) {
        messagingTemplate.convertAndSend("/topic/incidents/new", incident);
    }

    public void publishStatusUpdate(IncidentResponse incident) {
        messagingTemplate.convertAndSend("/topic/incidents/update", incident);
    }

    public void publishAgentActivity(String message) {
        messagingTemplate.convertAndSend("/topic/agents/activity", message);
    }
}
