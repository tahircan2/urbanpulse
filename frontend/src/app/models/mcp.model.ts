/**
 * MCP (Model Context Protocol) data models for the frontend visualization.
 *
 * These types map to the AI service's MCP status/tools/history API responses.
 */

// ── MCP Connection ──────────────────────────────────────────────────────────

export type MCPConnectionState = 'connected' | 'connecting' | 'disconnected' | 'error';

export interface MCPStatusResponse {
  success: boolean;
  timestamp: string;
  mcp: {
    protocol: string;
    transport: string;
    sdk: string;
    spec_version: string;
    state?: string;  // fallback state on error
  };
  connection: {
    state: MCPConnectionState;
    uptime_seconds: number;
  };
  tools: {
    discovered_count: number;
    tool_names: string[];
  };
  telemetry: {
    total_calls: number;
    failed_calls: number;
    success_rate_pct: number;
    avg_latency_ms: number;
  };
  error?: string;
}

// ── MCP Tools ───────────────────────────────────────────────────────────────

export interface MCPToolSchema {
  name: string;
  description: string;
  input_schema: {
    type?: string;
    properties?: Record<string, { type: string; description?: string; default?: any }>;
    required?: string[];
  };
}

export interface MCPToolsResponse {
  success: boolean;
  timestamp: string;
  mode: string;
  tools_count: number;
  tools: MCPToolSchema[];
}

// ── MCP History ─────────────────────────────────────────────────────────────

export interface MCPCallRecord {
  tool_name: string;
  arguments: Record<string, any>;
  result_preview: string;
  duration_ms: number;
  success: boolean;
  error: string | null;
  timestamp: string;
}

export interface MCPHistoryResponse {
  success: boolean;
  timestamp: string;
  total_in_buffer: number;
  returned: number;
  records: MCPCallRecord[];
}

// ── Flow Visualization ──────────────────────────────────────────────────────

export type FlowStepId =
  | 'frontend'
  | 'backend'
  | 'ai_service'
  | 'langgraph'
  | 'mcp_client'
  | 'stdio_transport'
  | 'mcp_server'
  | 'tool_execution'
  | 'llm_decision'
  | 'response';

export interface FlowStep {
  id: FlowStepId;
  label: string;
  sublabel: string;
  icon: string;
  color: string;
  layer: 'host' | 'client' | 'transport' | 'server';
}

export const MCP_FLOW_STEPS: FlowStep[] = [
  { id: 'frontend',        label: 'Angular Frontend',      sublabel: 'Incident Form Submit',          icon: 'fa-desktop',           color: '#00D4FF', layer: 'host' },
  { id: 'backend',         label: 'Spring Boot Backend',   sublabel: 'REST API → /api/incidents',     icon: 'fa-server',            color: '#FF6B35', layer: 'host' },
  { id: 'ai_service',      label: 'FastAPI AI Service',    sublabel: 'POST /api/langgraph/process',   icon: 'fa-brain',             color: '#A78BFA', layer: 'host' },
  { id: 'langgraph',       label: 'LangGraph Pipeline',    sublabel: 'StateGraph → Nodes',            icon: 'fa-sitemap',           color: '#00E5A0', layer: 'client' },
  { id: 'mcp_client',      label: 'MCP Client Session',    sublabel: 'ClientSession (JSON-RPC 2.0)',  icon: 'fa-plug',              color: '#22D3EE', layer: 'client' },
  { id: 'stdio_transport', label: 'stdio Transport',       sublabel: 'stdin/stdout Pipe',             icon: 'fa-exchange-alt',      color: '#FFB020', layer: 'transport' },
  { id: 'mcp_server',      label: 'MCP Server (FastMCP)',  sublabel: 'urbanpulse-tools v3.0',         icon: 'fa-shield-halved',     color: '#FF4D6D', layer: 'server' },
  { id: 'tool_execution',  label: 'Tool Execution',        sublabel: 'weather / risk / infra / …',    icon: 'fa-wrench',            color: '#84CC16', layer: 'server' },
];

export const LAYER_META: Record<string, { label: string; color: string; description: string }> = {
  host:      { label: 'HOST PROCESS',      color: '#00D4FF', description: 'Application layer — where your frontend, backend and AI service live' },
  client:    { label: 'MCP CLIENT',        color: '#22D3EE', description: 'Manages MCP sessions, tool discovery, and invocation via JSON-RPC 2.0' },
  transport: { label: 'TRANSPORT LAYER',   color: '#FFB020', description: 'stdio pipes connecting client ↔ server as child process' },
  server:    { label: 'MCP SERVER',        color: '#FF4D6D', description: 'Exposes UrbanPulse tools as MCP-compliant endpoints' },
};

/**
 * Tool metadata used in the MCP flow visualization.
 * Maps MCP server tool names to display metadata.
 */
export const MCP_TOOL_META: Record<string, { icon: string; label: string; color: string; description: string }> = {
  weather_context:       { icon: 'fa-cloud-rain',          label: 'Weather Context',         color: '#00D4FF', description: 'Real-time weather via Open-Meteo API' },
  district_risk_profile: { icon: 'fa-map-location-dot',    label: 'District Risk Profile',   color: '#A78BFA', description: 'Static Antalya district risk data' },
  time_risk_context:     { icon: 'fa-clock',               label: 'Time Risk Context',       color: '#FFB020', description: 'Time-based risk factors (rush hour, holidays)' },
  nearby_infrastructure: { icon: 'fa-hospital',            label: 'Nearby Infrastructure',   color: '#FF4D6D', description: 'Critical infrastructure via Overpass/OSM' },
  reverse_geocode:       { icon: 'fa-location-crosshairs', label: 'Reverse Geocode',         color: '#FF6B35', description: 'Reverse geocoding via Nominatim' },
  similar_incidents:     { icon: 'fa-chart-line',          label: 'Similar Incidents',       color: '#00E5A0', description: 'Pattern detection from backend DB' },
};
