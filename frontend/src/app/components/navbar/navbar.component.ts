import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  HostListener,
  inject,
  NgZone,
  OnInit,
  signal,
} from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NavbarComponent implements OnInit {
  readonly auth   = inject(AuthService);
  private readonly zone   = inject(NgZone);
  private readonly destroy = inject(DestroyRef);

  // Expose auth as public for template
  protected readonly authService = this.auth;

  scrolled   = signal(false);
  mobileOpen = signal(false);

  navLinks = [
    { path: '/',          label: 'Home',      icon: 'fa-house',       public: true,  staff: false },
    { path: '/map',       label: 'Live Map',  icon: 'fa-map',         public: true,  staff: false },
    { path: '/report',    label: 'Report',    icon: 'fa-circle-plus', public: false, staff: false },
    { path: '/dashboard', label: 'Dashboard', icon: 'fa-chart-line',  public: false, staff: false },
    { path: '/about',     label: 'About',     icon: 'fa-circle-info', public: true,  staff: false },
  ];

  private rafId = 0;

  ngOnInit(): void {
    // Passive scroll listener outside Angular zone — no CD triggered per scroll
    this.zone.runOutsideAngular(() => {
      const handler = () => {
        // Cancel pending rAF — only run once per frame
        cancelAnimationFrame(this.rafId);
        this.rafId = requestAnimationFrame(() => {
          const shouldScroll = window.scrollY > 20;
          // Only re-enter zone if value actually changed
          if (shouldScroll !== this.scrolled()) {
            this.zone.run(() => this.scrolled.set(shouldScroll));
          }
        });
      };
      window.addEventListener('scroll', handler, { passive: true });

      // Clean up on destroy
      this.destroy.onDestroy(() => {
        window.removeEventListener('scroll', handler);
        cancelAnimationFrame(this.rafId);
      });
    });
  }

  toggleMobile(): void { this.mobileOpen.update(v => !v); }
  logout(): void { this.auth.logout(); this.mobileOpen.set(false); }
}
