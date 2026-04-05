import { ChangeDetectionStrategy, Component, inject, signal, effect } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { NavbarComponent } from './components/navbar/navbar.component';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, NavbarComponent],
  template: `
    <app-navbar />
    <main class="page-wrapper">
      <router-outlet />
    </main>

    @if (auth.sessionExpired()) {
      <div class="expired-overlay">
        <div class="expired-modal card">
          <div class="modal-icon"><i class="fas fa-lock"></i></div>
          <h2>Session Expired</h2>
          <p>Oturum süreniz dolmuştur. Güvenliğiniz için çıkış yapılıyor.</p>
          <div class="timer">Redirecting in {{ countdown() }} seconds...</div>
          <div class="progress-bar"><div class="progress-fill" [style.animation-duration.s]="3"></div></div>
        </div>
      </div>
    }
  `,
  styles: [`
    .expired-overlay {
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(10, 14, 26, 0.85); backdrop-filter: blur(8px);
      display: flex; align-items: center; justify-content: center; z-index: 9999;
    }
    .expired-modal {
      width: 400px; max-width: 90%; text-align: center; padding: 2.5rem 2rem;
      animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
    }
    .modal-icon {
      font-size: 3rem; color: #FF4D6D; margin-bottom: 1rem;
    }
    .expired-modal h2 { margin: 0 0 0.5rem 0; font-size: 1.5rem; }
    .expired-modal p { color: var(--text-secondary); margin: 0; font-size: 0.95rem; }
    .timer { margin-top: 1.5rem; font-weight: 500; color: #8896A9; }
    .progress-bar {
      margin-top: 1rem; height: 4px; background: #1C2333; border-radius: 4px; overflow: hidden;
    }
    .progress-fill {
      height: 100%; background: #00D4FF; width: 100%;
      animation: shrink linear forwards;
    }
    @keyframes popIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
    @keyframes shrink { from { width: 100%; } to { width: 0%; } }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent {
  auth = inject(AuthService);
  countdown = signal(3);

  constructor() {
    effect(() => {
      if (this.auth.sessionExpired()) {
        this.startCountdown();
      }
    });
  }

  private startCountdown() {
    this.countdown.set(3);
    const interval = setInterval(() => {
      this.countdown.update(c => c - 1);
      if (this.countdown() <= 0) {
        clearInterval(interval);
        this.auth.executeLogout();
      }
    }, 1000);
  }
}
