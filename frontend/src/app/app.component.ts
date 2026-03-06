import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { NavbarComponent } from './components/navbar/navbar.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, NavbarComponent],
  template: `
    <app-navbar />
    <main class="page-wrapper">
      <router-outlet />
    </main>
  `,
  /*
    AppComponent itself has no dynamic bindings, so OnPush prevents
    the root from ever triggering change detection top-down.
    Children with signals handle their own CD.
  */
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent {}
