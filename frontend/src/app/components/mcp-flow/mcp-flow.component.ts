import {
  ChangeDetectionStrategy, Component, DestroyRef, OnInit,
  signal, computed, inject
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { JsonPipe, NgClass, UpperCasePipe, SlicePipe } from '@angular/common';
import { McpService } from '../../services/mcp.service';
import {
  MCPStatusResponse, MCPToolSchema, MCPCallRecord, MCPConnectionState,
  MCP_FLOW_STEPS, LAYER_META, MCP_TOOL_META, FlowStep, FlowStepId,
} from '../../models/mcp.model';

@Component({
  selector: 'app-mcp-flow',
  standalone: true,
  imports: [JsonPipe, NgClass, UpperCasePipe, SlicePipe],
  templateUrl: './mcp-flow.component.html',
  styleUrl: './mcp-flow.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class McpFlowComponent implements OnInit {
  private readonly mcpService = inject(McpService);
  private readonly destroyRef = inject(DestroyRef);

  // ── Data signals ──────────────────────────────────────────────────────────
  readonly status         = this.mcpService.status;
  readonly tools          = this.mcpService.tools;
  readonly history        = this.mcpService.history;
  readonly loading        = this.mcpService.loading;
  readonly error          = this.mcpService.error;
  readonly connectionState = this.mcpService.connectionState;

  // ── UI state ──────────────────────────────────────────────────────────────
  readonly flowSteps       = MCP_FLOW_STEPS;
  readonly layerMeta       = LAYER_META;
  readonly toolMeta        = MCP_TOOL_META;
  readonly activeStepIndex = signal(-1);
  readonly isAnimating     = signal(false);
  readonly animationPhase  = signal<'idle' | 'running' | 'complete'>('idle');
  readonly selectedTool    = signal<MCPToolSchema | null>(null);
  readonly selectedRecord  = signal<MCPCallRecord | null>(null);
  readonly activeSection   = signal<'overview' | 'tools' | 'history' | 'protocol'>('overview');

  // ── Computed ──────────────────────────────────────────────────────────────
  readonly isConnected = computed(() => this.connectionState() === 'connected');
  readonly uptimeFormatted = computed(() => {
    const s = this.status()?.connection?.uptime_seconds ?? 0;
    if (s < 60) return `${Math.round(s)}s`;
    if (s < 3600) return `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;
    return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
  });

  readonly layers = computed(() => {
    const groups: Record<string, FlowStep[]> = {};
    for (const step of this.flowSteps) {
      if (!groups[step.layer]) groups[step.layer] = [];
      groups[step.layer].push(step);
    }
    return groups;
  });

  readonly toolsList = computed(() => this.tools()?.tools ?? []);
  readonly historyRecords = computed(() => this.history()?.records ?? []);

  readonly protocolMessages = computed(() => {
    // Generate synthetic JSON-RPC 2.0 message examples based on real tool calls
    const records = this.historyRecords();
    if (records.length === 0) return this.getDefaultProtocolMessages();

    const latest = records[0];
    return [
      {
        direction: 'request' as const,
        label: 'tools/list',
        description: 'Client discovers available tools from server',
        json: JSON.stringify({
          jsonrpc: '2.0',
          method: 'tools/list',
          id: 1,
        }, null, 2),
      },
      {
        direction: 'response' as const,
        label: 'tools/list result',
        description: `Server responds with ${this.toolsList().length} discovered tools`,
        json: JSON.stringify({
          jsonrpc: '2.0',
          result: {
            tools: this.toolsList().map(t => ({
              name: t.name,
              description: t.description.slice(0, 60) + '…',
              inputSchema: { type: 'object', properties: '…' },
            }))
          },
          id: 1,
        }, null, 2),
      },
      {
        direction: 'request' as const,
        label: 'tools/call',
        description: `Invoke ${latest.tool_name} with arguments`,
        json: JSON.stringify({
          jsonrpc: '2.0',
          method: 'tools/call',
          params: {
            name: latest.tool_name,
            arguments: latest.arguments,
          },
          id: 2,
        }, null, 2),
      },
      {
        direction: 'response' as const,
        label: 'tools/call result',
        description: `Tool returns in ${latest.duration_ms}ms`,
        json: JSON.stringify({
          jsonrpc: '2.0',
          result: {
            content: [{
              type: 'text',
              text: latest.result_preview.slice(0, 120) + '…',
            }],
            isError: !latest.success,
          },
          id: 2,
        }, null, 2),
      },
    ];
  });

  private animationTimer: any;

  // ── Lifecycle ─────────────────────────────────────────────────────────────

  ngOnInit(): void {
    this.mcpService.loadAll();

    this.destroyRef.onDestroy(() => {
      if (this.animationTimer) clearInterval(this.animationTimer);
    });
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  refreshData(): void {
    this.mcpService.loadAll();
  }

  reconnect(): void {
    this.mcpService.reconnect().pipe(
      takeUntilDestroyed(this.destroyRef)
    ).subscribe();
  }

  startFlowAnimation(): void {
    if (this.isAnimating()) return;

    this.isAnimating.set(true);
    this.animationPhase.set('running');
    this.activeStepIndex.set(0);

    let i = 0;
    this.animationTimer = setInterval(() => {
      i++;
      if (i >= this.flowSteps.length) {
        this.animationPhase.set('complete');
        this.isAnimating.set(false);
        clearInterval(this.animationTimer);
        // Auto-reset after 3s
        setTimeout(() => {
          this.animationPhase.set('idle');
          this.activeStepIndex.set(-1);
        }, 3000);
        return;
      }
      this.activeStepIndex.set(i);
    }, 800);
  }

  selectTool(tool: MCPToolSchema): void {
    this.selectedTool.set(
      this.selectedTool()?.name === tool.name ? null : tool
    );
  }

  selectRecord(record: MCPCallRecord): void {
    this.selectedRecord.set(
      this.selectedRecord()?.timestamp === record.timestamp ? null : record
    );
  }

  setSection(section: 'overview' | 'tools' | 'history' | 'protocol'): void {
    this.activeSection.set(section);
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  objectKeys(obj: any): string[] {
    return obj ? Object.keys(obj) : [];
  }

  getToolMeta(name: string) {
    return MCP_TOOL_META[name] ?? { icon: 'fa-wrench', label: name, color: '#8896A9', description: '' };
  }

  getLayerLabel(layer: string): string {
    return LAYER_META[layer]?.label ?? layer.toUpperCase();
  }

  getLayerColor(layer: string): string {
    return LAYER_META[layer]?.color ?? '#8896A9';
  }

  getLayerDesc(layer: string): string {
    return LAYER_META[layer]?.description ?? '';
  }

  getConnectionIcon(): string {
    switch (this.connectionState()) {
      case 'connected': return 'fa-circle-check';
      case 'connecting': return 'fa-spinner fa-spin';
      case 'disconnected': return 'fa-circle-xmark';
      case 'error': return 'fa-triangle-exclamation';
      default: return 'fa-circle-question';
    }
  }

  getConnectionColor(): string {
    switch (this.connectionState()) {
      case 'connected': return 'var(--success)';
      case 'connecting': return 'var(--warning)';
      case 'disconnected': return 'var(--text-muted)';
      case 'error': return 'var(--danger)';
      default: return 'var(--text-muted)';
    }
  }

  formatTime(iso: string): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  timeAgo(iso: string): string {
    if (!iso) return '—';
    const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
    if (s < 60)    return `${s}s ago`;
    if (s < 3600)  return `${Math.floor(s/60)}m ago`;
    if (s < 86400) return `${Math.floor(s/3600)}h ago`;
    return new Date(iso).toLocaleDateString();
  }

  private getDefaultProtocolMessages() {
    return [
      {
        direction: 'request' as const,
        label: 'initialize',
        description: 'Client initiates MCP handshake with server',
        json: JSON.stringify({
          jsonrpc: '2.0',
          method: 'initialize',
          params: {
            protocolVersion: '2025-11-25',
            clientInfo: { name: 'urbanpulse-client', version: '3.1.0' },
            capabilities: {},
          },
          id: 0,
        }, null, 2),
      },
      {
        direction: 'response' as const,
        label: 'initialize result',
        description: 'Server acknowledges and reports its capabilities',
        json: JSON.stringify({
          jsonrpc: '2.0',
          result: {
            protocolVersion: '2025-11-25',
            serverInfo: { name: 'urbanpulse-tools', version: '3.0.0' },
            capabilities: { tools: { listChanged: true } },
          },
          id: 0,
        }, null, 2),
      },
      {
        direction: 'request' as const,
        label: 'tools/list',
        description: 'Client discovers available tools',
        json: JSON.stringify({ jsonrpc: '2.0', method: 'tools/list', id: 1 }, null, 2),
      },
      {
        direction: 'response' as const,
        label: 'tools/list result',
        description: 'Server responds with 6 city-intelligence tools',
        json: JSON.stringify({
          jsonrpc: '2.0',
          result: {
            tools: [
              { name: 'weather_context', description: 'Current weather at coordinates…' },
              { name: 'district_risk_profile', description: 'District risk data…' },
              { name: 'time_risk_context', description: 'Time-based risk factors…' },
              { name: 'nearby_infrastructure', description: 'Critical infrastructure…' },
              { name: 'reverse_geocode', description: 'Reverse geocoding…' },
              { name: 'similar_incidents', description: 'Pattern detection…' },
            ]
          },
          id: 1,
        }, null, 2),
      },
    ];
  }
}
