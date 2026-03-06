import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';
import { ApiResponse, AdminUser, DashboardStats, PageResponse } from '../models/api.model';
import {
  Incident, IncidentSubmission, IncidentStatus, IncidentCategory,
  CATEGORY_LABELS, CATEGORY_ICONS, STATUS_LABELS, STATUS_CLASSES,
  PRIORITY_LABELS, PRIORITY_CLASSES,
} from '../models/incident.model';
import { AgentLog } from '../models/agent-log.model';

export interface IncidentFilters {
  status?:   IncidentStatus;
  category?: IncidentCategory;
  district?: string;
  agentProcessed?: boolean;
  page?:     number;
  size?:     number;
}

@Injectable({ providedIn: 'root' })
export class IncidentService {
  private readonly http = inject(HttpClient);

  // Expose lookup tables for templates
  readonly CATEGORY_LABELS = CATEGORY_LABELS;
  readonly CATEGORY_ICONS  = CATEGORY_ICONS;
  readonly STATUS_LABELS   = STATUS_LABELS;
  readonly STATUS_CLASSES  = STATUS_CLASSES;
  readonly PRIORITY_LABELS = PRIORITY_LABELS;
  readonly PRIORITY_CLASSES = PRIORITY_CLASSES;

  // Optimistic local cache with Signal
  private readonly _cache = signal<Incident[]>([]);
  readonly incidents = this._cache.asReadonly();

  // ── Incidents ───────────────────────────────────────────────────────────

  getIncidents(filters: IncidentFilters = {}): Observable<ApiResponse<PageResponse<Incident>>> {
    let params = new HttpParams()
      .set('page', String(filters.page ?? 0))
      .set('size', String(Math.min(filters.size ?? 50, 100)));
    if (filters.status)   params = params.set('status',   filters.status);
    if (filters.category) params = params.set('category', filters.category);
    if (filters.district) params = params.set('district', filters.district);
    if (filters.agentProcessed !== undefined) params = params.set('agentProcessed', String(filters.agentProcessed));

    return this.http
      .get<ApiResponse<PageResponse<Incident>>>(`${environment.apiUrl}/incidents`, { params })
      .pipe(tap(res => { if (res.success) this._cache.set(res.data.content); }));
  }

  getIncidentById(id: number): Observable<ApiResponse<Incident>> {
    return this.http.get<ApiResponse<Incident>>(`${environment.apiUrl}/incidents/${id}`);
  }

  submitIncident(req: IncidentSubmission): Observable<ApiResponse<Incident>> {
    return this.http
      .post<ApiResponse<Incident>>(`${environment.apiUrl}/incidents`, req)
      .pipe(tap(res => {
        if (res.success) {
          this._cache.update(list => [res.data, ...list]);
        }
      }));
  }

  // FIX: id is now properly typed as number (was string causing Number() cast everywhere)
  updateStatus(id: number, status: IncidentStatus, notes?: string): Observable<ApiResponse<Incident>> {
    return this.http
      .patch<ApiResponse<Incident>>(
        `${environment.apiUrl}/incidents/${id}/status`,
        { status, notes }
      )
      .pipe(tap(res => {
        if (res.success) {
          this._cache.update(list =>
            list.map(i => i.id === res.data.id ? res.data : i)
          );
        }
      }));
  }

  getCritical(): Observable<ApiResponse<Incident[]>> {
    return this.http.get<ApiResponse<Incident[]>>(`${environment.apiUrl}/incidents/critical`);
  }

  // ── Agent Logs ──────────────────────────────────────────────────────────

  // FIX: Properly typed return instead of any
  getAgentLogs(page = 0, size = 50): Observable<ApiResponse<PageResponse<AgentLog>>> {
    const params = new HttpParams()
      .set('page', String(page))
      .set('size', String(size));
    return this.http.get<ApiResponse<PageResponse<AgentLog>>>(
      `${environment.apiUrl}/agent-logs`, { params }
    );
  }

  getNotificationLogs(page = 0, size = 10): Observable<ApiResponse<PageResponse<AgentLog>>> {
    const params = new HttpParams()
      .set('page', String(page))
      .set('size', String(size));
    return this.http.get<ApiResponse<PageResponse<AgentLog>>>(
      `${environment.apiUrl}/agent-logs/notifications`, { params }
    );
  }

  getLogsByIncident(incidentId: number): Observable<ApiResponse<AgentLog[]>> {
    return this.http.get<ApiResponse<AgentLog[]>>(
      `${environment.apiUrl}/agent-logs/incident/${incidentId}`
    );
  }

  deleteIncident(id: number): Observable<ApiResponse<void>> {
    return this.http
      .delete<ApiResponse<void>>(`${environment.apiUrl}/incidents/${id}`)
      .pipe(tap(res => {
        if (res.success) this._cache.update(list => list.filter(i => i.id !== id));
      }));
  }

  // ── Admin ────────────────────────────────────────────────────────────────

  getAdminUsers(): Observable<ApiResponse<AdminUser[]>> {
    return this.http.get<ApiResponse<AdminUser[]>>(`${environment.apiUrl}/admin/users`);
  }

  updateUserRole(userId: number, role: string): Observable<ApiResponse<AdminUser>> {
    return this.http.patch<ApiResponse<AdminUser>>(
      `${environment.apiUrl}/admin/users/${userId}/role?role=${role}`, {}
    );
  }

  toggleUserEnabled(userId: number): Observable<ApiResponse<AdminUser>> {
    return this.http.patch<ApiResponse<AdminUser>>(
      `${environment.apiUrl}/admin/users/${userId}/toggle`, {}
    );
  }

  deleteUser(userId: number): Observable<ApiResponse<void>> {
    return this.http.delete<ApiResponse<void>>(`${environment.apiUrl}/admin/users/${userId}`);
  }

  // ── Dashboard ───────────────────────────────────────────────────────────

  getDashboardStats(): Observable<ApiResponse<DashboardStats>> {
    return this.http.get<ApiResponse<DashboardStats>>(
      `${environment.apiUrl}/dashboard/stats`
    );
  }

  // ── Helpers ─────────────────────────────────────────────────────────────

  getLocalStats() {
    const list = this._cache();
    return {
      total:       list.length,
      active:      list.filter(i => i.status === 'IN_PROGRESS').length,
      pending:     list.filter(i => i.status === 'PENDING').length,
      resolved:    list.filter(i => i.status === 'RESOLVED' || i.status === 'CLOSED').length,
      critical:    list.filter(i => i.priority >= 4).length,
      aiProcessed: list.filter(i => i.agentProcessed).length,
    };
  }
}
