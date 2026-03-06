import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { IncidentService } from '../../services/incident.service';
import { WebSocketService } from '../../services/websocket.service';
import { Incident, CATEGORY_LABELS, CATEGORY_ICONS, STATUS_LABELS } from '../../models/incident.model';
import { DashboardStats } from '../../models/api.model';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HomeComponent implements OnInit {
  private readonly incidentService = inject(IncidentService);
  private readonly ws              = inject(WebSocketService);
  private readonly destroyRef      = inject(DestroyRef);

  stats           = signal<DashboardStats>({
    total: 0, pending: 0, inProgress: 0, resolved: 0, closed: 0,
    critical: 0, aiProcessed: 0, agentLogsTotal: 0, agentSuccessRate: 0,
  });
  recentIncidents = signal<Incident[]>([]);
  loading         = signal(true);

  readonly CATEGORY_LABELS = CATEGORY_LABELS;
  readonly CATEGORY_ICONS  = CATEGORY_ICONS;
  readonly STATUS_LABELS   = STATUS_LABELS;

  ngOnInit(): void {
    this.ws.connect();
    this.loadData();

    // takeUntilDestroyed auto-unsubscribes — no ngOnDestroy needed
    this.ws.newIncident$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(inc => {
        this.recentIncidents.update(list => [inc, ...list].slice(0, 4));
        this.fetchStats();
      });

    this.ws.updatedIncident$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(inc => {
        this.recentIncidents.update(list => list.map(i => i.id === inc.id ? inc : i));
        this.fetchStats();
      });
  }

  fetchStats() {
    this.incidentService.getDashboardStats().subscribe(res => {
      if (res.success) {
        this.stats.set(res.data);
      }
    });
  }

  loadData(): void {
    this.loading.set(true);
    this.incidentService.getIncidents({ size: 4 })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          if (res.success) {
            this.recentIncidents.set(res.data.content);
          }
          this.fetchStats();
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }

  getPriorityClass(p: number): string {
    if (p >= 5) return 'badge-red';
    if (p >= 4) return 'badge-orange';
    if (p >= 3) return 'badge-yellow';
    return 'badge-cyan';
  }

  getPriorityLabel(p: number): string {
    return ({ 5: 'Critical', 4: 'High', 3: 'Medium', 2: 'Low', 1: 'Minimal' } as Record<number,string>)[p] ?? '';
  }

  getStatusClass(s: string): string {
    return ({
      PENDING: 'badge-yellow', IN_PROGRESS: 'badge-orange',
      RESOLVED: 'badge-green', CLOSED: 'badge-cyan',
    } as Record<string,string>)[s] ?? 'badge-cyan';
  }
}
