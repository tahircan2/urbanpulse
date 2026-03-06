export type AgentName = 'CLASSIFIER' | 'PLANNER' | 'MONITOR';
export type AgentAction =
  | 'CLASSIFY'
  | 'ASSIGN_PRIORITY'
  | 'ROUTE_TO_DEPARTMENT'
  | 'SLA_CHECK'
  | 'ESCALATE'
  | 'GENERATE_REPORT';

export interface AgentLog {
  id: number;
  incidentId: number;
  incidentTitle: string;
  agentName: AgentName;
  action: AgentAction;
  inputSummary: string;
  outputSummary: string;
  confidence?: number;
  processingMs: number;
  timestamp: string;
  success: boolean;
  toolsCalled?: string;        // comma-separated tool names
  notificationsSent?: string;  // comma-separated channel:status
}

export const AGENT_LABELS: Record<AgentName, string> = {
  CLASSIFIER: 'Classifier',
  PLANNER:    'Planner',
  MONITOR:    'Monitor',
};

export const AGENT_COLORS: Record<AgentName, string> = {
  CLASSIFIER: '#00D4FF',
  PLANNER:    '#FF6B35',
  MONITOR:    '#00E5A0',
};

export const AGENT_BADGE_CLASSES: Record<AgentName, string> = {
  CLASSIFIER: 'badge-cyan',
  PLANNER:    'badge-orange',
  MONITOR:    'badge-green',
};

export const TOOL_META: Record<string, { icon: string; label: string; color: string }> = {
  get_weather_context:                 { icon: 'fa-cloud-rain',          label: 'Weather',        color: '#00D4FF' },
  find_nearby_critical_infrastructure: { icon: 'fa-hospital',            label: 'Infrastructure', color: '#FF4D6D' },
  get_district_risk_profile:           { icon: 'fa-map-location-dot',    label: 'District Risk',  color: '#A78BFA' },
  get_time_risk_context:               { icon: 'fa-clock',               label: 'Time Context',   color: '#FFB020' },
  check_similar_incidents:             { icon: 'fa-chart-line',          label: 'Patterns',       color: '#00E5A0' },
  get_location_context:                { icon: 'fa-location-crosshairs', label: 'Location',       color: '#FF6B35' },
  send_pushover_notification:          { icon: 'fa-bell',                label: 'Pushover',       color: '#FF6B35' },
  send_reporter_email:                 { icon: 'fa-envelope',            label: 'Email',          color: '#00E5A0' },
};

