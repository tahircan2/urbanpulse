import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap, catchError, of, timer, switchMap } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  MCPStatusResponse,
  MCPToolsResponse,
  MCPHistoryResponse,
  MCPConnectionState,
} from '../models/mcp.model';

/**
 * MCP Service — communicates with the AI service's MCP Dashboard API.
 *
 * Endpoints consumed:
 *   GET  /api/mcp/status   → MCPStatusResponse
 *   GET  /api/mcp/tools    → MCPToolsResponse
 *   GET  /api/mcp/history  → MCPHistoryResponse
 *   POST /api/mcp/reconnect
 *
 * Note: These endpoints are on the AI service (port 8000), not the Spring Boot
 * backend. In production, requests are proxied through the Spring Boot gateway.
 * For local dev, we use the proxy.conf.json target.
 */
@Injectable({ providedIn: 'root' })
export class McpService {
  private readonly http = inject(HttpClient);

  /** AI service base URL — MCP endpoints live here, NOT on Spring Boot */
  private readonly aiBaseUrl = this.resolveAiUrl();

  // ── Reactive state ────────────────────────────────────────────────────────
  readonly status      = signal<MCPStatusResponse | null>(null);
  readonly tools       = signal<MCPToolsResponse | null>(null);
  readonly history     = signal<MCPHistoryResponse | null>(null);
  readonly loading     = signal(false);
  readonly error       = signal<string | null>(null);
  readonly connectionState = signal<MCPConnectionState>('disconnected');

  // ── API Methods ───────────────────────────────────────────────────────────

  /** Fetch full MCP status including connection, tools count, and telemetry */
  getStatus(): Observable<MCPStatusResponse> {
    this.loading.set(true);
    return this.http.get<MCPStatusResponse>(`${this.aiBaseUrl}/mcp/status`).pipe(
      tap(res => {
        this.status.set(res);
        this.connectionState.set(res.connection?.state ?? 'disconnected');
        this.loading.set(false);
        this.error.set(null);
      }),
      catchError(err => {
        this.loading.set(false);
        this.error.set(err.message || 'Failed to fetch MCP status');
        this.connectionState.set('error');
        return of({
          success: false,
          timestamp: new Date().toISOString(),
          mcp: { protocol: 'MCP', transport: 'stdio', sdk: 'N/A', spec_version: 'N/A' },
          connection: { state: 'error' as MCPConnectionState, uptime_seconds: 0 },
          tools: { discovered_count: 0, tool_names: [] },
          telemetry: { total_calls: 0, failed_calls: 0, success_rate_pct: 0, avg_latency_ms: 0 },
          error: err.message,
        } as MCPStatusResponse);
      })
    );
  }

  /** Fetch discovered MCP tool definitions with schemas */
  getTools(): Observable<MCPToolsResponse> {
    return this.http.get<MCPToolsResponse>(`${this.aiBaseUrl}/mcp/tools`).pipe(
      tap(res => this.tools.set(res)),
      catchError(err => {
        this.error.set('Failed to fetch MCP tools');
        return of({ success: false, timestamp: '', mode: 'unknown', tools_count: 0, tools: [] } as MCPToolsResponse);
      })
    );
  }

  /** Fetch recent MCP tool call history */
  getHistory(limit: number = 20): Observable<MCPHistoryResponse> {
    return this.http.get<MCPHistoryResponse>(`${this.aiBaseUrl}/mcp/history`, {
      params: { limit: String(limit) },
    }).pipe(
      tap(res => this.history.set(res)),
      catchError(err => {
        this.error.set('Failed to fetch MCP history');
        return of({ success: false, timestamp: '', total_in_buffer: 0, returned: 0, records: [] } as MCPHistoryResponse);
      })
    );
  }

  /** Force reconnect to MCP server */
  reconnect(): Observable<any> {
    this.connectionState.set('connecting');
    return this.http.post(`${this.aiBaseUrl}/mcp/reconnect`, {}).pipe(
      tap(() => {
        this.connectionState.set('connected');
        // Refresh all data after reconnect
        this.getStatus().subscribe();
        this.getTools().subscribe();
        this.getHistory().subscribe();
      }),
      catchError(err => {
        this.connectionState.set('error');
        this.error.set('Reconnect failed: ' + (err.error?.detail || err.message));
        return of({ success: false, error: err.message });
      })
    );
  }

  /** Load all MCP data in parallel */
  loadAll(): void {
    this.getStatus().subscribe();
    this.getTools().subscribe();
    this.getHistory().subscribe();
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  private resolveAiUrl(): string {
    // MCP endpoints are on the AI service, accessed through the Spring Boot proxy
    // In dev with proxy.conf.json, /ai-api/* proxies to http://localhost:8000/api/*
    // In production, the Spring Boot backend proxies /api/ai/* to the AI service
    return 'http://localhost:8000/api';
  }
}
