import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  inject,
  NgZone,
  OnDestroy,
  signal,
  ViewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import * as L from 'leaflet';
import 'leaflet.markercluster';
import { IncidentService } from '../../services/incident.service';
import { WebSocketService } from '../../services/websocket.service';
import {
  Incident, IncidentStatus,
  CATEGORY_LABELS, CATEGORY_ICONS, STATUS_LABELS, STATUS_CLASSES, PRIORITY_CLASSES
} from '../../models/incident.model';

@Component({
  selector: 'app-map',
  standalone: true,
  imports: [],
  templateUrl: './map.component.html',
  styleUrl: './map.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MapComponent implements AfterViewInit, OnDestroy {
  @ViewChild('mapContainer', { static: true })
  private mapContainer!: ElementRef<HTMLDivElement>;

  private readonly incidentService = inject(IncidentService);
  private readonly ws              = inject(WebSocketService);
  private readonly zone            = inject(NgZone);
  private readonly destroyRef      = inject(DestroyRef);

  readonly CATEGORY_LABELS = CATEGORY_LABELS;
  readonly CATEGORY_ICONS  = CATEGORY_ICONS;
  readonly STATUS_LABELS   = STATUS_LABELS;
  readonly STATUS_CLASSES  = STATUS_CLASSES;
  readonly PRIORITY_CLASSES = PRIORITY_CLASSES;

  readonly incidents    = signal<Incident[]>([]);
  readonly selected     = signal<Incident | null>(null);
  readonly filterStatus = signal<IncidentStatus | 'ALL'>('ALL');

  private map!: L.Map;
  private clusterGroup!: L.MarkerClusterGroup;
  // Map<incidentId, marker> for incremental updates
  private markerMap = new Map<number, L.Marker>();

  ngAfterViewInit(): void {
    // Run Leaflet outside Angular zone — zero CD triggered per map interaction
    this.zone.runOutsideAngular(() => {
      this.initMap();
      this.loadIncidents();
    });

    this.ws.connect();

    // WebSocket: add new markers incrementally
    this.ws.newIncident$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(inc => {
        this.incidents.update(list => [inc, ...list]);
        this.zone.runOutsideAngular(() => this.addMarker(inc));
      });

    this.ws.updatedIncident$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(inc => {
        this.incidents.update(list => list.map(i => i.id === inc.id ? inc : i));
        if (this.selected()?.id === inc.id) {
           this.selected.set(inc);
        }
        this.zone.runOutsideAngular(() => {
           this.removeMarker(inc.id);
           this.addMarker(inc);
        });
      });
  }

  ngOnDestroy(): void {
    if (this.map) this.map.remove();
    this.markerMap.clear();
  }

  private initMap(): void {
    this.map = L.map(this.mapContainer.nativeElement, {
      center: [41.0082, 28.9784],
      zoom: 11,
      zoomControl: false,
      // Performance: prefer canvas renderer for many markers
      preferCanvas: true,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
      // Performance: buffer extra tiles, skip updates during zoom/pan
      keepBuffer: 4,
      updateWhenIdle: true,
      updateWhenZooming: false,
    }).addTo(this.map);

    L.control.zoom({ position: 'topright' }).addTo(this.map);

    // Marker cluster — chunked rendering to avoid jank on 100+ markers
    this.clusterGroup = (L as unknown as { markerClusterGroup: (opts: object) => L.MarkerClusterGroup })
      .markerClusterGroup({
        chunkedLoading: true,
        chunkInterval: 100,
        chunkDelay: 50,
        maxClusterRadius: 60,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true,
      });

    this.map.addLayer(this.clusterGroup);
  }

  private loadIncidents(): void {
    this.incidentService.getIncidents({ size: 200 })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(res => {
        if (!res.success) return;
        const data = res.data.content;
        this.zone.run(() => this.incidents.set(data));
        data.forEach(inc => this.addMarker(inc));
      });
  }

  private getMarkerColor(priority: number): string {
    if (priority >= 5) return '#FF4D6D';
    if (priority >= 4) return '#FF6B35';
    if (priority >= 3) return '#FFB020';
    return '#00D4FF';
  }

  private addMarker(incident: Incident): void {
    if (!this.map || this.markerMap.has(incident.id)) return;

    const color = this.getMarkerColor(incident.priority);
    const icon  = L.divIcon({
      className: '',
      html: `<div style="
        width:30px;height:30px;
        background:${color};
        border-radius:50% 50% 50% 0;
        transform:rotate(-45deg);
        border:2px solid rgba(255,255,255,0.25);
        box-shadow:0 2px 8px ${color}66;
        display:flex;align-items:center;justify-content:center;
      "><div style="transform:rotate(45deg);color:#0A0E1A;font-size:10px;font-weight:700">P${incident.priority}</div></div>`,
      iconSize:   [30, 30],
      iconAnchor: [15, 30],
    });

    const marker = L.marker([incident.latitude, incident.longitude], { icon })
      .on('click', () => {
        // Re-enter Angular zone only on user interaction
        this.zone.run(() => {
          if (this.selected()?.id === incident.id) {
            this.selected.set(null);
          } else {
             this.selected.set(incident);
          }
        });
      });

    this.markerMap.set(incident.id, marker);
    this.clusterGroup.addLayer(marker);
  }

  private removeMarker(id: number): void {
    const marker = this.markerMap.get(id);
    if (marker) {
      this.clusterGroup.removeLayer(marker);
      this.markerMap.delete(id);
    }
  }

  /**
   * Incremental filter: only remove markers not matching, add missing ones.
   * No full clear/rebuild on every filter change.
   */
  setFilter(status: IncidentStatus | 'ALL'): void {
    this.filterStatus.set(status);

    const all      = this.incidents();
    const filtered = status === 'ALL' ? all : all.filter(i => i.status === status);
    const keep     = new Set(filtered.map(i => i.id));

    this.zone.runOutsideAngular(() => {
      // Remove markers no longer matching the filter
      this.markerMap.forEach((_, id) => {
        if (!keep.has(id)) this.removeMarker(id);
      });
      // Add markers now matching but not yet on map
      filtered.forEach(inc => this.addMarker(inc));
    });
  }

  timeAgo(dateStr: string): string {
    const m = Math.floor((Date.now() - new Date(dateStr).getTime()) / 60000);
    if (m < 1)  return 'just now';
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    return h < 24 ? `${h}h ago` : `${Math.floor(h / 24)}d ago`;
  }
}
