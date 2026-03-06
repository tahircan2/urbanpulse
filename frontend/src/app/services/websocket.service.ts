import { Injectable, OnDestroy, inject, NgZone } from '@angular/core';
import { Subject } from 'rxjs';
import { environment } from '../../environments/environment';
import { Incident } from '../models/incident.model';

// SockJS + STOMP loaded via CDN in index.html
declare const SockJS: new (url: string) => unknown;
declare const Stomp: {
  over: (socket: unknown) => StompClient;
};

interface StompClient {
  debug: null | ((msg: string) => void);
  connect: (headers: object, onConnect: () => void, onError: (error: unknown) => void) => void;
  disconnect: (callback?: () => void) => void;
  subscribe: (destination: string, callback: (msg: { body: string }) => void) => { unsubscribe: () => void };
}

@Injectable({ providedIn: 'root' })
export class WebSocketService implements OnDestroy {
  private readonly zone = inject(NgZone);

  private stompClient: StompClient | null = null;
  private connected = false;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  // Typed subjects
  readonly newIncident$     = new Subject<Incident>();
  readonly updatedIncident$ = new Subject<Incident>();
  readonly agentActivity$   = new Subject<string>();

  connect(): void {
    if (this.connected) return;
    try {
      const socket = new SockJS(environment.wsUrl);
      this.stompClient = Stomp.over(socket);
      this.stompClient.debug = null; // suppress verbose console output

      this.stompClient.connect(
        {},
        () => {
          this.connected = true;
          if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
          }

          this.stompClient!.subscribe('/topic/incidents/new', (msg) => {
            this.zone.run(() => {
              try {
                this.newIncident$.next(JSON.parse(msg.body) as Incident);
              } catch { /* ignore malformed messages */ }
            });
          });

          this.stompClient!.subscribe('/topic/incidents/update', (msg) => {
            this.zone.run(() => {
              try {
                this.updatedIncident$.next(JSON.parse(msg.body) as Incident);
              } catch { /* ignore malformed messages */ }
            });
          });

          this.stompClient!.subscribe('/topic/agents/activity', (msg) => {
            this.zone.run(() => this.agentActivity$.next(msg.body));
          });
        },
        () => {
          this.connected = false;
          // Attempt reconnect after 5s
          this.reconnectTimer = setTimeout(() => this.connect(), 5000);
        }
      );
    } catch {
      console.warn('WebSocket not available — running in offline mode');
    }
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.stompClient && this.connected) {
      this.stompClient.disconnect(() => {
        this.connected = false;
      });
    }
    this.connected = false;
  }

  ngOnDestroy(): void {
    this.disconnect();
  }
}
