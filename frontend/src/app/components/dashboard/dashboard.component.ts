import {
  ChangeDetectionStrategy, Component, DestroyRef, OnInit,
  signal, computed, inject
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { SlicePipe, TitleCasePipe } from '@angular/common';
import { IncidentService } from '../../services/incident.service';
import { WebSocketService } from '../../services/websocket.service';
import {
  Incident, IncidentStatus, IncidentCategory,
  CATEGORY_LABELS, CATEGORY_ICONS, STATUS_LABELS, STATUS_CLASSES, PRIORITY_CLASSES,
} from '../../models/incident.model';
import { AgentLog, AGENT_LABELS, AGENT_BADGE_CLASSES, TOOL_META } from '../../models/agent-log.model';
import { AdminUser, DashboardStats } from '../../models/api.model';
import { AuthService } from '../../services/auth.service';

type Tab = 'incidents' | 'pipeline' | 'notifications' | 'admin';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [FormsModule, RouterLink, SlicePipe, TitleCasePipe],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardComponent implements OnInit {
  private readonly incidentService = inject(IncidentService);
  private readonly ws              = inject(WebSocketService);
  private readonly destroyRef      = inject(DestroyRef);
  readonly authService             = inject(AuthService);

  readonly CATEGORY_LABELS  = CATEGORY_LABELS;
  readonly CATEGORY_ICONS   = CATEGORY_ICONS;
  readonly STATUS_LABELS    = STATUS_LABELS;
  readonly STATUS_CLASSES   = STATUS_CLASSES;
  readonly PRIORITY_CLASSES = PRIORITY_CLASSES;
  readonly AGENT_LABELS     = AGENT_LABELS;
  readonly AGENT_BADGE_CLASSES = AGENT_BADGE_CLASSES;
  readonly TOOL_META        = TOOL_META;

  readonly allIncidents = signal<Incident[]>([]);
  
  // Isolated Server-Side Paginated Signals
  readonly statsLogs    = signal<AgentLog[]>([]); // specifically for dashboard metrics
  readonly adminUsers   = signal<AdminUser[]>([]);
  readonly stats        = signal<DashboardStats>({
    total: 0, pending: 0, inProgress: 0, resolved: 0, closed: 0,
    critical: 0, aiProcessed: 0, agentLogsTotal: 0, agentSuccessRate: 0,
  });

  readonly filterStatus   = signal<IncidentStatus | 'ALL'>('ALL');
  readonly filterCategory = signal<IncidentCategory | 'ALL'>('ALL');
  readonly searchQuery    = signal('');
  readonly activeTab      = signal<Tab>('incidents');
  readonly loading        = signal(true);
  readonly actionMsg      = signal('');
  readonly actionError    = signal('');
  
  readonly undoIncidentId      = signal<number | null>(null);
  readonly undoIncidentSeconds = signal(10);
  readonly undoUserId          = signal<number | null>(null);
  readonly undoUserSeconds     = signal(10);

  // Pagination states
  readonly pipelinePage   = signal(1);
  readonly pipelineTotalPages = signal(1);
  readonly pipelineIncidents = signal<{ id: number, title: string, logs: AgentLog[], timestamp: string }[]>([]);

  readonly rawLogsPage = signal(1);
  readonly rawLogsTotalPages = signal(1);
  readonly rawAgentLogs = signal<AgentLog[]>([]);

  readonly notifPage = signal(1);
  readonly notifTotalPages = signal(1);
  readonly notifTotalElements = signal(0);
  readonly notificationLogs = signal<AgentLog[]>([]);

  readonly statuses:   IncidentStatus[]   = ['PENDING','IN_PROGRESS','RESOLVED','CLOSED'];
  readonly categories: IncidentCategory[] = [
    'TRAFFIC_ACCIDENT','ROAD_DAMAGE','FLOODING','POWER_OUTAGE',
    'FIRE_HAZARD','VANDALISM','NOISE_COMPLAINT','OTHER',
  ];
  readonly roles = ['CITIZEN', 'STAFF', 'ADMIN'];

  readonly isAdmin = computed(() => this.authService.currentUser()?.role === 'ADMIN');

  readonly filteredIncidents = computed(() => {
    let list = this.allIncidents();
    const status   = this.filterStatus();
    const category = this.filterCategory();
    const q        = this.searchQuery().toLowerCase().trim();
    if (status   !== 'ALL') list = list.filter(i => i.status   === status);
    if (category !== 'ALL') list = list.filter(i => i.category === category);
    if (q) list = list.filter(i =>
      i.title.toLowerCase().includes(q) || i.district.toLowerCase().includes(q) || String(i.id).includes(q)
    );
    return list;
  });

  readonly toolUsageStats = computed(() => {
    const counts: Record<string, number> = {};
    for (const log of this.statsLogs()) {
      if (log.toolsCalled) {
        for (const t of log.toolsCalled.split(',')) {
          const name = t.trim();
          if (name) counts[name] = (counts[name] || 0) + 1;
        }
      }
    }
    return Object.entries(counts).sort((a, b) => b[1] - a[1])
      .map(([name, count]) => ({ name, count, meta: TOOL_META[name] }));
  });

  readonly notificationEvents = computed(() => {
    const events: { time: string; channel: string; status: string; incidentId: number; title: string }[] = [];
    for (const log of this.notificationLogs()) {
      if (log.notificationsSent) {
        for (const n of log.notificationsSent.split(',')) {
          const [channel, status] = n.trim().split(':');
          if (channel && status) events.push({ time: log.timestamp, channel, status, incidentId: log.incidentId, title: log.incidentTitle });
        }
      }
    }
    return events.sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime()).slice(0, 30);
  });

  readonly notifStats = computed(() => {
    const evs = this.notificationEvents();
    return {
      total:   evs.length,
      sent:    evs.filter(e => e.status === 'sent').length,
      failed:  evs.filter(e => e.status === 'failed').length,
      skipped: evs.filter(e => e.status === 'skipped').length,
      emails:  evs.filter(e => e.channel === 'email').length,
      pushes:  evs.filter(e => e.channel === 'pushover').length,
    };
  });

  readonly avgProcessingMs = computed(() => {
    const logs = this.statsLogs();
    if (!logs.length) return 0;
    return Math.round(logs.reduce((s, l) => s + l.processingMs, 0) / logs.length);
  });

  readonly successRate = computed(() => {
    const logs = this.statsLogs();
    if (!logs.length) return 100;
    return Math.round(logs.filter(l => l.success).length / logs.length * 100);
  });

  ngOnInit(): void {
    this.ws.connect();
    this.loadData();
    this.ws.newIncident$.pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(inc => this.allIncidents.update(list => [inc, ...list]));

    // Listen to real-time AI and Admin updates
    this.ws.updatedIncident$.pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(inc => {
        this.allIncidents.update(list => list.map(i => i.id === inc.id ? inc : i));
        // Refresh logs and stats dynamically
        this.incidentService.getAgentLogs(0, 100).subscribe(r => {
          if (r.success) this.statsLogs.set(r.data.content);
        });
        if (this.rawLogsPage() === 1) this.loadRawLogs();
        if (this.pipelinePage() === 1) this.loadPipelineLogs();
        if (this.notifPage() === 1) this.loadNotifications();

        this.incidentService.getDashboardStats().subscribe(r => {
          if (r.success) this.stats.set(r.data);
        });
      });

    this.destroyRef.onDestroy(() => {
      if (this.deleteTimeout) clearTimeout(this.deleteTimeout);
      if (this.deleteInterval) clearInterval(this.deleteInterval);
      if (this.userDeleteTimeout) clearTimeout(this.userDeleteTimeout);
      if (this.userDeleteInterval) clearInterval(this.userDeleteInterval);
    });
  }

  loadData(): void {
    this.loading.set(true);
    let loaded = 0;
    const done = () => { if (++loaded >= 3) this.loading.set(false); };

    this.incidentService.getIncidents({ size: 100 }).pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({ next: r => { if (r.success) this.allIncidents.set(r.data.content); done(); }, error: done });
    this.incidentService.getAgentLogs(0, 100).pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({ next: r => { if (r.success) this.statsLogs.set(r.data.content); done(); }, error: done });
    this.incidentService.getDashboardStats().pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({ next: r => { if (r.success) this.stats.set(r.data); done(); }, error: done });

    this.loadRawLogs();
    this.loadPipelineLogs();
    this.loadNotifications();

    if (this.isAdmin()) {
      this.incidentService.getAdminUsers().pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({ next: r => { if (r.success) this.adminUsers.set(r.data); }, error: () => {} });
    }
  }

  setFilter(type: 'status' | 'category', val: string): void {
    if (type === 'status')   this.filterStatus.set(val as any);
    if (type === 'category') this.filterCategory.set(val as any);
  }

  // ── Incident actions ──────────────────────────────────────────────────────
  updateStatus(id: number, status: IncidentStatus): void {
    this.incidentService.updateStatus(id, status).subscribe({
      next: r => {
        if (r.success) {
          this.allIncidents.update(list => list.map(i => i.id === r.data.id ? r.data : i));
          this.showMsg(`Incident #${id} status → ${STATUS_LABELS[status]}`);
        }
      },
      error: () => this.showError('Status update failed'),
    });
  }

  private deleteTimeout: any;
  private deleteInterval: any;
  private pendingDeletes = new Map<number, { item: Incident }>();

  commitDelete(id: number) {
    if (this.deleteTimeout && this.undoIncidentId() === id) {
       clearTimeout(this.deleteTimeout);
       clearInterval(this.deleteInterval);
       this.undoIncidentId.set(null);
    }
    const pending = this.pendingDeletes.get(id);
    if (pending) {
       this.incidentService.deleteIncident(id).subscribe({
          error: () => this.allIncidents.update(l => [pending.item, ...l].sort((a, b) => b.id - a.id))
       });
       this.pendingDeletes.delete(id);
    }
  }

  deleteIncident(id: number, title: string): void {
    const item = this.allIncidents().find(i => i.id === id);
    if (!item) return;

    if (this.undoIncidentId() !== null) {
       this.commitDelete(this.undoIncidentId()!);
    }

    this.allIncidents.update(list => list.filter(i => i.id !== id));
    this.undoIncidentId.set(id);
    this.undoIncidentSeconds.set(10);
    this.pendingDeletes.set(id, { item });

    if (this.deleteInterval) clearInterval(this.deleteInterval);
    this.deleteInterval = setInterval(() => {
      this.undoIncidentSeconds.update(s => s - 1);
    }, 1000);

    this.deleteTimeout = setTimeout(() => {
      this.commitDelete(id);
    }, 10000);
  }

  undoDelete() {
    const id = this.undoIncidentId();
    if (id !== null) {
      clearTimeout(this.deleteTimeout);
      clearInterval(this.deleteInterval);
      const pending = this.pendingDeletes.get(id);
      if (pending) {
         this.allIncidents.update(l => [pending.item, ...l].sort((a,b)=>b.id - a.id));
         this.pendingDeletes.delete(id);
      }
      this.undoIncidentId.set(null);
      this.showMsg(`Restored incident #${id}`);
    }
  }

  // ── Pagination Loaders ────────────────────────────────────────────────────────
  loadRawLogs() {
    this.incidentService.getAgentLogs(this.rawLogsPage() - 1, 10).subscribe(r => {
      if (r.success) {
        this.rawAgentLogs.set(r.data.content);
        this.rawLogsTotalPages.set(r.data.totalPages || 1);
      }
    });
  }

  setRawLogsPage(p: number) {
    if (p >= 1 && p <= this.rawLogsTotalPages()) {
      this.rawLogsPage.set(p);
      this.loadRawLogs();
    }
  }

  loadNotifications() {
    this.incidentService.getNotificationLogs(this.notifPage() - 1, 10).subscribe(r => {
      if (r.success) {
        this.notificationLogs.set(r.data.content);
        this.notifTotalPages.set(r.data.totalPages || 1);
        this.notifTotalElements.set(r.data.totalElements || 0);
      }
    });
  }

  setNotifPage(p: number) {
    if (p >= 1 && p <= this.notifTotalPages()) {
      this.notifPage.set(p);
      this.loadNotifications();
    }
  }

  loadPipelineLogs() {
    this.incidentService.getIncidents({ agentProcessed: true, page: this.pipelinePage() - 1, size: 3 }).subscribe(r => {
      if (r.success) {
        this.pipelineTotalPages.set(r.data.totalPages || 1);
        const incidents = r.data.content;
        if (!incidents.length) {
          this.pipelineIncidents.set([]);
          return;
        }
        
        // Fetch logs for these 3 incidents sequentially or parallel. Easiest is to track in an object
        const finalArr = incidents.map(inc => ({ id: inc.id, title: inc.title, logs: [] as AgentLog[], timestamp: inc.createdAt }));
        const pending = finalArr.length;
        let done = 0;
        finalArr.forEach(item => {
          this.incidentService.getLogsByIncident(item.id).subscribe(logRes => {
            if (logRes.success) item.logs = logRes.data;
            if (++done === pending) {
              this.pipelineIncidents.set(finalArr.sort((a,b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()));
            }
          });
        });
      }
    });
  }

  setPipelinePage(page: number) {
    if (page >= 1 && page <= this.pipelineTotalPages()) {
      this.pipelinePage.set(page);
      this.loadPipelineLogs();
    }
  }

  // ── User admin actions ────────────────────────────────────────────────────
  updateUserRole(userId: number, role: string): void {
    this.incidentService.updateUserRole(userId, role).subscribe({
      next: r => {
        if (r.success) {
          this.adminUsers.update(list => list.map(u => u.id === r.data.id ? r.data : u));
          this.showMsg(`User role updated to ${role}`);
        }
      },
      error: () => this.showError('Role update failed'),
    });
  }

  toggleUser(userId: number): void {
    this.incidentService.toggleUserEnabled(userId).subscribe({
      next: r => {
        if (r.success) {
          this.adminUsers.update(list => list.map(u => u.id === r.data.id ? r.data : u));
          this.showMsg(r.message);
        }
      },
      error: () => this.showError('Toggle failed'),
    });
  }

  private userDeleteTimeout: any;
  private userDeleteInterval: any;
  private pendingUserDeletes = new Map<number, { user: AdminUser }>();

  commitUserDelete(userId: number) {
    if (this.userDeleteTimeout && this.undoUserId() === userId) {
      clearTimeout(this.userDeleteTimeout);
      clearInterval(this.userDeleteInterval);
      this.undoUserId.set(null);
    }
    const pending = this.pendingUserDeletes.get(userId);
    if (pending) {
      this.incidentService.deleteUser(userId).subscribe({
        error: () => this.adminUsers.update(l => [pending.user, ...l].sort((a,b) => a.id - b.id))
      });
      this.pendingUserDeletes.delete(userId);
    }
  }

  deleteUser(userId: number, name: string): void {
    const user = this.adminUsers().find(u => u.id === userId);
    if (!user) return;

    if (this.undoUserId() !== null) {
      this.commitUserDelete(this.undoUserId()!);
    }

    this.adminUsers.update(list => list.filter(u => u.id !== userId));
    this.undoUserId.set(userId);
    this.undoUserSeconds.set(10);
    this.pendingUserDeletes.set(userId, { user });

    if (this.userDeleteInterval) clearInterval(this.userDeleteInterval);
    this.userDeleteInterval = setInterval(() => {
      this.undoUserSeconds.update(s => s - 1);
    }, 1000);

    this.userDeleteTimeout = setTimeout(() => {
      this.commitUserDelete(userId);
    }, 10000);
  }

  undoUserDelete() {
    const id = this.undoUserId();
    if (id !== null) {
      clearTimeout(this.userDeleteTimeout);
      clearInterval(this.userDeleteInterval);
      const pending = this.pendingUserDeletes.get(id);
      if (pending) {
         this.adminUsers.update(l => [pending.user, ...l].sort((a,b) => a.id - b.id));
         this.pendingUserDeletes.delete(id);
      }
      this.undoUserId.set(null);
      this.showMsg(`Restored user #${id}`);
    }
  }

  // ── Helpers ───────────────────────────────────────────────────────────────
  getToolMeta(name: string) {
    return TOOL_META[name] ?? { icon: 'fa-wrench', label: name, color: '#8896A9' };
  }
  getToolsForLog(log: AgentLog): string[] {
    return log.toolsCalled ? log.toolsCalled.split(',').map(t => t.trim()).filter(Boolean) : [];
  }
  getNotifIcon(channel: string): string {
    return channel === 'email' ? 'fa-envelope' : channel === 'pushover' ? 'fa-bell' : 'fa-satellite-dish';
  }
  getNotifColor(status: string): string {
    return status === 'sent' ? 'var(--success)' : status === 'failed' ? 'var(--danger)' : 'var(--text-muted)';
  }
  getRoleColor(role: string): string {
    return role === 'ADMIN' ? '#FF4D6D' : role === 'STAFF' ? '#FF6B35' : '#8896A9';
  }

  private showMsg(msg: string): void {
    this.actionMsg.set(msg); this.actionError.set('');
    setTimeout(() => this.actionMsg.set(''), 3000);
  }
  private showError(msg: string): void {
    this.actionError.set(msg); this.actionMsg.set('');
    setTimeout(() => this.actionError.set(''), 4000);
  }

  timeAgo(iso: string): string {
    if (!iso) return '—';
    const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
    if (s < 60)    return `${s}s ago`;
    if (s < 3600)  return `${Math.floor(s/60)}m ago`;
    if (s < 86400) return `${Math.floor(s/3600)}h ago`;
    return new Date(iso).toLocaleDateString();
  }
  formatTime(iso: string): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
}
